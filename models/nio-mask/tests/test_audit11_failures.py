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
    ('"\\x70assword": AlphaSecret123!\n','AlphaSecret123!'),
    ('"\\U00000070assword": BravoValueHidden!\n','BravoValueHidden!'),
])
def test_yaml_specific_key_escapes_are_recognized(redactor,text,secret):
    result=redactor.redact(text)
    assert secret not in result['redacted_text'],result

def test_numeric_json_secret_preserves_siblings(redactor):
    text=r'{"pass\u0077ord":1234567890,"name":"public"}'
    assert json.loads(text)['password']==1234567890
    result=redactor.redact(text)
    assert json.loads(result['redacted_text'])['name']=='public'

def test_yaml_json_style_escape_control(redactor):
    result=redactor.redact('"\\u0070assword": AlphaSecret123!\n')
    assert 'AlphaSecret123!' not in result['redacted_text'],result
