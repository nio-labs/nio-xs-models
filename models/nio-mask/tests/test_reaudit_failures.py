import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import NioMaskRedactor

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1] / "models/nio_mask.onnx"))

def test_explicit_yaml_indentation_must_cover_second_line(redactor):
    text = "password: |2\n    AlphaSecret123!\n  BravoValueHidden!\n"
    result = redactor.redact(text)
    assert "BravoValueHidden!" not in result["redacted_text"], result

def test_single_quoted_yaml_key_must_hide_value(redactor):
    text = "'password': 'AlphaSecret123!'\n"
    result = redactor.redact(text)
    assert "AlphaSecret123!" not in result["redacted_text"], result
