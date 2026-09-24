"""
Test script for services and utilities
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_slug_generator():
    """Test slug generation utilities"""
    print("Testing slug generator...")
    from utils.slug_generator import generate_slug, generate_unique_hash
    
    # Test basic slug generation
    slug = generate_slug("Hello World")
    assert slug == "hello-world", f"Expected 'hello-world', got '{slug}'"
    print(f"  ✓ Basic slug: 'Hello World' -> '{slug}'")
    
    slug = generate_slug("Test Article Title")
    assert slug == "test-article-title", f"Expected 'test-article-title', got '{slug}'"
    print(f"  ✓ Multi-word slug: 'Test Article Title' -> '{slug}'")
    
    # Test hash generation
    hash1 = generate_unique_hash()
    assert len(hash1) == 6, f"Expected hash length 6, got {len(hash1)}"
    print(f"  ✓ Generated hash: '{hash1}' (length: {len(hash1)})")
    
    print("✓ Slug generator tests passed\n")


def test_reading_time():
    """Test reading time calculator"""
    print("Testing reading time calculator...")
    from utils.reading_time import calculate_reading_time, format_reading_time, count_words
    
    # Test word counting
    text = "This is a test. Hello world."
    words = count_words(text)
    assert words == 6, f"Expected 6 words, got {words}"
    print(f"  ✓ Word count: '{text}' -> {words} words")
    
    # Test reading time calculation
    text = "word " * 200  # 200 words = 1 minute
    reading_time = calculate_reading_time(text)
    assert reading_time >= 1, f"Expected at least 1 minute, got {reading_time}"
    print(f"  ✓ Reading time (200 words): {reading_time} minutes")
    
    # Test formatting
    formatted = format_reading_time(1)
    assert formatted == "1 minute read", f"Expected '1 minute read', got '{formatted}'"
    print(f"  ✓ Formatted (1 min): '{formatted}'")
    
    formatted = format_reading_time(5)
    assert formatted == "5 minute read", f"Expected '5 minute read', got '{formatted}'"
    print(f"  ✓ Formatted (5 min): '{formatted}'")
    
    formatted = format_reading_time(0)
    assert formatted == "Less than a minute", f"Expected 'Less than a minute', got '{formatted}'"
    print(f"  ✓ Formatted (0 min): '{formatted}'")
    
    print("✓ Reading time tests passed\n")


def test_toc_extractor():
    """Test TOC extraction"""
    print("Testing TOC extractor...")
    from utils.toc_extractor import extract_toc
    
    # Test markdown TOC extraction
    markdown = """
# Main Title
Some content here.

## Section 1
More content.

### Subsection 1.1
Even more content.

## Section 2
Final content.
"""
    toc = extract_toc(markdown, "markdown")
    assert len(toc) == 4, f"Expected 4 headings, got {len(toc)}"
    print(f"  ✓ Markdown TOC: Extracted {len(toc)} headings")
    assert toc[0]["text"] == "Main Title", "Expected 'Main Title'"
    assert toc[1]["text"] == "Section 1", "Expected 'Section 1'"
    assert toc[2]["level"] == 3, "Expected level 3 for subsection"
    print(f"  ✓ Heading levels: {[(h['text'], h['level']) for h in toc]}")
    
    # Test HTML TOC extraction
    html = """
<h1>Main Title</h1>
<p>Content</p>
<h2>Section 1</h2>
<p>More content</p>
<h3>Subsection</h3>
<p>Final content</p>
"""
    toc = extract_toc(html, "html")
    assert len(toc) == 3, f"Expected 3 headings, got {len(toc)}"
    print(f"  ✓ HTML TOC: Extracted {len(toc)} headings")
    
    print("✓ TOC extractor tests passed\n")


def test_pagination():
    """Test pagination utilities"""
    print("Testing pagination...")
    from utils.pagination import PaginationParams, PaginationResult
    
    # Test pagination params
    params = PaginationParams(page=1, page_size=10)
    assert params.offset == 0, f"Expected offset 0, got {params.offset}"
    print(f"  ✓ Page 1 offset: {params.offset}")
    
    params = PaginationParams(page=2, page_size=10)
    assert params.offset == 10, f"Expected offset 10, got {params.offset}"
    print(f"  ✓ Page 2 offset: {params.offset}")
    
    # Test pagination result
    result = PaginationResult(
        items=["a", "b", "c"],
        total=25,
        page=1,
        page_size=10
    )
    assert result.total_pages == 3, f"Expected 3 pages, got {result.total_pages}"
    print(f"  ✓ Total pages (25 items, 10/page): {result.total_pages}")
    assert result.has_next == True, "Expected has_next=True"
    print(f"  ✓ Has next page: {result.has_next}")
    
    result_dict = result.to_dict()
    assert "total_pages" in result_dict, "to_dict() should include total_pages"
    print(f"  ✓ Pagination dict: keys={list(result_dict.keys())}")
    
    print("✓ Pagination tests passed\n")


def test_healthcare_safeguards():
    """Test healthcare safeguards"""
    print("Testing healthcare safeguards...")
    from utils.healthcare_safeguards import (
        validate_healthcare_content,
        add_healthcare_disclaimer,
        format_healthcare_payload
    )
    
    # Test validation - valid healthcare content
    valid_data = {
        "author": {"name": "Dr. Smith", "credentials": "MD"},
        "references": [{"title": "Source", "source": "https://example.com"}],
        "content": "Medical content here"
    }
    is_valid, errors = validate_healthcare_content(valid_data)
    assert is_valid, f"Expected valid, got errors: {errors}"
    print("  ✓ Valid healthcare content passed validation")
    
    # Test validation - missing author credentials
    invalid_data = {
        "author": {"name": "Dr. Smith"},  # Missing credentials
        "references": [{"title": "Source"}],  # Missing source
        "content": "Medical content"
    }
    is_valid, errors = validate_healthcare_content(invalid_data)
    assert not is_valid, "Expected validation to fail"
    print(f"  ✓ Invalid content failed validation: {len(errors)} errors")
    
    # Test disclaimer addition
    content = "Some medical information."
    with_disclaimer = add_healthcare_disclaimer(content)
    assert "DISCLAIMER" in with_disclaimer, "Disclaimer not added"
    print("  ✓ Disclaimer added to content")
    
    # Test healthcare payload formatting
    article_data = {
        "title": "Medical Article",
        "blog_type": "HEALTHCARE"
    }
    formatted = format_healthcare_payload(article_data)
    assert "_healthcare" in formatted, "_healthcare metadata not added"
    print("  ✓ Healthcare metadata added to payload")
    
    print("✓ Healthcare safeguards tests passed\n")


def main():
    print("=" * 50)
    print("Testing Services & Utilities")
    print("=" * 50)
    print()
    
    try:
        test_slug_generator()
        test_reading_time()
        test_toc_extractor()
        test_pagination()
        test_healthcare_safeguards()
        
        print("=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
