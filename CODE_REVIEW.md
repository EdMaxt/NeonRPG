# Neon Odyssey Character Sheet Generator — Code Review Report

**Date:** 2026-10-07  
**Reviewer:** Automated Code Review  
**Files Reviewed:** `app.py`, `templates/index.html`, `static/style.css`, `template.pdf`

---

## Executive Summary

The application is a functional Flask web app that generates filled PDF character sheets for the Neon Odyssey TTRPG. The core PDF-filling logic works, but there are **critical field-mapping bugs**, **security concerns**, and **significant UX gaps** that should be addressed before production use.

---

## 1. Bugs & Field Mapping Issues

### 1.1 CRITICAL: First Spell Name Field Mismatch

The template PDF has spell name fields named `Spell Name 1` through `Spell Name 32`. The HTML JavaScript generates:
- `Spell Name` (no suffix) for the first spell → **does NOT match any template field**
- `Spell Name 1` through `Spell Name 31` for spells 2–32 → matches template fields 1–31

**Result:** The first spell's name is silently dropped. The template's `Spell Name 32` is never filled.

**Fix:** Change the JavaScript suffix logic so the first spell uses `Spell Name 1` (not `Spell Name`):
```javascript
const suffix = i === 0 ? ' 1' : ` ${i+1}`;
```

### 1.2 CRITICAL: Ability Score Field Names Are Misleading

The template has 8 ability score fields: `Score STR` through `Score STR 7`. The HTML generates only 6: `Score STR` through `Score STR 5`.

**Problems:**
- The field names are confusing — `Score STR 1` is actually DEX, `Score STR 2` is CON, etc.
- Template fields `Score STR 6` and `Score STR 7` are never filled
- The `Mod` and `Save` fields follow the same pattern

**Fix:** Rename fields to match their actual abilities:
- `Score STR`, `Score DEX`, `Score CON`, `Score INT`, `Score WIS`, `Score CHA`
- Update the template PDF field names to match, OR update the HTML to use the correct mapping

### 1.3 Faction Slot Count Mismatch

- Template has 12 faction slots: `Faction` through `Faction 11`
- HTML generates only 11: `Faction` through `Faction 10`
- **Result:** `Faction 11` and `Faction Score 11` are never filled

**Fix:** Change the loop to `i < 12` in the factions JavaScript.

### 1.4 Magic Item Slot Count Mismatch

- Template has 6 magic item slots: `Magic Item` through `Magic Item 5`
- HTML generates only 5: `Magic Item` through `Magic Item 4`
- **Result:** `Magic Item 5` is never filled

**Fix:** Change the loop to `i < 6` in the magic items JavaScript.

### 1.5 Unfilled Template Fields

These template fields have no corresponding HTML input and will always be empty:

| Template Field | Likely Purpose |
|---|---|
| `Player 1` | Second player / NPC name |
| `Speed 1` | Secondary speed (fly, swim, etc.) |
| `Score STR 6` | 7th ability score (possibly NPC or mount) |
| `Score STR 7` | 8th ability score |
| `Skill 1` – `Skill 19` | Individual skill note fields |
| `Total 1` – `Total 9` | Calculated totals (HP, weight, etc.) |

**Recommendation:** Either add these fields to the HTML form or remove them from the template if they're not needed.

### 1.6 "Skill" Field Name Collision

The HTML has:
- A text input named `Skill` (for "Skill Notes")
- 20 checkboxes named `Skills` through `Skills 19`

The template has:
- `Skill` through `Skill 19` (20 text fields for individual skill notes)
- `Skills` through `Skills 19` (20 checkbox fields)

**Result:** The HTML's single `Skill` text input maps to the template's `Skill` field, but `Skill 1` through `Skill 19` are never filled. The checkboxes map correctly.

**Recommendation:** Either add 19 more text inputs for individual skill notes, or clarify that only one "Skill Notes" field is needed.

---

## 2. Security Issues

### 2.1 CRITICAL: Debug Mode Enabled in Production

```python
app.run(debug=True, port=5000)
```

The Werkzeug debugger is exposed, which allows **arbitrary code execution** if an attacker can trigger an error. This is a well-known RCE vector.

**Fix:**
```python
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)  # debug=False by default
```

Use environment variables for configuration:
```python
import os
debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
app.run(debug=debug, port=int(os.environ.get("PORT", 5000)))
```

### 2.2 No CSRF Protection

The form has no CSRF token. While the impact is limited (the app only generates PDFs, no state changes), it's still a best practice to include CSRF protection, especially if the app is extended later.

**Fix:** Add Flask-WTF or implement a simple CSRF token:
```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

### 2.3 No Input Validation

All form data is passed directly to the PDF without validation. While pypdf will handle most malformed input gracefully, there's no guarantee.

**Fix:** Add server-side validation for critical fields:
```python
def generate():
    form_data = request.form.to_dict()
    
    # Validate character name
    char_name = form_data.get("Character Name", "").strip()
    if len(char_name) > 100:
        return "Character name too long", 400
    
    # Sanitize other fields as needed
    # ...
```

### 2.4 Filename Sanitization Is Insufficient

```python
safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in char_name)
```

This allows spaces and other characters that could cause issues on some filesystems. It also doesn't prevent path traversal if the input contains `..` (though the `os.path.basename` approach would be safer).

**Fix:**
```python
import re
safe_name = re.sub(r'[^\w\-_ ]', '_', char_name).strip()
safe_name = safe_name.replace(' ', '_')  # or keep spaces
if not safe_name:
    safe_name = 'character'
```

### 2.5 No Rate Limiting

An attacker could spam the `/generate` endpoint to exhaust server resources.

**Fix:** Add Flask-Limiter:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route("/generate", methods=["POST"])
@limiter.limit("10 per minute")
def generate():
    ...
```

---

## 3. Code Quality

### 3.1 Private Attribute Access

```python
if "/AcroForm" in writer._root_object:
    writer._root_object["/AcroForm"].update(...)
```

Using `_root_object` (a private attribute) is fragile and may break with pypdf updates.

**Fix:** Use the public API if available, or add a comment explaining why this is necessary:
```python
# pypdf doesn't expose NeedAppearances via public API yet
# See: https://github.com/py-pdf/pypdf/issues/XXX
```

### 3.2 No Error Handling

- No check if `template.pdf` exists
- No handling for corrupted PDF
- No handling for pypdf exceptions

**Fix:**
```python
import logging

logger = logging.getLogger(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        if not os.path.exists(TEMPLATE_PDF):
            logger.error("Template PDF not found: %s", TEMPLATE_PDF)
            return "Server configuration error", 500
        
        reader = PdfReader(TEMPLATE_PDF)
        # ...
    except Exception as e:
        logger.exception("PDF generation failed")
        return "Error generating PDF", 500
```

### 3.3 No Logging

The application has no logging whatsoever. This makes debugging production issues impossible.

**Fix:** Add basic logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### 3.4 No Tests

There are no unit tests or integration tests.

**Recommendation:** Add tests for:
- Field mapping correctness
- PDF generation with various inputs
- Edge cases (empty form, special characters, etc.)

### 3.5 Hardcoded Configuration

The template path and port are hardcoded.

**Fix:** Use environment variables or a config file:
```python
TEMPLATE_PDF = os.environ.get("TEMPLATE_PDF", os.path.join(BASE_DIR, "template.pdf"))
PORT = int(os.environ.get("PORT", 5000))
```

---

## 4. UX Problems

### 4.1 No Form Validation Feedback

Users get no feedback if they enter invalid data (e.g., negative HP, non-numeric level).

**Fix:** Add client-side validation:
```html
<input type="number" name="Level" min="1" max="20" required>
```
And server-side validation as described above.

### 4.2 No Loading Indicator

PDF generation may take a few seconds. Users have no feedback that anything is happening.

**Fix:** Add a loading spinner:
```javascript
document.getElementById('sheetForm').addEventListener('submit', function() {
    document.querySelector('.btn-generate').textContent = 'GENERANDO...';
    document.querySelector('.btn-generate').disabled = true;
});
```

### 4.3 No Auto-Save / Draft Functionality

If a user accidentally refreshes the page, all their input is lost.

**Fix:** Use `localStorage` to auto-save form data:
```javascript
// Save on input
document.getElementById('sheetForm').addEventListener('input', function() {
    localStorage.setItem('neonDraft', JSON.stringify(new FormData(this)));
});

// Restore on load
window.addEventListener('load', function() {
    const draft = localStorage.getItem('neonDraft');
    if (draft) {
        // Restore form values
    }
});
```

### 4.4 Excessive Spell Slots

32 spell slots is overwhelming for most users. Consider:
- Showing only 10 by default with an "Add more" button
- Or using a dynamic add/remove interface

### 4.5 Confusing Field Labels

- "Score STR 1" for DEX is confusing
- "Skill Notes" field named just "Skill" is ambiguous
- "Ability Save Prof" / "Ability Save 2" etc. don't indicate which ability they refer to

**Recommendation:** Use clear, descriptive labels that match the template PDF's visual layout.

### 4.6 No Preview Before Generating

Users can't see what the PDF will look like before downloading it.

**Recommendation:** Consider adding a preview mode or at least a summary of what will be filled.

### 4.7 Long Form Without Navigation

The form is very long with many collapsible sections. There's no way to jump to a specific section.

**Fix:** Add a sticky navigation bar or table of contents.

---

## 5. Missing Features

### 5.1 No Multi-Page Support

The template PDF may have multiple pages, but the code doesn't handle page-specific fields. If fields are on different pages, the current approach of iterating all pages and applying all fields to each page may cause issues.

**Recommendation:** Verify that `update_page_form_field_values` correctly handles fields that only exist on specific pages.

### 5.2 No PDF Flattening

The generated PDF has fillable form fields. Users may want a "flat" (non-editable) version for printing.

**Fix:** Add a "Flatten PDF" option:
```python
writer.flatten_pages()  # pypdf >= 3.12.0
```

### 5.3 No Custom Filename Option

The filename is auto-generated from the character name. Users may want to customize it.

**Fix:** Add a "Filename" input field.

### 5.4 No Save/Load Characters

Users can't save their character data and load it later.

**Recommendation:** Add JSON export/import functionality.

---

## 6. CSS / Styling Issues

### 6.1 No Print Styles

If users want to print the form (not the PDF), there are no print styles.

**Fix:** Add `@media print` rules.

### 6.2 No Dark/Light Mode Toggle

The app is dark-only. Some users may prefer light mode.

**Recommendation:** Add a theme toggle.

### 6.3 Responsive Design Gaps

The responsive breakpoints at 768px and 480px are good, but:
- The ability grid jumps from 3 columns to 2 to 1 — consider a smoother transition
- The grid-4 layout for attacks/spells may be too cramped on tablets

### 6.4 No Focus Indicators for Keyboard Navigation

The focus styles are minimal. Consider adding more visible focus indicators for accessibility.

---

## 7. Dependencies & Deployment

### 7.1 No Requirements File

There's no `requirements.txt` or `pyproject.toml`.

**Fix:** Create a `requirements.txt`:
```
flask>=3.0.0
pypdf>=4.0.0
```

### 7.2 No Docker Support

No Dockerfile for easy deployment.

**Recommendation:** Add a simple Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### 7.3 No Production WSGI Server

Using `app.run()` is not suitable for production.

**Fix:** Use gunicorn or waitress:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 8. Summary of Recommendations

### Must Fix (Critical)
1. **Disable debug mode** in production
2. **Fix spell name field mapping** (first spell name is lost)
3. **Fix faction slot count** (12 slots needed, not 11)
4. **Fix magic item slot count** (6 slots needed, not 5)
5. **Add error handling** for missing template and PDF generation failures

### Should Fix (Important)
6. **Rename ability score fields** to be less confusing
7. **Add CSRF protection**
8. **Add input validation**
9. **Add logging**
10. **Create requirements.txt**
11. **Add loading indicator** for UX
12. **Add auto-save/draft** functionality

### Nice to Have
13. Add tests
14. Add PDF flattening option
15. Add save/load character (JSON export/import)
16. Add print styles
17. Add theme toggle
18. Add rate limiting
19. Add Docker support
20. Use production WSGI server

---

## 9. Field Mapping Reference

### Correctly Mapped Fields
- Basic info: Character Name, Player, Class, Subclass, Species, Homeworld, Level, XP, Size, Speed, Armor, Initiative, HP Max, HP Temp, HD Max, HD Spent, Resistances, Features and Traits
- Attacks: Attack Name/Bonus/Damage/Notes (10 slots)
- Skills: Skills checkboxes (20 skills)
- Saving throws: Ability Save checkboxes (6), Death Save checkboxes (6)
- Exhaustion: 6 levels
- Heroic Inspiration
- Magic Item Attunement: 6 slots
- Equipment: Equipment, Languages, Feats and Professions, Weapon/Tool/Vehicle Proficiencies, Lifestyle
- Armor Proficiencies: Light, Medium, Heavy, Shields
- Spellcasting: Spell Attack Bonus, Spell Save DC, Spellcasting Modifier, Spellcasting Ability (3)
- Spell Slots: Spell Expended (28 slots with gaps)
- Notes: Notes, Galactic Notes

### Mismatched / Unfilled Fields
| HTML Field | Template Field | Issue |
|---|---|---|
| `Spell Name` (no suffix) | `Spell Name 1` – `Spell Name 32` | First spell name lost |
| `Faction` – `Faction 10` (11) | `Faction` – `Faction 11` (12) | 12th faction unfilled |
| `Magic Item` – `Magic Item 4` (5) | `Magic Item` – `Magic Item 5` (6) | 6th item unfilled |
| `Score STR` – `Score STR 5` (6) | `Score STR` – `Score STR 7` (8) | 7th/8th ability unfilled |
| `Skill` (1 field) | `Skill` – `Skill 19` (20 fields) | 19 skill note fields unfilled |
| — | `Player 1` | No HTML input |
| — | `Speed 1` | No HTML input |
| — | `Total 1` – `Total 9` | No HTML inputs |

---

*End of Report*
