import re

def auto_triage_severity(description: str, user_provided_severity: str = 'Low') -> str:
    """
    Analyzes ticket description text and automatically elevates severity
    if critical business-impacting keywords are detected.
    """
    desc_lower = description.lower()
    
    # High severity indicators
    high_keywords = [
        r'\bdown\b', r'\bcrash\b', r'\boutage\b', r'\bemergency\b',
        r'\bcritical\b', r'\bdatabase\b', r'\bdata loss\b', r'\bsecurity\b'
    ]
    
    # Medium severity indicators
    medium_keywords = [
        r'\bslow\b', r'\bbug\b', r'\berror\b', r'\bbroken\b',
        r'\bcannot access\b', r'\bcan\'t access\b', r'\btimeout\b', r'\bdegraded\b'
    ]
    
    if any(re.search(kw, desc_lower) for kw in high_keywords):
        return 'High'
        
    if any(re.search(kw, desc_lower) for kw in medium_keywords):
        return 'Medium' if user_provided_severity == 'Low' else user_provided_severity
        
    return user_provided_severity
