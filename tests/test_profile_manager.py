import os
import json
import types
import sys
import tempfile

sys.modules.setdefault("pandas", types.ModuleType("pandas"))

from parser import profile_manager as pm


def test_match_profile(tmp_path):
    pm.PROFILE_PATH = os.path.join(tmp_path, "profiles.json")
    pm.save_profiles({
        "Test Bank": {
            "Date": "date",
            "Narrative": "description",
            "Amount": "amount"
        }
    })
    profiles = pm.load_profiles()
    name, mapping = pm.match_profile(["Date", "Narrative", "Amount"], profiles)
    assert name == "Test Bank"
    assert mapping == {
        "date": "date",
        "description": "narrative",
        "amount": "amount",
    }


def test_add_profile(tmp_path):
    pm.PROFILE_PATH = os.path.join(tmp_path, "profiles.json")
    pm.add_profile("My Bank", ["Date", "Desc", "Value"], {
        "date": "date",
        "description": "desc",
        "amount": "value",
    })
    profiles = pm.load_profiles()
    assert "My Bank" in profiles
    name, mapping = pm.match_profile(["Date", "Desc", "Value"], profiles)
    assert name == "My Bank"
    assert mapping["description"] == "desc"
