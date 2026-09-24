"""
Table of Contents (TOC) Extractor
Parse markdown/HTML headings and populate table_of_contents JSON array
"""
import re
import html


class TOCExtractor:
    """Extract table of contents from markdown or HTML content"""
    
    def __init__(self, content: str, content_format: str = "markdown"):
        self.content = content
        self.content_format = content_format
        self.headings = []
    
    def extract(self) -> list:
        """Extract headings and return TOC structure"""
        if self.content_format == "html":
            self._extract_html_headings()
        elif self.content_format == "markdown":
            self._extract_markdown_headings()
        else:
            self._extract_html_headings()  # Default to HTML parsing
        
        return self._build_toc()
    
    def _extract_markdown_headings(self):
        """Extract headings from markdown format"""
        # Match # Heading syntax
        pattern = r'^(#{1,6})\s+(.+?)\s*#*\s*$'
        
        for line in self.content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                # Remove any inline markdown
                text = re.sub(r'[*_`\[\]]', '', text)
                self.headings.append({
                    "level": level,
                    "text": text,
                    "id": self._generate_id(text, level)
                })
    
    def _extract_html_headings(self):
        """Extract headings from HTML format"""
        # Match <h1>, <h2>, etc.
        pattern = r'<h([1-6])[^>]*>(.*?)</h\1>'
        
        for match in re.finditer(pattern, self.content, re.IGNORECASE | re.DOTALL):
            level = int(match.group(1))
            text = html.unescape(re.sub(r'<[^>]+>', '', match.group(2)).strip())
            text = re.sub(r'\s+', ' ', text)
            if text:
                self.headings.append({
                    "level": level,
                    "text": text,
                    "id": self._generate_id(text, level)
                })
    
    def _generate_id(self, text: str, level: int) -> str:
        """Generate unique ID for heading"""
        # Convert to lowercase, replace spaces with hyphens
        base_id = text.lower().replace(' ', '-')
        # Remove non-alphanumeric characters
        base_id = re.sub(r'[^a-z0-9-]', '', base_id)
        # Remove multiple hyphens
        base_id = re.sub(r'-+', '-', base_id)
        # Remove leading/trailing hyphens
        base_id = base_id.strip('-')
        
        if not base_id:
            base_id = f"h{level}-{len(self.headings) + 1}"
        
        # Ensure uniqueness
        original_id = base_id
        counter = 1
        while any(h.get("id") == base_id for h in self.headings):
            base_id = f"{original_id}-{counter}"
            counter += 1
        
        return base_id
    
    def _build_toc(self) -> list:
        """Build table of contents structure"""
        return [
            {
                "id": h["id"],
                "text": h["text"],
                "level": h["level"]
            }
            for h in self.headings
        ]


def extract_toc(content: str, content_format: str = "markdown") -> list:
    """
    Convenience function to extract table of contents.
    """
    extractor = TOCExtractor(content, content_format)
    return extractor.extract()
