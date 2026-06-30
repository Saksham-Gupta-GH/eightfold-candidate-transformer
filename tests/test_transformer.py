import pytest
from src.normalize import normalize_phone, normalize_country, canonicalize_skill, normalize_date
from src.merge import MergeEngine
from src.schema import CanonicalProfile, Skill

def test_normalize_phone():
    assert normalize_phone("4155552671") == "+14155552671"
    assert normalize_phone("415-555-2671") == "+14155552671"
    assert normalize_phone("9876543210", default_region="IN") == "+919876543210"
    assert normalize_phone("invalid") is None

def test_normalize_date():
    assert normalize_date("Jan 2020") == "2020-01"
    assert normalize_date("2020-01-15") == "2020-01"
    assert normalize_date("01/2020") == "2020-01"
    assert normalize_date("invalid date") is None

def test_merge_duplicate_emails():
    p1 = CanonicalProfile(
        candidate_id="1",
        full_name="John",
        emails=["test@test.com"],
        overall_confidence=0.5,
        provenance=[{"field": "full_name", "source": "GitHub", "method": "api"}]
    )
    p2 = CanonicalProfile(
        candidate_id="2",
        full_name="John Doe",
        emails=["test@test.com"],
        overall_confidence=0.9,
        provenance=[{"field": "full_name", "source": "CSV", "method": "api"}]
    )
    merger = MergeEngine()
    merged = merger.merge([p1, p2])
    assert len(merged) == 1
    assert merged[0].full_name == "John Doe"
    assert merged[0].overall_confidence == 0.68

from src.projector import Projector

def test_projector():
    p = CanonicalProfile(
        candidate_id="1",
        full_name="John Doe",
        emails=["john@example.com"],
        phones=["4155552671"],
        skills=[Skill(name="Python", confidence=0.9, sources=[])]
    )
    config = {
        "fields": [
            { "path": "name", "from": "full_name", "type": "string" },
            { "path": "email", "from": "emails[0]", "type": "string" }
        ],
        "include_confidence": False
    }
    proj = Projector(config)
    out = proj.project(p)
    
    assert out["name"] == "John Doe"
    assert out["email"] == "john@example.com"
    assert "overall_confidence" not in out
