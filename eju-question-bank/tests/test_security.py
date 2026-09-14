import pytest
from eju_bank.security import validate_host, validate_origin, verify_admin_token, sanitize_paper_for_learner
from eju_bank.errors import SecurityError

def test_host_validation():
    # Localhost allowed
    validate_host("127.0.0.1:8765")
    validate_host("localhost:8765")
    
    # Remote blocked unless allowed
    with pytest.raises(SecurityError):
        validate_host("192.168.1.100:8765", allow_remote=False)
    with pytest.raises(SecurityError):
        validate_host("192.168.1.100:8765", allow_remote=True)
    validate_host("192.168.1.100:8765", allow_remote=True, host_allowlist={"192.168.1.100"})

def test_origin_validation():
    # Safe methods without Origin allowed
    validate_origin(None, "GET")
    validate_origin(None, "POST")
    
    # Origin from localhost allowed
    validate_origin("http://127.0.0.1:8765", "POST")
    validate_origin("http://localhost:8765", "POST")
    
    # Cross-origin blocked
    with pytest.raises(SecurityError):
        validate_origin("http://malicious-site.com", "POST")

def test_admin_token():
    # No admin token required
    verify_admin_token(None, None)
    
    # Token required and provided
    verify_admin_token("Bearer secret-123", "secret-123")
    
    # Token missing or invalid
    with pytest.raises(SecurityError):
        verify_admin_token(None, "secret-123")
    with pytest.raises(SecurityError):
        verify_admin_token("Bearer wrong-token", "secret-123")

def test_zero_correct_answer_leakage():
    paper = {
        "paperId": "p1",
        "title": "Sample",
        "forms": [
            {
                "formCode": "PHYSICS_JA",
                "groups": [
                    {
                        "groupCode": "I",
                        "questions": [
                            {
                                "questionId": "q1",
                                "correctAnswer": {"optionKey": "4"},
                                "answerRef": "PHYSICS:1",
                                "stemAst": [{"type": "text", "value": "Question 1"}],
                            }
                        ]
                    }
                ]
            }
        ]
    }
    sanitized = sanitize_paper_for_learner(paper)
    q = sanitized["forms"][0]["groups"][0]["questions"][0]
    assert "correctAnswer" not in q
    assert "answerRef" not in q
    assert "stemAst" in q
