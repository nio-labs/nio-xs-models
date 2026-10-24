"""
Regression tests for NioMaskRedactor covering all probe cases, nested certificates, escaped quotes, YAML blocks, and IP formats.
"""

import sys
import os
from pathlib import Path
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from infer import NioMaskRedactor

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "nio_mask.onnx"

@pytest.fixture(scope="module")
def redactor():
    return NioMaskRedactor(str(MODEL_PATH))

def test_certificate_wrapped_secrets(redactor):
    # PAT inside certificate must be redacted
    res = redactor.redact("-----BEGIN CERTIFICATE-----\nghp_aB12aB12aB12aB12aB12aB12aB12aB12aB12\n-----END CERTIFICATE-----")
    assert "[REDACTED_SECRET]" in res["redacted_text"]
    assert "ghp_" not in res["redacted_text"]

    # Password inside certificate must be redacted
    res = redactor.redact("-----BEGIN CERTIFICATE-----\npassword=SuperSecretPass123!\n-----END CERTIFICATE-----")
    assert "[REDACTED_SECRET]" in res["redacted_text"]
    assert "SuperSecretPass123!" not in res["redacted_text"]

    # Nested private key inside certificate must be redacted
    res = redactor.redact("-----BEGIN CERTIFICATE-----\n-----BEGIN PRIVATE KEY-----\nMIIEowIBAAKCAQEAAbCd\n-----END PRIVATE KEY-----\n-----END CERTIFICATE-----")
    assert "[REDACTED_SECRET]" in res["redacted_text"]
    assert "MIIEowIBAAKCAQEA" not in res["redacted_text"]

    # Benign public certificate must be preserved
    benign_cert = "-----BEGIN CERTIFICATE-----\nPUBLICDATA\n-----END CERTIFICATE-----"
    res = redactor.redact(benign_cert)
    assert res["redacted_text"] == benign_cert

def test_password_formats(redactor):
    # JSON with escaped quotes
    res = redactor.redact('{"password":"Alpha\\"BravoSecret123!"}')
    assert res["redacted_text"] == '{"password":"[REDACTED_SECRET]"}'

    # Double-quoted with apostrophe
    res = redactor.redact('password="Alpha\'BravoSecret123!"')
    assert res["redacted_text"] == 'password="[REDACTED_SECRET]"'

    # YAML block scalar
    res = redactor.redact('password: |\n  SuperSecretPass123!\n')
    assert res["redacted_text"] == 'password: |\n  [REDACTED_SECRET]\n'

def test_ip_url_and_brackets(redactor):
    # Bracketed IPv6
    res = redactor.redact("https://[2001:db8::1]/status")
    assert res["redacted_text"] == "https://[[REDACTED_PII]]/status"

    # Bracketed link-local IPv6
    res = redactor.redact("host=[fe80::1]")
    assert res["redacted_text"] == "host=[[REDACTED_PII]]"

    # IPv4 URL
    res = redactor.redact("https://192.168.1.100/status")
    assert res["redacted_text"] == "https://[REDACTED_PII]/status"
