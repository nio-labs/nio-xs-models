import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import NioMaskRedactor

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1] / "models/nio_mask.onnx"))

@pytest.mark.parametrize("text,secret", [
    ("password: |\n  AlphaSecret123!\n\n  BravoSecret456!\n", "BravoSecret456!"),
    ("password: | #comment\n  AlphaSecret123!\n  BravoSecret456!\n", "AlphaSecret123!"),
    ("'password': |\n  AlphaSecret123!\n", "AlphaSecret123!"),
])
def test_yaml_body_is_secret(redactor, text, secret):
    assert secret not in redactor.redact(text)["redacted_text"]

def test_yaml_sibling_is_preserved(redactor):
    text="credentials:\n  password: |\n    AlphaSecret123!\n  username: safeuser\n"
    assert "username: safeuser" in redactor.redact(text)["redacted_text"]

def test_uri_preserves_host_and_path(redactor):
    assert redactor.redact("postgres://u:AlphaSecret123!@localhost/status")["redacted_text"] == "postgres://u:[REDACTED_SECRET]@localhost/status"
