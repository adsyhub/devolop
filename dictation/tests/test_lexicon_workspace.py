"""Regression tests for complete lexicon workflows, using isolated learning data."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).parent)]
from local_backend import LearningStore,source_card_id
from lexicon_store import LexiconStore,PackQualityError
from lexicon_api import LexiconServices
from lexicon_practice_store import ConflictError
from lexicon_exercise import score,questions_for
from lexicon_schema import content_revision
from lexicon_fixtures import make_pack,make_word_pack
from test_lexicon_api import write_pack
from support import RunningServer,write_course

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.grammar=make_pack();self.words=make_word_pack()
        write_pack(self.root/'lexicon','grammar',self.grammar);write_pack(self.root/'lexicon','words',self.words)
        self.store=LearningStore(self.root/'learning.sqlite3');self.addCleanup(self.store.close)
        self.s=LexiconServices(self.store,LexiconStore(self.root/'lexicon'))
    def session(self,**kwargs):return self.s.practice.create({'types':['reading'],'kind':'word','count':1,**kwargs})
    def answer(self,session,answer='うけたまわる',**kwargs):
        cursor=session['state']['queue'][session['state']['cursor']]
        return self.s.practice.answer(session['id'],{**cursor,'answer':answer,'version':session['version'],**kwargs},'op_'+str(session['version'])+'_'+session['id'])
    def test_daily_pending_does_not_reintroduce_a_reviewed_card(self):
        deck=self.store.create_deck({'dailyNew':1},self.grammar);first=self.store.serve_deck(deck['id'],self.grammar)
        card=first['items'][0];self.store.grade_vocab_review(card['id'],'good')
        again=self.store.serve_deck(deck['id'],self.grammar)
        self.assertEqual(again['pendingItems'],[]);self.assertEqual(again['items'][0]['id'],card['id'])
    def test_empty_batch_is_frozen_after_daily_limit_changes(self):
        deck=self.store.create_deck({'dailyNew':0},self.grammar);self.store.serve_deck(deck['id'],self.grammar)
        self.store.update_deck(deck['id'],{'dailyNew':10})
        self.assertEqual(self.store.serve_deck(deck['id'],self.grammar)['items'],[])
    def test_source_revision_preserves_every_personal_override(self):
        deck=self.store.create_deck({'dailyNew':1},self.grammar);card=self.store.serve_deck(deck['id'],self.grammar)['items'][0]
        edits={'note':'个人笔记','tags':['自己的标签'],'meaning':'我的释义','reading':'自选读音','term':'个人显示'}
        self.store.update_vocab(card['id'],edits)
        self.store.sync_deck_pack(deck['id'],self.grammar)
        result=self.store._get_vocab(card['id'])
        for k,v in edits.items():self.assertEqual(result[k],v,k)
    def test_broken_pack_entry_is_also_blocked(self):
        bad=copy.deepcopy(self.grammar);bad['entries'][0]['grammar']['connection']=[];bad['contentRevision']=content_revision(bad)
        write_pack(self.root/'lexicon','bad',bad)
        with self.assertRaises(PackQualityError):self.s.lexicon.get_entry('bad',bad['entries'][0]['id'])
    def test_existing_cards_can_be_read_when_the_pack_disappears(self):
        deck=self.store.create_deck({'dailyNew':1},self.grammar);self.store.serve_deck(deck['id'],self.grammar)
        (self.root/'lexicon/grammar/pack.json').unlink()
        result=self.s.learning.today(deck['id'],introduce=True)
        self.assertEqual(result['count'],1);self.assertTrue(result['warnings'])
    def test_search_reading_normalization_and_revision_invalidation(self):
        self.assertEqual(self.s.index.search('ウケタマワル')['total'],1)
        changed=copy.deepcopy(self.words);changed['entries'][0]['gloss']['zh']='新的唯一释义';changed['contentRevision']=content_revision(changed)
        write_pack(self.root/'lexicon','words',changed)
        self.assertEqual(self.s.index.search('唯一释义')['total'],1)
        self.assertEqual(self.s.index.search('%')['total'],0)
    def test_student_api_payload_has_no_answer_or_reading_leak(self):
        session=self.session();q=session['items'][0]
        self.assertNotIn('acceptedAnswers',q);self.assertNotIn('reading',q);self.assertNotIn('explanation',q)
    def test_answer_report_and_srs_write_together(self):
        result=self.answer(self.session());self.assertTrue(result['result']['correct']);self.assertTrue(result['result']['srsApplied'])
        report=self.s.practice.submit(result['session']['id']);self.assertEqual(report['summary']['accuracy'],100)
        self.assertEqual(len(self.store.list_vocab()),1)
    def test_same_operation_cannot_advance_the_session_twice(self):
        session=self.session();result=self.answer(session);second=self.answer(session)
        self.assertTrue(second['duplicate']);self.assertEqual(second['session']['state']['cursor'],1)
        self.assertEqual(self.store.list_vocab()[0]['srsRepetitions'],1)
    def test_two_tabs_conflict_instead_of_double_scoring(self):
        session=self.session();self.answer(session)
        with self.assertRaises(ConflictError):self.s.practice.answer(session['id'],{'itemId':session['items'][0]['id'],'answer':'うけたまわる','version':1},'op_other')
    def test_incorrect_reading_retries_without_erasing_first_result(self):
        result=self.answer(self.session(),'うけだまわる');self.assertFalse(result['result']['correct'])
        result=self.answer(result['session']);report=self.s.practice.submit(result['session']['id'])
        self.assertEqual(report['summary']['accuracy'],0);self.assertEqual(report['summary']['retries'],1)
        self.assertEqual(self.store.list_vocab()[0]['srsRepetitions'],0)
        self.assertFalse(self.s.practice.mistakes()[0]['resolved'])
    def test_a_hint_cannot_be_reported_as_independent_success(self):
        session=self.session();q=session['items'][0]
        self.s.practice.expose(session['id'],{'itemId':q['id']});session=self.s.practice.get(session['id'])
        result=self.answer(session);self.assertEqual(result['result']['classification'],'assisted')
    def test_end_feedback_does_not_reveal_or_schedule_before_submit(self):
        session=self.session(feedback='end');result=self.answer(session,answer='まちがい')
        self.assertTrue(result['result']['saved'])
        # Nothing that states or implies the outcome may travel back before submit.
        for leak in ('correct','classification','explanation','referenceAnswer','choices','needsRetry','srsApplied'):
            self.assertNotIn(leak,result['result'],leak)
        self.assertEqual(self.store.list_vocab(),[])
        self.assertNotIn('result',result['session']['attempts'][0])
        # …and neither may the mistake book or the statistics, which are separate routes.
        self.assertEqual(self.s.practice.mistakes(),[])
        self.assertEqual(self.s.practice.stats()['totalAttempts'],0)
        with self.assertRaises(ConflictError):self.s.practice.report(session['id'])
        self.s.practice.submit(session['id'])
        self.assertEqual(len(self.store.list_vocab()),1)
        self.assertEqual(len(self.s.practice.mistakes()),1)
        self.assertEqual(self.s.practice.stats()['totalAttempts'],1)
    def test_closed_sessions_are_idempotent_and_cannot_receive_new_answers(self):
        session=self.answer(self.session())['session'];first=self.s.practice.submit(session['id']);second=self.s.practice.submit(session['id']);self.assertEqual(first,second)
        with self.assertRaises(ConflictError):self.s.practice.answer(session['id'],{'itemId':session['items'][0]['id'],'answer':'x'},'op_new')
    def test_user_entry_versions_and_tombstones(self):
        first=self.s.practice.save_user_entry({'sourceRef':'user:test','headword':'例','gloss':{'zh':'例子'},'starred':True})
        self.s.practice.save_user_entry({**first,'note':'新笔记'})
        with self.assertRaises(ConflictError):self.s.practice.save_user_entry({**first,'note':'旧页面'})
        self.s.practice.save_user_entry({'sourceRef':'user:test','deleted':True})
        self.assertEqual(self.s.practice.user_entries(),[])
    def test_vocabulary_and_grammar_filters_do_not_mix(self):
        session=self.s.practice.create({'types':['cloze'],'kind':'grammar','count':2})
        self.assertTrue(all(q['kind']=='grammar' for q in session['items']))
    def test_no_qualified_questions_is_an_explicit_error(self):
        with self.assertRaises(ValueError):self.s.practice.create({'types':['listening'],'count':10})
    def test_invalid_answers_do_not_partially_mutate_state(self):
        session=self.session()
        with self.assertRaises(ValueError):self.answer(session,['invalid'])
        self.assertEqual(self.store.list_vocab(),[]);self.assertEqual(self.s.practice.get(session['id'])['state']['cursor'],0)
    def test_offline_bundle_is_explicit_and_keeps_frozen_answers(self):
        session=self.session();offline=self.s.practice.get(session['id'],offline=True)
        self.assertIn('acceptedAnswers',offline['items'][0]);self.assertTrue(offline['offlinePrepared'])
        changed=copy.deepcopy(self.words);changed['entries'][0]['snapshot']['reading']='different';changed['contentRevision']=content_revision(changed)
        write_pack(self.root/'lexicon','words',changed)
        self.assertTrue(self.answer(session)['result']['correct'])
    def test_source_updates_do_not_reset_review_history(self):
        deck=self.store.create_deck({'dailyNew':1},self.grammar);card=self.store.serve_deck(deck['id'],self.grammar)['items'][0]
        result=self.store.grade_vocab_review(card['id'],'easy');self.store.sync_deck_pack(deck['id'],self.grammar)
        self.assertEqual(self.store._get_vocab(card['id'])['nextReviewAt'],result['nextReviewAt'])

class PlanScopeTests(unittest.TestCase):
    """LEX-06 / LEX-07 / LEX-13: what a plan holds, and when it stops holding it."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.words=make_word_pack();self.grammar=make_pack()
        write_pack(self.root/'lexicon','words',self.words);write_pack(self.root/'lexicon','grammar',self.grammar)
        self.store=LearningStore(self.root/'learning.sqlite3');self.addCleanup(self.store.close)
        self.s=LexiconServices(self.store,LexiconStore(self.root/'lexicon'))
    def plan(self,pack,**settings):
        deck=self.store.create_deck({'dailyNew':5,'studyTimezone':'UTC'},pack)
        self.s.learning.save_settings(deck['id'],settings)
        return deck['id']
    def reload_packs(self):
        self.s.lexicon=LexiconStore(self.root/'lexicon');self.s.learning.lexicon=self.s.lexicon;self.s.practice.lexicon=self.s.lexicon
    @staticmethod
    def rebuild(pack,**overrides):
        """Re-derive a fixture pack after editing it: ids follow from packId + entryKey,
        so units must name keys again rather than the ids of the previous build."""
        from lexicon_schema import prepare_pack
        raw={k:v for k,v in copy.deepcopy(pack).items()
             if k not in ('quality','entryCount','contentRevision','schemaVersion')}
        raw.update(copy.deepcopy(overrides))
        raw['entries']=[{k:v for k,v in e.items() if k not in ('id','sourceRef','order')} for e in raw['entries']]
        keys=[e['entryKey'] for e in raw['entries']]
        for unit in raw.get('units',[]):
            unit['entryIds']=[k for k in keys if k]
        return prepare_pack(raw)

    def test_a_paused_plan_is_paused_in_the_all_plans_queue_too(self):
        deck=self.plan(self.words,packSlugs=['words'],promptTypes=['recall'])
        self.store.serve_deck(deck,self.s.learning.pack(deck))
        self.s.learning.save_settings(deck,{'paused':True})
        # Before this the trailing full `due_vocab()` swept the paused plan's cards back,
        # so one plan and "all plans" gave opposite answers for the same setting.
        self.assertEqual(self.s.learning.today(deck)['count'],0)
        every=self.s.learning.today()
        self.assertEqual(every['count'],0)
        self.assertEqual(every['pausedHeld'],1)

    def test_a_card_shared_with_an_active_plan_still_appears_once(self):
        first=self.plan(self.words,packSlugs=['words'],promptTypes=['recall'])
        self.store.serve_deck(first,self.s.learning.pack(first))
        second=self.plan(self.words,packSlugs=['words'],promptTypes=['recall'])
        self.store.serve_deck(second,self.s.learning.pack(second))
        self.s.learning.save_settings(first,{'paused':True})
        every=self.s.learning.today()
        self.assertEqual(every['count'],1)
        self.assertEqual(every['items'][0]['deckIds'],[second])

    def test_a_card_no_plan_holds_is_still_reviewed(self):
        deck=self.plan(self.words,packSlugs=['words'],promptTypes=['recall'])
        self.store.serve_deck(deck,self.s.learning.pack(deck))
        self.s.learning.save_settings(deck,{'paused':True})
        self.store.create_vocab({'term':'手動','meaning':'自己加的'})
        self.assertEqual(self.s.learning.today()['count'],1)

    def test_auto_include_false_freezes_the_membership(self):
        deck=self.plan(self.words,packSlugs=['words'],autoInclude=False,promptTypes=['recall'])
        before=len(self.s.learning.pack(deck)['entries'])
        extra=copy.deepcopy(self.words['entries'][0]);extra.update({'entryKey':'e0002','headword':'承知'})
        grown=self.rebuild(self.words,entries=[*self.words['entries'],extra])
        write_pack(self.root/'lexicon','words',grown);self.reload_packs()
        self.assertEqual(len(self.s.learning.pack(deck)['entries']),before)
        # …while a plan that opted in does grow.
        opted=self.plan(self.words,packSlugs=['words'],autoInclude=True,promptTypes=['recall'])
        self.assertEqual(len(self.s.learning.pack(opted)['entries']),before+1)

    def test_a_frozen_member_still_tracks_its_content_revision(self):
        deck=self.plan(self.words,packSlugs=['words'],autoInclude=False,promptTypes=['recall'])
        card=self.store.serve_deck(deck,self.s.learning.pack(deck))['items'][0]
        revised=copy.deepcopy(self.words)
        revised['entries'][0]['gloss']['zh']='订正后的释义'
        revised['contentRevision']=content_revision(revised)
        write_pack(self.root/'lexicon','words',revised);self.reload_packs()
        self.store.sync_deck_pack(deck,self.s.learning.pack(deck))
        self.assertEqual(self.store._get_vocab(card['id'])['meaning'],'订正后的释义')

    def test_same_named_units_in_two_packs_do_not_match_each_other(self):
        other=self.rebuild(self.words,packId='Other-words-fixture')
        write_pack(self.root/'lexicon','other',other);self.reload_packs()
        scoped=self.s.learning.unit_ref(self.words,self.words['entries'][0])
        deck=self.plan(self.words,packSlugs=['words','other'],unitIds=[scoped],promptTypes=['recall'])
        entries=self.s.learning.pack(deck)['entries']
        # A bare `u1` would have matched the identically named unit in the other pack.
        self.assertEqual({e['_sourcePackId'] for e in entries},{self.words['packId']})

    def test_each_card_records_the_revision_of_its_own_pack(self):
        variant=copy.deepcopy(self.words['entries'][0]);variant['gloss']['zh']='另一个包的释义'
        other=self.rebuild(self.words,packId='Other-words-fixture',entries=[variant])
        write_pack(self.root/'lexicon','other',other);self.reload_packs()
        deck=self.plan(self.words,packSlugs=['words','other'],promptTypes=['recall'])
        served=self.store.serve_deck(deck,self.s.learning.pack(deck))['items']
        revisions={c['sourceRef'].split('#')[0]:c['sourceRevision'] for c in served}
        self.assertEqual(revisions[f"lex:{self.words['packId']}"],self.words['contentRevision'])
        self.assertEqual(revisions['lex:Other-words-fixture'],other['contentRevision'])
        self.assertNotEqual(*revisions.values())

    def test_a_retired_entry_stops_producing_cards_but_keeps_the_old_one(self):
        deck=self.plan(self.words,packSlugs=['words'],promptTypes=['recall'])
        card=self.store.serve_deck(deck,self.s.learning.pack(deck))['items'][0]
        retired=copy.deepcopy(self.words)
        retired['entries'][0]['qualityStatus']='retired'
        retired['contentRevision']=content_revision(retired)
        write_pack(self.root/'lexicon','words',retired);self.reload_packs()
        self.assertEqual(retired['entries'][0]['id'],self.words['entries'][0]['id'])
        self.store.sync_deck_pack(deck,self.s.learning.pack(deck))
        self.assertIsNotNone(self.store._get_vocab(card['id']))
        second=self.plan(retired,packSlugs=['words'],promptTypes=['recall'])
        self.assertEqual(self.store.serve_deck(second,self.s.learning.pack(second))['items'],[])

    def test_a_declared_alias_moves_the_card_instead_of_replacing_it(self):
        deck=self.plan(self.words,packSlugs=['words'],promptTypes=['recall'])
        card=self.store.serve_deck(deck,self.s.learning.pack(deck))['items'][0]
        self.store.grade_vocab_review(card['id'],'good',reviewed_at='2026-01-05T09:00:00+00:00')
        graded=self.store._get_vocab(card['id'])

        renamed=copy.deepcopy(self.words['entries'][0])
        renamed.update({'entryKey':'e0007',
                        'idAliases':[{'id':self.words['entries'][0]['id'],'reason':'renumbered'}]})
        moved=self.rebuild(self.words,entries=[renamed])
        write_pack(self.root/'lexicon','words',moved);self.reload_packs()
        self.store.sync_deck_pack(deck,self.s.learning.pack(deck))

        canonical=source_card_id(f"lex:{moved['packId']}#{moved['entries'][0]['id']}",'recall','default')
        migrated=self.store._get_vocab(canonical)
        self.assertIsNotNone(migrated)
        self.assertEqual(migrated['srsRepetitions'],graded['srsRepetitions'])
        self.assertIsNone(self.store._get_vocab(card['id']))
        alias=self.store.connection.execute(
            'SELECT canonical_vocab_id,reason FROM lex_identity_aliases WHERE old_vocab_id=?',(card['id'],)).fetchone()
        self.assertEqual((alias[0],alias[1]),(canonical,'source-id-alias'))

    def test_a_plan_edit_that_fails_leaves_no_partial_configuration(self):
        deck=self.plan(self.words,packSlugs=['words'],promptTypes=['recall'])
        before=self.s.learning.settings(deck)
        with self.assertRaises((ValueError,KeyError)):
            self.s.learning.update_plan(deck,{'promptTypes':['production'],'packSlugs':['does-not-exist']})
        self.assertEqual(self.s.learning.settings(deck),before)

    def test_the_batch_records_the_configuration_it_was_generated_under(self):
        deck=self.plan(self.words,packSlugs=['words'],quotaUnit='entry',promptTypes=['recall'])
        self.store.serve_deck(deck,self.s.learning.pack(deck))
        run=self.store.connection.execute(
            'SELECT study_timezone,quota_unit,daily_new,settings_version FROM lex_daily_batch_runs WHERE deck_id=?',
            (deck,)).fetchone()
        self.assertEqual((run['study_timezone'],run['quota_unit'],run['daily_new']),('UTC','entry',5))
        self.assertTrue(run['settings_version'])
        # A later quota change belongs to the next learning day, not to this batch.
        self.store.update_deck(deck,{'dailyNew':50})
        self.store.serve_deck(deck,self.s.learning.pack(deck))
        self.assertEqual(self.store.connection.execute(
            'SELECT daily_new FROM lex_daily_batch_runs WHERE deck_id=?',(deck,)).fetchone()[0],5)

    def test_the_server_states_the_learning_day(self):
        deck=self.store.create_deck({'dailyNew':1,'studyTimezone':'Asia/Tokyo'},self.words)
        self.s.learning.save_settings(deck['id'],{'packSlugs':['words'],'promptTypes':['recall']})
        result=self.s.learning.today(deck['id'])
        self.assertEqual(result['learningDay'],self.store.learning_day('Asia/Tokyo'))
        self.assertEqual(result['batchKeys'][deck['id']],result['learningDay'])


class WorkspaceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
        manifest=write_course(root/'courses/demo');write_pack(root/'lexicon','words',make_word_pack())
        self.server=RunningServer(manifest,root/'data',lexicon_root=root/'lexicon');self.server.__enter__();self.addCleanup(lambda:self.server.__exit__(None,None,None))
    def call(self,method,path,body=None,operation=''):
        headers={'X-Learning-Operation-Id':operation} if operation else None
        code,data=self.server.request(method,path,origin=f'http://127.0.0.1:{self.server.port}',body=body,headers=headers)
        return code,json.loads(data) if data else {}
    def graded_card(self):
        code,result=self.call('POST','/api/lexicon/sessions',{'types':['reading'],'count':1})
        self.assertEqual(code,201);session=result['session']
        code,result=self.call('POST',f"/api/lexicon/sessions/{session['id']}/answers",
                              {'itemId':session['items'][0]['id'],'answer':'うけたまわる','operationId':'op_seed'})
        self.assertEqual(code,200,result)
        return result['result']['vocabId']
    def test_review_route_enforces_the_card_version_over_the_wire(self):
        vocab_id=self.graded_card()
        code,listing=self.call('GET','/api/vocab')
        card=next(item for item in listing['items'] if item['id']==vocab_id)
        stale=card['reviewVersion']
        code,result=self.call('POST','/api/vocab/review',{'vocabId':vocab_id,'grade':'good','expectedReviewVersion':stale},operation='op_http_grade_1')
        self.assertEqual(code,200,result)
        self.assertEqual(result['item']['reviewVersion'],stale+1)
        code,result=self.call('POST','/api/vocab/review',{'vocabId':vocab_id,'grade':'good','expectedReviewVersion':stale},operation='op_http_grade_2')
        self.assertEqual(code,409,result);self.assertEqual(result['code'],'review-conflict')
        code,result=self.call('POST','/api/vocab/review',{'vocabId':vocab_id,'grade':'good','expectedReviewVersion':'soon'})
        self.assertEqual(code,400,result)
    def test_delete_and_restore_are_distinct_explicit_operations(self):
        vocab_id=self.graded_card()
        code,result=self.call('DELETE','/api/vocab/'+vocab_id,operation='op_http_delete')
        self.assertEqual(code,200,result);self.assertEqual(result['tombstoneVersion'],1)
        code,repeat=self.call('DELETE','/api/vocab/'+vocab_id,operation='op_http_delete')
        self.assertEqual(code,200,repeat);self.assertTrue(repeat['duplicate'])
        # A queued grade replayed after the deletion is refused, not silently applied.
        code,result=self.call('POST','/api/vocab/review',{'vocabId':vocab_id,'grade':'good'},operation='op_http_late')
        self.assertEqual(code,409,result);self.assertEqual(result['code'],'card-deleted')
        self.assertFalse(result['srsApplied'])
        code,result=self.call('POST',f'/api/vocab/{vocab_id}/restore',{'expectedTombstoneVersion':9})
        self.assertEqual(code,409,result)
        code,result=self.call('POST',f'/api/vocab/{vocab_id}/restore',{'expectedTombstoneVersion':1})
        self.assertEqual(code,200,result);self.assertTrue(result['restored'])
    def test_a_reveal_replays_under_its_own_operation_id(self):
        code,result=self.call('POST','/api/lexicon/sessions',{'types':['reading'],'count':1})
        session=result['session'];item=session['items'][0]['id']
        code,first=self.call('POST',f"/api/lexicon/sessions/{session['id']}/reveal",{'itemId':item,'round':0},operation='op_http_reveal')
        self.assertEqual(code,200,first)
        code,again=self.call('POST',f"/api/lexicon/sessions/{session['id']}/reveal",{'itemId':item,'round':0},operation='op_http_reveal')
        self.assertEqual(code,200,again);self.assertTrue(again['duplicate'])
        self.assertEqual(first['sequence'],again['sequence'])
        code,clash=self.call('POST',f"/api/lexicon/sessions/{session['id']}/reveal",{'itemId':item,'round':1},operation='op_http_reveal')
        self.assertEqual(code,409,clash)
    def test_full_api_practice_roundtrip(self):
        code,result=self.call('POST','/api/lexicon/sessions',{'types':['reading'],'count':1})
        self.assertEqual(code,201);session=result['session']
        code,result=self.call('POST',f"/api/lexicon/sessions/{session['id']}/answers",{'itemId':session['items'][0]['id'],'answer':'うけたまわる','operationId':'op_http_1'})
        self.assertEqual(code,200,result)
        code,result=self.call('POST',f"/api/lexicon/sessions/{session['id']}/submit")
        self.assertEqual(result['report']['summary']['accuracy'],100)
    def test_new_routes_keep_the_existing_token_boundary(self):
        code,_=self.server.request('GET','/api/lexicon/sessions',token=None)
        self.assertEqual(code,403)
    def test_scope_and_size_parameters_are_checked(self):
        code,_=self.call('GET','/api/lexicon/search?q=x&limit=-1');self.assertEqual(code,400)
        code,_=self.call('POST','/api/lexicon/sessions',{'count':0});self.assertEqual(code,400)

if __name__=='__main__':unittest.main()
