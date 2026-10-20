import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from infer import NioMaskRedactor


@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(Path(__file__).resolve().parents[1] / "models/nio_mask.onnx"))


def test_explicit_yaml_key_with_line_continuation(redactor):
    # Valid explicit YAML key; escaped line break and indentation fold to password.
    text = '? "pass\\\n  word"\n: AlphaSecret123!\n'
    out = redactor.redact(text)["redacted_text"]
    assert "AlphaSecret123!" not in out, out


def test_json_array_sensitive_key_masks_all_elements(redactor):
    text = r'{"to\u006ben":["violet","orchid"],"name":"public"}'
    assert json.loads(text)["token"][1] == "orchid"
    out = redactor.redact(text)["redacted_text"]
    assert "orchid" not in out, out


def test_json_object_sensitive_key_masks_value(redactor):
    text = r'{"to\u006ben":{"value":"violet"},"name":"public"}'
    assert json.loads(text)["token"]["value"] == "violet"
    out = redactor.redact(text)["redacted_text"]
    assert "violet" not in out, out


def test_plain_numeric_json_keeps_siblings(redactor):
    text = '{"password":1234567890,"name":"public"}'
    out = redactor.redact(text)["redacted_text"]
    assert json.loads(out)["name"] == "public"


@pytest.mark.parametrize("key", ["token", r"to\u006ben"])
@pytest.mark.parametrize("value", [
    "1234567890", "-123.456e+7", "false", "null", "[]", "{}",
    '["violet","orchid"]', '{"value":"violet"}',
    '[{"secret":123,"value":"orchid"}]',
    '{"x":["quote\\\"}\\\\",["orchid"]]}',
    '{"value":"紫orchid"}',
])
def test_complete_json_value_is_masked_and_siblings_preserved(redactor, key, value):
    text = '{"' + key + '":' + value + ',"name":"public"}'
    json.loads(text)
    out = redactor.redact(text)["redacted_text"]
    parsed = json.loads(out)
    assert parsed["name"] == "public"
    assert parsed["token"] == "[REDACTED_SECRET]"


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_yaml_continuation_indentation_is_folded(redactor, newline):
    text = '? "pass\\' + newline + '  word"' + newline + ': AlphaSecret123!' + newline
    out = redactor.redact(text)["redacted_text"]
    assert out == text.replace("AlphaSecret123!", "[REDACTED_SECRET]")
