import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import NioMaskRedactor

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1] / "models/nio_mask.onnx"))

def test_multiple_yaml_comments_do_not_expose_password_prefix(redactor):
    text = "password:\n# first\n# second\n  AlphaSecret123!\n"
    result = redactor.redact(text)
    assert "AlphaSecr" not in result["redacted_text"], result

def test_pretty_json_preserves_quoted_value_and_comma(redactor):
    text = '{\n  "password":\n    "AlphaSecret123!",\n  "name": "public"\n}\n'
    result = redactor.redact(text)
    value = json.loads(result["redacted_text"])
    assert value == {"password": "[REDACTED_SECRET]", "name": "public"}

def test_compact_json_control(redactor):
    result = redactor.redact('{"password":"AlphaSecret123!","name":"public"}')
    assert json.loads(result["redacted_text"]) == {"password": "[REDACTED_SECRET]", "name": "public"}
