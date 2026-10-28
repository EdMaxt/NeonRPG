import io
import json
import logging
import os
import re
import secrets
import uuid
from datetime import datetime, timezone

from flask import Flask, render_template, request, send_file, abort
from flask_wtf import CSRFProtect
from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject
from pypdf.errors import PdfReadError
from io import BytesIO
import pymupdf  # PDF flattening: fill and bake form fields

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("neon_odyssey")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Secret key — used for CSRF token signing. Persisted to disk so that
# restarting the server does NOT invalidate tokens already issued to open
# browser tabs. Override with FLASK_SECRET_KEY in production.
SECRET_KEY_PATH = os.path.join(BASE_DIR, ".flask_secret")
if os.environ.get("FLASK_SECRET_KEY"):
    _secret_key = os.environ["FLASK_SECRET_KEY"]
elif os.path.isfile(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, "r", encoding="utf-8") as _f:
        _secret_key = _f.read().strip()
else:
    _secret_key = secrets.token_hex(32)
    try:
        with open(SECRET_KEY_PATH, "w", encoding="utf-8") as _f:
            _f.write(_secret_key)
    except OSError as _exc:
        logger.warning("Could not persist secret key to %s: %s", SECRET_KEY_PATH, _exc)

app.config["SECRET_KEY"] = _secret_key
app.config["WTF_CSRF_ENABLED"] = True
app.config["WTF_CSRF_TIME_LIMIT"] = 86400  # 24 hours

csrf = CSRFProtect(app)

TEMPLATE_PDF = os.path.join(BASE_DIR, "template.pdf")

# Directory for storing generated preview PDFs (for the preview endpoint)
TEMP_DIR = os.path.join(BASE_DIR, "temp")

MAX_NAME_LENGTH = 64

# Mapping from HTML field names to PDF template field names.
# The template numbers the non-STR abilities (DEX=1, CON=2, INT=3, WIS=4, CHA=5).
ABILITY_SCORE_MAP = {
    "Score DEX": "Score STR 1",
    "Mod DEX": "Mod STR 1",
    "Save DEX": "Save STR 1",
    "Ability Save DEX": "Ability Save 1",
    "Score CON": "Score STR 2",
    "Mod CON": "Mod STR 2",
    "Save CON": "Save STR 2",
    "Ability Save CON": "Ability Save 2",
    "Score INT": "Score STR 3",
    "Mod INT": "Mod STR 3",
    "Save INT": "Save STR 3",
    "Ability Save INT": "Ability Save 3",
    "Score WIS": "Score STR 4",
    "Mod WIS": "Mod STR 4",
    "Save WIS": "Save STR 4",
    "Ability Save WIS": "Ability Save 4",
    "Score CHA": "Score STR 5",
    "Mod CHA": "Mod STR 5",
    "Save CHA": "Save STR 5",
    "Ability Save CHA": "Ability Save 5",
    # STR maps to the un-suffixed "Ability Save" field
    "Ability Save STR": "Ability Save",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_filename(name: str) -> str:
    """Return a filesystem-safe filename fragment from *name*."""
    safe = re.sub(r"[^\w\- ]", "_", name, flags=re.UNICODE)
    safe = re.sub(r"\s+", " ", safe).strip()
    safe = safe[:MAX_NAME_LENGTH].strip()
    return safe or "character"


def _validate_character_name(name: str) -> str | None:
    """Return an error message if *name* is invalid, else None."""
    if not name or not name.strip():
        return "Character name is required."
    if len(name) > MAX_NAME_LENGTH:
        return f"Character name must be {MAX_NAME_LENGTH} characters or fewer."
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Render the main character sheet form."""
    logger.debug("Serving index page")
    return render_template("index.html")


@app.context_processor
def inject_game_data():
    """Always make game data available to every template."""
    game_data_path = os.path.join(BASE_DIR, "game_data.json")
    if os.path.isfile(game_data_path):
        try:
            with open(game_data_path, "r", encoding="utf-8") as f:
                return {"game_data": json.load(f)}
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load game_data.json: %s", exc)
    return {"game_data": {}}


@app.route("/health")
def health():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "ok", "template_exists": os.path.exists(TEMPLATE_PDF)}, 200


@app.route("/generate", methods=["POST"])
def generate():
    """Generate and return a filled PDF character sheet."""
    logger.info("Received PDF generation request from %s", request.remote_addr)

    form_data = request.form.to_dict()
    logger.debug("Form data keys: %s", list(form_data.keys()))

    # --- Input validation ---------------------------------------------------
    char_name = form_data.get("Character Name", "").strip()
    name_error = _validate_character_name(char_name)
    if name_error:
        logger.warning("Validation failed: %s", name_error)
        return render_template("index.html", error=name_error), 400

    # --- Read template ------------------------------------------------------
    if not os.path.isfile(TEMPLATE_PDF):
        logger.error("Template PDF not found at %s", TEMPLATE_PDF)
        return render_template(
            "index.html", error="Server misconfiguration: template PDF is missing."
        ), 500

    try:
        reader = PdfReader(TEMPLATE_PDF)
    except (PdfReadError, OSError) as exc:
        logger.error("Failed to read template PDF: %s", exc)
        return render_template(
            "index.html", error="Failed to read the character sheet template."
        ), 500

    # --- Build output PDF ---------------------------------------------------
    writer = PdfWriter(clone_from=reader)
    form_data = request.form.to_dict(flat=False)

    # Multi-select fields arrive as lists; join them for the single-line PDF fields
    MULTI_SELECT_FIELDS = {
        "Languages",
        "Feats and Professions",
        "Weapon Proficiencies",
        "Tool Proficiencies",
    }
    flat_data = {}
    for key, values in form_data.items():
        if key in MULTI_SELECT_FIELDS and isinstance(values, list):
            flat_data[key] = ", ".join(v for v in values if v)
        else:
            flat_data[key] = values[0] if values else ""

    # Translate ability score field names to match PDF template
    for html_name, pdf_name in ABILITY_SCORE_MAP.items():
        if html_name in flat_data:
            flat_data[pdf_name] = flat_data.pop(html_name)

    for page in writer.pages:
        writer.update_page_form_field_values(page, flat_data)

    # Set NeedAppearances so viewers regenerate field appearances
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"].update(
            {"/NeedAppearances": BooleanObject(True)}
        )

    output = io.BytesIO()
    try:
        writer.write(output)
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        return render_template(
            "index.html", error="An unexpected error occurred while generating the PDF."
        ), 500
    output.seek(0)

    # --- Apply PDF flattening if requested -----------------------------------
    if request.form.get("flattenPDF") == "/Yes":
        # Fill and bake form fields using pymupdf to produce a non-editable PDF
        pdf_bytes = output.getvalue()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            for widget in page.widgets():
                try:
                    widget.update()
                except Exception as exc:
                    logger.warning("Widget update failed: %s", exc)
        doc.bake(widgets=True, annots=True)
        flat_output = doc.tobytes()
        doc.close()
        output = BytesIO(flat_output)
        output.seek(0)

    # --- Build download filename --------------------------------------------
    safe_name = _safe_filename(char_name)
    filename = f"{safe_name}_Neon_Odyssey.pdf"

    logger.info("Generated sheet for '%s' (%d bytes)", char_name, output.getbuffer().nbytes)

    # --- Save preview PDF to temp directory ---------------------------------
    os.makedirs(TEMP_DIR, exist_ok=True)
    preview_name = f"{uuid.uuid4().hex}_Neon_Odyssey.pdf"
    preview_path = os.path.join(TEMP_DIR, preview_name)
    with open(preview_path, "wb") as f:
        f.write(output.getvalue())

    logger.info("Generated sheet for '%s' (%d bytes)", char_name, os.path.getsize(preview_path))

    # --- Show preview page ---------------------------------------------------
    return render_template(
        "preview.html",
        pdf_filename=preview_name,
        char_name=char_name,
        now_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


# ---------------------------------------------------------------------------
# PDF preview endpoints
# ---------------------------------------------------------------------------
@app.route("/preview/<filename>")
def preview(filename):
    """Serve a preview PDF inline (for the iframe)."""
    if ".." in filename or "/" in filename or "\\" in filename:
        abort(404)
    filepath = os.path.join(TEMP_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(filepath, mimetype="application/pdf", as_attachment=False)


@app.route("/download/<filename>")
def download(filename):
    """Trigger a download of a previously generated sheet."""
    if ".." in filename or "/" in filename or "\\" in filename:
        abort(404)
    filepath = os.path.join(TEMP_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_):
    return render_template("index.html", error="Page not found."), 404


@app.errorhandler(500)
def internal_error(_):
    return render_template(
        "index.html", error="An internal server error occurred."
    ), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    logger.info("Starting Neon Odyssey on port %d (debug=%s)", port, debug_mode)
    app.run(debug=debug_mode, port=port)
