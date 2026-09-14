"""Plan settings and a deduplicated, recoverable today queue."""
from __future__ import annotations
import copy
import hashlib
import json
from lexicon_exercise import source_ref, capabilities, questions_for


class LexiconLearning:
    def __init__(self,store,lexicon):self.store=store; self.lexicon=lexicon

    def settings(self,deck_id):
        with self.store.lock:
            row=self.store.connection.execute('SELECT settings_json FROM lex_deck_settings WHERE deck_id=?',(deck_id,)).fetchone()
        return json.loads(row[0]) if row else {'quotaUnit':'card'}

    def save_settings(self,deck_id,payload):
        settings=self.settings(deck_id)
        for key in ('packSlugs','unitIds','sourceRefs','promptTypes','quotaUnit','paused','autoInclude'):
            if key in payload:settings[key]=payload[key]
        if settings.get('quotaUnit','card') not in {'entry','card'}:raise ValueError('每日额度单位无效。')
        for key in ('packSlugs','unitIds','sourceRefs','promptTypes'):
            if key in settings and (not isinstance(settings[key],list) or len(settings[key])>2000 or any(not isinstance(v,str) for v in settings[key])):raise ValueError('计划范围无效。')
        from lexicon_exercise import TYPES
        if any(t not in TYPES for t in settings.get('promptTypes',[])):raise ValueError('学习卡片方向无效。')
        # A fixed plan needs the membership it was created with, not a filter re-evaluated
        # against whatever the pack contains later (LEX-07, §7.2).
        if settings.get('autoInclude') is False and 'memberRefs' not in settings:
            settings['memberRefs']=sorted(self._scoped_refs(settings))
        if settings.get('autoInclude') is not False:
            settings.pop('memberRefs',None)
        with self.store.atomic():
            self.store.connection.execute('INSERT OR REPLACE INTO lex_deck_settings VALUES (?,?)',(deck_id,json.dumps(settings,ensure_ascii=False)))
        return settings

    def update_plan(self,deck_id,body):
        """Apply a whole plan edit at once.

        Settings, the deck row and the candidate refresh are one change as far as the
        learner is concerned, so a failure in any of them leaves none of them applied
        (§7.3). Previously the settings were already committed when the refresh failed.
        """
        with self.store.atomic():
            self.save_settings(deck_id,body)
            self.store.update_deck(deck_id,body)
            self.store.sync_deck_pack(deck_id,self.pack(deck_id))
        return self.detail(deck_id)

    @staticmethod
    def unit_ref(pack,entry):
        """Units are only unique inside their pack; a bare `u1` matches across packs."""
        return f"{pack['packId']}#{entry.get('unitId','')}"

    def _unit_selected(self,settings,pack,entry):
        selected=settings.get('unitIds') or []
        if not selected:return True
        unit=str(entry.get('unitId') or '')
        return self.unit_ref(pack,entry) in selected or (unit in selected and '#' not in ''.join(selected))

    def _scoped_refs(self,settings):
        """Every entry the plan's filters select right now."""
        refs=set()
        for identifier in settings.get('packSlugs') or []:
            pack=self.lexicon.find_pack(identifier)
            if not pack or pack.get('quality',{}).get('blocked'):continue
            for entry in pack['entries']:
                if not self._unit_selected(settings,pack,entry):continue
                ref=source_ref(pack,entry)
                if settings.get('sourceRefs') and ref not in settings['sourceRefs']:continue
                refs.add(ref)
        return refs

    def detail(self,deck_id):
        deck=self.store.get_deck(deck_id); deck['settings']=self.settings(deck_id)
        deck['learningDay']=self.store.learning_day(deck.get('studyTimezone','UTC'))
        with self.store.lock:
            counts=self.store.connection.execute("SELECT COUNT(DISTINCT source_ref),COUNT(DISTINCT CASE WHEN introduced_at<>'' THEN source_ref END) FROM lex_deck_cards WHERE deck_id=?",(deck_id,)).fetchone()
        deck['progress'].update({'entryTotal':counts[0],'entriesIntroduced':counts[1]})
        return deck

    def pack(self,deck_id):
        deck=self.store.get_deck(deck_id); settings=self.settings(deck_id)
        identifiers=settings.get('packSlugs') or [deck['packId']]
        combined=None; entries=[]
        for identifier in identifiers:
            pack=self.lexicon.find_pack(identifier)
            if not pack:raise ValueError('来源包不可用；已有卡片仍可复习。')
            if pack.get('quality',{}).get('blocked'):raise ValueError('内容包未通过质量审计。')
            if combined is None:combined=copy.deepcopy(pack)
            members=settings.get('memberRefs')
            for entry in pack['entries']:
                if not self._unit_selected(settings,pack,entry):continue
                ref=source_ref(pack,entry)
                if settings.get('sourceRefs') and ref not in settings['sourceRefs']:continue
                # autoInclude=false froze the membership at creation; new entries in the
                # source do not join it, though existing members still track revisions.
                if members is not None and ref not in members:continue
                entry=copy.deepcopy(entry)
                templates=entry.get('cardTemplates',[])
                if settings.get('promptTypes'):
                    selected=settings['promptTypes']
                    templates=[t for t in templates if t.get('promptType') in selected]
                    # A direction the plan offers must resolve to a real card. Directions the
                    # adapter can build but the pack never wrote a template for (production,
                    # reading) used to create a plan with zero cards (LEX-01 §4.3, LEX-07).
                    covered={(t.get('promptType'),t.get('variantKey','default')) for t in templates}
                    for question in questions_for(pack,entry):
                        target=question['reviewTarget']; identity=(target['promptType'],target['variantKey'])
                        if target['promptType'] not in selected or identity in covered:continue
                        covered.add(identity)
                        # Carry the question itself: a reading card served by the plan has no
                        # authored template to render, and reviewing it as a flip card would
                        # drop the direction the learner chose (LEX-01 §4.3).
                        templates.append({'promptType':target['promptType'],'variantKey':target['variantKey'],
                                          'exerciseType':question['type'],'questionId':question['id'],
                                          'exercise':question})
                elif settings.get('quotaUnit')=='entry':
                    preferred='cloze' if entry['kind']=='grammar' and any(t.get('promptType')=='cloze' for t in templates) else 'recall'
                    templates=[t for t in templates if t.get('promptType')==preferred][:1]
                if settings.get('quotaUnit')=='entry':
                    available=capabilities(pack,entry)['types']
                    templates=[t for t in templates if t.get('promptType') in available]
                entry.update({'_sourcePackId':pack['packId'],'_packSlug':pack.get('slug',pack['packId']),'_packTitle':pack['title'],'_sourceRevision':pack['contentRevision'],'cardTemplates':templates})
                entries.append(entry)
        if combined is None:raise ValueError('计划没有来源。')
        combined['packId']=deck['packId'];combined['entries']=entries;combined['_quotaUnit']=settings.get('quotaUnit','card')
        combined['_settingsVersion']=hashlib.sha256(
            json.dumps(settings,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16]
        return combined

    def introduce(self,pairs,prompt_types=None):
        """Put entries the learner has just studied into the review queue.

        The walkthrough is first exposure: it needs to create the card now, for the
        directions the entry can actually support, without making the learner build a
        plan first. Directions are resolved through the same adapter the plan uses, so a
        card created here and a card served by a plan are one card (§4.2).
        """
        from lexicon_exercise import TYPES
        selected=list(prompt_types or ['recall'])
        if any(t not in TYPES for t in selected):raise ValueError('学习卡片方向无效。')
        introduced=[];skipped=[]
        for pack,entry in pairs:
            targets={}
            for template in entry.get('cardTemplates') or []:
                if template.get('promptType') in selected:
                    targets[(template.get('promptType'),template.get('variantKey','default'))]=template
            for question in questions_for(pack,entry):
                target=question['reviewTarget']
                if target['promptType'] not in selected:continue
                identity=(target['promptType'],target['variantKey'])
                targets.setdefault(identity,{'promptType':target['promptType'],'variantKey':target['variantKey'],
                                             'exerciseType':question['type'],'questionId':question['id'],
                                             'exercise':question})
            if not targets:
                # Say which entry could not be learned in the chosen direction rather
                # than reporting a smaller number with no explanation.
                skipped.append({'sourceRef':source_ref(pack,entry),'headword':entry.get('headword',''),
                                'reason':'no-direction'})
                continue
            cards=[{'sourceRef':source_ref(pack,entry),'promptType':prompt,'variantKey':variant,
                    'entry':entry,'template':template} for (prompt,variant),template in sorted(targets.items())]
            introduced.extend(self.store.introduce_cards(pack,cards))
        return {'items':introduced,'count':len(introduced),'skipped':skipped}

    def serve(self,deck_id):
        settings=self.settings(deck_id)
        if settings.get('paused'):return {'deck':self.detail(deck_id),'items':[],'pendingItems':[],'paused':True}
        result=self.store.serve_deck(deck_id,self.pack(deck_id));result['deck']=self.detail(deck_id)
        return result

    def today(self,deck_id='',introduce=False):
        """The day's queue.

        Built from three sources: the due cards of active plans, then the due cards that
        belong to no plan at all. A card that only belongs to paused plans is in neither,
        so pausing one plan and pausing all of them agree — before this, the trailing
        全量 `due_vocab()` put the paused plan's cards straight back (LEX-06, §7.1).
        """
        decks=[self.detail(deck_id)] if deck_id else [self.detail(d['id']) for d in self.store.list_decks()]
        warnings=[]; by_id={}; memberships={}; paused_only={}
        for deck in decks:
            paused=bool(deck['settings'].get('paused'))
            if not paused and introduce:
                try:self.serve(deck['id'])
                except (ValueError,KeyError) as exc:warnings.append(str(exc))
            for card in self.store.due_vocab(deck_id=deck['id']):
                if paused:
                    paused_only.setdefault(card['id'],card);continue
                by_id[card['id']]=card;memberships.setdefault(card['id'],[]).append(deck['id'])
        if not deck_id:
            # Cards no plan claims are still the learner's; cards only paused plans claim
            # are not. `unplanned_due_vocab` draws exactly that line in one query.
            for card in self.store.unplanned_due_vocab():by_id.setdefault(card['id'],card)
        held=[card for key,card in paused_only.items() if key not in by_id]
        for key,card in by_id.items():card['deckIds']=memberships.get(key,[])
        cards=sorted(by_id.values(),key=lambda c:(not bool(c.get('lastReviewedAt')),c.get('nextReviewAt',''),c['id']))
        # The learning day belongs to the plan's timezone, so the server states it rather
        # than the browser guessing from its own locale (§7.3).
        primary=decks[0] if deck_id and decks else None
        return {'items':cards,'count':len(cards),'warnings':warnings,'decks':decks,
                'pausedHeld':len(held),
                'learningDay':(primary or {}).get('learningDay') or self.store.learning_day('UTC'),
                'batchKeys':{d['id']:d.get('learningDay','') for d in decks}}
