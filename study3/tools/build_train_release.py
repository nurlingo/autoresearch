#!/usr/bin/env python3
"""Owner-only preparation from private, split-reviewed inputs. Never run in an entrant runtime.
Outputs allowlisted training inputs and aggregate counts; attribution/exclusions go to --audit.
The gold file is read only for overlap checks, never copied into the release.
"""
import argparse, hashlib, json, math, unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

def norm(s):
    s=''.join(c for c in s if not unicodedata.category(c).startswith(('M','P')) and c!='ـ')
    return ' '.join(s.translate(str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا'})).split())

def edits(c):
    ref=norm(c['reference_text']).split(); hyp=norm(c['transcript']).split()
    return {(op,i,j,tuple(hyp[a:b])) for op,i,j,a,b in SequenceMatcher(None,ref,hyp,autojunk=False).get_opcodes() if op!='equal'}

def signature(r):
    return tuple((c['ayah_id'],norm(c['transcript'])) for c in r['chunks'])

def write_json(path,x): path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def write_lines(path,rows): path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--gold',type=Path,required=True);ap.add_argument('--quran',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--overlap-policy',choices=['event_chunks','strict'],default='event_chunks');a=ap.parse_args()
    if a.audit.resolve().is_relative_to(a.out.resolve()):ap.error('private audit must be outside release directory')
    source=json.loads(a.prepared.read_text());gold=[json.loads(l) for l in a.gold.read_text().splitlines() if l.strip()]
    q=json.loads(a.quran.read_text());refs={r['id']:r['titles']['clean'] for v in q.values() for r in v if r.get('type')=='ayah' and len(r['id'])==6 and int(r['id'][:3])<=114}
    lookup=defaultdict(list)
    gold_cores={norm(' '.join(c['transcript'] for c in r['chunks'])) for r in gold}
    for r in gold:
        for c in r['chunks']:
            if norm(c['transcript']):lookup[c['ayah_id']].append(c)
    reasons={};eligible=[]
    for r in source:
        why=[]
        if r.get('non_quran_review'):why.append('outside_ayah_task')
        if r.get('preparation_issues'):why.append('unresolved_split_or_source_mismatch')
        if r.get('selection_status')=='exclude_gold_equivalent' or norm(' '.join(c['transcript'] for c in r['chunks'])) in gold_cores:why.append('gold_recitation_core')
        for c in r['chunks']:
            for z in lookup[c['ayah_id']]:
                if norm(c['transcript']) and norm(c['transcript'])==norm(z['transcript']) and (a.overlap_policy=='strict' or z.get('events')):why.append('gold_equivalent_event_chunk' if a.overlap_policy=='event_chunks' else 'gold_equivalent_ayah_chunk')
                if a.overlap_policy=='strict' and 'reference_text' in c and edits(c)&edits(z):why.append('shared_reference_aligned_difference')
        if not r.get('split_qc_complete'):why.append('split_qc_incomplete')
        why=list(dict.fromkeys(why))
        if why:reasons[r['recording_id']]=why
        else:eligible.append(r)
    # Prefer the longer case; a shorter case adds nothing if every assigned text unit
    # occurs as a contiguous sequence in one retained recording. Ignore formulas.
    eligible.sort(key=lambda r:(-len(r['chunks']),-len(r['transcript'].split()),hashlib.sha256(r['transcript'].encode()).hexdigest()))
    selected=[]
    for r in eligible:
        sig=signature(r)
        if any(any(signature(z)[i:i+len(sig)]==sig for i in range(len(z['chunks'])-len(sig)+1)) for z in selected):reasons[r['recording_id']]=['duplicate_or_redundant_training_case']
        else:selected.append(r)
    selected.sort(key=lambda r:hashlib.sha256(r['transcript'].encode()).hexdigest())
    out=[];records=[];membership=[]
    for i,r in enumerate(selected,1):
        rid=f'train-{i:03}';units=[];pre=r.get('preamble_text','');chunks=r['chunks']
        if pre: units.append({'review_id':rid,'chunk_idx':-1,'n_chunks':len(chunks),'ayah_id':None,'transcript':pre,'transcript_tokens':pre.split(),'reference_text':'','reference_tokens':[]})
        for j,c in enumerate(chunks):
            assert c['ayah_id'] in refs and c['reference_text']==refs[c['ayah_id']]
            units.append({'review_id':rid,'chunk_idx':j,'n_chunks':len(chunks),'ayah_id':c['ayah_id'],'transcript':c['transcript'],'transcript_tokens':c['transcript'].split(),'reference_text':refs[c['ayah_id']],'reference_tokens':refs[c['ayah_id']].split()})
        assert [t for u in units for t in u['transcript_tokens']]==r['transcript'].split()
        out.extend(units);records.append({'review_id':rid,'transcript':r['transcript'],'units':units})
        membership.append({'review_id':rid,'recording_id':r['recording_id'],'candidate_id':r['candidate_id'],'split_source':r['split_source']})
    # A train-only sample large enough for 10% of train+gold, by recordings AND units.
    gold_units=sum(len(r['chunks'])+bool((r.get('preamble') or {}).get('text')) for r in gold)
    min_records=math.ceil(.1*(len(records)+len(gold)));min_units=math.ceil(.1*(len(out)+gold_units))
    sample=[];covered=set();left=records.copy()
    while len(sample)<min_records or sum(len(r['units']) for r in sample)<min_units:
        if not left:raise ValueError('not enough training material for sample')
        chosen=max(left,key=lambda r:(len({u['ayah_id'] for u in r['units'] if u['ayah_id']}-covered),len(r['units']),r['review_id']))
        sample.append(chosen);left.remove(chosen);covered|={u['ayah_id'] for u in chosen['units'] if u['ayah_id']}
    sample.sort(key=lambda r:r['review_id'])
    counts=Counter(why[0] for why in reasons.values())
    summary={'overlap_policy':a.overlap_policy,'version':'1.0','date':'2026-09-09','candidate_recordings':len(source),'train_recordings':len(records),'train_units':len(out),'train_ayah_units':sum(u['ayah_id'] is not None for u in out),'train_preamble_units':sum(u['ayah_id'] is None for u in out),'train_distinct_ayahs':len({u['ayah_id'] for u in out if u['ayah_id']}),'train_surahs':len({u['ayah_id'][:3] for u in out if u['ayah_id']}),'old_recordings':sum(r['split_source']!='production_splitter_assistant_checked' for r in selected),'new_recordings':sum(r['split_source']=='production_splitter_assistant_checked' for r in selected),'excluded_recordings':len(reasons),'exclusion_first_reason_counts':dict(counts),'gold_recordings':len(gold),'gold_units':gold_units,'review_sample_recordings':len(sample),'review_sample_units':sum(len(r['units']) for r in sample),'sample_from':'train only; subset, not additional data','sample_min_recordings_using_train_plus_gold':min_records,'sample_min_units_using_train_plus_gold':min_units,'event_annotations':'not supplied','reference_source':'quran.json titles.clean','reference_source_sha256':hashlib.sha256(a.quran.read_bytes()).hexdigest(),'split_provenance':'Previously human-reviewed old splits; new production splits checked and repaired by the preparation assistant. Unresolved cases excluded. No claim of new human approval.','gold_exposure':'Gold inputs previously public; new annotations and membership remain private. No claim of unseen-input evaluation.'}
    a.out.mkdir(parents=True,exist_ok=True)
    write_lines(a.out/'train.jsonl',out);write_lines(a.out/'train-recordings.jsonl',records);write_lines(a.out/'review-sample.jsonl',[u for r in sample for u in r['units']]);write_json(a.out/'manifest.json',summary);write_json(a.out/'quran-reference.json',refs)
    write_json(a.audit,{'prepared_sha256':hashlib.sha256(a.prepared.read_bytes()).hexdigest(),'gold_sha256':hashlib.sha256(a.gold.read_bytes()).hexdigest(),'selected':membership,'excluded':[{'recording_id':i,'reasons':why} for i,why in reasons.items()]});a.audit.chmod(0o600)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
