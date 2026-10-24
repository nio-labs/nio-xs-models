"""Viper 2.0 (100M) — High-Entropy Training Curriculum Generator.

Generates 5 specialized tiers of terminal developer intent:
1. Multi-Stage Pipelines (30%): xargs, awk, sed, jq, sort, uniq, subshells
2. Modern DevOps Suites (25%): kubectl, docker compose, terraform, gh, aws, systemctl
3. Deep Windows PowerShell (20%): object pipelines, Where-Object, Select-Object
4. Fast Atomic Reflexes (15%): grep, find, kill, git, curl
5. Destructive Safety Clutch (10%): Dangerous operations tagged for interactive confirmation
"""

import json
import random
import os
from typing import Dict, Any, List


class Viper2DatasetGenerator:
    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate_multistage_pipeline(self) -> Dict[str, Any]:
        templates = [
            (
                "find all files larger than {size}MB and list their disk usage sorted",
                "find . -type f -size +{size}M -exec du -h {{}} + | sort -hr",
                False,
            ),
            (
                "search for '{pattern}' across rust files and count occurrences per file",
                "grep -roh --include='*.rs' '{pattern}' . | sort | uniq -c | sort -nr",
                False,
            ),
            (
                "extract container names from docker compose config using jq",
                "docker compose config --format json | jq -r '.services | keys[]'",
                False,
            ),
            (
                "find and compress all log files older than {days} days",
                "find /var/log -type f -name '*.log' -mtime +{days} | xargs -r gzip -9",
                True,
            ),
            (
                "find git branches merged into main and delete them",
                "git branch --merged main | grep -v '^[ *]*main$' | xargs -r git branch -d",
                True,
            ),
            (
                "monitor top 5 processes by memory usage continuously",
                "ps aux --sort=-%mem | awk 'NR<=6 {{print $2, $4, $11}}'",
                False,
            ),
            (
                "find broken symlinks in current directory tree",
                "find . -xtype l -print",
                False,
            ),
            (
                "extract status codes and request paths from nginx access logs",
                "awk '{{print $7, $9}}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -n 20",
                False,
            ),
            (
                "kill all running node processes on the system",
                "pgrep -f node | xargs -r kill -9",
                True,
            ),
            (
                "replace all occurrences of '{old_var}' with '{new_var}' across typescript files",
                "find src/ -name '*.ts' -o -name '*.tsx' | xargs -r sed -i 's/{old_var}/{new_var}/g'",
                True,
            ),
        ]
        intent_tmpl, cmd_tmpl, is_destructive = random.choice(templates)
        size = random.choice([50, 100, 250, 500])
        days = random.choice([7, 14, 30, 90])
        pattern = random.choice(["TODO", "FIXME", "unwrap()", "panic!", "unsafe"])
        old_var = random.choice(["apiEndpoint", "authSecret", "maxRetries", "timeoutMs"])
        new_var = random.choice(["apiBaseUrl", "jwtSecretKey", "retryLimit", "requestTimeout"])

        intent = intent_tmpl.format(size=size, days=days, pattern=pattern, old_var=old_var, new_var=new_var)
        cmd = cmd_tmpl.format(size=size, days=days, pattern=pattern, old_var=old_var, new_var=new_var)

        return {
            "prompt": intent,
            "response": cmd,
            "shell": "bash",
            "tier": "multistage_pipeline",
            "is_destructive": is_destructive,
        }

    def generate_devops_suite(self) -> Dict[str, Any]:
        templates = [
            (
                "show pods in namespace '{ns}' sorted by restart count",
                "kubectl get pods -n {ns} --sort-by='.status.containerStatuses[0].restartCount'",
                False,
            ),
            (
                "stream real-time logs from pod with label 'app={app}' in namespace '{ns}'",
                "kubectl logs -n {ns} -l app={app} --tail=100 -f --all-containers",
                False,
            ),
            (
                "force restart deployment '{app}' in namespace '{ns}'",
                "kubectl rollout restart deployment/{app} -n {ns}",
                True,
            ),
            (
                "rebuild and restart docker compose service '{app}' without cache",
                "docker compose build --no-cache {app} && docker compose up -d {app}",
                False,
            ),
            (
                "prune all unused docker images, volumes, and networks",
                "docker system prune -a --volumes -f",
                True,
            ),
            (
                "run terraform plan saving execution output to tfplan",
                "terraform plan -out=tfplan",
                False,
            ),
            (
                "apply saved terraform plan with auto approval",
                "terraform apply -auto-approve tfplan",
                True,
            ),
            (
                "view failed systemd services on this machine",
                "systemctl --failed --type=service",
                False,
            ),
            (
                "list pull requests targeting main opened by me using gh cli",
                "gh pr list --state open --base main --author @me",
                False,
            ),
            (
                "check status of ec2 instances with tag 'Environment={env}'",
                "aws ec2 describe-instances --filters 'Name=tag:Environment,Values={env}' --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PrivateIpAddress]' --output table",
                False,
            ),
        ]
        intent_tmpl, cmd_tmpl, is_destructive = random.choice(templates)
        ns = random.choice(["production", "staging", "ingress-nginx", "monitoring", "kube-system"])
        app = random.choice(["api-gateway", "auth-service", "worker", "postgres", "redis"])
        env = random.choice(["prod", "stage", "dev"])

        intent = intent_tmpl.format(ns=ns, app=app, env=env)
        cmd = cmd_tmpl.format(ns=ns, app=app, env=env)

        return {
            "prompt": intent,
            "response": cmd,
            "shell": "bash",
            "tier": "devops_suite",
            "is_destructive": is_destructive,
        }

    def generate_powershell_suite(self) -> Dict[str, Any]:
        templates = [
            (
                "get top 5 processes using most memory in powershell",
                "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 Name, Id, @{{Name='RAM (MB)';Expression={{[math]::Round($_.WorkingSet64 / 1MB, 2)}}}}",
                False,
            ),
            (
                "find and stop process listening on port {port} in powershell",
                "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force }}",
                True,
            ),
            (
                "test tcp connection to host '{host}' on port {port}",
                "Test-NetConnection -ComputerName '{host}' -Port {port} -InformationLevel Detailed",
                False,
            ),
            (
                "recursively find files matching '*{ext}' modified in last {days} days in powershell",
                "Get-ChildItem -Path . -Filter '*{ext}' -Recurse | Where-Object {{ $_.LastWriteTime -ge (Get-Date).AddDays(-{days}) }} | Select-Object FullName, Length, LastWriteTime",
                False,
            ),
            (
                "delete temp files older than {days} days in windows temp directory",
                "Get-ChildItem -Path $env:TEMP -Recurse -Force -ErrorAction SilentlyContinue | Where-Object {{ $_.LastWriteTime -lt (Get-Date).AddDays(-{days}) }} | Remove-Item -Recurse -Force",
                True,
            ),
            (
                "get all running windows services with start type automatic",
                "Get-Service | Where-Object {{ $_.Status -eq 'Running' -and $_.StartType -eq 'Automatic' }} | Select-Object Name, DisplayName",
                False,
            ),
        ]
        intent_tmpl, cmd_tmpl, is_destructive = random.choice(templates)
        port = random.choice([3000, 5432, 6379, 8080, 8000, 9090])
        host = random.choice(["db.internal", "redis.internal", "api.github.com", "gateway.aws"])
        ext = random.choice([".rs", ".ts", ".py", ".log", ".json"])
        days = random.choice([1, 7, 14, 30])

        intent = intent_tmpl.format(port=port, host=host, ext=ext, days=days)
        cmd = cmd_tmpl.format(port=port, host=host, ext=ext, days=days)

        return {
            "prompt": intent,
            "response": cmd,
            "shell": "powershell",
            "tier": "powershell_suite",
            "is_destructive": is_destructive,
        }

    def generate_atomic_reflex(self) -> Dict[str, Any]:
        templates = [
            ("list directory contents including hidden files", "ls -la", False),
            ("show current git status with short branch format", "git status -sb", False),
            ("search for '{symbol}' across all files anchored to root", "grep -rIn '{symbol}' --exclude-dir={{target,.git,node_modules}} .", False),
            ("find files named '{filename}' in current directory", "find . -name '{filename}'", False),
            ("show active listening tcp sockets with process pid", "ss -tlpn", False),
            ("inspect memory usage in megabytes", "free -m", False),
            ("kill process holding port {port}", "lsof -ti:{port} | xargs kill -9", True),
            ("discard all unstaged git modifications", "git checkout -- .", True),
            ("show latest commit hash and subject", "git log -1 --oneline", False),
            ("display disk free space in human readable format", "df -h", False),
        ]
        intent_tmpl, cmd_tmpl, is_destructive = random.choice(templates)
        symbol = random.choice(["ViperConfig", "MicroEngine", "handle_request", "Router"])
        filename = random.choice(["Cargo.toml", "package.json", "Dockerfile", ".env.example"])
        port = random.choice([3000, 4000, 8080, 5000])

        intent = intent_tmpl.format(symbol=symbol, filename=filename, port=port)
        cmd = cmd_tmpl.format(symbol=symbol, filename=filename, port=port)

        return {
            "prompt": intent,
            "response": cmd,
            "shell": "bash",
            "tier": "atomic_reflex",
            "is_destructive": is_destructive,
        }

    def generate_clutch_counter_example(self) -> Dict[str, Any]:
        templates = [
            ("delete the whole target directory completely", "rm -rf target/", True),
            ("wipe git working tree and reset hard to origin main", "git reset --hard origin/main", True),
            ("drop database users_production immediately", "dropdb users_production", True),
            ("stop docker daemon service right now", "systemctl stop docker.service", True),
            ("safely dry run clean untracked files without deleting", "git clean -nd", False),
            ("inspect what would be deleted in target folder", "find target/ -type f | wc -l", False),
            ("view processes that would be terminated", "pgrep -f node -l", False),
        ]
        intent, cmd, is_destructive = random.choice(templates)
        return {
            "prompt": intent,
            "response": cmd,
            "shell": "bash",
            "tier": "clutch_guard",
            "is_destructive": is_destructive,
        }

    def generate_sample(self) -> Dict[str, Any]:
        roll = random.random()
        if roll < 0.30:
            return self.generate_multistage_pipeline()
        elif roll < 0.55:
            return self.generate_devops_suite()
        elif roll < 0.75:
            return self.generate_powershell_suite()
        elif roll < 0.90:
            return self.generate_atomic_reflex()
        else:
            return self.generate_clutch_counter_example()

    def generate_curriculum(self, num_samples: int, output_path: str):
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for _ in range(num_samples):
                sample = self.generate_sample()
                f.write(json.dumps(sample) + "\n")
        print(f"Generated {num_samples:,} curriculum samples at: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--out", type=str, default="viper2_curriculum_sample.jsonl")
    args = parser.parse_args()

    gen = Viper2DatasetGenerator()
    gen.generate_curriculum(args.samples, args.out)
