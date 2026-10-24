import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import NioMaskRedactor

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1] / "models/nio_mask.onnx"))

def test_hash_inside_plain_value_does_not_end_secret(redactor):
    text = "password:\n# comment\n  Alpha#BravoValueHidden!\n"
    result = redactor.redact(text)
    assert "BravoValueHidden!" not in result["redacted_text"], result

def test_literal_hash_line_control(redactor):
    text = "password: |\n  #AlphaSecret123!\n  BravoValueHidden!\n"
    result = redactor.redact(text)
    assert "#AlphaSecret123!" not in result["redacted_text"], result
