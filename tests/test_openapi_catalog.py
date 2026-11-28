"""The OpenAPI document describes the real catalog (spec 008, FR-010/FR-011).

The frontend generates its client and docs from the full schema, so stale
examples (foreign mythologies, categories the API does not have) would spread
downstream. Scanning the schema keeps the cleanup from regressing.
"""
import json

from app.main import app

# Words that belong to the template examples this API started from, not to a
# Salvadoran myths and legends catalog with types CHARACTER/PLACE/OBJECT/GROUP/
# EVENT and categories MYTH/LEGEND/TRADITION.
STALE_WORDS = (
    "egypt",
    "greek",
    "norse",
    "aztec",
    "japanese",
    "anubis",
    "osiris",
    "zeus",
    "quetzalcoatl",
    "nile",
    "deity",
    "creature",
    "mythologies",
)


def test_should_not_mention_foreign_mythologies_or_unknown_categories():
    schema_text = json.dumps(app.openapi()).lower()

    found = [word for word in STALE_WORDS if word in schema_text]

    assert found == []


def test_should_describe_a_salvadoran_catalog():
    description = app.openapi()["info"]["description"]

    assert "Salvador" in description


def test_should_carry_a_fair_use_note_in_the_docs():
    description = app.openapi()["info"]["description"]

    assert "Fair Use" in description
