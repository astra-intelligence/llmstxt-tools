# llmstxt-tools

Validate and generate `llms.txt` files for your website.

The [llms.txt standard](https://llmstxt.org/) helps AI systems discover and understand your website's content. This tool validates existing files and helps generate new ones.

## Installation

```bash
pip install llmstxt-tools
```

## Quick Start

### Check if a domain has an llms.txt

```bash
llmstxt check example.com
```

### Validate a local llms.txt file

```bash
llmstxt validate ./llms.txt

# JSON output
llmstxt validate ./llms.txt --json
```

### Generate a new llms.txt from a sitemap (premium)

```bash
llmstxt generate --sitemap https://example.com/sitemap.xml
```

### Manage your premium license

```bash
llmstxt license set LLMSTXT-ABCD-1234-EFGH
llmstxt license check
```

## Commands

| Command | Description | Free | Premium |
|---------|-------------|------|---------|
| `check <domain>` | Check a domain's llms.txt | ✓ | ✓ |
| `validate <file>` | Validate a local llms.txt file | ✓ | ✓ |
| `generate` | Generate an llms.txt from a sitemap | Basic | Full |
| `license` | Manage your premium license | ✓ | ✓ |

## Premium Features

- Generate llms.txt from sitemap URLs
- Custom section configuration
- Priority support

Get a premium license: https://grantshatz.gumroad.com/l/llmstxt-pro

## License

MIT