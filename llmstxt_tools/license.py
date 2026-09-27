"""License key validation for premium features."""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".config" / "llmstxt-tools"
LICENSE_FILE = CONFIG_DIR / "license.json"
GUMROAD_PRODUCT_URL = "https://grantshatz.gumroad.com/l/llmstxt-pro"


def get_stored_license() -> Optional[str]:
    """Get stored license key from config file."""
    if LICENSE_FILE.exists():
        try:
            data = json.loads(LICENSE_FILE.read_text())
            return data.get("key")
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def store_license(key: str) -> None:
    """Store a license key."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(json.dumps({"key": key, "version": 1}))


def validate_license(key: str) -> bool:
    """Validate a license key format.
    
    License keys follow format: LLMSTXT-XXXX-XXXX-XXXX
    Where X is alphanumeric. This is a lightweight client-side check.
    The actual license validation happens on the Gumroad side.
    """
    import re
    pattern = r'^LLMSTXT-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
    return bool(re.match(pattern, key))


def check_premium() -> bool:
    """Check if premium features are available."""
    key = get_stored_license()
    if key and validate_license(key):
        return True
    return False


def require_premium(command_name: str) -> bool:
    """Check premium and print message if not available."""
    if check_premium():
        return True
    
    print(f"\n  ✗ '{command_name}' requires a premium license.")
    print(f"\n  Get your license key:")
    print(f"  {GUMROAD_PRODUCT_URL}")
    print(f"\n  Then activate with: llmstxt license set <KEY>")
    return False