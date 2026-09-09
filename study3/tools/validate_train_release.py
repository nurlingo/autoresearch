#!/usr/bin/env python3
"""Validate the public training contract without accessing gold."""
import argparse,hashlib,json,math,re
from pathlib import Path

def lines(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('release',type=Path);a=ap.parse_args();b=a.release
 m=json.loads((b/'manifest.json').read_text());refs=json.loads((b/'quran-reference.json').read_text());units=lines(b/'train.jsonl');records=lines(b/'train-recordings.jsonl');sample=lines(b/'review-sample.jsonl')
 assert len(units)==m['train_units'] and len(records)==m['train_recordings']
 allowed={'review_id','chunk_idx','n_chunks','ayah_id','transcript','transcript_tokens','reference_text','reference_tokens'}
 keys=set()
 for u in units:
  assert set(u)==allowed,'unexpected field: potential annotation/identity leakage'
  assert re.fullmatch(r'train-\d{3}',u['review_id'])
  key=(u['review_id'],u['chunk_idx']);assert key not in keys;keys.add(key)
  assert u['transcript_tokens']==u['transcript'].split() and u['reference_tokens']==u['reference_text'].split()
  if u['chunk_idx']==-1:assert u['ayah_id'] is None and u['reference_text']=='' and u['transcript_tokens']
  else:assert u['reference_text']==refs[u['ayah_id']] and 0<=u['chunk_idx']<u['n_chunks']
 assert len({r['review_id'] for r in records})==len(records)
 assert [u for r in records for u in r['units']]==units
 for r in records:
  assert set(r)=={'review_id','transcript','units'}
  assert r['transcript'].split()==[t for u in r['units'] for t in u['transcript_tokens']]
  assert all(u['review_id']==r['review_id'] for u in r['units'])
  ayahs=[u for u in r['units'] if u['chunk_idx']>=0]
  assert [u['chunk_idx'] for u in ayahs]==list(range(len(ayahs)))
  assert all(u['n_chunks']==len(ayahs) for u in r['units'])
 lookup={(u['review_id'],u['chunk_idx']):u for u in units}
 assert all(lookup[(u['review_id'],u['chunk_idx'])]==u for u in sample)
 ids={u['review_id'] for u in sample};assert len(ids)==m['review_sample_recordings'] and len(sample)==m['review_sample_units']
 assert sample==[u for u in units if u['review_id'] in ids],'sample must contain complete recordings'
 assert len(ids)>=math.ceil(.1*(len(records)+m['gold_recordings']))
 assert len(sample)>=math.ceil(.1*(len(units)+m['gold_units']))
 if (b/'SHA256SUMS').exists():
  for line in (b/'SHA256SUMS').read_text().splitlines():
   digest,name=line.split('  ',1);assert hashlib.sha256((b/name).read_bytes()).hexdigest()==digest,name
 print(f'PASS: {len(records)} recordings, {len(units)} units; exact references, original token reconstruction, answer-free schema, complete train-only sample and hashes.')
if __name__=='__main__':main()
