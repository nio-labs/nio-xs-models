"""Generate all 164 HumanEval+ solutions using an official llama.cpp CPU server.

Run after native timed workloads so no benchmark processes compete for CPU.
The server is launched per model, bound to localhost, and stopped in finally.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.request
from run import chat_prompt, STOP, QWEN_COMMIT, DATA_URL


def request_json(url, data=None, timeout=300):
    encoded = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(url, encoded, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--server', required=True, type=Path)
    parser.add_argument('--threads', type=int, default=6)
    args = parser.parse_args()
    problems = [json.loads(line) for line in (args.output / 'HumanEvalPlus-v0.1.10.jsonl').read_text().splitlines()]
    assert len(problems) == 164
    metadata = {
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'backend': subprocess.check_output([str(args.server), '--version'], text=True, stderr=subprocess.STDOUT).strip(),
        'server_sha256': hashlib.sha256(args.server.read_bytes()).hexdigest(),
        'source': 'https://github.com/ggml-org/llama.cpp/releases/tag/b11778',
        'dataset_url': DATA_URL, 'dataset_sha256': hashlib.sha256((args.output / 'HumanEvalPlus-v0.1.10.jsonl').read_bytes()).hexdigest(),
        'prompt_source_commit': QWEN_COMMIT, 'threads':args.threads,
        'batch_size':1, 'temperature':0, 'top_k':1, 'top_p':1, 'min_p':0,
        'repeat_penalty':1, 'seed':0, 'max_new_tokens':2048, 'context_tokens':4096,
        'stop':STOP, 'cache_prompt':False, 'gpu_layers':0,
        'evaluation':'EvalPlus 0.2.1 with NumPy 1.26.4; base and expanded tests',
        'notes':'Quality backend differs from native Candle performance harness; no Qwen inference.',
    }
    (args.output / 'quality-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    for variant, filename in [('standard','nio-ray.Q4_K_M.gguf'), ('dev','nio-ray-dev.Q4_K_M.gguf')]:
        records_path = args.output / f'{variant}-quality.ndjson'
        if records_path.exists():
            raise FileExistsError(records_path)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        url=f'http://127.0.0.1:{port}'
        command=[str(args.server),'-m',str(args.models/filename),'-t',str(args.threads),'-tb',str(args.threads),
                 '-ngl','0','-c','4096','--parallel','1','--host','127.0.0.1','--port',str(port),
                 '--no-warmup','--no-webui']
        with (args.output / f'{variant}-llama.stderr.log').open('w') as logs:
            process=subprocess.Popen(command,stdout=logs,stderr=logs)
            try:
                deadline=time.monotonic()+120
                while time.monotonic()<deadline:
                    if process.poll() is not None:raise RuntimeError(f'Server failed: {(args.output / f"{variant}-llama.stderr.log").read_text()[-2500:]}')
                    try:
                        if request_json(url+'/health',timeout=2).get('status')=='ok':break
                    except Exception:time.sleep(.5)
                else:raise TimeoutError('server startup timed out')
                with records_path.open('w') as output, (args.output/f'{variant}-solutions.jsonl').open('w') as solutions:
                    for index,problem in enumerate(problems):
                        start=time.monotonic()
                        result=request_json(url+'/completion',{
                            'prompt':chat_prompt(problem['prompt']), 'n_predict':2048,
                            'temperature':0, 'top_k':1, 'top_p':1, 'min_p':0, 'repeat_penalty':1,
                            'seed':0, 'stop':STOP, 'cache_prompt':False, 'stream':False,
                        })
                        record={'task_id':problem['task_id'],'wall_seconds':time.monotonic()-start,'response':result}
                        output.write(json.dumps(record)+'\n');output.flush()
                        solutions.write(json.dumps({'task_id':problem['task_id'],'solution':result['content'].replace('\t','    ')})+'\n');solutions.flush()
                        print(variant,f'{index+1}/164',problem['task_id'],result.get('tokens_predicted'),
                              'tokens',f"{record['wall_seconds']:.1f}s",flush=True)
            finally:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()


if __name__=='__main__':
    main()
