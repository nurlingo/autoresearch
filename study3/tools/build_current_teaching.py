#!/usr/bin/env python3
"""Adapt constructed v1 examples to the current reference and granular rubric.

Never reads recording data. Historical approved examples remain unchanged.
"""
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import eval21


def build():
    old=json.loads((HERE/'calibration/teaching-draft.json').read_text())
    refs=json.loads((HERE/'quran-reference.json').read_text())
    result=[]
    for source in old['examples']:
        cid=source['example_id'];units=[];events=[]
        def add(label, idx, spans, refspan, note=''):
            u=next(u for u in units if u['chunk_idx']==idx);eid=f'{cid}:e{len(events)+1:03}'
            events.append({'event_id':eid,'label':label,
                'hyp_locations':[{'chunk_idx':idx,'span':s,'words':' '.join(u['transcript_tokens'][slice(*s)])} for s in spans],
                'reference':{'ayah_id':u['ayah_id'],'span':refspan,'words':' '.join(u['reference_tokens'][slice(*refspan)])},'note':note})
            u['event_ids'].append(eid)
        for i,c in enumerate(source['chunks']):
            oldtokens=c['reference_text'].split();newtokens=refs[c['ayah_id']].split()
            assert len(oldtokens)==len(newtokens)
            # Restore faithful spelling in constructed matching words, keeping intentional errors.
            mapping=dict(zip(oldtokens,newtokens));hyp=[mapping.get(w,w) for w in c['transcript'].split()]
            if cid=='t15':hyp[0]='أين'
            if cid=='t07':hyp[-1]='أذنين'
            if cid=='t10':hyp='والشمس إذا تلاها والقمر إذا تلاها'.split()
            units.append({'chunk_idx':i,'ayah_id':c['ayah_id'],'transcript':' '.join(hyp),'transcript_tokens':hyp,
                'reference_text':' '.join(newtokens),'reference_tokens':newtokens,'event_ids':[]})
            if cid in {'t09','t10','t11','t12'}:continue
            for e in c.get('events',[]):add(e['label'],i,[e['hyp_span']],e['ref_span'],e.get('note',''))
        if cid=='t09':add('repetition_benign',0,[[0,2],[2,4]],[0,2])
        if cid=='t10':
            add('substitution_corrected',0,[[0,1],[3,4]],[0,1],'Repeated matching clause context establishes the two attempts.')
            add('repetition_benign',0,[[1,3],[4,6]],[1,3])
        if cid=='t11':
            add('substitution_mistake',0,[[0,1],[3,4]],[0,1],'First correct, then wrong; final attempt remains wrong.')
            add('repetition_benign',0,[[1,3],[4,6]],[1,3])
        if cid=='t12':
            add('omission_corrected',0,[[4,4],[9,10]],[4,5])
            add('repetition_benign',0,[[0,4],[5,9]],[0,4])
            add('repetition_benign',0,[[4,5],[10,11]],[5,6])
        for formula in source.get('preamble',[]):
            assert not any(u['chunk_idx']==-1 for u in units)
            units.insert(0,{'chunk_idx':-1,'ayah_id':None,'transcript':formula['text'],
                'transcript_tokens':formula['text'].split(),'reference_text':'','reference_tokens':[],'event_ids':[]})
            add(formula['label'],-1,[[0,len(formula['text'].split())]],[0,0])
        result.append({'case_id':cid,'provenance':'constructed; adapted from approved historical teaching example; current adaptation assistant-validated',
            'summary': 'Exact reference match.' if cid=='t01' else source['name'], 'units':units,'events':events})
    eval21.validate_corpus(result)
    assert eval21.score(result,eval21.gold_as_predictions(result))['micro_f1']==1
    path=HERE/'calibration/teaching-current.json'
    path.write_text(json.dumps({'status':'assistant-validated adaptation of approved constructed examples',
        'reference':'../quran-reference.json','examples':result},ensure_ascii=False,indent=2)+'\n')
    lines=['# Current constructed teaching examples','These are synthetic examples, never recordings or gold answers. The original twenty examples were approved; this adaptation updates reference spelling and granular grouping under the current rubric. The adaptation is assistant-validated. Do not count scores on exposed teaching answers as held-out evidence.','',
        't10 now repeats the clause context so the corrected substitution is anchored. t11 and t12 separate the changed words from correctly repeated context. t01 now matches the faithful reference exactly.','']
    for r in result:
        lines += [f"## {r['case_id']} — {r['summary']}"]
        for u in r['units']:lines += [f"Ayah {u['ayah_id']} · chunk {u['chunk_idx']}",f"Transcript: {u['transcript'] or '∅'}",f"Reference: {u['reference_text'] or '∅'}",'']
        lines += ['```json',json.dumps(r['events'],ensure_ascii=False,indent=2),'```','']
    (HERE/'calibration/teaching-current.md').write_text('\n'.join(lines)+'\n')
    print('Built 20 constructed examples; span/word validation and oracle pass.')


if __name__=='__main__':build()
