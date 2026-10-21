"""Measure Dev token inflation on the exact 164 evaluation prompts."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import tokenizers
from tokenizers import Tokenizer
from run import chat_prompt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    standard,dev=[Tokenizer.from_file(str(args.models/name)) for name in ['tokenizer.json','nio-ray-dev-tokenizer.json']]
    rows=[]
    for line in (args.output/'HumanEvalPlus-v0.1.10.jsonl').read_text().splitlines():
        problem=json.loads(line);text=chat_prompt(problem['prompt'])
        a,b=len(standard.encode(text,add_special_tokens=False).ids),len(dev.encode(text,add_special_tokens=False).ids)
        rows.append({'task_id':problem['task_id'],'standard_tokens':a,'dev_tokens':b,'ratio':b/a})
    assert len(rows)==164
    result={'scope':'164 HumanEval prompts using the fixed Qwen ChatML evaluation template; not a general coding corpus',
            'tokenizers_version':tokenizers.__version__,
            'tokenizer_sha256':{name:hashlib.sha256((args.models/name).read_bytes()).hexdigest() for name in ['tokenizer.json','nio-ray-dev-tokenizer.json']},
            'standard_tokens_total':sum(r['standard_tokens'] for r in rows),
            'dev_tokens_total':sum(r['dev_tokens'] for r in rows),'per_task':rows}
    result['aggregate_token_ratio']=result['dev_tokens_total']/result['standard_tokens_total']
    result['median_task_ratio']=statistics.median(r['ratio'] for r in rows)
    (args.output/'tokenization.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='per_task'})


if __name__=='__main__':main()
