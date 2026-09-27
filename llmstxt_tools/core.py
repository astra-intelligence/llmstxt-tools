"""Core validation and generation logic for llms.txt files."""

import re
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


# The llms.txt spec (v2) requires:
# - A file named llms.txt at the root of a domain
# - UTF-8 encoded
# - Markdown format with specific sections
# - Optional: llms-full.txt for complete content

SPEC_URL = "https://llmstxt.org/"


def fetch_url(url: str, timeout: int = 15) -> Tuple[str, int]:
    """Fetch a URL and return (content, status_code).
    
    Uses urllib to avoid external dependencies.
    Falls back to printing instructions if fetch fails.
    """
    import urllib.request
    import urllib.error
    
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "llmstxt-tools/0.1.0 (llmstxt validator; +https://github.com/astra-intelligence/llmstxt-tools)",
            "Accept": "text/markdown, text/plain, */*",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            return content, resp.status
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", errors="replace"), e.code
    except urllib.error.URLError as e:
        return f"DNS/connection error: {e.reason}", 0
    except Exception as e:
        return f"Error: {e}", 0


def validate_llmstxt(content: str, url: str = "") -> Dict:
    """Validate an llms.txt file against the spec.
    
    Returns a dict with:
    - valid: bool
    - score: int (0-100)
    - checks: list of check results
    """
    checks = []
    score = 100
    
    # Check 1: Non-empty
    if not content.strip():
        checks.append({"check": "non-empty", "pass": False, 
                       "detail": "File is empty"})
        return {"valid": False, "score": 0, "checks": checks}
    checks.append({"check": "non-empty", "pass": True, "detail": f"{len(content)} chars"})
    
    lines = content.split("\n")
    
    # Check 2: Has a title (first line should be # Title)
    first_line = lines[0].strip() if lines else ""
    if first_line.startswith("# ") and not first_line.startswith("## "):
        title = first_line[2:].strip()
        checks.append({"check": "has-title", "pass": True, "detail": f"Title: {title}"})
    else:
        score -= 15
        checks.append({"check": "has-title", "pass": False, 
                       "detail": "First line should be a H1 heading (# Title)"})
    
    # Check 3: Has a description/lead paragraph
    has_lead = False
    for line in lines[1:5]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("-") and not stripped.startswith("> "):
            has_lead = True
            break
    if has_lead:
        checks.append({"check": "has-description", "pass": True, "detail": "Has lead paragraph"})
    else:
        score -= 10
        checks.append({"check": "has-description", "pass": False, 
                       "detail": "Add a lead paragraph describing the site/content"})
    
    # Check 4: Contains links
    link_count = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
    if link_count > 0:
        checks.append({"check": "has-links", "pass": True, "detail": f"{link_count} links found"})
    else:
        score -= 20
        checks.append({"check": "has-links", "pass": False, 
                       "detail": "No markdown links found. llms.txt should link to key pages"})
    
    # Check 5: Has section headers
    section_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
    if section_count > 0:
        checks.append({"check": "has-sections", "pass": True, "detail": f"{section_count} sections found"})
    else:
        score -= 10
        checks.append({"check": "has-sections", "pass": False,
                       "detail": "No H2 sections found. Use ## headings to organize content"})
    
    # Check 6: Encoding - check for non-ASCII without being markdown
    try:
        content.encode("utf-8")
        checks.append({"check": "utf-8", "pass": True, "detail": "Valid UTF-8"})
    except UnicodeEncodeError:
        score -= 5
        checks.append({"check": "utf-8", "pass": False, "detail": "Contains non-UTF-8 characters"})
    
    # Check 7: Not too long (llms.txt should be concise, < 100KB)
    if len(content) > 100_000:
        score -= 10
        checks.append({"check": "file-size", "pass": False,
                       "detail": f"{len(content)} bytes - llms.txt should be < 100KB"})
    else:
        checks.append({"check": "file-size", "pass": True, "detail": f"{len(content)} bytes"})
    
    # Valid if score >= 50
    valid = score >= 50
    
    return {
        "valid": valid,
        "score": max(0, score),
        "checks": checks,
        "summary": "PASS" if valid else "NEEDS WORK",
    }


def check_live_llmstxt(domain: str) -> Dict:
    """Check a live domain's llms.txt file."""
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    url = domain.rstrip("/") + "/llms.txt"
    
    content, status = fetch_url(url)
    
    if status == 404:
        return {
            "url": url,
            "exists": False,
            "status": 404,
            "message": "No llms.txt found at this URL",
        }
    
    if status != 200:
        return {
            "url": url,
            "exists": False,
            "status": status,
            "message": f"HTTP {status}",
        }
    
    validation = validate_llmstxt(content, url)
    validation["url"] = url
    validation["exists"] = True
    validation["status"] = 200
    validation["content_preview"] = content[:500] + ("..." if len(content) > 500 else "")
    
    return validation


def generate_llmstxt(
    title: str,
    description: str,
    sections: Optional[List[Dict]] = None,
) -> str:
    """Generate an llms.txt file from provided data.
    
    sections: list of {"heading": str, "links": [{"title": str, "url": str, "description": str}]}
    """
    lines = [f"# {title}", "", description, ""]
    
    if sections:
        for section in sections:
            lines.append(f"## {section['heading']}")
            lines.append("")
            for link in section.get("links", []):
                desc = f" — {link.get('description', '')}" if link.get("description") else ""
                lines.append(f"- [{link['title']}]({link['url']}){desc}")
            lines.append("")
    
    # Remove trailing empty lines
    while lines and lines[-1] == "":
        lines.pop()
    lines.append("")  # Final newline
    
    return "\n".join(lines)


def generate_from_sitemap(sitemap_url: str, max_pages: int = 20) -> Tuple[Optional[str], str]:
    """Generate a basic llms.txt from a sitemap URL.
    
    Returns (content or None, message).
    """
    content, status = fetch_url(sitemap_url)
    
    if status != 200:
        return None, f"Failed to fetch sitemap (HTTP {status})"
    
    # Try to parse as XML sitemap
    urls = re.findall(r'<loc>(.*?)</loc>', content)
    
    if not urls:
        # Try RSS/Atom
        urls = re.findall(r'<link>(.*?)</link>', content)
    
    if not urls:
        return None, "No URLs found in sitemap"
    
    urls = urls[:max_pages]
    
    # Try to extract titles from URLs for better link text
    sections = [{
        "heading": "Pages",
        "links": [
            {
                "title": url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title() or "Home",
                "url": url,
            }
            for url in urls
        ]
    }]
    
    title = f"{urlparse(sitemap_url).hostname or 'Website'} llms.txt"
    result = generate_llmstxt(
        title=title,
        description=f"Key pages from {urlparse(sitemap_url).hostname or 'the site'}.",
        sections=sections,
    )
    
    return result, f"Generated llms.txt with {len(urls)} URLs from sitemap"