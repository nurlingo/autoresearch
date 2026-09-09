#!/usr/bin/env python3
"""Render the constructed teaching cases as a review page. No gold access."""
import argparse,html,json
from pathlib import Path

CSS=("body{font:16px/1.5 system-ui;max-width:1000px;margin:30px auto;padding:0 20px;color:#172033}"
 "article{border:1px solid #d5dbe5;border-radius:10px;padding:20px;margin:24px 0}"
 ".arabic{font:25px/1.8 serif;direction:rtl;background:#f5f7fb;padding:12px;white-space:pre-wrap}"
 ".label{font-family:monospace;color:#174b85}code{white-space:pre-wrap}summary{cursor:pointer}"
 "h2{margin-top:0}.note{color:#555}.ok{color:#186a3b}")

def span(toks,s):
 if s is None:return '—'
 a,b=s
 return html.escape(' '.join(toks[a:b])) if b>a else f'∅ empty at {a}'

def render(ex):
 o=[f'<article id="{ex["example_id"]}"><h2>{html.escape(ex["example_id"])} — {html.escape(ex["name"])}</h2>']
 st=ex['review_status']
 o.append(f'<p class="note{" ok" if st=="approved" else ""}">{"Approved by the owner." if st=="approved" else "Draft; awaiting owner approval."}</p>')
 for p in ex.get('preamble') or []:
  o.append(f'<b>Preamble — <span class="label">{html.escape(p["label"])}</span></b>'
           f'<div class="arabic" lang="ar">{html.escape(p["text"])}</div>')
 for c in ex['chunks']:
  aid=c.get('ayah_id')
  o.append(f'<h3>Ayah {int(aid[:3])}:{int(aid[3:])}</h3>' if aid else '<h3>Chunk</h3>')
  o.append('<b>Transcript</b><div class="arabic" lang="ar">'
           f'{html.escape(c["transcript"]) or "<i>empty — adjudicated whole-ayah omission</i>"}</div>')
  o.append(f'<b>Reference — actual ayah</b><div class="arabic" lang="ar">{html.escape(c["reference_text"])}</div>')
  evs=c.get('events') or []
  if not evs:o.append('<p class="label">clean — no events</p>')
  for e in evs:
   o.append(f'<p class="label">{html.escape(e["label"])}<br>'
            f'&nbsp;&nbsp;transcript {e["hyp_span"]} = «{span(c["transcript_tokens"],e["hyp_span"])}»<br>'
            f'&nbsp;&nbsp;reference {e["ref_span"]} = «{span(c["reference_tokens"],e["ref_span"])}»</p>')
 if (ex.get('annotation_note') or '').strip():
  o.append(f'<p class="note"><b>Note.</b> {html.escape(ex["annotation_note"])}</p>')
 o.append('<details><summary>Full data point</summary><pre><code>'
          f'{html.escape(json.dumps(ex,ensure_ascii=False,indent=2))}</code></pre></details></article>')
 return ''.join(o)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('draft',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
 d=json.loads(a.draft.read_text());ex=d['examples']
 pending=[e['example_id'] for e in ex if e['review_status']!='approved']
 head=(f'<!doctype html><html lang="en"><meta charset="utf-8">'
  f'<meta name="viewport" content="width=device-width, initial-scale=1">'
  f'<title>Teaching examples — owner review</title><style>{CSS}</style>'
  f'<h1>{len(ex)} constructed teaching examples</h1>'
  f'<p>These are deliberate transcript variants, not recordings. “Reference” always means the actual '
  f'ayah text from quran.json titles.clean. Transcripts retain their spelling. Event spans use '
  f'zero-based, half-open whitespace indices. No gold cases are shown.</p>'
  f'<p>Taxonomy {html.escape(d["taxonomy_version"])}. '
  +(f'Awaiting approval: {", ".join(pending)}.' if pending else 'All examples approved.')
  +' The JSON beneath each example contains the full data point.</p>')
 a.out.write_text(head+'\n'.join(render(e) for e in ex)+'\n')
 print(f'wrote {a.out}: {len(ex)} examples, {len(pending)} awaiting approval')
if __name__=='__main__':main()
