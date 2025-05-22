"""
Utility functions for URL handling.
"""


def normalize_url(url: str) -> str:
    """
    Normalize a URL by converting it to lowercase.
    
    Args:
        url: URL to normalize.
        
    Returns:
        Normalized URL.
    """
    if not url:
        return url
    
    # Convert to lowercase
    normalized = url.lower()
    
    # Remove trailing slash if present
    if normalized.endswith('/'):
        normalized = normalized[:-1]
    
    return normalized
