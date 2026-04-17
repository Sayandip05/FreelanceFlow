"""Input sanitization utilities for XSS protection."""
import html
import re


def sanitize_html(text: str, allow_basic_formatting: bool = False) -> str:
    """
    Sanitize HTML input to prevent XSS attacks.
    
    Args:
        text: Input text that may contain HTML
        allow_basic_formatting: If True, allows basic formatting tags (b, i, u, p, br)
    
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    if allow_basic_formatting:
        # Allow only safe tags
        allowed_tags = ['b', 'i', 'u', 'p', 'br', 'strong', 'em']
        
        # Remove all tags except allowed ones
        pattern = r'<(?!\s*/?(' + '|'.join(allowed_tags) + r')\b)[^>]*>'
        text = re.sub(pattern, '', text)
        
        # Escape attributes in allowed tags
        text = re.sub(r'<(\w+)\s+[^>]*>', r'<\1>', text)
    else:
        # Escape all HTML
        text = html.escape(text)
    
    return text


def sanitize_text_field(text: str) -> str:
    """
    Sanitize plain text fields by escaping HTML.
    
    Args:
        text: Input text
    
    Returns:
        Sanitized text with HTML escaped
    """
    if not text:
        return text
    
    return html.escape(text)


def strip_dangerous_content(text: str) -> str:
    """
    Remove potentially dangerous content like scripts, iframes, etc.
    
    Args:
        text: Input text
    
    Returns:
        Text with dangerous content removed
    """
    if not text:
        return text
    
    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove iframe tags
    text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove on* event handlers
    text = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*on\w+\s*=\s*[^\s>]*', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text
