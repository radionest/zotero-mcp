"""
Simple token estimation utility for response chunking.
"""

def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    
    Uses simple heuristic: ~4 characters per token for mixed content.
    This is a conservative estimate that works well for markdown text.
    
    Args:
        text: Input text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    
    # Basic token estimation: 4 characters per token on average
    # This accounts for spaces, punctuation, and markdown formatting
    char_count = len(text)
    token_estimate = char_count // 4
    
    # Add some overhead for markdown formatting
    if '**' in text or '#' in text or '`' in text:
        token_estimate = int(token_estimate * 1.1)
    
    return token_estimate