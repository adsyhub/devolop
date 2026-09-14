from conftest import install_fixture_media
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from eju_bank.audit import prepare_paper, iter_questions
from eju_bank.db import Database
from eju_bank.errors import ContractError, SessionError, RightsError
from eju_bank.grading import grade_paper


@pytest.fixture
def bank(tmp_path):
    paper = json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    db = Database(tmp_path / 'test.db')
    install_fixture_media(db.path.parent / 'media')
    db.publish(paper, channel='PUBLIC')
    yield db, paper
    db.close()


def test_unanswered_and_essay_denominators(bank):
    db, paper = bank
    result = grade_paper(paper, {}, selected_forms=['PHYSICS_JA', 'CHEMISTRY_JA'])
    assert (result['objectiveTotal'], result['objectiveUnanswered'], result['objectiveAccuracy']) == (2, 2, 0)
    q = next(q for f, _, q in iter_questions(paper) if f['formCode'] == 'PHYSICS_JA')
    result = grade_paper(paper, {q['questionId']: {'type': 'SINGLE_CHOICE', **q['correctAnswer']}}, selected_forms=['PHYSICS_JA', 'CHEMISTRY_JA'])
    assert (result['objectiveTotal'], result['objectiveAccuracy']) == (2, .5)
    result = grade_paper(paper, {}, selected_forms=['JAPANESE_JA'])
    assert result['essayPending'] == 0
    assert result['essayUnanswered'] == 1
    assert result['objectiveTotal'] == 2


def test_atomic_batch_receipts_and_versions(bank):
    db, paper = bank
    sid = db.create_session(paper['paperId'], ['PHYSICS_JA'])['sessionId']
    q = next(q for f, _, q in iter_questions(paper) if f['formCode'] == 'PHYSICS_JA')
    item = {'questionId': q['questionId'], 'response': {'type': 'SINGLE_CHOICE', 'optionKey': '1'}}
    with pytest.raises(SessionError):
        db.record_responses_batch(sid, [item, {'questionId': 'missing', 'response': {}}])
    assert db.get_session(sid)['responses'] == {}
    first = db.record_responses_batch(sid, [item], expected_version=0, request_id='one')
    assert db.record_responses_batch(sid, [item], expected_version=0, request_id='one') == first
    with pytest.raises(SessionError, match='conflict'):
        db.record_responses_batch(sid, [item], expected_version=0, request_id='two')
    assert db.get_session(sid)['responseVersion'] == 1
    with pytest.raises(SessionError):
        db.get_result(sid)
    db.pause_session(sid)
    with pytest.raises(SessionError):
        db.record_responses_batch(sid, [item])
    db.resume_session(sid)
    db.submit_session(sid)
    with pytest.raises(SessionError):
        db.record_responses_batch(sid, [item])


def test_version_pinned_result_and_restart(bank):
    db, paper = bank
    sid = db.create_session(paper['paperId'], ['PHYSICS_JA'])['sessionId']
    q = next(q for f, _, q in iter_questions(paper) if f['formCode'] == 'PHYSICS_JA')
    db.record_response(sid, q['questionId'], {'type': 'SINGLE_CHOICE', **q['correctAnswer']})
    db.save_progress(sid, {'currentQuestionId': q['questionId'], 'flaggedQuestionIds': [q['questionId']]})
    new = copy.deepcopy(paper)
    new['title'] = 'Changed title'
    newq = next(q for f, _, q in iter_questions(new) if f['formCode'] == 'PHYSICS_JA')
    newq['stemAst'] = [{'type': 'text', 'value': 'Changed question'}]
    newq['correctAnswer'] = {'optionKey': '1'}
    db.publish(prepare_paper(new), channel='PUBLIC')
    db.close()
    assert db.get_session(sid)['paperVersion'] == 1
    assert db.get_session(sid)['progress']['currentQuestionId'] == q['questionId']
    delivery = db.get_session_paper(sid)
    assert 'correctAnswer' not in json.dumps(delivery)
    db.submit_session(sid)
    result = db.get_result(sid)
    assert result['paperTitle'] == paper['title']
    assert result['questions'][0]['question']['stemAst'] == q['stemAst']
    assert result['objectiveCorrect'] == 1


def test_concurrent_submit_is_idempotent(bank):
    db, paper = bank
    sid = db.create_session(paper['paperId'], ['PHYSICS_JA', 'CHEMISTRY_JA'])['sessionId']
    def submit(_):
        try:
            return db.submit_session(sid)
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(submit, range(4)))
    assert all(r == results[0] for r in results)
    assert db.connection.execute('SELECT count(*) FROM results').fetchone()[0] == 1
    assert db.connection.execute("SELECT count(*) FROM session_events WHERE event_type='SUBMIT'").fetchone()[0] == 1


def test_every_publish_entry_checks_rights(bank):
    db, paper = bank
    paper['source']['rights']['status'] = 'PRIVATE_STUDY'
    with pytest.raises(RightsError):
        db.publish(paper, channel='PUBLIC')


def test_expired_session_auto_submit(bank):
    db, paper = bank
    sid = db.create_session(paper['paperId'], ['PHYSICS_JA', 'CHEMISTRY_JA'], mode='MOCK')['sessionId']
    # Set deadline in the past
    past_deadline = '2020-01-01T00:00:00Z'
    db.connection.execute("UPDATE practice_sessions SET deadline=? WHERE id=?", (past_deadline, sid))
    db.connection.commit()

    # get_session should auto-submit the expired session
    sess = db.get_session(sid)
    assert sess['status'] == 'SUBMITTED'

    # Result should have EXPIRED_SUBMIT
    result = db.get_result(sid)
    assert result['submissionType'] == 'EXPIRED_SUBMIT'

    # Trying to record responses after expiration should fail
    q = next(q for f, _, q in iter_questions(paper) if f['formCode'] == 'PHYSICS_JA')
    with pytest.raises(SessionError, match='Responses can only be saved while a session is in progress'):
        db.record_response(sid, q['questionId'], {'type': 'SINGLE_CHOICE', 'optionKey': '1'})


def test_submit_expected_response_version_conflict(bank):
    db, paper = bank
    sid = db.create_session(paper['paperId'], ['PHYSICS_JA'])['sessionId']
    q = next(q for f, _, q in iter_questions(paper) if f['formCode'] == 'PHYSICS_JA')
    db.record_response(sid, q['questionId'], {'type': 'SINGLE_CHOICE', 'optionKey': '1'})
    assert db.get_session(sid)['responseVersion'] == 1

    # Mismatched expected version raises SessionError
    with pytest.raises(SessionError, match='Response version conflict'):
        db.submit_session(sid, expected_response_version=0)

    # Correct expected version succeeds
    res = db.submit_session(sid, expected_response_version=1)
    assert res['submissionType'] == 'NORMAL'

