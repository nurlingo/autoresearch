#!/usr/bin/env python3
"""Owner-side independent witness audit; outputs only aggregate findings unless --report is used.
--gold-dir and --report are private. This tool is not part of an entrant workspace.
"""
import argparse,hashlib,json,unicodedata
from collections import Counter
from pathlib import Path

def norm(text):
    return ' '.join(''.join(c for c in text if not unicodedata.category(c).startswith(('M','P')) and c!='ـ').translate(str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا'})).split())
def core(text):
    text=norm(text)
    for formula in ('اعوذ بالله من الشيطان الرجيم','بسم الله الرحمن الرحيم'):
        if text.startswith(formula):text=text[len(formula):].strip()
    return text

def signature(record):return [(c['ayah_id'],norm(c['transcript'])) for c in record['chunks']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--attribution',type=Path,required=True);ap.add_argument('--gold-dir',type=Path,required=True);ap.add_argument('--gold-bundle',type=Path,required=True);ap.add_argument('--release',type=Path,required=True);ap.add_argument('--report',type=Path);a=ap.parse_args()
    if a.report and a.report.resolve().is_relative_to(a.release.resolve()):ap.error('private report must be outside training release')
    attr=json.loads(a.attribution.read_text());source=json.loads(a.prepared.read_text());byid={r['recording_id']:r for r in source};sel={r['recording_id'] for r in attr['selected']};excluded={r['recording_id'] for r in attr['excluded']}
    gm=json.loads((a.gold_dir/'selected100_manifest.json').read_text())['records'];gold=[json.loads((a.gold_dir/(r['review_id']+'.json')).read_text()) for r in gm]
    assert sha(a.prepared)==attr['prepared_sha256'] and sha(a.gold_bundle)==attr['gold_sha256'],'saved preparation/gold changed'
    assert len(byid)==len(source) and len(sel)==len(attr['selected']) and len(excluded)==len(attr['excluded'])
    assert not sel&excluded and sel|excluded==set(byid)
    assert not sel&{r['recording_id'] for r in gm}
    records=[json.loads(l) for l in (a.release/'train-recordings.jsonl').read_text().splitlines()];pub={r['review_id']:r for r in records}
    assert set(pub)=={r['review_id'] for r in attr['selected']}
    for r in attr['selected']:
        assert pub[r['review_id']]['transcript']==byid[r['recording_id']]['transcript']
        assert [(u['ayah_id'],u['transcript'],u['reference_text']) for u in pub[r['review_id']]['units'] if u['chunk_idx']>=0]==[(c['ayah_id'],c['transcript'],c['reference_text']) for c in byid[r['recording_id']]['chunks']]
    # Use canonical full ASR for recitation identity, not concatenated ayah chunks:
    # basmala can be reference ayah 1:1 in one split and opening text in another.
    goldcores={core(r['asr_transcript']) for r in gold}
    eventchunks={(c['ayah_id'],norm(c['transcript'])) for r in gold for c in r['chunks'] if c.get('events') and norm(c['transcript'])}
    cleanchunks={(c['ayah_id'],norm(c['transcript'])) for r in gold for c in r['chunks'] if not c.get('events') and norm(c['transcript'])}
    counts=Counter();dups=Counter();witnesses=[]
    for e in attr['excluded']:
        r=byid[e['recording_id']];reason=e['reasons'][0];w={'recording_id':r['recording_id'],'reason':reason}
        if reason=='gold_recitation_core':assert core(r['transcript']) in goldcores
        elif reason=='gold_equivalent_event_chunk':assert any(c in eventchunks for c in signature(r))
        elif reason=='unresolved_split_or_source_mismatch':assert r['preparation_issues'];w['issues']=r['preparation_issues']
        elif reason=='outside_ayah_task':assert r['non_quran_review']
        elif reason=='duplicate_or_redundant_training_case':
            sig=signature(r);matches=[i for i in sorted(sel) if any(signature(byid[i])[j:j+len(sig)]==sig for j in range(len(signature(byid[i]))-len(sig)+1))]
            assert matches,'no retained witness for redundant recording'
            exact=[i for i in matches if signature(byid[i])==sig];kind='exact_duplicate' if exact else 'shorter_contained_passage';dups[kind]+=1;w.update(kind=kind,retained_witness=(exact or matches)[0])
        else:raise AssertionError('unknown exclusion reason: '+reason)
        counts[reason]+=1;witnesses.append(w)
    for i in sel:
        r=byid[i];assert core(r['transcript']) not in goldcores;assert not any(c in eventchunks for c in signature(r));assert not r['preparation_issues'] and r['split_qc_complete']
    summary={'status':'passed','candidate_recordings':len(source),'retained_recordings':len(sel),'excluded_recordings':len(excluded),'exclusion_counts':dict(counts),'redundancy_breakdown':dict(dups),'permitted_shared_clean_units':sum(c in cleanchunks for i in sel for c in signature(byid[i])),'checks':['saved source/gold hashes','unique source identities and complete disjoint partition','selected IDs absent from gold','released transcript and split attribution','independent witness for every exclusion','no retained complete gold copy or event-bearing chunk copy','retained split QC complete'],'caveat':'Checks validate the declared partition, not all semantic overlap or human correctness of new split assignments.'}
    if a.report:
        a.report.write_text(json.dumps({'summary':summary,'witnesses_private':witnesses,'input_hashes':{'prepared':sha(a.prepared),'attribution':sha(a.attribution),'gold_bundle':sha(a.gold_bundle),'train_recordings':sha(a.release/'train-recordings.jsonl')}},ensure_ascii=False,indent=2)+'\n');a.report.chmod(0o600)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
