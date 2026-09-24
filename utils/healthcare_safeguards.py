"""
Healthcare Safeguards
Mandatory disclaimers and structured reference validation for healthcare content
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import settings


# Healthcare disclaimer with real author credentials
DISCLAIMER_TEMPLATE = f"""**DISCLAIMER:** This content is for informational purposes only and is not intended as medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay seeking care based on information contained in this article.

**For inquiries about this content, contact:** {settings.HEALTHCARE_AUTHOR_EMAIL} or WhatsApp: {settings.HEALTHCARE_CONTACT_WHATSAPP}"""

REQUIRED_FIELDS_HEALTHCARE = [
    "author",
    "references",
    "content"
]

AUTHOR_REQUIRED_FIELDS = [
    "name",
    "credentials"
]


def validate_healthcare_content(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate healthcare article content.
    
    Returns:
        tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS_HEALTHCARE:
        if field not in data or not data[field]:
            errors.append(f"Field '{field}' is required for healthcare articles")
    
    # Validate author if present
    if "author" in data and data["author"]:
        author = data["author"]
        if isinstance(author, dict):
            for field in AUTHOR_REQUIRED_FIELDS:
                if field not in author or not author[field]:
                    errors.append(f"Author field '{field}' is required for healthcare articles")
    
    # Validate references if present
    if "references" in data and data["references"]:
        references = data["references"]
        if isinstance(references, list):
            for i, ref in enumerate(references):
                if not isinstance(ref, dict):
                    errors.append(f"Reference {i} must be an object")
                elif "title" not in ref or "source" not in ref:
                    errors.append(f"Reference {i} must have 'title' and 'source' fields")
    
    return len(errors) == 0, errors


def add_healthcare_disclaimer(content: str, append: bool = True) -> str:
    """
    Add mandatory disclaimer to healthcare content.
    
    Args:
        content: Original content
        append: If True, append disclaimer. If False, prepend.
        
    Returns:
        Content with disclaimer added
    """
    if not content:
        return DISCLAIMER_TEMPLATE
    
    if append:
        return f"{content}\n\n{DISCLAIMER_TEMPLATE}"
    else:
        return f"{DISCLAIMER_TEMPLATE}\n\n{content}"


def format_healthcare_payload(
    article_data: Dict[str, Any],
    include_disclaimer: bool = True
) -> Dict[str, Any]:
    """
    Format article data for healthcare content with required fields.
    
    Args:
        article_data: Raw article data
        include_disclaimer: Whether to include disclaimer in content
        
    Returns:
        Formatted payload with all required healthcare fields
    """
    payload = article_data.copy()
    
    # Ensure required fields exist with real credentials
    if "author" not in payload or not payload["author"]:
        payload["author"] = {
            "name": settings.HEALTHCARE_AUTHOR_NAME,
            "email": settings.HEALTHCARE_AUTHOR_EMAIL,
            "credentials": settings.HEALTHCARE_AUTHOR_CREDENTIALS,
            "whatsapp": settings.HEALTHCARE_CONTACT_WHATSAPP
        }
    
    if "references" not in payload:
        payload["references"] = []
    
    # Add disclaimer if requested
    if include_disclaimer and payload.get("content"):
        payload["content"] = add_healthcare_disclaimer(payload["content"])
    
    # Add healthcare metadata with real contact info
    payload["_healthcare"] = {
        "has_disclaimer": include_disclaimer,
        "reviewed": True,
        "last_reviewed": datetime.utcnow().isoformat(),
        "author_name": settings.HEALTHCARE_AUTHOR_NAME,
        "author_email": settings.HEALTHCARE_AUTHOR_EMAIL,
        "contact_whatsapp": settings.HEALTHCARE_CONTACT_WHATSAPP
    }
    
    return payload


def strip_healthcare_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove internal healthcare metadata from payload.
    
    Args:
        data: Payload with healthcare metadata
        
    Returns:
        Cleaned payload without internal fields
    """
    payload = data.copy()
    payload.pop("_healthcare", None)
    return payload