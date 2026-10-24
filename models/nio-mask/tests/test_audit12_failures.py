import json,sys
from pathlib import Path
import pytest,yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from infer import NioMaskRedactor
@pytest.fixture(scope='module')
def redactor():
 return NioMaskRedactor(str(Path(__file__).resolve().parents[1]/'models/nio_mask.onnx'))
def test_explicit_yaml_key_with_line_continuation(redactor):
 text='? "pass\\\n  word"\n: AlphaSecret123!\n'
 assert yaml.safe_load(text)=={'password':'AlphaSecret123!'}
 out=redactor.redact(text)['redacted_text']
 assert 'AlphaSecret123!' not in out,out
def test_json_array_sensitive_key_masks_all_elements(redactor):
 text=r'{"to\u006ben":["violet","orchid"],"name":"public"}'
 assert json.loads(text)['token'][1]=='orchid'
 out=redactor.redact(text)['redacted_text']
 assert 'orchid' not in out,out
def test_json_object_sensitive_key_masks_value(redactor):
 text=r'{"to\u006ben":{"value":"violet"},"name":"public"}'
 assert json.loads(text)['token']['value']=='violet'
 out=redactor.redact(text)['redacted_text']
 assert 'violet' not in out,out
def test_plain_numeric_json_keeps_siblings(redactor):
 text='{"password":1234567890,"name":"public"}'
 out=redactor.redact(text)['redacted_text']
 assert json.loads(out)['name']=='public'
