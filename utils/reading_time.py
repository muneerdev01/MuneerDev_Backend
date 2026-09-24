"""
Reading Time Calculator
Calculate reading time based on average 200 words per minute
"""
import re
from html import unescape


def count_words(text: str) -> int:
    """
    Count words in text, handling HTML and markdown.
    """
    if not text:
        return 0
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove markdown syntax but keep content
    text = re.sub(r'[*_#>`\[\]\(\)]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    if not text:
        return 0
    
    return len(text.split())


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Calculate reading time in minutes based on word count.
    Returns at least 1 minute if there's content.
    """
    word_count = count_words(text)
    
    if word_count == 0:
        return 0
    
    reading_time = word_count / words_per_minute
    return max(1, int(reading_time))


def format_reading_time(minutes: int) -> str:
    """
    Format reading time as human-readable string.
    """
    if minutes == 0:
        return "Less than a minute"
    elif minutes == 1:
        return "1 minute read"
    else:
        return f"{minutes} minute read"
