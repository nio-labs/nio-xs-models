import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import NioMaskRedactor

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1] / "models/nio_mask.onnx"))

@pytest.mark.parametrize("text,secret", [
    ("password: |  \n  AlphaSecret123!\n", "AlphaSecret123!"),
    ("password: !!str |\n  AlphaSecret123!\n", "AlphaSecret123!"),
    ("password: &credential |\n  BravoValueHidden!\n", "BravoValueHidden!"),
])
def test_valid_yaml_block_body_must_be_hidden(redactor, text, secret):
    result = redactor.redact(text)
    assert secret not in result["redacted_text"], result
