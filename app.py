import io
import json
import logging
import os
import re
import secrets

from flask import Flask, render_template, request, send_file
from flask_wtf import CSRFProtect
from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject
from pypdf.errors import PdfReadError

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

# Secret key — used for CSRF token signing. In production set via env var.
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["WTF_CSRF_ENABLED"] = True
app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hour

csrf = CSRFProtect(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PDF = os.path.join(BASE_DIR, "template.pdf")

MAX_NAME_LENGTH = 64

# Mapping from HTML field names to PDF template field names for ability scores
ABILITY_SCORE_MAP = {
    "Score DEX": "Score STR 1",
    "Mod DEX": "Mod STR 1",
    "Save DEX": "Save STR 1",
    "Score CON": "Score STR 2",
    "Mod CON": "Mod STR 2",
    "Save CON": "Save STR 2",
    "Score INT": "Score STR 3",
    "Mod INT": "Mod STR 3",
    "Save INT": "Save STR 3",
    "Score WIS": "Score STR 4",
    "Mod WIS": "Mod STR 4",
    "Save WIS": "Save STR 4",
    "Score CHA": "Score STR 5",
    "Mod CHA": "Mod STR 5",
    "Save CHA": "Save STR 5",
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
    game_data_path = os.path.join(BASE_DIR, "game_data.json")
    game_data = {}
    if os.path.isfile(game_data_path):
        try:
            with open(game_data_path, "r", encoding="utf-8") as f:
                game_data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load game_data.json: %s", exc)
    return render_template("index.html", game_data=game_data)


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
    form_data = request.form.to_dict()

    # Translate ability score field names to match PDF template
    for html_name, pdf_name in ABILITY_SCORE_MAP.items():
        if html_name in form_data:
            form_data[pdf_name] = form_data.pop(html_name)

    for page in writer.pages:
        writer.update_page_form_field_values(page, form_data)

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

    # --- Build download filename --------------------------------------------
    safe_name = _safe_filename(char_name)
    filename = f"{safe_name}_Neon_Odyssey.pdf"

    logger.info("Generated sheet for '%s' (%d bytes)", char_name, output.getbuffer().nbytes)

    return send_file(
        output,
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
