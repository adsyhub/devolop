"""Workspace-scoped source review with immutable drafts and explicit signatures."""
from __future__ import annotations
import copy
import json
import tempfile
import uuid
from pathlib import Path
from .answers import answers_from_page_contracts
from .constants import MACHINE_REVIEWER
from .assemble import assemble_paper
from .audit import iter_questions, prepare_paper, review_content_digest, audit_paper
from .errors import ContractError, QualityGateError, SessionError
from .page_contract import validate_page_contract
from .source import source_file, validate_source_manifest
from .util import canonical_json, load_json, sha256_file, utc_now, write_json


class ContentWorkspace:
    def __init__(self, root, database):
        self.root = Path(root).resolve()
        self.database = database
        # 每次 source() 都重读全部清单，一套卷清完要读几万遍同样的文件。
        # 按 (mtime, size) 记住解析结果：文件一变就重读，语义不变，只是不白读。
        self._manifest_cache = {}

    def _sources(self):
        result = []
        for path in sorted((self.root / 'work').glob('*/source-manifest.json')):
            if path.is_symlink() or not path.resolve().is_relative_to(self.root): continue
            try: stat = path.stat()
            except OSError: continue
            key = (stat.st_mtime_ns, stat.st_size)
            cached = self._manifest_cache.get(path)
            if cached and cached[0] == key:
                manifest = cached[1]
            else:
                manifest = load_json(path)
                self._manifest_cache[path] = (key, manifest)
            result.append((path, manifest))
        return result

    def source(self, source_id):
        matches = [(path, manifest) for path, manifest in self._sources() if manifest.get('sourceId') == source_id]
        if len(matches) != 1: raise KeyError(source_id)
        path, manifest = matches[0]
        validate_source_manifest(manifest, path, verify_files=True)
        for item in manifest['files']:
            resolved = source_file(manifest, path, item['role']).resolve()
            if not resolved.is_relative_to(self.root): raise ContractError('Source must be inside this workspace')
        return path, manifest

    def list_sources(self):
        # 列表要能列出坏掉的那一份。工作目录里有一个字段残缺的清单时，这里原来
        # 直接 KeyError，于是整个工作台的来源列表连同首屏一起空白——一份坏文件
        # 让所有好的卷都看不见。缺字段的条目照列，由读取它的人报告它坏在哪。
        return [{'sourceId': m.get('sourceId'), 'session': m.get('session'),
                 'subject': m.get('subject'), 'language': m.get('language'),
                 'inventoryId': m.get('inventoryId'),
                 'expectedForms': m.get('expectedForms', []),
                 'roles': [f.get('role') for f in (m.get('files') or [])]}
                for _, m in self._sources()]

    def _pdf(self, source_id, role):
        import pymupdf
        if role not in {'QUESTION_BOOKLET', 'ANSWER_KEY'}: raise ContractError('Invalid PDF role')
        path, manifest = self.source(source_id)
        pdf = source_file(manifest, path, role)
        doc = pymupdf.open(pdf)
        return path, manifest, pdf, doc

    def _latest(self, source_id, role, page):
        return self.database.connection.execute('SELECT * FROM page_revisions WHERE source_id=? AND role=? AND page_number=? '
                                                'ORDER BY created_at DESC,rowid DESC LIMIT 1', (source_id, role, page)).fetchone()

    def read_page(self, source_id, role, page):
        path, manifest, pdf, doc = self._pdf(source_id, role)
        try:
            if type(page) is not int or not 1 <= page <= doc.page_count: raise ContractError('Page outside source PDF')
            count = doc.page_count
        finally: doc.close()
        row = self._latest(source_id, role, page)
        original = path.parent / 'pages' / f'p{page:04d}-{role.lower()}.json'
        if row:
            contract, revision = json.loads(row['contract_json']), row['id']
        elif original.is_file():
            contract, revision = load_json(original), 'file:' + sha256_file(original)
        else:
            contract = {'schemaVersion': 2, 'page': page, 'sourceFileRole': role, 'blocks': [],
                        'coverage': {'inkRegions': 0, 'accountedRegions': 0, 'regionIds': [], 'accountedRegionIds': []},
                        'issues': [{'code': 'review.pending', 'message': 'This page has not been transcribed or reviewed'}]}
            revision = None
        previous = None
        if row:
            prior = self.database.connection.execute('SELECT contract_json FROM page_revisions WHERE source_id=? AND role=? AND page_number=? '
                'AND id<>? ORDER BY created_at DESC,rowid DESC LIMIT 1', (source_id,role,page,row['id'])).fetchone()
            previous = json.loads(prior[0]) if prior else None
        return {'sourceId':source_id,'role':role,'page':page,'pageCount':count,'revisionId':revision,
                'contract':contract,'previousContract':previous,'signedBy':row['signed_by'] if row else None,
                'signedAt':row['signed_at'] if row else None,
                'actorKind':row['actor_kind'] if row else None,
                'authoredBy':row['authored_by'] if row else None,
                'validation':validate_page_contract(contract)}

    def page_image(self, source_id, role, page):
        _, _, _, doc = self._pdf(source_id, role)
        try:
            if not 1 <= page <= doc.page_count: raise ContractError('Page outside source PDF')
            import pymupdf
            return doc[page-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes('png')
        finally: doc.close()

    def save_page(self, source_id, role, page, contract, base_revision, *, withdrawal_reason=None, reviewer=None):
        if withdrawal_reason is not None and (not isinstance(withdrawal_reason,str) or not 3<=len(withdrawal_reason.strip())<=2000 or not isinstance(reviewer,str) or not 1<=len(reviewer.strip())<=100):
            raise ContractError('Withdrawal requires a reviewer and a reason of 3 to 2000 characters')
        if not isinstance(contract, dict) or len(canonical_json(contract)) > 1_500_000: raise ContractError('Invalid page contract')
        path, manifest = self.source(source_id)
        source_hash = next(f['sha256'] for f in manifest['files'] if f['role'] == role)
        current = self.read_page(source_id, role, page)
        if contract.get('page') != page or contract.get('sourceFileRole') != role: raise ContractError('Page identity cannot be changed')
        contract = copy.deepcopy(contract)
        for key in ['reviewedBy','reviewedAt']: contract.pop(key, None)
        contract['sourceFileHash'] = source_hash
        with self.database._transaction():
            latest = self._latest(source_id, role, page)
            actual = latest['id'] if latest else current['revisionId']
            if base_revision != actual: raise SessionError('Review page changed; reload before saving')
            if withdrawal_reason is not None and (not latest or not latest['signed_by']):raise SessionError('Only the current signed page can be withdrawn')
            now, rid = utc_now(), 'pr_' + uuid.uuid4().hex
            author = (reviewer or '').strip() or None
            kind = None if author is None else ('SYSTEM' if author == MACHINE_REVIEWER else 'HUMAN')
            self.database.connection.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?)',
                (source_id,manifest['rights']['status'],canonical_json(manifest),now))
            self.database.connection.execute(
                'INSERT INTO page_revisions (id,run_id,source_id,page_number,role,contract_json,signed_by,signed_at,created_at,actor_kind,authored_by) VALUES (?,NULL,?,?,?,?,NULL,NULL,?,?,?)',
                (rid,source_id,page,role,canonical_json(contract),now,kind,author))
            if latest and latest['signed_by']:
                self._revoke_page_certificates(latest['id'], withdrawal_reason or 'Page edited')
            if withdrawal_reason is not None:
                self.database.connection.execute('INSERT INTO review_decisions VALUES (?,?,?,?,?,?,?)',
                    ('rd_'+uuid.uuid4().hex,latest['id'],reviewer.strip(),'WITHDRAWN',withdrawal_reason.strip(),canonical_json({'draftRevisionId':rid}),now))
        return self.read_page(source_id, role, page)

    def withdraw_page(self,source_id,role,page,revision_id,reviewer,reason):
        if reason is None:raise ContractError('Withdrawal reason is required')
        current=self.read_page(source_id,role,page)
        return self.save_page(source_id,role,page,current['contract'],revision_id,withdrawal_reason=reason,reviewer=reviewer)

    def sign_page(self, source_id, role, page, revision_id, reviewer, confirmed):
        if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer)>100 or confirmed is not True:
            raise ContractError('Reviewer and explicit source comparison confirmation are required')
        current = self.read_page(source_id,role,page)
        contract = current['contract']
        if validate_page_contract(contract)['status'] != 'passed' or contract.get('issues'):
            raise QualityGateError('Resolve all contract issues before signing')
        if not contract.get('blocks'):
            raise QualityGateError('Blank/instruction pages require an explicit ignored or instruction block and reason')
        if any(b.get('kind')=='ignored' and not b.get('reason') for b in contract['blocks']):
            raise QualityGateError('Ignored regions need a reason')
        if not contract.get('sourceFileHash'): raise QualityGateError('Save this candidate before signing')
        # 人的签名取代机器证明，不继承它。coverage 里的区域证据性质留着，
        # 因为那是关于这份合约怎么来的事实，签名并不改变它。
        contract=copy.deepcopy(contract);contract.pop('attestation',None)
        coverage=contract.get('coverage',{})
        if contract.get('needsReview') or contract.get('schemaVersion') != 2 or not isinstance(coverage.get('regionIds'),list):
            raise QualityGateError('Current region evidence is required before signing')
        regions=[]
        for block in contract['blocks']:
            refs=block.get('regionIds',[block.get('regionId')] if block.get('regionId') else [])
            if not refs: raise QualityGateError('Every block requires its source region identity')
            regions.extend(refs)
        if len(regions)!=len(set(regions)) or set(regions)!=set(coverage['regionIds']):
            raise QualityGateError('Every source region must have exactly one block disposition')

        with self.database._transaction():
            row=self._latest(source_id,role,page)
            if not row or row['id'] != revision_id: raise SessionError('Review revision changed')
            rid,now='pr_'+uuid.uuid4().hex,utc_now()
            self.database.connection.execute(
                'INSERT INTO page_revisions (id,run_id,source_id,page_number,role,contract_json,signed_by,signed_at,created_at,actor_kind,authored_by) VALUES (?,NULL,?,?,?,?,?,?,?,?,?)',
                (rid,source_id,page,role,canonical_json(contract),reviewer.strip(),now,now,'HUMAN',reviewer.strip()))
            self.database.connection.execute('INSERT INTO review_decisions VALUES (?,?,?,?,?,?,?)',
                ('rd_'+uuid.uuid4().hex,rid,reviewer.strip(),'APPROVED','Source compared',canonical_json({'previousRevision':revision_id}),now))
        return self.read_page(source_id,role,page)

    def attest_page(self, source_id, role, page, revision_id):
        """Record a machine attestation for a page the pipeline fully verified.

        This is not a signature and does not pretend to be one. A signature says
        a person compared the page with the scan; an attestation says the
        pipeline checked the things a pipeline can check — the text is verbatim
        from this page's OCR, the answer comes from the official 正解表, the
        answer is one of the options that were read — and records, in the page
        itself, that page geometry was *not* verified.

        The distinction is kept in the data: ``signed_by`` carries the machine
        identity, the decision is ``MACHINE_ATTESTED`` rather than ``APPROVED``,
        and the attestation has to re-derive from the stored contract before
        anything is written. A person signing the same page afterwards supersedes
        it through the ordinary :meth:`sign_page` path.
        """
        from .ocr.attested_contracts import GRADE, verify_attestation
        current=self.read_page(source_id,role,page)
        contract=current['contract']
        if validate_page_contract(contract)['status'] != 'passed':
            raise QualityGateError('Page contract does not pass validation')
        # 证明引用的 OCR 产物就在来源清单旁边的工作目录里。不把它交给验证器，
        # 「证据摘要」就只是个没人回读的字段。
        manifest_path,_manifest=self.source(source_id)
        problems=verify_attestation(contract,work_dir=manifest_path.parent)
        if problems:
            raise QualityGateError('Machine attestation does not hold: '+'; '.join(problems))
        if not contract.get('sourceFileHash'):
            raise QualityGateError('Save this candidate before attesting it')
        if not contract.get('blocks'):
            raise QualityGateError('An attested page needs an explicit block disposition')
        if any(b.get('kind')=='ignored' and not b.get('reason') for b in contract['blocks']):
            raise QualityGateError('Ignored regions need a reason')
        with self.database._transaction():
            row=self._latest(source_id,role,page)
            if not row or row['id'] != revision_id: raise SessionError('Review revision changed')
            rid,now='pr_'+uuid.uuid4().hex,utc_now()
            self.database.connection.execute(
                'INSERT INTO page_revisions (id,run_id,source_id,page_number,role,contract_json,signed_by,signed_at,created_at,actor_kind,authored_by) VALUES (?,NULL,?,?,?,?,?,?,?,?,?)',
                (rid,source_id,page,role,canonical_json(contract),MACHINE_REVIEWER,now,now,'SYSTEM',MACHINE_REVIEWER))
            self.database.connection.execute('INSERT INTO review_decisions VALUES (?,?,?,?,?,?,?)',
                ('rd_'+uuid.uuid4().hex,rid,MACHINE_REVIEWER,'MACHINE_ATTESTED',
                 f'Machine-verified ({GRADE}); page geometry not verified, no human comparison',
                 canonical_json({'previousRevision':revision_id,'attestation':contract['attestation']}),now))
        return self.read_page(source_id,role,page)

    def page_review_grades(self, source_id, page_revision_ids):
        """How each page of a release was cleared: by a person or by the machine."""
        if not page_revision_ids: return {}
        rows=self.database.connection.execute(
            'SELECT id,signed_by FROM page_revisions WHERE id IN ('
            +','.join('?' for _ in page_revision_ids)+')',list(page_revision_ids)).fetchall()
        return {row['id']: ('MACHINE_ATTESTED' if row['signed_by']==MACHINE_REVIEWER else 'HUMAN_SIGNED')
                for row in rows}

    def _assemble_cleared(self, source_id, path, manifest, partial):
        """Assemble a paper from the pages that are currently cleared for release.

        Cleared means a current revision with a signer on it — a person through
        :meth:`sign_page` or the pipeline through :meth:`attest_page`. This is
        the one place a release is built, so :meth:`candidate` and
        :meth:`proposed_structure` cannot drift apart about question order.
        """
        required={'QUESTION_BOOKLET','ANSWER_KEY'}
        if not required <= {f['role'] for f in manifest['files']}: raise QualityGateError('Question and independent answer PDF are required')
        pages,counts,revision_ids=[],{},[]
        for role in sorted(required):
            _,_,_,doc=self._pdf(source_id,role)
            try: counts[role]=doc.page_count
            finally: doc.close()
            for number in (partial["pages"][role] if partial else range(1,counts[role]+1)):
                row=self._latest(source_id,role,number)
                if not row or not row['signed_by']: raise QualityGateError(f'{role} page {number} has no current signed revision')
                page=json.loads(row['contract_json'])
                expected=next(f['sha256'] for f in manifest['files'] if f['role']==role)
                if page.get('sourceFileHash')!=expected: raise QualityGateError('Signed page source hash is stale')
                pages.append(page);revision_ids.append(row['id'])
        with tempfile.TemporaryDirectory(prefix='eju-reviewed-') as temp:
            root=Path(temp)
            for page in pages: write_json(root/f"p{page['page']:04d}-{page['sourceFileRole'].lower()}.json",page)
            ledger=answers_from_page_contracts(root)
            needed={str(b.get('formCode'))+'|'+str(b.get('answerRef')) for p in pages if p['sourceFileRole']=='QUESTION_BOOKLET' for b in p['blocks'] if b.get('kind') in {'question','writing-prompt'}}
            ledger_keys=sorted(ledger['entries'])
            excluded=[key for key,value in ledger['entries'].items() if key not in needed]
            ledger['entries']={key:value for key,value in ledger['entries'].items() if key not in excluded}
            write_json(root/'answers.json',ledger)
            paper=assemble_paper(manifest_path=path,pages_dir=root,answer_ledger_path=root/'answers.json',output_path=root/'paper.json')
        self._last_ledger_keys=ledger_keys
        return counts,revision_ids,excluded,paper

    def proposed_structure(self, source_id, *, cleared_pages, expected_forms, form_refs=None):
        """Derive a structure baseline from the pages currently cleared for release.

        The baseline has to state two different things and must not confuse them:
        ``forms`` is what the source *contains*, evidenced by the 正解表 — every
        answer slot the key prints for each of this source's forms; while
        ``reviewedScope.forms`` is what this release actually carries, in the
        order the assembler produced. Every key entry with no question behind it
        is listed in ``excludedAnswerRefs`` with the reason, so a partial release
        says out loud what it is missing instead of looking complete.
        """
        path,manifest=self.source(source_id)
        partial={'pages':{role:sorted(pages) for role,pages in cleared_pages.items()}}
        counts,revision_ids,excluded,paper=self._assemble_cleared(source_id,path,manifest,partial)
        all_keys=list(getattr(self,'_last_ledger_keys',[]))
        forms={}
        for key in all_keys:
            form,_,ref=str(key).partition('|')
            forms.setdefault(form,[]).append(ref)
        for form in expected_forms:
            # 正解表没覆盖到这个 form（整段没读出来）时，结构仍然可以照实描述：
            # 题册上那些题印着自己的解答欄号，这些欄号存在是有证据的，只是答案没读到。
            # 两者都空，这份卷才真的无从描述。
            if not forms.get(form):
                refs=[q.get('answerRef') or q['questionId'] for f,_,q in iter_questions(paper)
                      if f.get('formCode')==form]
                refs=refs or list((form_refs or {}).get(form) or [])
                if refs: forms[form]=sorted(set(refs))
        forms={f:sorted(set(refs)) for f,refs in forms.items() if f in set(expected_forms)}
        actual={f['formCode']:[q.get('answerRef') or q['questionId']
                               for ff,_,q in iter_questions(paper) if ff is f] for f in paper['forms']}
        carried={ref for refs in actual.values() for ref in refs}
        excluded_reasons={}
        for key in excluded:
            form,_,ref=str(key).partition('|')
            excluded_reasons[key]=(
                f'正解表给出了 {ref} 的答案，但题册里对应的题目没有通过核验'
                '（未读到解答欄号、选项与答案不符，或题干未读到），本次发布不收录。')
        missing=[]
        for form in sorted(forms):
            absent=[r for r in forms[form] if r not in carried]
            if absent:
                missing.append(f'{form}：正解表列出 {len(forms[form])} 个解答欄，'
                               f'本次发布收录 {len(forms[form])-len(absent)} 个，'
                               f'其余 {len(absent)} 个的题目未通过核验。')
        if not missing:
            missing.append('本次发布收录了正解表列出的全部解答欄。')
        return {
            'forms':forms,'pages':counts,
            'reviewedScope':{
                'pages':partial['pages'],'forms':actual,
                'missingReasons':missing,'excludedAnswerRefs':excluded_reasons,
            },
        },paper,revision_ids

    def candidate(self, source_id, scope="FULL"):
        path, manifest = self.source(source_id)
        from .inventory import get_inventory_item
        inventory_id=manifest.get('inventoryId')
        item=get_inventory_item(inventory_id,self.root/'content/content-inventory.json') if inventory_id else None
        if not item or any(item[k]!=manifest[k] for k in ['session','subject','language']):
            raise QualityGateError('Bind this source to its exact inventory item before assembling a release')
        if scope not in {'FULL','REVIEWED_PARTIAL'}:raise ContractError('Invalid review scope')
        structure_row=self.database.connection.execute('SELECT id,structure_json FROM source_structure_revisions WHERE source_id=? ORDER BY revision DESC LIMIT 1',(source_id,)).fetchone()
        if not structure_row:raise QualityGateError('An independent signed source structure baseline is required')
        structure=json.loads(structure_row['structure_json'])
        partial=structure.get('reviewedScope') if scope=='REVIEWED_PARTIAL' else None
        if scope=='REVIEWED_PARTIAL' and not partial:raise QualityGateError('Sign an explicit reviewed scope and missing-content reasons before partial release')
        counts,revision_ids,excluded,paper=self._assemble_cleared(source_id,path,manifest,partial)
        paper['contentKind']='SOURCE'
        row=self.database.connection.execute('SELECT id,structure_json FROM source_structure_revisions WHERE source_id=? ORDER BY revision DESC LIMIT 1',(source_id,)).fetchone()
        if not row: raise QualityGateError('An independent signed source structure baseline is required')
        baseline=json.loads(row['structure_json'])
        if set(baseline['forms']) != set(item['expectedForms']):raise QualityGateError('Source structure baseline forms do not match the bound inventory item')
        actual={f['formCode']:[q.get('answerRef') or q['questionId'] for ff,_,q in iter_questions(paper) if ff is f] for f in paper['forms']}
        if (partial['forms'] if partial else baseline['forms'])!=actual or baseline['pages']!=counts:
            raise QualityGateError('Assembled forms, question order or physical pages mismatch source structure baseline')
        if baseline.get('sourceHashes')!={f['role']:f['sha256'] for f in manifest['files']}:
            raise QualityGateError('Source structure baseline file hashes are stale')
        if set(excluded)!=set((partial or baseline).get('excludedAnswerRefs',{})):
            raise QualityGateError('Excluded answers need explicit reasons in the source structure baseline')
        paper['expectedStructure']={**baseline,'structureRevisionId':row['id']}
        paper['reviewScope']=scope
        previous=self.database.connection.execute("SELECT pv.paper_id,pv.payload_json FROM paper_versions pv JOIN sources s ON json_extract(pv.payload_json,'$.source.sourceId')=s.id WHERE s.id=? ORDER BY pv.version_number DESC LIMIT 1",(source_id,)).fetchone()
        if previous:
            old=json.loads(previous['payload_json']);paper['paperId']=previous['paper_id'];paper['stableCode']=old['stableCode']
        paper['syllabusId']=item['syllabusId']
        paper['sections']=baseline.get('sections',[])
        paper['audioTracks']=[{'trackId':r['id'],'assetId':r['asset_id'],'durationMs':r['duration_ms'],'cues':json.loads(r['cues_json'])} for r in self.database.connection.execute("SELECT * FROM audio_tracks WHERE source_id=? AND status='REVIEWED' ORDER BY created_at,id",(source_id,))]
        # All page evidence is accounted for; final reviewer still confirms the assembled structure.
        paper['completeness']='COMPLETE';paper['availableModes']=['PRACTICE']
        if paper['sections']: paper['availableModes'].append('SECTION')
        if baseline.get('rulesReviewed') and baseline.get('ruleEvidence'): paper['availableModes'].append('MOCK')
        if manifest['subject']=='JAPANESE':
            # The reviewed audio segments are usable for practice; the complete
            # Japanese section timing policy still needs its own state machine.
            paper['availableModes']=[mode for mode in paper['availableModes'] if mode!='MOCK']
            listening={q.get('answerRef') for _,_,q in iter_questions(paper) if q.get('sectionCode') in {'LISTENING','LISTENING_READING'}}
            mapped={ref for track in paper['audioTracks'] for cue in track['cues'] if cue.get('assetId') for ref in cue.get('questionRefs',[])}
            if not paper['audioTracks'] or not listening<=mapped:
                paper['completeness']='PARTIAL';paper['availableModes']=['PRACTICE'] + (['SECTION'] if paper['sections'] else [])
        if partial:
            paper['completeness']='PARTIAL';paper['availableModes']=['PRACTICE'];paper['missingContentReasons']=partial['missingReasons']
            paper['sections']=[section for section in paper['sections'] if set(section['questionRefs'])<=set(partial['forms'].get(section['formCode'],[]))]
            if paper['sections']:paper['availableModes'].append('SECTION')
        grades=set(self.page_review_grades(source_id,revision_ids).values())
        # 一份卷的把关程度由它最弱的那一页决定，并且一路带到学习者界面。
        paper['reviewGrade']=('MIXED' if len(grades)>1 else (grades.pop() if grades else 'HUMAN_SIGNED'))
        return {'paper':prepare_paper(paper),'pageRevisionIds':revision_ids,'excludedOtherFormAnswerRefs':excluded}

    def sign_source_structure(self, source_id, structure, reviewer):
        from .schema_validation import require_schema
        from .constants import FORM_SPECS
        require_schema('source-structure',structure)
        if not isinstance(reviewer,str) or not reviewer.strip() or len(reviewer)>100: raise ContractError('Reviewer is required')
        path,manifest=self.source(source_id)
        if not set(structure['forms']) <= set(FORM_SPECS): raise ContractError('Unknown form in baseline')
        for role,count in structure['pages'].items():
            _,_,_,doc=self._pdf(source_id,role)
            try:
                if doc.page_count!=count: raise ContractError('Baseline must account for all physical source pages')
            finally: doc.close()
        partial=structure.get('reviewedScope')
        if partial is not None:
            if not isinstance(partial,dict) or not isinstance(partial.get('forms'),dict) or not partial['forms'] or not isinstance(partial.get('missingReasons'),list) or not partial['missingReasons'] or not all(isinstance(r,str) and r.strip() for r in partial['missingReasons']):raise ContractError('Partial scope requires forms and missing-content reasons')
            if not isinstance(partial.get('pages'),dict) or set(partial['pages'])!={'QUESTION_BOOKLET','ANSWER_KEY'}:raise ContractError('Partial scope requires question and answer page selections')
            for role,pages in partial['pages'].items():
                if not isinstance(pages,list) or not pages or any(type(n) is not int or not 1<=n<=structure['pages'][role] for n in pages) or len(set(pages))!=len(pages):raise ContractError('Invalid partial page scope')
            for code,refs in partial['forms'].items():
                if not isinstance(refs,list) or not refs or any(not isinstance(ref,str) for ref in refs) or len(set(refs))!=len(refs) or not set(refs)<=set(structure['forms'].get(code,[])):raise ContractError('Partial references must belong to the full source baseline')
        section_ids=set()
        for section in structure.get('sections',[]):
            if section['sectionId'] in section_ids or not set(section['questionRefs'])<=set(structure['forms'].get(section['formCode'],[])):
                raise ContractError('Invalid section identity or question references')
            section_ids.add(section['sectionId'])
        structure=copy.deepcopy(structure)
        structure['sourceHashes']={f['role']:f['sha256'] for f in manifest['files']}
        # 内容和依赖都没变时，重签必须是空操作。原来每次都插一版新基线，并撤销这个
        # 来源上所有整卷证书 —— 一次什么都没改的重跑就把已发布的卷全挂起了，于是
        # "重跑一遍看看"和"把题库下架"是同一个动作。
        # 比较用的是规范化后的业务字段：proposed_structure 不含时间戳，同样的输入
        # 得到逐字相同的结构。
        existing=self.database.connection.execute(
            'SELECT * FROM source_structure_revisions WHERE source_id=? ORDER BY revision DESC LIMIT 1',
            (source_id,)).fetchone()
        if existing and existing['structure_json']==canonical_json(structure):
            return {'structureRevisionId':existing['id'],'revision':existing['revision'],
                    'signedBy':existing['signed_by'],'signedAt':existing['signed_at'],
                    'unchanged':True}
        now=utc_now();rid='ssr_'+uuid.uuid4().hex
        with self.database._transaction():
            self.database.connection.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?)',(source_id,manifest['rights']['status'],canonical_json(manifest),now))
            rev=self.database.connection.execute('SELECT COALESCE(MAX(revision),0)+1 FROM source_structure_revisions WHERE source_id=?',(source_id,)).fetchone()[0]
            self.database.connection.execute('INSERT INTO source_structure_revisions VALUES (?,?,?,?,?,?,?)',(rid,source_id,rev,canonical_json(structure),reviewer.strip(),now,now))
            for review in self.database.connection.execute('SELECT id,page_revision_ids_json FROM paper_reviews WHERE source_id=?',(source_id,)).fetchall():
                self.database.connection.execute('INSERT OR IGNORE INTO paper_review_revocations VALUES (?,?,?,?)',(review['id'],reviewer.strip(),'Source structure baseline changed',now))
                for page_id in json.loads(review['page_revision_ids_json']): self._revoke_page_certificates(page_id,'Source structure baseline changed')
        return {'structureRevisionId':rid,'revision':rev,'signedBy':reviewer.strip(),'signedAt':now}

    def read_source_structure(self, source_id):
        self.source(source_id)
        row = self.database.connection.execute(
            'SELECT * FROM source_structure_revisions WHERE source_id=? ORDER BY revision DESC LIMIT 1',
            (source_id,)).fetchone()
        if not row:
            return {'structure': None}
        return {'structure': json.loads(row['structure_json']), 'structureRevisionId': row['id'],
                'revision': row['revision'], 'signedBy': row['signed_by'], 'signedAt': row['signed_at']}

    def approve_paper(self, source_id, content_digest, reviewer, confirmed, scope="FULL"):
        if not isinstance(reviewer,str) or not reviewer.strip() or confirmed is not True: raise ContractError('Final review confirmation is required')
        candidate=self.candidate(source_id,scope);paper=candidate['paper']
        digest=review_content_digest(paper)
        if content_digest!=digest: raise SessionError('Candidate changed; review the latest assembled paper')
        rid,now='rev_'+uuid.uuid4().hex,utc_now()
        paper['reviewSummary']={'status':'REVIEWED','reviewId':rid,'contentDigest':digest,'reviewedBy':reviewer.strip(),'reviewedAt':now}
        paper=prepare_paper(paper)
        report=audit_paper(paper)
        if report['status']!='passed': raise QualityGateError('Assembled candidate does not pass publication audit')
        with self.database._transaction():
            latest_ids=[self._latest(source_id,json.loads(row['contract_json'])['sourceFileRole'],row['page_number'])['id'] for row in
                        self.database.connection.execute('SELECT * FROM page_revisions WHERE id IN ('+','.join('?' for _ in candidate['pageRevisionIds'])+')',candidate['pageRevisionIds']).fetchall()]
            if set(latest_ids)!=set(candidate['pageRevisionIds']): raise SessionError('Page review changed during approval')
            latest_baseline=self.database.connection.execute('SELECT id FROM source_structure_revisions WHERE source_id=? ORDER BY revision DESC LIMIT 1',(source_id,)).fetchone()
            if latest_baseline['id']!=paper['expectedStructure']['structureRevisionId']: raise SessionError('Source structure changed during approval')
            self.database.connection.execute('INSERT INTO paper_reviews VALUES (?,?,?,?,?,?,?,?)',
                (rid,source_id,digest,'APPROVED',reviewer.strip(),canonical_json(paper),canonical_json(candidate['pageRevisionIds']),now))
        return {'reviewId':rid,'paper':paper,'audit':report}

    def publish_review(self, review_id, channel):
        row=self.database.connection.execute('SELECT * FROM paper_reviews WHERE id=?',(review_id,)).fetchone()
        if not row: raise KeyError(review_id)
        self.source(row['source_id'])
        paper=json.loads(row['payload_json'])
        self.database.verify_paper_review(paper)
        result=self.database.publish(paper,channel=channel)
        self.sync_publications()
        return result

    def sync_publications(self):
        inventory_path=self.root/'content/content-inventory.json'
        if not inventory_path.is_file(): return
        from .inventory import load_inventory,save_inventory
        for event in self.database.connection.execute("SELECT * FROM publication_outbox WHERE status='PENDING' ORDER BY created_at,id").fetchall():
            with self.database._transaction():
                current=self.database.connection.execute('SELECT status FROM publication_outbox WHERE id=?',(event['id'],)).fetchone()
                if current['status']!='PENDING':continue
                data=load_inventory(inventory_path)
                matches=[item for item in data['items'] if item['inventoryId']==event['inventory_id']]
                if len(matches)!=1: continue
                matches[0].update(json.loads(event['payload_json']))
                save_inventory(data,inventory_path)
                self.database.connection.execute("UPDATE publication_outbox SET status='SYNCED' WHERE id=?",(event['id'],))

    def _revoke_page_certificates(self, page_revision_id, reason):
        for row in self.database.connection.execute('SELECT * FROM paper_reviews').fetchall():
            if page_revision_id not in json.loads(row['page_revision_ids_json']): continue
            self.database.connection.execute('INSERT OR IGNORE INTO paper_review_revocations VALUES (?,?,?,?)',
                (row['id'],'system',reason,utc_now()))
            for version in self.database.connection.execute('SELECT id,payload_json FROM paper_versions').fetchall():
                if json.loads(version['payload_json']).get('reviewSummary',{}).get('reviewId')==row['id']:
                    self.database.connection.execute("INSERT INTO paper_delivery_state VALUES (?,'SUSPENDED',?,?) ON CONFLICT(paper_version_id) DO UPDATE SET state='SUSPENDED',note=excluded.note,updated_at=excluded.updated_at", (version['id'],reason,utc_now()))
