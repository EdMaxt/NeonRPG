"""
Tests for the Neon Odyssey Character Sheet Generator.
"""

import io
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

import pytest
from pypdf import PdfReader

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import (
    app,
    _safe_filename,
    _validate_character_name,
    TEMPLATE_PDF,
    MAX_NAME_LENGTH,
)

# Disable CSRF for testing
app.config["WTF_CSRF_ENABLED"] = False


class TestSafeFilename(unittest.TestCase):
    """Tests for _safe_filename helper."""

    def test_simple_name(self):
        self.assertEqual(_safe_filename("Gandalf"), "Gandalf")

    def test_name_with_spaces(self):
        self.assertEqual(_safe_filename("Luke Skywalker"), "Luke Skywalker")

    def test_name_with_special_chars(self):
        self.assertEqual(_safe_filename("Zaphod <Beeblebrox>"), "Zaphod _Beeblebrox_")

    def test_name_with_path_separators(self):
        self.assertEqual(_safe_filename("foo/bar\\baz"), "foo_bar_baz")

    def test_empty_name_returns_fallback(self):
        self.assertEqual(_safe_filename(""), "character")

    def test_whitespace_only_returns_fallback(self):
        self.assertEqual(_safe_filename("   "), "character")

    def test_name_exceeding_max_length(self):
        long_name = "A" * (MAX_NAME_LENGTH + 10)
        result = _safe_filename(long_name)
        self.assertEqual(len(result), MAX_NAME_LENGTH)

    def test_name_with_unicode(self):
        result = _safe_filename("Ñoño")
        self.assertIn("o", result)

    def test_name_with_dots(self):
        self.assertEqual(_safe_filename("file.name"), "file_name")

    def test_name_with_multiple_spaces(self):
        self.assertEqual(_safe_filename("a   b"), "a b")


class TestValidateCharacterName(unittest.TestCase):
    """Tests for _validate_character_name helper."""

    def test_valid_name(self):
        self.assertIsNone(_validate_character_name("Gandalf"))

    def test_empty_name(self):
        result = _validate_character_name("")
        self.assertIsNotNone(result)
        self.assertIn("required", result.lower())

    def test_whitespace_only_name(self):
        result = _validate_character_name("   ")
        self.assertIsNotNone(result)
        self.assertIn("required", result.lower())

    def test_name_at_max_length(self):
        name = "A" * MAX_NAME_LENGTH
        self.assertIsNone(_validate_character_name(name))

    def test_name_exceeding_max_length(self):
        name = "A" * (MAX_NAME_LENGTH + 1)
        result = _validate_character_name(name)
        self.assertIsNotNone(result)
        self.assertIn(str(MAX_NAME_LENGTH), result)


class TestIndexRoute(unittest.TestCase):
    """Tests for the index route."""

    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_index_contains_form(self):
        response = self.client.get("/")
        self.assertIn(b"sheetForm", response.data)

    def test_index_contains_character_name_input(self):
        response = self.client.get("/")
        self.assertIn(b"Character Name", response.data)


class TestHealthRoute(unittest.TestCase):
    """Tests for the health check route."""

    def setUp(self):
        self.client = app.test_client()

    def test_health_returns_200(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_health_returns_json(self):
        response = self.client.get("/health")
        self.assertEqual(response.content_type, "application/json")

    def test_health_status_ok(self):
        response = self.client.get("/health")
        data = response.get_json()
        self.assertEqual(data["status"], "ok")

    def test_health_template_exists(self):
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("template_exists", data)


class TestGenerateRoute(unittest.TestCase):
    """Tests for the PDF generation route."""

    def setUp(self):
        self.client = app.test_client()

    def test_generate_requires_post(self):
        response = self.client.get("/generate")
        self.assertEqual(response.status_code, 405)

    def test_generate_missing_character_name(self):
        response = self.client.post("/generate", data={})
        self.assertEqual(response.status_code, 400)

    def test_generate_empty_character_name(self):
        response = self.client.post("/generate", data={"Character Name": ""})
        self.assertEqual(response.status_code, 400)

    def test_generate_whitespace_character_name(self):
        response = self.client.post("/generate", data={"Character Name": "   "})
        self.assertEqual(response.status_code, 400)

    def test_generate_name_too_long(self):
        long_name = "A" * (MAX_NAME_LENGTH + 1)
        response = self.client.post("/generate", data={"Character Name": long_name})
        self.assertEqual(response.status_code, 400)

    @patch("app.PdfReader")
    def test_generate_success(self, mock_reader_cls):
        """Test successful PDF generation with mocked PdfReader."""
        # Setup mock
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_reader_cls.return_value = mock_reader

        # Mock PdfWriter
        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            # Mock the write to produce valid PDF bytes
            def mock_write(buf):
                # Write a minimal valid PDF
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write

            # Mock _root_object
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Test Character",
                "Class": "Fighter",
            })

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "application/pdf")
            self.assertIn("attachment", response.headers.get("Content-Disposition", ""))

    @patch("app.PdfReader")
    def test_generate_with_special_characters(self, mock_reader_cls):
        """Test PDF generation with special characters in name."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Zaphod <Beeblebrox>",
            })

            self.assertEqual(response.status_code, 200)

    @patch("app.PdfReader")
    def test_generate_with_unicode_name(self, mock_reader_cls):
        """Test PDF generation with unicode characters."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Ñoño Pérez",
            })

            self.assertEqual(response.status_code, 200)

    @patch("app.PdfReader")
    def test_generate_with_all_fields(self, mock_reader_cls):
        """Test PDF generation with all form fields populated."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Test Character",
                "Player": "Test Player",
                "Class": "Fighter",
                "Subclass": "Champion",
                "Species": "Human",
                "Homeworld": "Earth",
                "Level": "5",
                "XP": "10000",
                "Size": "Medium",
                "Speed": "30 ft",
                "Armor": "18",
                "Initiative": "+3",
                "HP Max": "50",
                "HP Temp": "0",
                "HD Max": "5d10",
                "HD Spent": "2",
                "Resistances": "Fire",
                "Features and Traits": "Second Wind",
                "Score STR": "18",
                "Mod STR": "+4",
                "Score STR 1": "14",
                "Mod STR 1": "+2",
                "Score STR 2": "16",
                "Mod STR 2": "+3",
                "Score STR 3": "10",
                "Mod STR 3": "+0",
                "Score STR 4": "12",
                "Mod STR 4": "+1",
                "Score STR 5": "8",
                "Mod STR 5": "-1",
                "Skills": "/Off",
                "Skills 1": "/Off",
                "Ability Save": "/Off",
                "Ability Save 1": "/Off",
                "Death Save 1": "/Off",
                "Death Save 2": "/Off",
                "Exhaustion 1": "/Off",
                "Heroic Inspiration": "/Off",
                "Attack Name": "Longsword",
                "Attack Bonus": "+6",
                "Attack Damage": "1d8+4",
                "Attack Notes": "Versatile",
                "Faction": "Rebels",
                "Faction Score": "10",
                "Magic Item": "Sword of Sharpness",
                "Equipment": "Chain mail, shield",
                "Languages": "Common, Elvish",
                "Feats and Professions": "Alert",
                "Weapon Proficiencies": "Martial",
                "Tool Proficiencies": "Smith",
                "Vehicle Proficiencies": "Land",
                "Lifestyle": "Modest",
                "Armor Proficiency 1": "/Off",
                "Armor Proficiency 2": "/Off",
                "Armor Proficiency 3": "/Off",
                "Armor Proficiency 4": "/Off",
                "Magic Item Attunement 1": "/Off",
                "Magic Item Attunement 2": "/Off",
                "Magic Item Attunement 3": "/Off",
                "Magic Item Attunement 4": "/Off",
                "Magic Item Attunement 5": "/Off",
                "Magic Item Attunement 6": "/Off",
                "Spell Attack Bonus": "+5",
                "Spell Save DC": "13",
                "Spellcasting Modifier": "+3",
                "Spellcasting Ability 1": "/Off",
                "Spellcasting Ability 2": "/Off",
                "Spellcasting Ability 3": "/Off",
                "Spell Expended 1": "/Off",
                "Spell Expended 2": "/Off",
                "Spell Expended 3": "/Off",
                "Spell Expended 4": "/Off",
                "Spell Expended 5": "/Off",
                "Spell Expended 6": "/Off",
                "Spell Expended 7": "/Off",
                "Spell Expended 9": "/Off",
                "Spell Expended 10": "/Off",
                "Spell Expended 11": "/Off",
                "Spell Expended 13": "/Off",
                "Spell Expended 14": "/Off",
                "Spell Expended 15": "/Off",
                "Spell Expended 16": "/Off",
                "Spell Expended 17": "/Off",
                "Spell Expended 18": "/Off",
                "Spell Expended 19": "/Off",
                "Spell Expended 20": "/Off",
                "Spell Expended 25": "/Off",
                "Spell Expended 26": "/Off",
                "Spell Expended 27": "/Off",
                "Spell Expended 28": "/Off",
                "Spell Name 1": "Fireball",
                "Spell Level 1": "3",
                "Spell Casting Time 1": "1 action",
                "Spell Range 1": "150 ft",
                "Spell Features 1": "Fire damage",
                "Spell School 1": "Evocation",
                "Spell Notes 1": "PHB 241",
                "Spell Page 1": "241",
                "Notes": "Test notes",
                "Galactic Notes": "Space notes",
            })

            self.assertEqual(response.status_code, 200)

    @patch("app.PdfReader")
    def test_generate_with_minimal_fields(self, mock_reader_cls):
        """Test PDF generation with only required fields."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Minimal",
            })

            self.assertEqual(response.status_code, 200)

    @patch("app.PdfReader")
    def test_generate_with_empty_optional_fields(self, mock_reader_cls):
        """Test PDF generation with empty optional fields."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Test",
                "Player": "",
                "Class": "",
                "Level": "",
            })

            self.assertEqual(response.status_code, 200)

    @patch("app.PdfReader")
    def test_generate_with_acroform(self, mock_reader_cls):
        """Test that NeedAppearances is set when AcroForm exists."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write

            # Simulate AcroForm presence
            mock_acroform = {}
            mock_writer_instance._root_object = {"/AcroForm": mock_acroform}

            response = self.client.post("/generate", data={
                "Character Name": "Test",
            })

            self.assertEqual(response.status_code, 200)
            # Verify NeedAppearances was set
            from pypdf.generic import BooleanObject
            self.assertIn("/NeedAppearances", mock_acroform)

    @patch("app.PdfReader")
    def test_generate_without_acroform(self, mock_reader_cls):
        """Test PDF generation when no AcroForm exists."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write

            # No AcroForm
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Test",
            })

            self.assertEqual(response.status_code, 200)

    @patch("app.PdfReader")
    def test_generate_multiple_pages(self, mock_reader_cls):
        """Test PDF generation with multiple pages."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock(), MagicMock(), MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Test",
            })

            self.assertEqual(response.status_code, 200)

    @patch("app.PdfReader")
    def test_generate_filename_sanitization(self, mock_reader_cls):
        """Test that filename is properly sanitized."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "My Character!",
            })

            self.assertEqual(response.status_code, 200)
            content_disp = response.headers.get("Content-Disposition", "")
            # "!" is replaced with "_", space is preserved
            self.assertIn("My Character__Neon_Odyssey.pdf", content_disp)

    @patch("app.PdfReader")
    def test_generate_with_checkbox_fields(self, mock_reader_cls):
        """Test PDF generation with checkbox fields."""
        mock_reader = MagicMock()
        mock_reader_cls.return_value = mock_reader

        with patch("app.PdfWriter") as mock_writer_cls:
            mock_writer_instance = MagicMock()
            mock_writer_cls.return_value = mock_writer_instance
            mock_writer_instance.pages = [MagicMock()]

            def mock_write(buf):
                buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            mock_writer_instance.write = mock_write
            mock_writer_instance._root_object = {}

            response = self.client.post("/generate", data={
                "Character Name": "Test",
                "Skills": "/Off",
                "Skills 1": "/Off",
                "Skills 2": "/Off",
                "Ability Save": "/Off",
                "Ability Save 1": "/Off",
                "Death Save 1": "/Off",
                "Death Save 2": "/Off",
                "Death Save 3": "/Off",
                "Death Save 4": "/Off",
                "Death Save 5": "/Off",
                "Death Save 6": "/Off",
                "Exhaustion 1": "/Off",
                "Exhaustion 2": "/Off",
                "Exhaustion 3": "/Off",
                "Exhaustion 4": "/Off",
                "Exhaustion 5": "/Off",
                "Exhaustion 6": "/Off",
                "Heroic Inspiration": "/Off",
                "Armor Proficiency 1": "/Off",
                "Armor Proficiency 2": "/Off",
                "Armor Proficiency 3": "/Off",
                "Armor Proficiency 4": "/Off",
                "Magic Item Attunement 1": "/Off",
                "Magic Item Attunement 2": "/Off",
                "Magic Item Attunement 3": "/Off",
                "Magic Item Attunement 4": "/Off",
                "Magic Item Attunement 5": "/Off",
                "Magic Item Attunement 6": "/Off",
                "Spellcasting Ability 1": "/Off",
                "Spellcasting Ability 2": "/Off",
                "Spellcasting Ability 3": "/Off",
                "Spell Expended 1": "/Off",
                "Spell Expended 2": "/Off",
                "Spell Expended 3": "/Off",
                "Spell Expended 4": "/Off",
                "Spell Expended 5": "/Off",
                "Spell Expended 6": "/Off",
                "Spell Expended 7": "/Off",
                "Spell Expended 9": "/Off",
                "Spell Expended 10": "/Off",
                "Spell Expended 11": "/Off",
                "Spell Expended 13": "/Off",
                "Spell Expended 14": "/Off",
                "Spell Expended 15": "/Off",
                "Spell Expended 16": "/Off",
                "Spell Expended 17": "/Off",
                "Spell Expended 18": "/Off",
                "Spell Expended 19": "/Off",
                "Spell Expended 20": "/Off",
                "Spell Expended 25": "/Off",
                "Spell Expended 26": "/Off",
                "Spell Expended 27": "/Off",
                "Spell Expended 28": "/Off",
            })

            self.assertEqual(response.status_code, 200)


class TestErrorHandlers(unittest.TestCase):
    """Tests for error handlers."""

    def setUp(self):
        self.client = app.test_client()

    def test_404_handler(self):
        response = self.client.get("/nonexistent")
        self.assertEqual(response.status_code, 404)


class TestTemplateExists(unittest.TestCase):
    """Test that template PDF exists."""

    def test_template_pdf_exists(self):
        self.assertTrue(os.path.isfile(TEMPLATE_PDF))


if __name__ == "__main__":
    unittest.main()
