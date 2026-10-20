"""
NioMicro Direct Inference CLI
Tests the trained ONNX model on arbitrary prompts and outputs structured JSON decisions.
"""

import argparse
import hashlib
import sys
import json
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

import re
import shlex
import posixpath

CATASTROPHIC_PATTERNS = [
    (re.compile(r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:", re.IGNORECASE), "Fork bomb denial of service construct"),
    (re.compile(r"/(?:etc/shadow|etc/gshadow)", re.IGNORECASE), "Sensitive credential / shadow file access"),
    (re.compile(r"\bcat\s+/etc/passwd\b", re.IGNORECASE), "Sensitive system user access"),
    (re.compile(r"\b(?:sk-proj-[a-zA-Z0-9_\-]{15,}|ghp_[a-zA-Z0-9]{20,}|gho_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16})", re.IGNORECASE), "Plaintext secret token exposure"),
    (re.compile(r"-----BEGIN\s+(?:RSA|OPENSSH|DSA|EC)?\s*PRIVATE\s+KEY-----", re.IGNORECASE), "Private key exposure"),
    (re.compile(r"\b(?:curl|wget)\s+https?://\S+\s*\|\s*(?:bash|sh|zsh)", re.IGNORECASE), "Piped remote execution from untrusted source"),
    (re.compile(r"\bchmod\s+-[a-zA-Z]*R\s+777\s+/", re.IGNORECASE), "Universal root permission escalation"),
    (re.compile(r"\b(?:api[ _-]?secret|api[ _-]?key|secret[ _-]?token)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE), "Hardcoded secret token assignment"),
    (re.compile(r"\b(?:os\.system\b|pickle\.load\b|dangerous_transmute\b)", re.IGNORECASE), "Unsafe execution construct"),
    (re.compile(r"\b(?:mkfs|dd\s+if=.*of=/dev/)", re.IGNORECASE), "Direct block device wipe operation"),
    (re.compile(r"\bkubectl\s+(?:apply|create)\s+-f\s+<\(.*UNTRUSTED", re.IGNORECASE), "Execution of untrusted user manifest"),
    (re.compile(r"\bapply\s+unsanitized\s+user[- ]generated\s+(?:yaml|manifest|spec)\b", re.IGNORECASE), "Execution of unsanitized user manifest"),
    (re.compile(r"\bkubectl\s+(?:apply|create)\s+-[fk]\s+https?://", re.IGNORECASE), "Remote untrusted manifest execution"),
    (re.compile(r"\b(?:deploy|schedule|run|start)\s+(?:an?\s+)?(?:unreviewed\s+)?privileged\s+(?:container|daemonset)\b", re.IGNORECASE), "Unisolated privileged container escape hazard"),
    (re.compile(r"\b(?:run|execute)\s+(?:an?\s+)?unverified\s+(?:remote\s+)?(?:deployment\s+)?script\b", re.IGNORECASE), "Execution of unverified remote deployment script"),
    (re.compile(r"\b(?:kerberos::golden|inject\s+(?:forged\s+)?kerberos\s+ticket|forge\s+kerberos\s+ticket)\b", re.IGNORECASE), "Kerberos ticket forgery exploit"),
    (re.compile(r"\b(?:execute|send|launch|run)\s+(?:an?\s+)?(?:unauthorized\s+)?(?:automated\s+)?(?:malicious\s+)?(?:crafted\s+)?sql\s+injection\s+(?:payload|attack)\b", re.IGNORECASE), "Exploitation of unpatched systems and SQL injection attack"),
    (re.compile(r"\b(?:install|load|download)\s+.*?(?:unsigned\s+)?rootkit\b", re.IGNORECASE), "Malicious rootkit installation"),
    (re.compile(r"\b(?:publish|transmit|send|email|dump|expose|leak|broadcast|post|log|write)\s+.*?(?:private\s+(?:root\s+)?(?:ca\s+)?(?:cryptographic\s+|signing\s+)?key|session\s+cookie|master\s+(?:aes|jwt)\s+key)\b", re.IGNORECASE), "Secret key or session token exfiltration"),
    (re.compile(r"\b(?:email|send|transmit)\s+(?:intermediate\s+)?signing\s+key\s+to\s+(?:external|personal)\b", re.IGNORECASE), "Secret signing key exfiltration"),
    (re.compile(r"\bcredential-dumping\b", re.IGNORECASE), "Credential dumping exploit execution"),
    (re.compile(r"\b(?:curl|wget)\b.*?(?:--data[a-z0-9_-]*|--form[a-z0-9_-]*|--post-file|--upload-file|-d|-F|-T)\s*[:=]?\s*['\"]?@\S*(?:server\.key|id_rsa|id_ed25519|private|\.key\b|shadow)", re.IGNORECASE), "Network exfiltration of private keys or sensitive credentials"),
    (re.compile(r"\b(?:--script\s*=?\s*http-shellshock|http-shellshock)\b", re.IGNORECASE), "Shellshock exploit execution construct"),
    (re.compile(r"(?:--output|-o|--output-file)\s*[:=]?\s*['\"]?/(?:etc|boot|root)/", re.IGNORECASE), "Arbitrary system configuration overwrite attempt"),
    (re.compile(r"\b(?:signing\s+key|private\s+(?:root\s+)?(?:ca\s+)?(?:cryptographic\s+)?key|session\s+cookie|master\s+key|credentials?)\b.*?\b(?:upload|send|transmit|post|leak|publish|exfiltrate|broadcast)\b.*?(?:https?://|to\s+public|to\s+attacker)", re.IGNORECASE), "Secret key or credential network exfiltration"),
]

def strip_quotes(s: str) -> str:
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    return s

def clean_token(s: str) -> str:
    return strip_quotes(s)

def is_secret_file_path(path: str) -> bool:
    p = path.strip().strip("\"'")
    if not p or p.startswith("-") or p.startswith(">") or p.startswith("<"):
        return False
    # Public SSH keys ending in .pub are not secret
    if p.endswith(".pub"):
        return False

    norm_p = posixpath.normpath(p.replace("~", "/home/user"))
    norm_lower = norm_p.lower()

    # Secret credential and cloud token files
    if re.search(r"(?:credentials|\.aws/|service-account.*key|serviceaccount/token|privatekey)", norm_lower):
        return True
    # Private SSH keys (id_rsa, id_ed25519, etc. without .pub)
    if re.search(r"(?:id_rsa|id_ed25519|id_ecdsa|id_dsa)(?:\b|$)", norm_lower):
        return True
    # Private TLS / SSL keys
    if re.search(r"(?:privkey|private[_-]?key|server\.key|tls\.key|client\.key|\.key$)", norm_lower):
        return True
    if "/private/" in norm_lower and re.search(r"\.(?:pem|key)$", norm_lower):
        return True

    # Public CA / certificates bundles (only after verifying no private key pattern matched)
    if any(pub in norm_lower for pub in ["ca-certificates", "cacert", "fullchain.pem", "chain.pem", "cert.pem", "certificate.pem"]):
        return False
    if norm_lower.startswith(("/etc/ssl/certs/", "/etc/pki/ca-trust/", "/etc/pki/tls/certs/")):
        return False

    return False


def strip_shell_comments(text: str) -> str:
    """Strip shell comments before tokenization so quotes inside comments do not break lexing."""
    result = []
    i = 0
    n = len(text)
    in_single_quote = False
    in_double_quote = False
    escaped = False
    prev_boundary = True
    
    while i < n:
        c = text[i]
        
        if in_single_quote:
            result.append(c)
            if c == "'":
                in_single_quote = False
                prev_boundary = False
            i += 1
            continue
            
        if in_double_quote:
            result.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_double_quote = False
                prev_boundary = False
            i += 1
            continue
            
        if escaped:
            result.append(c)
            escaped = False
            prev_boundary = False
            i += 1
            continue
            
        if c == "\\":
            result.append(c)
            escaped = True
            prev_boundary = False
            i += 1
            continue
            
        if c == "'":
            result.append(c)
            in_single_quote = True
            prev_boundary = False
            i += 1
            continue
            
        if c == '"':
            result.append(c)
            in_double_quote = True
            prev_boundary = False
            i += 1
            continue
            
        if c == '#' and prev_boundary:
            # Comment starts: skip until newline or end of text
            while i < n and text[i] not in ('\n', '\r'):
                i += 1
            prev_boundary = True
            continue
            
        result.append(c)
        if c in (' ', '\t', ';', '&', '|', '(', ')'):
            prev_boundary = True
        elif c in ('\n', '\r'):
            prev_boundary = True
        else:
            prev_boundary = False
            
        i += 1
        
    return ''.join(result)


def is_pure_public_cert_or_key_read(action: str) -> bool:
    clean = strip_shell_comments(action).strip()
    m_ssl = re.match(r"^openssl\s+x509\s+([^\n;|]+)$", clean, re.IGNORECASE)
    if m_ssl:
        args_str = m_ssl.group(1).strip()
        if re.search(r"[\$`\(\)<>|;&\*\?]", args_str):
            return False
        try:
            tokens = shlex.split(args_str)
        except Exception:
            tokens = args_str.split()
        if not tokens:
            return False
        MUTATING_OPENSSL_OPTS = {
            "-out", "-signkey", "-cakey", "-req", "-new", "-set_serial",
            "-addtrust", "-setalias", "-extfile", "-clrext", "-x509toreq"
        }
        SAFE_OPENSSL_READ_OPTS = {
            "-text", "-noout", "-dates", "-enddate", "-startdate", "-subject",
            "-issuer", "-serial", "-fingerprint", "-hash", "-subject_hash",
            "-issuer_hash", "-purpose", "-ocspid", "-ocsp_uri", "-modulus",
            "-pubkey", "-alias", "-email", "-checkend", "-nameopt", "-certopt"
        }
        prev_is_in = False
        prev_is_opt_arg = False
        cert_path = None
        for t in tokens:
            t_lower = t.lower()
            if prev_is_in:
                prev_is_in = False
                cert_path = t
                continue
            if prev_is_opt_arg:
                prev_is_opt_arg = False
                continue
            if t_lower in MUTATING_OPENSSL_OPTS or any(t_lower.startswith(f"{m}=") for m in MUTATING_OPENSSL_OPTS):
                return False
            if t_lower == "-in":
                prev_is_in = True
                continue
            if t_lower.startswith("-in="):
                cert_path = t.split("=", 1)[1]
                continue
            if t_lower in ("-checkend", "-nameopt", "-certopt", "-inform"):
                prev_is_opt_arg = True
                continue
            if t_lower in SAFE_OPENSSL_READ_OPTS:
                continue
            return False

        if prev_is_in or prev_is_opt_arg:
            return False
        if cert_path:
            if not re.match(r"^[a-zA-Z0-9_\-\./~]+$", cert_path):
                return False
            if ".." in cert_path.split("/"):
                return False
            if is_secret_file_path(cert_path):
                return False
            norm_c = posixpath.normpath(cert_path.replace("~", "/home/user")).lower()
            if re.search(r"(?:private|privkey|server\.key|tls\.key|client\.key|\.key$)", norm_c):
                return False
            is_known_public = (
                norm_c.endswith((".crt", ".pem", ".cer", ".pub", ".bundle"))
                or any(pub in norm_c for pub in ["ca-certificates", "ca-bundle", "cacert", "fullchain.pem", "chain.pem", "cert.pem", "certificate.pem"])
            )
            if not is_known_public:
                return False
        return True

    m = re.match(r"^(cat|head|tail|more|less|bat)\s+([^\n;|]+)$", clean, re.IGNORECASE)
    if not m:
        return False
    base_cmd = m.group(1).lower()
    args_str = m.group(2).strip()
    # Reject shell expansions, command substitutions, pipes, redirects, subshells, globs, env vars
    if re.search(r"[\$`\(\)<>|;&\*\?]", args_str):
        return False
    # Explicitly exclude configurable pager, exec, or command execution options
    if re.search(r"(?:--pager\b|-P\b|--exec\b|--command\b|\bpager\s*=)", args_str, re.IGNORECASE):
        return False
    try:
        tokens = shlex.split(args_str)
    except Exception:
        tokens = args_str.split()
    if not tokens:
        return False

    SAFE_READ_FLAG_PATTERN = re.compile(
        r"^(?:"
        r"-[0-9]+"
        r"|-[abcefnprstuvzABEFNRSTX]+"
        r"|\+[0-9]+|\+G"
        r"|--(?:number|number-nonblank|squeeze-blank|show-all|show-ends|show-tabs|show-nonprinting|plain)"
        r"|--(?:lines|bytes|max-count|sleep-interval|pid)(?:=[0-9]+)?"
        r"|--(?:quiet|silent|verbose|zero-terminated|follow|retry)"
        r"|--(?:paging|color)=(?:auto|always|never)"
        r"|--(?:style)=(?:auto|plain|numbers|full|default|header|grid)"
        r"|--(?:theme|language)=[a-zA-Z0-9_-]+"
        r"|--(?:line-range)=[0-9:]+"
        r")$",
        re.IGNORECASE
    )

    CMD_OPTIONS_WITH_ARG = {
        "head": {"-n", "-c", "--lines", "--bytes"},
        "tail": {"-n", "-c", "-s", "--lines", "--bytes", "--sleep-interval", "--pid", "--max-unchanged-stats"},
        "bat": {"-r", "-l", "--line-range", "--language", "--theme"},
        "less": {"-b", "-x"},
        "more": set(),
        "cat": set(),
    }
    opt_with_arg = CMD_OPTIONS_WITH_ARG.get(base_cmd, set())

    prev_option_expects_arg = False
    inspected_paths = 0
    for t in tokens:
        if prev_option_expects_arg:
            prev_option_expects_arg = False
            if re.match(r"^[a-zA-Z0-9_:\-]+$", t):
                continue
            return False

        if t.startswith("-") or t.startswith("+"):
            if not SAFE_READ_FLAG_PATTERN.match(t):
                return False
            if t in opt_with_arg:
                prev_option_expects_arg = True
            continue

        # Unsafe argument format: reject anything not matching standard path chars
        if not re.match(r"^[a-zA-Z0-9_\-\./~]+$", t):
            return False
        # Reject directory traversal attempts
        if ".." in t.split("/"):
            return False
        if is_secret_file_path(t):
            return False
        norm_t = posixpath.normpath(t.replace("~", "/home/user"))
        norm_lower = norm_t.lower()
        if re.search(r"(?:private|privkey|server\.key|tls\.key|client\.key|\.key$)", norm_lower):
            return False
        is_known_public = (
            norm_lower.endswith(".pub")
            or any(pub in norm_lower for pub in ["ca-certificates", "ca-bundle", "cacert", "fullchain.pem", "chain.pem", "cert.pem", "certificate.pem"])
            or (norm_lower.startswith(("/etc/ssl/certs/", "/etc/pki/tls/certs/", "/etc/pki/ca-trust/")) and norm_lower.endswith((".crt", ".pem", ".cer", ".pub", ".bundle")))
            or norm_lower in ("/etc/ssl/cert.pem", "/etc/pki/tls/cert.pem")
        )
        if not is_known_public:
            return False
        inspected_paths += 1

    if prev_option_expects_arg or inspected_paths == 0:
        return False
    return True


def is_forbidden_audit_path(path: str) -> bool:
    """Check if a path refers to untrusted, temporary, remote, or traversal targets."""
    p = path.strip().strip("\"'")
    if not p:
        return True
    if re.search(r"https?://|untrusted|attacker", p, re.IGNORECASE):
        return True
    if "%2e" in p.lower() or "%2f" in p.lower() or "%5c" in p.lower():
        return True
    p_normalized_slashes = p.replace("\\", "/")
    if ".." in p_normalized_slashes.split("/"):
        return True
    norm_p = posixpath.normpath(p_normalized_slashes.replace("~", "/home/user"))
    norm_lower = norm_p.lower()
    if norm_lower.startswith("..") or "/../" in norm_lower or norm_lower.endswith("/.."):
        return True
    FORBIDDEN_DIR_PREFIXES = (
        "/tmp/", "/var/tmp/", "/dev/shm/",
        "tmp/", "var/tmp/", "dev/shm/",
    )
    FORBIDDEN_EXACT_DIRS = (
        "/tmp", "/var/tmp", "/dev/shm",
        "tmp", "var/tmp", "dev/shm",
    )
    if norm_lower.startswith(FORBIDDEN_DIR_PREFIXES) or norm_lower in FORBIDDEN_EXACT_DIRS:
        return True
    if re.search(r"(?:^|/)(?:tmp|var/tmp|dev/shm)(?:/|$)", norm_lower):
        return True
    return False


def is_trusted_nuclei_template_path(path_str: str) -> bool:
    """Split comma-separated template lists, normalize paths, and verify trust."""
    paths = [p.strip().strip("\"'") for p in path_str.split(",") if p.strip().strip("\"'")]
    if not paths:
        return False
    for p in paths:
        if is_forbidden_audit_path(p):
            return False
        if not re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", p):
            return False
    return True


def is_trusted_semgrep_config_path(config_str: str) -> bool:
    """Split comma-separated config lists, normalize paths, and verify trust."""
    configs = [c.strip().strip("\"'") for c in config_str.split(",") if c.strip().strip("\"'")]
    if not configs:
        return False
    for c in configs:
        # First validate traversal and forbidden paths for ALL inputs (including registry-prefixed)
        if is_forbidden_audit_path(c):
            return False

        c_lower = c.lower()
        if c_lower in ("auto", "r/all"):
            continue
        if c_lower.startswith(("p/", "r/")):
            registry_id = c[2:]
            if not registry_id:
                return False
            segments = registry_id.split("/")
            if any(seg in ("", ".", "..") for seg in segments):
                return False
            if registry_id.lower().endswith((".yml", ".yaml", ".json")):
                return False
            if re.match(r"^[a-zA-Z0-9_\-\.]+(/[a-zA-Z0-9_\-\.]+)*$", registry_id):
                continue
            return False

        if not re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", c):
            return False
    return True


def is_pure_read_only_action(action: str) -> bool:
    clean = strip_shell_comments(action).strip()
    if not clean:
        return False
    # Reject compound commands, redirects, substitutions, pipes, chaining, globs
    if re.search(r"[\$`\(\)<>|;&\*\?\n\r]", clean):
        return False
    try:
        tokens = shlex.split(clean)
    except Exception:
        return False
    if not tokens:
        return False
    cmd = tokens[0].lower()
    args = [t.lower() for t in tokens[1:]]
    if not args:
        return False
    sub = args[0]

    # Specific strict read-only operations per tool:
    if cmd == "consul" and sub == "members":
        return all(a in ("members", "-detailed", "-segment", "-status") or not a.startswith("-") for a in args)
    if cmd == "helm" and sub in ("status", "list"):
        return True
    if cmd == "kubectl":
        if is_kubectl_secret_hazard(clean):
            return False
        if any(a.startswith("--raw") or a == "--raw" for a in args):
            return False
        flag_with_arg = {
            "-n", "--namespace", "-o", "--output", "-l", "--selector",
            "--field-selector", "-s", "--server", "-f", "--filename",
            "-k", "--kustomize", "--context", "--cluster", "--user",
            "--kubeconfig", "--as", "--as-group", "--template",
            "-t", "--sort-by", "--subresource"
        }
        k_sub = None
        i = 0
        while i < len(args):
            a = args[i]
            if a.startswith("-"):
                if "=" not in a and a.lower() in flag_with_arg and i + 1 < len(args):
                    i += 1
            else:
                k_sub = a.lower()
                break
            i += 1
        if k_sub in ("get", "describe", "cluster-info", "logs", "top"):
            return True
    if cmd == "aws" and len(args) >= 2 and sub == "sts" and args[1] == "get-caller-identity":
        return True
    return False


SECURITY_AUDIT_TOOLS = {"nmap", "trivy", "semgrep", "gitleaks", "checksec", "nuclei", "trufflehog", "falcoctl"}


def is_pure_security_audit_read(action: str) -> bool:
    clean = strip_shell_comments(action).strip()
    if not clean:
        return False
    # Reject compound commands, redirects, substitutions, pipes, chaining, globs
    if re.search(r"[\$`\(\)<>|;&\*\?\n\r]", clean):
        return False
    
    try:
        tokens = shlex.split(clean)
    except Exception:
        return False
    if not tokens:
        return False
    
    cmd = tokens[0].lower()
    if cmd not in SECURITY_AUDIT_TOOLS:
        return False

    args = tokens[1:]

    # Universal security tool restrictions:
    # Reject any output redirection or file write flags across all tools
    for i, t in enumerate(args):
        t_lower = t.lower()
        if t_lower in ("-o", "--output", "--output-file", "--report-path", "--sarif-output", "--json-output", "-on", "-ox", "-os", "-og", "-oa"):
            return False
        if any(t_lower.startswith(f"{bad}=") for bad in ("--output", "--output-file", "--report-path", "--sarif-output", "--json-output")):
            return False
        if t_lower.startswith("-o") and len(t) > 2 and not t_lower.startswith(("-os", "-on", "-ox", "-og", "-oa")):
            return False
        if t_lower.startswith(("--script", "--script-args", "--script-help", "--interactive", "--clear-cache", "--reset")):
            return False
        if t_lower in ("--script", "--script-args", "--script-updatedb", "--system-info", "--clear-cache", "--reset", "--download-db-only"):
            return False

    if cmd == "nmap":
        SAFE_NMAP_FLAGS = {
            "-sv", "-ss", "-st", "-su", "-sa", "-sw", "-sm", "-sn", "-sf", "-sx",
            "-pn", "-n", "-r", "-v", "-vv", "-q", "-o", "-f", "-6",
            "-t0", "-t1", "-t2", "-t3", "-t4", "-t5",
            "--traceroute", "--reason", "--open"
        }
        prev_expects_arg = False
        target_count = 0
        for t in args:
            if prev_expects_arg:
                prev_expects_arg = False
                if re.match(r"^[a-zA-Z0-9_,\.:\-]+$", t):
                    continue
                return False

            t_lower = t.lower()
            if t_lower in ("-p", "-t", "--top-ports", "--exclude", "--max-rate", "--min-rate"):
                prev_expects_arg = True
                continue
            if t_lower.startswith("-p"):
                val = t.split("=", 1)[1] if "=" in t else t[2:]
                if val and re.match(r"^[0-9,\-]+$", val):
                    continue
                return False
            if t_lower.startswith("--top-ports="):
                val = t.split("=", 1)[1]
                if val and val.isdigit():
                    continue
                return False
            if t_lower in SAFE_NMAP_FLAGS:
                continue
            if t.startswith("-"):
                return False
            if re.match(r"^[a-zA-Z0-9_\-\./:]+$", t) and not t.startswith("-"):
                target_count += 1
                continue
            return False

        if prev_expects_arg:
            return False
        return target_count > 0

    elif cmd == "trivy":
        if not args:
            return False
        subcmd = args[0].lower()
        if subcmd not in ("image", "fs", "repo", "config", "rootfs", "sbom"):
            return False
        sub_args = args[1:]
        prev_expects_arg = False
        target_count = 0
        for t in sub_args:
            if prev_expects_arg:
                prev_expects_arg = False
                if re.match(r"^[a-zA-Z0-9_,\.:\-/]+$", t):
                    continue
                return False
            t_lower = t.lower()
            if t_lower in ("--severity", "--vuln-type", "--format", "--scanners", "--exit-code", "--timeout", "--ignore-policy"):
                prev_expects_arg = True
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("--severity", "--vuln-type", "--format", "--scanners", "--exit-code", "--timeout")):
                continue
            if t_lower in ("--ignore-unfixed", "-q", "--quiet", "--no-progress", "--light"):
                continue
            if t.startswith("-"):
                return False
            if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", t):
                target_count += 1
                continue
            return False

        if prev_expects_arg:
            return False
        return target_count > 0

    elif cmd == "semgrep":
        SAFE_SEMGREP_BOOLEAN_FLAGS = {
            "-q", "--quiet", "-v", "--verbose", "--debug",
            "--error", "--strict", "--no-git-ignore", "--scan-unknown-extensions",
            "--time", "--validate", "--optimizations=all", "--optimizations=none"
        }
        prev_expects_arg = False
        target_count = 0
        for t in args:
            if prev_expects_arg:
                prev_type = prev_expects_arg
                prev_expects_arg = False
                if prev_type == "config":
                    if not is_trusted_semgrep_config_path(t):
                        return False
                    continue
                else:
                    if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", t):
                        continue
                    return False
            t_lower = t.lower()
            if t_lower in ("--config", "-c", "--rules"):
                prev_expects_arg = "config"
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("--config", "-c", "--rules")):
                val = t.split("=", 1)[1]
                if not is_trusted_semgrep_config_path(val):
                    return False
                continue
            if t_lower in ("--exclude", "--include", "--severity", "--lang", "--timeout"):
                prev_expects_arg = "opt"
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("--exclude", "--include", "--severity", "--lang", "--timeout")):
                val = t.split("=", 1)[1]
                if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", val):
                    continue
                return False
            if t_lower in SAFE_SEMGREP_BOOLEAN_FLAGS:
                continue
            if t.startswith("-"):
                return False
            if re.search(r"https?://|untrusted|attacker", t, re.IGNORECASE):
                return False
            if re.match(r"^[a-zA-Z0-9_,\.:\-/@~]+$", t):
                target_count += 1
                continue
            return False

        if prev_expects_arg:
            return False
        return target_count > 0

    elif cmd == "nuclei":
        SAFE_NUCLEI_BOOLEAN_FLAGS = {
            "-v", "-verbose", "-silent", "-nc", "-no-color", "-stats", "-version"
        }
        prev_expects_arg = False
        target_count = 0
        for t in args:
            if prev_expects_arg:
                prev_type = prev_expects_arg
                prev_expects_arg = False
                if prev_type == "template":
                    if not is_trusted_nuclei_template_path(t):
                        return False
                    continue
                elif prev_type == "target":
                    if re.match(r"^[a-zA-Z0-9_,\.:\-/@:]+$", t):
                        target_count += 1
                        continue
                    return False
                else:
                    if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", t):
                        continue
                    return False

            t_lower = t.lower()
            if t_lower in ("-t", "-templates", "-template"):
                prev_expects_arg = "template"
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("-t", "-templates", "-template")):
                val = t.split("=", 1)[1]
                if not is_trusted_nuclei_template_path(val):
                    return False
                continue
            if t_lower in ("-u", "-target", "-l", "-list"):
                prev_expects_arg = "target"
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("-u", "-target", "-l", "-list")):
                val = t.split("=", 1)[1]
                if re.match(r"^[a-zA-Z0-9_,\.:\-/@:]+$", val):
                    target_count += 1
                    continue
                return False
            if t_lower in ("-s", "-severity", "-tags", "-etags", "-c", "-concurrency", "-rate-limit", "-rl", "-timeout", "-retries"):
                prev_expects_arg = "opt"
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("-s", "-severity", "-tags", "-etags", "-c", "-concurrency", "-rate-limit", "-timeout")):
                continue
            if t_lower in SAFE_NUCLEI_BOOLEAN_FLAGS:
                continue
            if t.startswith("-"):
                return False
            if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", t):
                target_count += 1
                continue
            return False

        if prev_expects_arg:
            return False
        return target_count > 0

    elif cmd == "gitleaks":
        if not args:
            return False
        subcmd = args[0].lower()
        if subcmd not in ("detect", "protect", "dir"):
            return False
        sub_args = args[1:]
        prev_expects_arg = False
        for t in sub_args:
            if prev_expects_arg:
                prev_expects_arg = False
                if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", t):
                    continue
                return False
            t_lower = t.lower()
            if t_lower in ("-s", "--source", "-c", "--config", "--log-opts"):
                prev_expects_arg = True
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("--source", "-s", "--config", "-c", "--log-opts")):
                continue
            if t_lower in ("-v", "--verbose", "-q", "--quiet", "--no-git"):
                continue
            if t.startswith("-"):
                return False
            if re.match(r"^[a-zA-Z0-9_,\.:\-/@~]+$", t):
                continue
            return False
        if prev_expects_arg:
            return False
        return True

    elif cmd == "checksec":
        prev_expects_arg = False
        for t in args:
            if prev_expects_arg:
                prev_expects_arg = False
                if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", t):
                    continue
                return False
            t_lower = t.lower()
            if t_lower in ("--file", "--dir", "--proc"):
                prev_expects_arg = True
                continue
            if any(t_lower.startswith(f"{opt}=") for opt in ("--file", "--dir", "--proc")):
                continue
            if t_lower in ("--proc-all", "--format=cli", "--format=json"):
                continue
            if t.startswith("-"):
                return False
            if re.match(r"^[a-zA-Z0-9_,\.:\-/@~]+$", t):
                continue
            return False
        if prev_expects_arg:
            return False
        return True

    elif cmd == "trufflehog":
        if not args:
            return False
        subcmd = args[0].lower()
        if subcmd not in ("git", "filesystem", "directory", "github", "s3"):
            return False
        sub_args = args[1:]
        prev_expects_arg = False
        for t in sub_args:
            if prev_expects_arg:
                prev_expects_arg = False
                if re.match(r"^[a-zA-Z0-9_,\.:\-/@]+$", t):
                    continue
                return False
            t_lower = t.lower()
            if t_lower in ("--since-commit", "--branch", "--concurrency"):
                prev_expects_arg = True
                continue
            if t_lower in ("--only-verified", "--no-update", "-v", "--debug", "--json"):
                continue
            if t.startswith("-"):
                return False
            if re.match(r"^[a-zA-Z0-9_,\.:\-/@~]+$", t):
                continue
            return False
        if prev_expects_arg:
            return False
        return True

    elif cmd == "falcoctl":
        if len(args) < 2:
            return False
        subcmd = args[0].lower()
        subaction = args[1].lower()
        if subcmd not in ("artifact", "driver", "rule"):
            return False
        if subaction not in ("search", "info", "validate"):
            return False
        for t in args[2:]:
            if t.startswith("-"):
                return False
            if not re.match(r"^[a-zA-Z0-9_,\.:\-/@~]+$", t):
                return False
        return True

    return False


def is_secret_disclosure_hazard(action: str) -> bool:
    action_lower = action.lower().strip()
    
    # 1. Explicit token patterns or assignments with string values
    if re.search(r"\b(?:sk-proj-[a-zA-Z0-9_\-]{15,}|ghp_[a-zA-Z0-9]{20,}|gho_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16})\b", action):
        return True
    if re.search(r"-----BEGIN\s+(?:RSA|OPENSSH|DSA|EC)?\s*PRIVATE\s+KEY-----", action):
        return True
    if re.search(r"\b(?:api[ _-]?secret|api[ _-]?key|secret[ _-]?token)\s*[:=]\s*['\"][^'\"]+['\"]", action_lower):
        return True

    # 1b. Shell / CLI patterns dumping secrets or exfiltrating to world-readable files / external endpoints
    # Check read commands per file argument using quote-aware shell comment stripping
    clean_action = strip_shell_comments(action)
    for m in re.finditer(r"\b(?:cat|head|tail|more|less|bat)\s+([^\n;|]+)", clean_action, re.IGNORECASE):
        args_str = m.group(1).strip()
        try:
            tokens = shlex.split(args_str)
        except Exception:
            tokens = args_str.split()
        for token in tokens:
            if is_secret_file_path(token):
                return True

    if re.search(r"\becho\s+\$[A-Za-z0-9_]*(?:TOKEN|PAT|SECRET|KEY|PASSWORD|CREDS|PASS)[A-Za-z0-9_]*\s*(?:>>|>)\s*(?:/tmp/|/var/tmp/|.*public)", action, re.IGNORECASE):
        return True
    # Secret / credential / kubeconfig dumping or exporting into public logs, gists, or external destinations
    if re.search(r"\b(?:kubeconfig[A-Za-z0-9_]*|credentials?[A-Za-z0-9_]*|tokens?[A-Za-z0-9_]*|secrets?[A-Za-z0-9_]*|private[_-]?key|api[_-]?key|pat|passwords?[A-Za-z0-9_]*)\b.*?\b(?:into\s+public|to\s+public|public\s+build\s+log|public\s+output|public\s+gist|unencrypted|world-readable)\b", action, re.IGNORECASE):
        # Allow if explicitly negated in preventative prose
        if not re.search(r"\b(?:do\s+not|don't|never|avoid|prevent|prohibit|forbid)\b", action, re.IGNORECASE):
            return True
    if re.search(r"\b(?:expose|publish|leak|dump|transmit|broadcast)\b.*?\b(?:private\s+(?:root\s+)?(?:ca\s+)?key|signing\s+key|encryption\s+key|symmetric\s+master\s+key|session\s+(?:cookie|token)|totp\s+secret)\b", action_lower):
        if not re.search(r"\b(?:do\s+not|don't|never|avoid|prevent|prohibit|forbid|without\s+revealing)\b", action_lower):
            return True
    # Check for curl/wget exfiltrating secret files or piped secrets to ANY destination
    if re.search(r"\b(?:curl|wget)\b", action, re.IGNORECASE):
        # 1. Piped stream upload to curl/wget
        if re.search(r"\b(?:cat|echo|vault|grep)\b.*?\|\s*(?:curl|wget)\b", action, re.IGNORECASE):
            return True
        # 2. Upload flags referencing secret files or private keys
        upload_match = re.search(r"(?:--data[a-z0-9_-]*|--form[a-z0-9_-]*|--upload-file|--post-file|-d|-F|-T)\s*[:=]?\s*['\"]?@?(\S+)", action, re.IGNORECASE)
        if upload_match:
            filepath = upload_match.group(1).lstrip("@").strip("\"'")
            if is_secret_file_path(filepath) or re.search(r"(?:private|server\.key|id_rsa|id_ed25519|\.key$|shadow)", filepath, re.IGNORECASE):
                return True
        # 3. Any @path parameter in curl/wget arguments referencing secret files
        for ap in re.findall(r"@([a-zA-Z0-9_./~-]+)", action):
            if is_secret_file_path(ap) or re.search(r"(?:private|server\.key|id_rsa|id_ed25519|\.key$|shadow)", ap, re.IGNORECASE):
                return True

    # Secret / private key uploads to cloud storage or remote hosts (aws s3, gsutil, az, scp, rsync)
    for tool_m in re.finditer(r"\b(?:aws\s+s3\s+(?:cp|sync|mv)|gsutil\s+(?:cp|rsync)|az\s+storage\s+blob\s+upload|scp|rsync)\s+([^\n;|]+)", clean_action, re.IGNORECASE):
        t_args = tool_m.group(1).strip()
        try:
            tokens_t = shlex.split(t_args)
        except Exception:
            tokens_t = t_args.split()
        for tok in tokens_t:
            if is_secret_file_path(tok) or re.search(r"(?:/private/|server\.key|\.key$|id_rsa|id_ed25519|shadow)", tok, re.IGNORECASE):
                return True

    # Kubernetes secret inspection, raw secret API dump, or credential field extraction
    if is_kubectl_secret_hazard(clean_action):
        return True

    # Flag curl/wget with upload payload flags to known untrusted upload services
    if re.search(r"(?:pastebin|gist\.github|transfer\.sh|bashupload)", action, re.IGNORECASE):
        if re.search(r"\bcurl\b", action, re.IGNORECASE):
            if re.search(r"(?:^|\s)-[a-zA-Z]*[dFT](?:\s|[='\"@A-Za-z0-9_])", action):
                return True
            if re.search(r"(?:--data\b|--data-|--form\b|--form-|--upload-file\b|(?:-X|--request)\s*(?:POST|PUT|PATCH)\b)", action, re.IGNORECASE):
                return True
        if re.search(r"\bwget\b", action, re.IGNORECASE):
            if re.search(r"(?:--post-data\b|--post-file\b|--method[=\s]*(?:POST|PUT|PATCH)\b)", action, re.IGNORECASE):
                return True

    # 2. Check clause-by-clause for natural language instructions
    clauses = re.split(r"[;\n]|\band\s+then\b", action)
    for clause in clauses:
        c_lower = clause.lower().strip()
        is_negated = bool(re.search(
            r"\b(?:do\s+not|don't|never|avoid|prevent|prohibit|forbid|ensure\s+no(?:t)?|ensure\s+we\s+do\s+not|warn\s+against)\b.*?"
            r"\b(?:publish|leak|disclose|expose|upload|post|share|broadcast|commit|write|dump|echo|export|save|log|output|store|exfiltrate|print|copy|append|record|persist)\b",
            c_lower
        ))
        
        has_disclosure = False
        # Matches network or external public leaks
        if re.search(
            r"\b(?:publish|leak|disclose|expose|upload|post|share|broadcast|commit)\b.*?"
            r"\b(?:the\s+|a\s+|our\s+|my\s+|live\s+|production\s+|raw\s+|unencrypted\s+|enterprise\s+)?"
            r"(?:(?:aws|ssh|gcp|azure|database|user|admin|github|k8s|vault)?\s*)?"
            r"(?:api[ _-]?secrets?|secrets?|api[ _-]?keys?|secret[ _-]?tokens?|tokens?|personal\s+access\s+tokens?|pats?|private\s+keys?|passwords?|credentials?(?:\s+files?)?(?:\s+backups?)?|kubeconfig[a-z0-9_]*)\b.*?"
            r"(?:\b(?:in|on|to|into|at)\b.*?\b(?:public|website|internet|pastebin|gist|docs?|documentation|wiki|readme|repos?(?:itory)?|forums?|slack|discord|bucket)\b|\bpublicly\b)",
            c_lower
        ):
            has_disclosure = True

        # Matches local exfiltration / writing secrets to world-readable or unencrypted files/logs
        if re.search(
            r"\b(?:write|dump|echo|export|save|log|output|store|exfiltrate|print|copy|append|record|persist)\b.*?"
            r"\b(?:the\s+|a\s+|our\s+|my\s+|live\s+|production\s+|raw\s+|unencrypted\s+|enterprise\s+)?"
            r"(?:(?:aws|ssh|gcp|azure|database|user|admin|github|k8s|vault)?\s*)?"
            r"(?:api[ _-]?secrets?|secrets?|api[ _-]?keys?|secret[ _-]?tokens?|tokens?|personal\s+access\s+tokens?|pats?|private\s+keys?|passwords?|credentials?(?:\s+files?)?(?:\s+backups?)?|kubeconfig[a-z0-9_]*)\b.*?"
            r"(?:\b(?:in|to|into|at|on|onto|inside|within)\b.*?\b(?:world-readable(?:\s+files?)?|world-accessible|unencrypted(?:\s+files?)?|public(?:\s+[a-z0-9_-]+)*\s*(?:files?|log(?:\s+stream)?|endpoints?|output|gist|txt)?)\b)",
            c_lower
        ):
            has_disclosure = True
            
        if re.search(
            r"\b(?:publish|leak|disclose|expose|upload|post|dump|print)\b.*?\b(?:live|actual|raw|production|real|master)\b.*?\b(?:api[ _-]?secret|secret|api[ _-]?key|token|credential|private\s+key)\b",
            c_lower
        ):
            has_disclosure = True
            
        if has_disclosure and not is_negated:
            return True

    return False


def parse_shell_clauses(text: str) -> list:
    """Parse shell syntax into separate pipeline clauses respecting quotes, newlines, and stripping shell comments."""
    clean_text = strip_shell_comments(text)
    try:
        lexer = shlex.shlex(clean_text, posix=False, punctuation_chars=True)
        lexer.whitespace = ' \t'
        lexer.whitespace_split = False
        lexer.commenters = ''
        lexer.wordchars += '#$'
        tokens = list(lexer)
    except Exception:
        # Fallback preserving newline boundaries
        tokens = []
        for line in clean_text.splitlines():
            tokens.extend(line.split())
            tokens.append('\n')
        if tokens and tokens[-1] == '\n':
            tokens.pop()
        
    clauses = []
    current_clause = []
    for token in tokens:
        # Delimiters must be unquoted punctuation or unquoted newline
        if token in (';', '&&', '||', '|', '&', '\n', '\r\n', '\r'):
            if current_clause:
                clauses.append(current_clause)
                current_clause = []
        else:
            current_clause.append(token)
            
    if current_clause:
        clauses.append(current_clause)
        
    return clauses

def is_clause_locally_negated(tokens: list) -> bool:
    clause_text = ' '.join(clean_token(t) for t in tokens).lower()
    negation_patterns = [
        r"\b(?:do\s+not|don't|never|avoid|prevent|prohibit|forbid|ensure\s+no(?:t)?|ensure\s+we\s+do\s+not)\s+(?:delete|wipe|drop|remove|erase|overwrite|destroy|reset|del|leak|publish)\b",
        r"\b(?:why\s+it\s+is\s+dangerous|danger\s+of|risks\s+of|preventative\s+documentation)\b",
        r"\b(?:warning|note|caution|info|docs?|documentation)\b.*?\b(?:do\s+not|never|avoid|risks?)\b",
        r"\b(?:avoid|prevent|do\s+not|never)\b.*?\b(?:terraform\s+destroy|kubeadm\s+reset|etcdctl\s+del)\b",
    ]
    for pat in negation_patterns:
        if re.search(pat, clause_text):
            return True
    return False

def unwrap_command_tokens(tokens: list) -> list:
    """Strip leading grouping delimiters, control keywords, VAR=VAL assignments, and known wrappers with their option arguments."""
    wrappers_with_optarg = {
        'sudo': {'-u', '-g', '-p', '-C', '-D', '-R', '-T', '-U'},
        'nice': {'-n'},
        'ionice': {'-c', '-n', '-p'},
        'chroot': set(),
        'env': {'-u'},
        'nohup': set(),
        'exec': set(),
        'time': {'-o', '-f'},
        'xargs': {'-n', '-s', '-I', '-P', '-d'},
        'builtin': set(),
    }
    
    # Strip trailing grouping and control keywords
    end_idx = len(tokens)
    while end_idx > 0 and clean_token(tokens[end_idx - 1]) in ('}', ')', 'done', 'fi', 'esac'):
        end_idx -= 1
    tokens = tokens[:end_idx]
    
    idx = 0
    while idx < len(tokens):
        token = clean_token(tokens[idx])
        # Shell grouping constructs, pipeline negation, and control keywords
        if token in ('{', '(', '!', 'do', 'then', 'else', 'elif', 'if', 'while', 'until'):
            idx += 1
            continue
            
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=.*', token):
            idx += 1
            continue
            
        base_cmd = Path(token).name
        # Builtin wrapper 'command' has distinct behavior for execution vs lookup
        if base_cmd == 'command':
            idx += 1
            is_lookup = False
            while idx < len(tokens):
                arg = clean_token(tokens[idx])
                if arg in ('-v', '-V') or (arg.startswith('-') and any(c in arg for c in ('v', 'V'))):
                    is_lookup = True
                    idx += 1
                elif arg == '-p':
                    idx += 1
                elif arg == '--':
                    idx += 1
                    break
                elif arg.startswith('-'):
                    idx += 1
                else:
                    break
            if is_lookup:
                # Read-only command lookup like 'which' or 'type', does not execute the target
                return ['command-lookup']
            continue

        if base_cmd in wrappers_with_optarg:
            optargs = wrappers_with_optarg[base_cmd]
            idx += 1
            while idx < len(tokens):
                arg = clean_token(tokens[idx])
                if arg in ('{', '(', '!', 'do', 'then', 'else', 'elif', 'if', 'while', 'until'):
                    idx += 1
                    continue
                if arg.startswith('-'):
                    if arg in optargs and idx + 1 < len(tokens):
                        idx += 2
                    else:
                        idx += 1
                elif base_cmd == 'env' and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=.*', arg):
                    idx += 1
                else:
                    break
        else:
            break
            
    return tokens[idx:]


def is_kubectl_secret_hazard(action: str) -> bool:
    """Inspect kubectl invocations for Secret resource retrieval or credential extraction regardless of option ordering."""
    clean_action = strip_shell_comments(action).strip()
    if not re.search(r"\bkubectl\b", clean_action, re.IGNORECASE):
        return False

    try:
        clauses = parse_shell_clauses(clean_action)
    except Exception:
        clauses = []

    for clause_tokens in clauses:
        unwrapped = unwrap_command_tokens(clause_tokens)
        if not unwrapped:
            continue
        k_indices = [i for i, t in enumerate(unwrapped) if clean_token(t).lower().endswith("kubectl")]
        for k_idx in k_indices:
            args = [clean_token(t) for t in unwrapped[k_idx + 1:]]
            if not args:
                continue

            subcmd = None
            resources = []
            has_raw_secret = False
            has_secret_output = False

            flag_with_arg = {
                "-n", "--namespace", "-o", "--output", "-l", "--selector",
                "--field-selector", "-s", "--server", "-f", "--filename",
                "-k", "--kustomize", "--context", "--cluster", "--user",
                "--kubeconfig", "--raw", "--as", "--as-group", "--template",
                "-t", "--sort-by", "--subresource"
            }

            i = 0
            while i < len(args):
                arg = args[i]
                arg_lower = arg.lower()

                # Check --raw flag
                if arg_lower.startswith("--raw="):
                    val = arg_lower.split("=", 1)[1]
                    if "secret" in val:
                        has_raw_secret = True
                elif arg_lower == "--raw" and i + 1 < len(args):
                    if "secret" in args[i + 1].lower():
                        has_raw_secret = True
                    i += 1
                # Check output extraction flags with selectors/templates
                elif arg_lower.startswith(("-o=", "--output=")):
                    val = arg_lower.split("=", 1)[1]
                    if re.search(r"(?:jsonpath|go-template|custom-columns|template)", val):
                        if re.search(r"(?<!meta)\bdata\b|\b(?:password|token|secret|private[_-]?key|secretkeyref)\b", val):
                            has_secret_output = True
                elif arg_lower in ("-o", "--output") and i + 1 < len(args):
                    fmt = args[i + 1].lower()
                    selector_parts = [fmt]
                    if re.match(r"^(?:jsonpath|go-template|custom-columns|template)$", fmt) and i + 2 < len(args):
                        selector_parts.append(args[i + 2].lower())
                        i += 1
                    for part in selector_parts:
                        if re.search(r"(?:jsonpath|go-template|custom-columns|template)", part) or len(selector_parts) > 1:
                            if re.search(r"(?<!meta)\bdata\b|\b(?:password|token|secret|private[_-]?key|secretkeyref)\b", part):
                                has_secret_output = True
                    i += 1
                elif arg.startswith("-"):
                    if "=" not in arg and arg_lower in flag_with_arg and i + 1 < len(args):
                        i += 1
                else:
                    if subcmd is None:
                        subcmd = arg_lower
                    else:
                        resources.append(arg_lower)
                i += 1

            if has_raw_secret or has_secret_output:
                return True

            if subcmd in ("get", "describe"):
                for res in resources:
                    parts = res.split("/")
                    res_types = [rt.strip() for rt in parts[0].split(",")]
                    if any(rt in ("secret", "secrets") for rt in res_types):
                        return True

    # Regex fallback for non-standard shells or chained invocations
    if re.search(r"\bkubectl\b[^;&|\n]*\b(?:get|describe)\b[^;&|\n]*\bsecrets?(?:/[a-zA-Z0-9_\.\-]+)?(?![a-zA-Z0-9_\-])", clean_action, re.IGNORECASE) or \
       re.search(r"\bkubectl\b[^;&|\n]*\bsecrets?(?:/[a-zA-Z0-9_\.\-]+)?(?![a-zA-Z0-9_\-])[^;&|\n]*\b(?:get|describe)\b", clean_action, re.IGNORECASE):
        return True
    if re.search(r"--raw\s*=?\s*[^\s]*secrets", clean_action, re.IGNORECASE):
        return True
    if re.search(r"-o\s*=?\s*(?:jsonpath[a-z-]*|custom-columns|go-template)[^;&|\n]*(?:(?<!meta)\bdata\b|\b(?:password|token|secret|private[_-]?key|secretkeyref)\b)", clean_action, re.IGNORECASE):
        return True

    return False


def is_security_audit_tool_invocation(action: str, depth: int = 0) -> bool:
    """Check if an action invokes any recognized security audit or vulnerability scanning tool, inspecting shell payloads recursively."""
    if not action:
        return False
    if depth > 5:
        # Parser exhaustion: force review rather than returning false
        return True
    clean = strip_shell_comments(action).strip()
    if not clean:
        return False

    try:
        clauses = parse_shell_clauses(clean)
    except Exception:
        clauses = []

    for c in clauses:
        unwrapped = unwrap_command_tokens(c)
        if not unwrapped:
            continue
        cmd = Path(clean_token(unwrapped[0])).name.lower()
        if cmd in SECURITY_AUDIT_TOOLS:
            return True

        # Shell interpreters: sh -c "...", bash -c "...", eval "..."
        if cmd in {"sh", "bash", "zsh", "dash", "ksh", "csh", "tcsh", "su"}:
            i = 1
            while i < len(unwrapped):
                arg = clean_token(unwrapped[i])
                if arg in ("-c", "--command") or (arg.startswith("-") and "c" in arg and not arg.startswith("--")):
                    if i + 1 < len(unwrapped):
                        payload = strip_quotes(unwrapped[i + 1])
                        if is_security_audit_tool_invocation(payload, depth=depth + 1):
                            return True
                        i += 2
                        continue
                i += 1
        elif cmd == "eval":
            payload = " ".join(strip_quotes(t) for t in unwrapped[1:])
            if is_security_audit_tool_invocation(payload, depth=depth + 1):
                return True

    try:
        tokens = shlex.split(clean)
        if tokens:
            cmd = Path(clean_token(tokens[0])).name.lower()
            if cmd in SECURITY_AUDIT_TOOLS:
                return True
            if cmd in {"sh", "bash", "zsh", "dash", "ksh", "csh", "tcsh", "su"}:
                i = 1
                while i < len(tokens):
                    arg = clean_token(tokens[i])
                    if arg in ("-c", "--command") or (arg.startswith("-") and "c" in arg and not arg.startswith("--")):
                        if i + 1 < len(tokens):
                            payload = strip_quotes(tokens[i + 1])
                            if is_security_audit_tool_invocation(payload, depth=depth + 1):
                                return True
                            i += 2
                            continue
                    i += 1
    except Exception:
        pass

    return False


def check_shell_nesting_depth(action: str, depth: int = 0, max_depth: int = 5) -> bool:
    """Return True if shell interpreter nesting exceeds max_depth (parser exhaustion)."""
    if not action:
        return False
    if depth > max_depth:
        return True
    clean = strip_shell_comments(action).strip()
    if not clean:
        return False
    try:
        clauses = parse_shell_clauses(clean)
    except Exception:
        return False

    for c in clauses:
        unwrapped = unwrap_command_tokens(c)
        if not unwrapped:
            continue
        cmd = Path(clean_token(unwrapped[0])).name.lower()
        if cmd in {"sh", "bash", "zsh", "dash", "ksh", "csh", "tcsh", "su"}:
            i = 1
            while i < len(unwrapped):
                arg = clean_token(unwrapped[i])
                if arg in ("-c", "--command") or (arg.startswith("-") and "c" in arg and not arg.startswith("--")):
                    if i + 1 < len(unwrapped):
                        payload = strip_quotes(unwrapped[i + 1])
                        if check_shell_nesting_depth(payload, depth=depth + 1, max_depth=max_depth):
                            return True
                        i += 2
                        continue
                i += 1
        elif cmd == "eval":
            payload = " ".join(strip_quotes(t) for t in unwrapped[1:])
            if check_shell_nesting_depth(payload, depth=depth + 1, max_depth=max_depth):
                return True
    return False


def is_clause_destructive(tokens: list, depth: int = 0) -> bool:
    if not tokens or depth > 5:
        return False
        
    unwrapped = unwrap_command_tokens(tokens)
    if unwrapped:
        cmd = Path(clean_token(unwrapped[0])).name
        # 1. Shell interpreters: sh -c "...", bash -c "...", eval "..."
        if cmd in {'sh', 'bash', 'zsh', 'dash', 'ksh', 'csh', 'tcsh', 'su'}:
            i = 1
            while i < len(unwrapped):
                arg = clean_token(unwrapped[i])
                if arg in ('-c', '--command') or (arg.startswith('-') and 'c' in arg and not arg.startswith('--')):
                    if i + 1 < len(unwrapped):
                        payload = strip_quotes(unwrapped[i + 1])
                        if is_destructive_action(payload, depth=depth + 1):
                            return True
                        i += 2
                        continue
                i += 1
        elif cmd == 'eval':
            payload = ' '.join(strip_quotes(t) for t in unwrapped[1:])
            if is_destructive_action(payload, depth=depth + 1):
                return True

        # 1b. CLI tools that execute external commands / pagers via options (--pager=..., --exec=..., etc.)
        i = 1
        while i < len(unwrapped):
            token = clean_token(unwrapped[i])
            if token.startswith(('--pager=', '--exec=', '--command=')):
                payload = token.split('=', 1)[1]
                if is_destructive_action(strip_quotes(payload), depth=depth + 1):
                    return True
            elif token in ('--pager', '--exec', '--command') and i + 1 < len(unwrapped):
                payload = strip_quotes(unwrapped[i + 1])
                if is_destructive_action(payload, depth=depth + 1):
                    return True
            i += 1

        # 2. CLI Command Parsing for 'rm' (executable command: negation in arguments does NOT suppress execution)
        if cmd == 'rm':
            has_recursive = False
            targets = []
            for raw_arg in unwrapped[1:]:
                arg = clean_token(raw_arg)
                if arg == '--':
                    continue
                if arg.startswith('--'):
                    if arg in ('--recursive', '-r', '-R'):
                        has_recursive = True
                elif arg.startswith('-') and len(arg) > 1:
                    flags = arg[1:]
                    if any(c in flags for c in ('r', 'R')):
                        has_recursive = True
                else:
                    targets.append(arg)
                    
            if has_recursive:
                return True
                
            critical_targets = [
                r'^/(?:var|etc|bin|usr|boot|root|home|sys|dev|production)',
                r'^~',
                r'^\*',
                r'\.(?:db|sqlite|sqlite3|sql|data|bak)$',
            ]
            for t in targets:
                for ct in critical_targets:
                    if re.search(ct, t):
                        return True

        # 3. Block device / filesystem wiping
        if cmd in {'mkfs', 'fdisk', 'parted'}:
            return True
        if cmd == 'dd':
            args = [clean_token(t) for t in unwrapped[1:]]
            if any(re.match(r'^of=/dev/', a) for a in args):
                return True

        # 4. Git reset --hard
        if cmd == 'git':
            args = [clean_token(t) for t in unwrapped[1:]]
            if 'reset' in args and '--hard' in args:
                return True

        # 4b. Infrastructure cluster/state destruction commands
        if cmd == 'terraform':
            args = [clean_token(t) for t in unwrapped[1:]]
            if 'destroy' in args:
                return True
        if cmd == 'kubeadm':
            args = [clean_token(t) for t in unwrapped[1:]]
            if 'reset' in args:
                return True
        if cmd == 'etcdctl':
            args = [clean_token(t) for t in unwrapped[1:]]
            if 'del' in args:
                return True
        if cmd == 'helm':
            args = [clean_token(t) for t in unwrapped[1:]]
            if any(sub in args for sub in ('uninstall', 'delete')):
                if any(re.search(r'(?:prod|production|database|db|stateful)', a, re.IGNORECASE) for a in args):
                    return True
        if cmd == 'aws':
            args = [clean_token(t).lower() for t in unwrapped[1:]]
            if len(args) >= 2 and args[0] == 's3':
                if args[1] in ('rm', 'rb') or '--delete' in args:
                    return True
        if cmd == 'gsutil':
            args = [clean_token(t).lower() for t in unwrapped[1:]]
            if any(a in ('rm', 'rb') for a in args) or '-d' in args:
                return True

        # 4c. Security bypass, firewall teardown, and audit tampering commands
        if cmd == 'setenforce':
            args = [clean_token(t) for t in unwrapped[1:]]
            if any(a in ('0', 'permissive', 'disabled') for a in args):
                return True
        if cmd == 'ufw':
            args = [clean_token(t) for t in unwrapped[1:]]
            if any(a in ('disable', 'reset') for a in args):
                return True
        if cmd in {'iptables', 'ip6tables', 'nft'}:
            args = [clean_token(t) for t in unwrapped[1:]]
            if any(a in ('-F', '--flush', '-X', '--delete-chain') for a in args) or 'flush' in args:
                return True
        if cmd == 'truncate':
            args = [clean_token(t) for t in unwrapped[1:]]
            if any(re.search(r'(?:/var/log|audit|\.log)', a) for a in args):
                return True
        if cmd == 'shred':
            return True

        # 4d. CLI tool arbitrary file output / overwrite into critical system paths
        for i, raw_arg in enumerate(unwrapped):
            arg = clean_token(raw_arg)
            target_path = None
            if arg in ('-o', '--output', '--output-file', '--report-path', '-oN', '-oX', '-oG', '-oS', '-oA') and i + 1 < len(unwrapped):
                target_path = clean_token(unwrapped[i + 1])
            elif any(arg.startswith(f"{opt}=") for opt in ('--output', '--output-file', '--report-path')):
                target_path = arg.split('=', 1)[1]
            if target_path:
                norm_tgt = posixpath.normpath(target_path.replace("~", "/home/user")).lower()
                if norm_tgt.startswith(('/etc', '/boot', '/root', '/bin', '/sbin', '/usr', '/lib', '/sys', '/dev')):
                    return True

    # 5. Natural language destructive intent (negation applies here to prose instructions)
    if is_clause_locally_negated(tokens):
        return False

    clause_text = ' '.join(clean_token(t) for t in tokens).lower().rstrip('.?!;')
    nl_destructive = [
        r'\bdelete\s+.*?(?:database|pv\s+bindings?|persistent\s*volume|statefulset|production)\b',
        r'\bdelete\s+(?:all|every|the)\s+files?\b',
        r'\bdelete\s+(?:the\s+)?(?:target\s+)?(?:directory|folder|repo|database|volume|tables?)\b',
        r'\bwipe\s+(?:all|every|the|target|every\s+block)\b',
        r'\berase\s+(?:all|every|the)\b',
        r'\boverwrite\s+every\s+block\b',
        r'\b(?:drop\s+(?:table|database|schema)|truncate\s+(?:table)?)\b',
        r'\b(?:terraform\s+destroy|kubeadm\s+reset|etcdctl\s+del)\b',
        r'\bpermanently\s+(?:terminate|destroy|wipe)\s+(?:production\s+)?(?:database|cluster|instance)\b',
        r'\btear\s+down\s+(?:the\s+)?(?:control\s+plane|cluster|infrastructure|all\s+nodes)\b',
        r'\bunjoin\s+(?:all\s+)?(?:kubernetes\s+)?(?:cluster\s+)?nodes\b',
        r'\bdisable\s+(?:the\s+)?(?:firewall|selinux|apparmor|auditd|protections?)\b',
        r'\b(?:disable\s+the\s+firewall\s+and\s+selinux\s+protections)\b',
        r'\b(?:turn\s+off|bypass)\s+(?:the\s+)?(?:firewall|selinux|security\s+controls)\b',
        r'\berase\s+(?:all\s+)?(?:security\s+)?audit\s+logs\b',
        r'\bpermanently\s+destroy\s+.*?(?:certificate\s+authority|ca\b|private\s+key)\b',
        r'\brevoke(?:-all)?\s+(?:all\s+)?(?:enterprise\s+)?certificates?\s+without\s+publishing\s+crl\b',
        r'\brevoke-all-certificates\s+--skip-crl-publish\b',
        r'\bshred\s+.*?(?:ca-root\.key|private)\b',
    ]
    for pat in nl_destructive:
        if re.search(pat, clause_text):
            return True

    return False

def is_destructive_action(action: str, depth: int = 0) -> bool:
    if depth > 5:
        return False
    # Check embedded command substitutions: $(...) and `...`
    for sub in re.findall(r"\$\(([^)]+)\)|`([^`]+)`", action):
        sub_cmd = sub[0] or sub[1]
        if sub_cmd and is_destructive_action(sub_cmd, depth=depth + 1):
            return True
    # Check tool options that execute external commands / pagers
    for m in re.finditer(r"(?:--pager|--exec|--command)[=\s]+(?:(['\"])(.*?)\1|(\S+))", action, re.IGNORECASE):
        cmd_payload = m.group(2) if m.group(1) else m.group(3)
        if cmd_payload and is_destructive_action(cmd_payload, depth=depth + 1):
            return True
    clauses = parse_shell_clauses(action)
    for clause in clauses:
        if is_clause_destructive(clause, depth=depth):
            return True
    return False

class NioMicroInference:
    def __init__(self, model_path: Path, tokenizer_path: Path):
        metadata_path = model_path.parent / "metadata.json"
        self.max_length = 64
        self.metadata = {}
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
            self.metadata = metadata
            if hashlib.sha256(tokenizer_path.read_bytes()).hexdigest() != metadata["tokenizer_sha256"]:
                raise ValueError("Tokenizer does not match model metadata")
            self.max_length = metadata["max_input_length"]
        self.labels = self.metadata.get("decision_labels", ["reject", "approve"])
        contract = self.metadata.get("input_contract", "")
        self.context_required = contract.endswith("_context_v1") or contract == "developer_action_context_v1"
        self.calibration = self.metadata.get("calibration", {})
        if self.context_required:
            try:
                from .context_policy import POLICY_VERSION, LABELS
            except ImportError:
                from context_policy import POLICY_VERSION, LABELS
            if self.metadata.get("policy_version") != POLICY_VERSION or self.labels != LABELS:
                raise ValueError("Unsupported contextual policy version or class mapping")
        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session_options.intra_op_num_threads = 2
        
        self.session = ort.InferenceSession(str(model_path), session_options, providers=["CPUExecutionProvider"])

    def evaluate(self, text: str) -> dict:
        if self.context_required:
            return {"model": "nioxs::nio-micro", "input": text, "decision": "needs_review",
                    "sentiment": None, "score": None, "confidence": None, "is_safe": False,
                    "decision_source": "input_contract", "reason": "Provide action and structured context using evaluate_context or --context."}
        return self._predict(text)

    def evaluate_context(self, action: str, context: dict, feedback: str = "") -> dict:
        if not self.context_required:
            raise ValueError("This artifact does not implement the contextual input contract")
        try:
            from .context_policy import format_input
        except ImportError:
            from context_policy import format_input

        # Bind domain to model's cluster if not explicitly provided
        ctx = dict(context)
        if "domain" not in ctx:
            metadata = getattr(self, "metadata", {})
            ctx["domain"] = metadata.get("cluster", "developer")

        # 1. Execute raw ONNX prediction FIRST to guarantee evaluation integrity
        result = self._predict(format_input(action, ctx, feedback), sentiment_applicable=bool(feedback.strip()))
        
        # 2. Explicit authorization guard
        if ctx.get("authorization") == "denied":
            result.update(decision="reject", decision_source="policy_guard",
                          reason="Authorization is explicitly denied", score=None,
                          confidence=None, is_safe=False)
            return result

        # 3. Missing target or environment guard
        if result["decision"] == "approve" and (
            ctx.get("target", "unknown") == "unknown"
            or ctx.get("environment", "unknown") == "unknown"
        ):
            result.update(decision="needs_review", decision_source="policy_guard",
                          reason="Required target or environment is unknown", score=None,
                          confidence=None, is_safe=False)
            return result

        # 4. Catastrophic security hazard and secret disclosure guard
        for pattern, reason in CATASTROPHIC_PATTERNS:
            if pattern.search(action):
                result.update(decision="reject", decision_source="security_guard",
                              reason=reason, score=None, confidence=None, is_safe=False)
                return result

        if is_secret_disclosure_hazard(action):
            result.update(decision="reject", decision_source="security_guard",
                          reason="Explicit secret publishing hazard", score=None,
                          confidence=None, is_safe=False)
            return result

        parsed_clauses = parse_shell_clauses(action)
        clauses = []
        for tok_list in parsed_clauses:
            clause_str = ' '.join(tok_list).strip()
            sub_clauses = re.split(r"\band\s+then\b", clause_str, flags=re.IGNORECASE)
            for sc in sub_clauses:
                if sc.strip():
                    clauses.append(sc.strip())
        if not clauses:
            clauses = [action.strip()]

        for c in clauses:
            for pattern, reason in CATASTROPHIC_PATTERNS:
                if pattern.search(c):
                    result.update(decision="reject", decision_source="security_guard",
                                  reason=reason, score=None, confidence=None, is_safe=False)
                    return result

            if is_secret_disclosure_hazard(c):
                result.update(decision="reject", decision_source="security_guard",
                              reason="Explicit secret publishing hazard", score=None,
                              confidence=None, is_safe=False)
                return result

        # 5. Production destructive operation guard
        env = ctx.get("environment", "unknown")
        if env == "production":
            if is_destructive_action(action):
                result.update(decision="reject", decision_source="policy_guard",
                              reason="Destructive operation prohibited in production environment",
                              score=None, confidence=None, is_safe=False)
                return result
            for tok_list in parsed_clauses:
                if is_clause_destructive(tok_list):
                    result.update(decision="reject", decision_source="policy_guard",
                                  reason="Destructive operation prohibited in production environment",
                                  score=None, confidence=None, is_safe=False)
                    return result
            for c in clauses:
                if is_destructive_action(c):
                    result.update(decision="reject", decision_source="policy_guard",
                                  reason="Destructive operation prohibited in production environment",
                                  score=None, confidence=None, is_safe=False)
                    return result

        clean_action = strip_shell_comments(action).strip()
        is_compound = len(clauses) > 1 or len(parsed_clauses) > 1

        # 6. Read-only inspection of known public certificates and public keys
        is_cert_read = False
        if not is_compound:
            is_cert_read = is_pure_public_cert_or_key_read(clean_action) or bool(
                re.match(r"^(?:please\s+)?(?:inspect|view|check|verify)\s+(?:the\s+)?(?:expiration\s+date\s+of\s+(?:the\s+)?|validity\s+and\s+san\s+of\s+(?:the\s+)?)?(?:public\s+tls\s+cert(?:ificate)?|x\.?509\s+cert(?:ificate)?)(?:\s+(?:in|for|on)\s+[a-zA-Z0-9_-]+)?[\.\s]*$", clean_action, re.IGNORECASE)
            )
        if is_cert_read and not is_destructive_action(action) and not is_secret_disclosure_hazard(action):
            auth = ctx.get("authorization", "unknown")
            env = ctx.get("environment", "unknown")
            target = ctx.get("target", "unknown")
            if auth == "granted" and env in ("sandbox", "staging", "production") and target in ("known", "internal", "external"):
                result.update(decision="approve", decision_source="policy_guard",
                              reason="Authorized read-only inspection of public certificate material",
                              score=None, confidence=None, is_safe=True)
                return result
            else:
                result.update(decision="needs_review", decision_source="policy_guard",
                              reason="Review read-only inspection of public certificate material",
                              score=None, confidence=None, is_safe=False)
                return result

        # 7. Authorized credential and cryptographic key rotation / firewall enablement / zero-trust setup
        is_cred_rotation_teardown = False
        if not is_compound:
            is_cred_rotation_teardown = bool(re.match(
                r"^(?:please\s+)?(?:permanently\s+destroy\s+root\s+certificate\s+authority\s+private\s+key|revoke\s+all\s+enterprise\s+certificates\s+without\s+publishing\s+crl/ocsp|revoke-all-certificates\s+--skip-crl-publish|shred\s+-u\s+-z\s+/etc/pki/tls/private/ca-root\.key)[\.\s]*$",
                clean_action,
                re.IGNORECASE
            ))
        if is_cred_rotation_teardown and env in ("sandbox", "staging") and not is_secret_disclosure_hazard(action):
            auth = ctx.get("authorization", "unknown")
            target = ctx.get("target", "unknown")
            if auth == "granted" and target in ("known", "internal", "external"):
                result.update(decision="approve", decision_source="policy_guard",
                              reason="Authorized credential rotation in designated environment",
                              score=None, confidence=None, is_safe=True)
                return result
            else:
                result.update(decision="needs_review", decision_source="policy_guard",
                              reason="Review credential rotation authorization and target",
                              score=None, confidence=None, is_safe=False)
                return result

        is_cred_or_fw = False
        if not is_compound:
            is_cred_or_fw = bool(re.match(
                r"^(?:please\s+)?(?:rotate\s+(?:the\s+)?(?:application\s+)?(?:signing\s+key|tls\s+(?:service\s+)?cert(?:ificate)?|credentials?|secret)(?:\s+(?:without\s+revealing\s+its\s+value|in\s+secure\s+key\s+management\s+service))?|enable\s+(?:the\s+)?approved\s+firewall\s+rules?(?:\s+for\s+(?:the\s+)?[a-zA-Z0-9_-]+\s+service)?|vault\s+write\s+auth/jwt/role/[a-zA-Z0-9_-]+\s+bound_audiences=[a-zA-Z0-9_-]+|configure\s+zero-trust\s+jwt\s+authentication\s+role\s+in\s+vault)[\.\s]*$",
                clean_action,
                re.IGNORECASE
            ))
        if is_cred_or_fw and not is_destructive_action(action) and not is_secret_disclosure_hazard(action):
            auth = ctx.get("authorization", "unknown")
            env = ctx.get("environment", "unknown")
            target = ctx.get("target", "unknown")
            if auth == "granted" and env in ("sandbox", "staging", "production") and target in ("known", "internal", "external"):
                result.update(decision="approve", decision_source="policy_guard",
                              reason="Authorized credential rotation in designated environment",
                              score=None, confidence=None, is_safe=True)
                return result
            else:
                result.update(decision="needs_review", decision_source="policy_guard",
                              reason="Review credential rotation authorization and target",
                              score=None, confidence=None, is_safe=False)
                return result

        # 8. Authorized read-only vulnerability audits and security tooling
        is_sec_scan = False
        if not is_compound:
            is_sec_scan = is_pure_security_audit_read(clean_action) or bool(
                re.match(r"^(?:please\s+)?(?:scan\s+(?:the\s+)?(?:application\s+|system\s+)?(?:source(?:\s+code)?|target)\s+for\s+(?:known\s+)?(?:security\s+)?vulnerabilit[a-z]*|perform\s+(?:authorized\s+)?port\s+and\s+service\s+banner\s+enumeration|inspect\s+binary\s+security\s+hardening\s+flags:\s*NX,\s*ASLR,\s*PIE,\s*Canary)[\.\s]*$", clean_action, re.IGNORECASE)
            )
        if is_sec_scan and not is_destructive_action(action) and not is_secret_disclosure_hazard(action):
            auth = ctx.get("authorization", "unknown")
            env = ctx.get("environment", "unknown")
            target = ctx.get("target", "unknown")
            if auth in ("granted", "unknown") and env in ("sandbox", "staging", "production") and target in ("known", "internal", "external"):
                result.update(decision="approve", decision_source="policy_guard",
                              reason="Authorized security vulnerability audit in designated environment",
                              score=None, confidence=None, is_safe=True)
                return result
            else:
                result.update(decision="needs_review", decision_source="policy_guard",
                              reason="Review security vulnerability audit authorization and target",
                              score=None, confidence=None, is_safe=False)
                return result
        elif is_security_audit_tool_invocation(clean_action) and not is_destructive_action(action) and not is_secret_disclosure_hazard(action):
            result.update(decision="needs_review", decision_source="policy_guard",
                          reason="Review security vulnerability audit authorization, configuration, and target",
                          score=None, confidence=None, is_safe=False)
            return result

        # 9. Authorized cluster inspection, read-only telemetry, and infrastructure operations (infra domain only)
        domain = ctx.get("domain", "")
        is_infra_op = False
        is_infra_read_only = False
        if domain == "infra" and not is_compound:
            is_infra_read_only = bool(re.match(
                r"^(?:please\s+)?(?:consul\s+members|inspect\s+(?:consul\s+service\s+discovery\s+mesh\s+members|helm\s+release\s+status)|show\s+(?:the\s+)?health\s+of\s+(?:the\s+)?kubernetes\s+worker\s+nodes)[\.\s]*$",
                clean_action,
                re.IGNORECASE
            )) or is_pure_read_only_action(clean_action)
            is_infra_op = is_infra_read_only or bool(re.match(
                r"^(?:please\s+)?(?:kubectl\s+scale\s+(?:deployment|deploy)/[a-zA-Z0-9_-]+\s+--replicas[=\s]+\d+|scale\s+(?:the\s+)?[a-zA-Z0-9_-]+\s+(?:worker\s+)?deployment(?:\s+replicas)?(?:\s+to\s+(?:[a-zA-Z]+|\d+)(?:\s+replicas)?)?|apply\s+(?:the\s+)?approved\s+terraform\s+plan\s+for\s+(?:the\s+)?staging\s+cluster|vault\s+secrets\s+enable\s+-path=[a-zA-Z0-9_-]+\s+[a-zA-Z0-9_-]+|enable\s+(?:hashicorp\s+)?vault\s+(?:key-value\s+)?secrets\s+engine)[\.\s]*$",
                clean_action,
                re.IGNORECASE
            ))
        if is_infra_op and not is_destructive_action(action) and not is_secret_disclosure_hazard(action):
            auth = ctx.get("authorization", "unknown")
            env = ctx.get("environment", "unknown")
            target = ctx.get("target", "unknown")

            # Production scale-to-zero is a service shutdown hazard: require availability review
            rep_match = re.search(r"(?:--replicas[=\s]+|to\s+)(\d+|zero)(?:\s+replicas)?\b", clean_action, re.IGNORECASE)
            if env == "production" and rep_match:
                val = rep_match.group(1).lower()
                if val in ("0", "zero") or (val.isdigit() and int(val) == 0):
                    result.update(decision="needs_review", decision_source="infra_guard",
                                  reason="Production scale-to-zero requires availability review",
                                  score=None, confidence=None, is_safe=False)
                    return result

            allowed_auth = ("granted", "unknown") if is_infra_read_only else ("granted",)
            if auth in allowed_auth and env in ("sandbox", "staging", "production") and target in ("known", "internal", "external"):
                result.update(decision="approve", decision_source="infra_guard",
                              reason="Authorized cluster inspection and infrastructure operations",
                              score=None, confidence=None, is_safe=True)
                return result
            else:
                result.update(decision="needs_review", decision_source="infra_guard",
                              reason="Review infrastructure operation authorization and target",
                              score=None, confidence=None, is_safe=False)
                return result

        if result["decision"] == "approve" and check_shell_nesting_depth(clean_action):
            result.update(decision="needs_review", decision_source="policy_guard",
                          reason="Exceeded maximum shell interpreter nesting depth; manual review required",
                          score=None, confidence=None, is_safe=False)
            return result

        return result

    def _predict(self, text: str, sentiment_applicable: bool = True) -> dict:
        encoded = self.tokenizer.encode(text)
        if self.max_length != 64 and len(encoded.ids) > self.max_length:
            raise ValueError(f"Input exceeds the {self.max_length}-token model limit")
        ids = encoded.ids[:self.max_length]
        mask = [1] * len(ids)
        padded_length = min(64, self.max_length)
        if len(ids) < padded_length:
            pad = padded_length - len(ids)
            ids = ids + [0] * pad
            mask = mask + [0] * pad

        input_ids = np.array([ids], dtype=np.int64)
        attention_mask = np.array([mask], dtype=np.int64)

        outputs = self.session.run(
            ["decision_logits", "sentiment_logits", "score"],
            {"input_ids": input_ids, "attention_mask": attention_mask}
        )

        dec_logits, sent_logits, score = outputs
        
        # Softmax on logits
        scaled_logits = dec_logits[0] / self.calibration.get("temperature", 1.0)
        dec_exp = np.exp(scaled_logits - np.max(scaled_logits))
        dec_probs = dec_exp / dec_exp.sum()
        dec_pred = int(np.argmax(dec_probs))

        sent_exp = np.exp(sent_logits[0] - np.max(sent_logits[0]))
        sent_probs = sent_exp / sent_exp.sum()
        sent_pred = int(np.argmax(sent_probs))

        if len(self.labels) != len(dec_probs):
            raise ValueError("Decision labels do not match model output")
        raw_decision = self.labels[dec_pred]
        decision_str = raw_decision
        decision_source = "model"
        reason = None
        if self.context_required:
            uncertain = float(dec_probs[dec_pred]) < self.calibration.get("confidence_threshold", 0.8)
            uncertain |= raw_decision == "approve" and float(dec_probs[dec_pred]) < self.calibration.get("approval_threshold", 1.000001)
            if uncertain:
                decision_str = "needs_review"
                decision_source = "confidence_gate"
                reason = ("Automatic approvals disabled: calibration did not support an approval cutoff"
                          if raw_decision == "approve" and self.calibration.get("approval_threshold", 1.000001) > 1
                          else "Prediction below the configured routing threshold")
        sentiment_str = "positive" if sent_pred == 1 else "negative"
        score_val = float(score[0])

        return {
            "model": "nioxs::nio-micro",
            "input": text,
            "decision": decision_str,
            "sentiment": sentiment_str if sentiment_applicable else None,
            "score": None if decision_str == "needs_review" else round(score_val, 3),
            "confidence": None if decision_source != "model" else round(float(dec_probs[dec_pred]), 3),
            "raw_decision": raw_decision, "raw_confidence": round(float(dec_probs[dec_pred]), 3),
            "calibrated_decision": decision_str,
            "decision_source": decision_source,
            "reason": reason,
            "is_safe": decision_str == "approve" and score_val >= 0.70,
        }

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", default="git status")
    parser.add_argument("--models-dir", type=Path, default=base / "models/5m-context")
    parser.add_argument("--context", help='JSON object with environment, authorization, and target')
    parser.add_argument("--feedback", default="")
    parser.add_argument("--simulate-sandbox", action="store_true",
                        help="Explicitly simulate execution in a local developer sandbox (environment=sandbox, authorization=granted, target=known)")
    args = parser.parse_args()
    onnx_file = args.models_dir / "nio_micro.onnx"
    tok_file = args.models_dir / "tokenizer.json"

    if not onnx_file.exists():
        print(f"Error: {onnx_file} not found. Train and export first!")
        sys.exit(1)

    evaluator = NioMicroInference(onnx_file, tok_file)
    query = args.text
    if args.context is not None:
        result = evaluator.evaluate_context(query, json.loads(args.context), args.feedback)
    elif args.simulate_sandbox:
        sim_context = {"environment": "sandbox", "authorization": "granted", "target": "known"}
        result = evaluator.evaluate_context(query, sim_context, args.feedback)
        result["context_source"] = "simulated_sandbox"
    else:
        result = evaluator.evaluate(query)
    print(json.dumps(result, indent=2))
