"""CLI entry point for llmstxt-tools."""

import argparse
import sys
import json
from pathlib import Path

from . import __version__
from .core import (
    check_live_llmstxt,
    validate_llmstxt,
    generate_llmstxt,
    generate_from_sitemap,
    fetch_url,
)
from .license import (
    get_stored_license,
    store_license,
    validate_license,
    check_premium,
    require_premium,
    GUMROAD_PRODUCT_URL,
)


def cmd_check(args):
    """Check a domain's llms.txt file."""
    result = check_live_llmstxt(args.domain)
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    if not result.get("exists"):
        print(f"\n  ✗ No llms.txt found at {result.get('url', '')}")
        print(f"    HTTP {result.get('status')}: {result.get('message', '')}")
        print(f"\n  Generate one from your sitemap: llmstxt generate --sitemap <url>")
        print(f"  Premium license: {GUMROAD_PRODUCT_URL}")
        return
    
    url = result.get("url", "")
    status = result.get("summary", "")
    score = result.get("score", 0)
    
    if status == "PASS":
        icon = "✓"
        color = ""
    else:
        icon = "!"
        color = ""
    
    print(f"\n  {icon} llms.txt at {url}")
    print(f"    Score: {score}/100 | Status: {status}")
    print()
    
    for check in result.get("checks", []):
        mark = "✓" if check["pass"] else "✗"
        print(f"  {mark} {check['check']}: {check['detail']}")
    
    if score < 100:
        print(f"\n  💡 Want to see how other sites handle this? Generate your own llms.txt:")
        print(f"     llmstxt generate --sitemap <your-sitemap-url>  (premium)")
        print(f"     {GUMROAD_PRODUCT_URL}")


def cmd_validate(args):
    """Validate an llms.txt file from disk."""
    content = Path(args.file).read_text(encoding="utf-8")
    result = validate_llmstxt(content, args.file)
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    status = result.get("summary", "")
    score = result.get("score", 0)
    icon = "✓" if result["valid"] else "!"
    
    print(f"\n  {icon} Validation: {status} (Score: {score}/100)")
    print()
    for check in result.get("checks", []):
        mark = "✓" if check["pass"] else "✗"
        print(f"  {mark} {check['check']}: {check['detail']}")


def cmd_generate(args):
    """Generate an llms.txt file."""
    sections = []
    
    if args.sitemap:
        if not require_premium("generate --sitemap"):
            return
        result, message = generate_from_sitemap(args.sitemap, args.max_pages)
        if result is None:
            print(f"\n  ✗ {message}")
            return
        print(f"\n  ✓ {message}")
        print()
        print(result)
        
        if args.output:
            Path(args.output).write_text(result)
            print(f"\n  Saved to {args.output}")
        return
    
    # Simple manual generation
    if args.sections:
        for s in args.sections:
            heading, *links_str = s.split("::", 1)
            links = []
            if links_str:
                for link_spec in links_str[0].split("|"):
                    parts = link_spec.strip().split("::")
                    if len(parts) >= 2:
                        links.append({"title": parts[0], "url": parts[1]})
            sections.append({"heading": heading.strip(), "links": links})
    
    result = generate_llmstxt(
        title=args.title or "Website llms.txt",
        description=args.description or "",
        sections=sections,
    )
    
    print(result)
    
    if args.output:
        Path(args.output).write_text(result)
        print(f"\n  Saved to {args.output}")


def cmd_license(args):
    """Manage license keys."""
    if args.action == "set":
        key = args.key.upper().strip()
        if validate_license(key):
            store_license(key)
            print(f"\n  ✓ License key saved: {key}")
        else:
            print(f"\n  ✗ Invalid license key format.")
            print(f"    Expected format: LLMSTXT-XXXX-XXXX-XXXX")
    
    elif args.action == "show":
        stored = get_stored_license()
        if stored:
            print(f"\n  License key: {stored}")
        else:
            print(f"\n  No license key stored.")
            print(f"  Get one at: {GUMROAD_PRODUCT_URL}")
    
    elif args.action == "check":
        if check_premium():
            print(f"\n  ✓ Premium features are active!")
        else:
            print(f"\n  ✗ Premium is not active.")
            print(f"  Get a license: {GUMROAD_PRODUCT_URL}")
    
    elif args.action == "remove":
        lic_file = Path.home() / ".config" / "llmstxt-tools" / "license.json"
        if lic_file.exists():
            lic_file.unlink()
            print(f"\n  ✓ License removed")
        else:
            print(f"\n  No license to remove")


def main():
    parser = argparse.ArgumentParser(
        prog="llmstxt",
        description="Validate and generate llms.txt files for your website",
        epilog=f"v{__version__} | {GUMROAD_PRODUCT_URL}",
    )
    parser.add_argument("--version", action="version", version=f"llmstxt-tools v{__version__}")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    sub = parser.add_subparsers(dest="command")
    
    # check
    p_check = sub.add_parser("check", help="Check a domain's llms.txt")
    p_check.add_argument("domain", help="Domain name (e.g., example.com)")
    p_check.set_defaults(func=cmd_check)
    
    # validate
    p_val = sub.add_parser("validate", help="Validate an llms.txt file")
    p_val.add_argument("file", help="Path to llms.txt file")
    p_val.set_defaults(func=cmd_validate)
    
    # generate
    p_gen = sub.add_parser("generate", help="Generate an llms.txt file")
    p_gen.add_argument("--title", help="Site title")
    p_gen.add_argument("--description", "-d", help="Site description")
    p_gen.add_argument("--sitemap", "-s", help="Generate from sitemap URL (premium)")
    p_gen.add_argument("--max-pages", type=int, default=20, help="Max pages from sitemap")
    p_gen.add_argument("--output", "-o", help="Output file path")
    p_gen.add_argument("--sections", nargs="*", help="Sections (premium): 'Heading::Title::url|Title2::url2'")
    p_gen.set_defaults(func=cmd_generate)
    
    # license
    p_lic = sub.add_parser("license", help="Manage premium license")
    p_lic.add_argument("action", choices=["set", "show", "check", "remove"])
    p_lic.add_argument("key", nargs="?", help="License key (for 'set')")
    p_lic.set_defaults(func=cmd_license)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print(f"\n  Get premium: {GUMROAD_PRODUCT_URL}")
        return
    
    args.func(args)


if __name__ == "__main__":
    main()