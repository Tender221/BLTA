"""Recompute BLTA transfer tables and audit recorded Agent task outcomes on CPU."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
os.environ.setdefault('OMP_NUM_THREADS','4')
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from blta import BLTA

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results')
    parser.add_argument('--refit',action='store_true',help='refit all 90 source heads and verify saved parameters')
    args=parser.parse_args(); start=time.perf_counter()
    manifest=json.loads((ROOT/'input_manifest.json').read_text())
    for filename,digest in manifest['files'].items():
        if hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()!=digest:
            raise ValueError('Input checksum mismatch: '+filename)
    records={kind:[json.loads(s) for s in (ROOT/f'data/{kind}.jsonl').read_text(encoding='utf-8').splitlines()] for kind in ['clean','injected']}
    groups={kind:np.array([r['group'] for r in rows]) for kind,rows in records.items()}
    folds=json.loads((ROOT/'data/folds.json').read_text())
    cross=defaultdict(lambda:np.zeros(4,dtype=np.int64))
    telemetry=defaultdict(lambda:np.zeros(4,dtype=np.int64))
    mismatches=[]; max_refit_difference=0.; exports={}
    sizes=defaultdict(list)
    for detector in ['piguard','wolf','protectai-v2']:
        with np.load(ROOT/f'data/{detector}_features.npz',allow_pickle=False) as z:
            vectors={k:z[k].astype(np.float64) for k in ['clean','injected']}
        for fold in (f for f in folds if f['detector']==detector):
            held=fold['tool']; source=np.array(fold['source_normal_indices']); attack=np.array(fold['source_attack_indices']);cal=np.array(fold['calibration_indices']);target=np.array(fold['target_normal_indices']);normal_test=np.array(fold['test_normal_indices']);attack_test=np.array(fold['test_attack_indices'])
            if (np.any(groups['clean'][source]==held) or np.any(groups['injected'][attack]==held)
                    or np.any(groups['clean'][cal]==held) or np.any(groups['clean'][target]!=held)
                    or set(target)&(set(source)|set(cal)|set(normal_test))
                    or set(source)&(set(cal)|set(normal_test)) or set(cal)&set(normal_test)
                    or set(attack)&set(attack_test)):
                raise ValueError('Source/target partition violation')
            reference=BLTA.from_dict(fold['model'])
            if args.refit:
                head=BLTA.fit(vectors['clean'][source],vectors['injected'][attack],vectors['clean'][cal])
                error=max(float(np.max(np.abs(head.weight-reference.weight))),abs(head.bias-reference.bias),abs(head.threshold-reference.threshold))
                max_refit_difference=max(max_refit_difference,error)
                if error>1e-10:raise ValueError('Source head refit mismatch')
            else:head=reference
            test={'clean':vectors['clean'][normal_test],'injected':vectors['injected'][attack_test]}
            raw={k:head.scores(v) for k,v in test.items()}
            offsets={'raw':0.,'global_recenter':head.adapt(held,vectors['clean'][target]),
                     'nearest_source':float(np.asarray(fold['nearest_offset'])/head.scale@head.weight)}
            for method,offset in offsets.items():
                count=np.array([np.sum(raw['clean']+offset>head.threshold),len(normal_test),np.sum(raw['injected']+offset>head.threshold),len(attack_test)],dtype=np.int64)
                expected=fold['expected'][method]
                if count.tolist()!=[expected[k] for k in ['fp','normal_n','tp','attack_n']]:mismatches.append([detector,fold['seed'],held,method])
                cross[detector,method]+=count
            exported=head.to_dict()
            exports[f'{detector}|{fold["seed"]}|{held}']=exported
            digest=hashlib.sha256(f'{fold["seed"]}|{held}|telemetry-v1'.encode()).digest()
            ordered=np.random.default_rng(int.from_bytes(digest[:8],'little')).permutation(target)
            for budget,expected in fold['telemetry_expected'].items():
                indices=target if budget=='all' else ordered[:min(int(budget),len(target))]
                if indices.tolist()!=fold['telemetry_selections'][budget]:raise ValueError('Telemetry selection mismatch')
                delta=head.adapt(held,vectors['clean'][np.sort(indices)])
                count=np.array([np.sum(raw['clean']+delta>head.threshold),len(normal_test),np.sum(raw['injected']+delta>head.threshold),len(attack_test)],dtype=np.int64)
                if count.tolist()!=[expected[k] for k in ['fp','normal_n','tp','attack_n']]:mismatches.append([detector,fold['seed'],held,'budget'+budget])
                telemetry[detector,budget]+=count;sizes[detector,budget].append(len(indices))
    agent=defaultdict(lambda:dict(n_clean=0,n_attack=0,clean_successes=0,goal_successes=0))
    agent_rows=0
    for line in (ROOT/'data/agent_outcomes.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line);t=r['task']; key=r['victim'],r['detector'],r['method'];a=agent[key]
        if r['variant']=='clean':a['n_clean']+=1;a['clean_successes']+=int(t['utility_success'])
        elif r['variant']=='attack':a['n_attack']+=1;a['goal_successes']+=int(t['goal_success'])
        else:raise ValueError('Unknown main-task variant')
        agent_rows+=1
    for key,a in agent.items():
        if a['n_clean']!=96 or a['n_attack']!=96:raise ValueError('Agent denominator mismatch')
        table=list(csv.DictReader((ROOT/f'data/paper_agent_{key[0]}.csv').read_text(encoding='utf-8').splitlines()))
        expected=next(r for r in table if r['detector']==key[1] and r['method']==key[2])
        if a['clean_successes']!=int(expected['clean_utility']) or a['goal_successes']!=int(expected['goal_asr']):mismatches.append(list(key))
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    def write(name,rows):
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    def pooled(d,k,v):
        return dict(detector=d,method=k,pooled_fp=int(v[0]),pooled_normal_n=int(v[1]),pooled_tp=int(v[2]),pooled_attack_n=int(v[3]),pooled_fpr=float(v[0]/v[1]),pooled_tpr=float(v[2]/v[3]))
    write('cross_tool.csv',[pooled(d,k,v) for (d,k),v in cross.items()])
    write('telemetry.csv',[pooled(d,k,v)|dict(actual_n_min=min(sizes[d,k]),actual_n_max=max(sizes[d,k])) for (d,k),v in telemetry.items()])
    write('agent_main.csv',[dict(victim=v,detector=d,method=m,**a,clean_rate=a['clean_successes']/a['n_clean'],asr=a['goal_successes']/a['n_attack']) for (v,d,m),a in agent.items()])
    (out/'deployable_heads.json').write_text(json.dumps(exports,separators=(',',':')),encoding='utf-8')
    receipt=dict(held_tool_folds=len(folds),source_or_target_partition_violations=0,archived_count_mismatches=len(mismatches),mismatches=mismatches,agent_outcome_rows=agent_rows,source_heads_refitted=args.refit,maximum_refit_parameter_difference=max_refit_difference,new_encoder_inference=False,new_victim_generation=False,seconds=time.perf_counter()-start)
    (out/'verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))
    if mismatches:raise SystemExit('Reproduced counts differ from original records')


if __name__=='__main__':main()
