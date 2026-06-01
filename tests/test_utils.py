
from app.utils import auto_triage_severity

def test_auto_triage_high_severity():
    assert auto_triage_severity("The server is down!") == 'High'
    assert auto_triage_severity("Database crash reported.") == 'High'
    assert auto_triage_severity("Critical security vulnerability found.") == 'High'

def test_auto_triage_medium_severity():
    # If user selected Low, it should elevate to Medium
    assert auto_triage_severity("The system is slow.", user_provided_severity='Low') == 'Medium'
    assert auto_triage_severity("There is a bug on the login page.", user_provided_severity='Low') == 'Medium'

def test_auto_triage_no_elevation():
    # Should maintain default severity if no keywords match
    assert auto_triage_severity("I need help resetting my password.", user_provided_severity='Low') == 'Low'
    assert auto_triage_severity("Can you change my display name?", user_provided_severity='Medium') == 'Medium'
