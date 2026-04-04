"""
Report templates for Showmaster.

Usage:
    from showmaster.templates import TEMPLATES, apply_template
    apply_template("bug_report", filepath, title="Login crash")
"""
from pathlib import Path


TEMPLATES = {
    "bug_report": {
        "name": "Bug Report",
        "description": "Structured bug report with reproduction steps",
        "content": """\
# {title}

**Reporter:** {author}
**Date:** {date}
**Severity:** {severity}

---

## Summary

_Brief description of the issue._

## Environment

### System Info
```
(run `uname -a` or `systeminfo`)
```

## Steps to Reproduce

1. Step one
2. Step two
3. Step three

## Expected Behavior

_What you expected to happen._

## Actual Behavior

_What actually happened._

## Screenshots / Logs

_Attach relevant screenshots or error logs._

## Additional Context

_Any other information that might help._
""",
        "defaults": {"severity": "Medium", "author": ""},
    },

    "feature_demo": {
        "name": "Feature Demo",
        "description": "Showcase a new feature with before/after",
        "content": """\
# {title}

**Author:** {author}
**Date:** {date}

---

## Overview

_Describe the feature being demonstrated._

## Before

_State of things before this feature._

## Implementation

### Key Changes

_Describe the core changes._

### Code Walkthrough

```
(add code snippets or run Showmaster exec commands)
```

## After / Demo

_Show the feature in action._

## Performance Impact

_Any performance considerations._

## Next Steps

- [ ] Item 1
- [ ] Item 2
""",
        "defaults": {"author": ""},
    },

    "api_walkthrough": {
        "name": "API Walkthrough",
        "description": "Document API endpoints with examples",
        "content": """\
# {title}

**Author:** {author}
**Date:** {date}
**Base URL:** `{base_url}`

---

## Authentication

_Describe authentication method (API key, OAuth, etc.)._

## Endpoints

### GET /endpoint

**Description:** _What this endpoint does._

**Request:**
```bash
curl -X GET {base_url}/endpoint -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{{
    "status": "ok"
}}
```

### POST /endpoint

**Description:** _What this endpoint does._

**Request:**
```bash
curl -X POST {base_url}/endpoint \\
  -H "Content-Type: application/json" \\
  -d '{{"key": "value"}}'
```

**Response:**
```json
{{
    "id": 1,
    "created": true
}}
```

## Error Handling

| Code | Meaning |
|------|---------|
| 400  | Bad Request |
| 401  | Unauthorized |
| 404  | Not Found |
| 500  | Server Error |

## Rate Limits

_Describe any rate limiting._

## SDKs / Libraries

_Links to client libraries._
""",
        "defaults": {"base_url": "https://api.example.com", "author": ""},
    },

    "project_setup": {
        "name": "Project Setup Guide",
        "description": "Document project setup and configuration",
        "content": """\
# {title}

**Author:** {author}
**Date:** {date}

---

## Prerequisites

- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Installation

### Step 1: Clone Repository
```bash
git clone <repo-url>
cd <project>
```

### Step 2: Install Dependencies
```bash
# Add install commands
```

### Step 3: Configuration
```bash
# Add config commands
```

## Running the Project

### Development
```bash
# Dev server command
```

### Production
```bash
# Production build command
```

## Testing

```bash
# Test command
```

## Troubleshooting

### Common Issues

1. **Issue**: _Description_
   **Fix**: _Solution_

2. **Issue**: _Description_
   **Fix**: _Solution_

## Resources

- [Documentation](link)
- [Issue Tracker](link)
""",
        "defaults": {"author": ""},
    },
}


def list_templates():
    """Return a list of (key, name, description) tuples."""
    return [
        (key, t["name"], t["description"])
        for key, t in TEMPLATES.items()
    ]


def apply_template(template_key, filepath, **kwargs):
    """Write a template to a file, substituting placeholders."""
    import datetime

    template = TEMPLATES.get(template_key)
    if not template:
        raise ValueError(
            f"Unknown template: {template_key}. "
            f"Available: {', '.join(TEMPLATES.keys())}"
        )

    # Merge defaults with user-provided values
    values = {**template["defaults"], **kwargs}
    values.setdefault("date", datetime.date.today().isoformat())
    values.setdefault("title", "Untitled Report")
    values.setdefault("author", "")

    content = template["content"].format(**values)
    Path(filepath).write_text(content)
    return f"Template '{template['name']}' applied to {filepath}"
