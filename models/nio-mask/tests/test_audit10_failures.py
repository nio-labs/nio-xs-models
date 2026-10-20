import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from infer import NioMaskRedactor

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1]/"models/nio_mask.onnx"))

@pytest.mark.parametrize("text,secret",[
    (r'{"pass\u0077ord":"AlphaSecret123!"}',"AlphaSecret123!"),
    (r'{"\u0070assword":"BravoValueHidden!"}',"BravoValueHidden!"),
])
def test_escaped_sensitive_json_keys_are_recognized(redactor,text,secret):
    assert json.loads(text)["password"]==secret
    result=redactor.redact(text)
    assert secret not in result["redacted_text"],result

def test_ordinary_sensitive_key_control(redactor):
    result=redactor.redact('{"password":"AlphaSecret123!"}')
    assert json.loads(result["redacted_text"])["password"]=="[REDACTED_SECRET]"
