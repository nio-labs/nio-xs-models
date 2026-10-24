import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import NioMaskRedactor

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1] / "models/nio_mask.onnx"))

def test_yaml_tagged_plain_value_on_following_line(redactor):
    text = "password: !!str\n  AlphaSecret123!\n"
    result = redactor.redact(text)
    assert "AlphaSecret123!" not in result["redacted_text"], result

def test_env_bang_prefixed_password_control(redactor):
    result = redactor.redact("password=!AlphaSecret123!\n")
    assert "!AlphaSecret123!" not in result["redacted_text"], result
