# -*- coding: utf-8 -*-
"""Build the Chinese human-evaluation site (100-error severity test + 60-item blind pairwise check).

Output: annotation/eval_site/data.json (items + Chinese aid translations + rubric).
The page itself is annotation/eval_site/index.html (hand-written, loads data.json).
System names are kept out of the page data, so raters stay blind.
"""
import hashlib
import json
from pathlib import Path

import openpyxl
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from common import single_error_hyp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'annotation/eval_site'

errors = {}
for f in ['outputs/errors.jsonl', 'outputs/errors_test_extra.jsonl']:
    for line in (ROOT / f).read_text().splitlines():
        e = json.loads(line)
        errors[e['error_id']] = e

ids = (ROOT / 'data/splits/human_test.txt').read_text().split()
sheet = list(openpyxl.load_workbook(ROOT / 'annotation/human_test_A.xlsx').active.iter_rows(min_row=2, values_only=True))
assert [r[-1] for r in sheet] == ids, 'human_test_A.xlsx order differs from data/splits/human_test.txt'

pairs = list(openpyxl.load_workbook(ROOT / 'annotation/pairwise_rater1.xlsx').active.iter_rows(min_row=2, values_only=True))
assert pairs == list(openpyxl.load_workbook(ROOT / 'annotation/pairwise_rater2.xlsx').active.iter_rows(min_row=2, values_only=True))

zh = json.loads((ROOT / 'annotation/pilot_zh.json').read_text())['translations']
zh.update(json.loads((ROOT / 'annotation/eval_zh.json').read_text())['translations'])

severity = []
for n, eid in enumerate(ids, 1):
    e = errors[eid]
    severity.append({
        'n': n, 'id': eid,
        'before': e['context_before'], 'after': e['context_after'],
        'ref': e['ref'], 'refMarked': e['ref_marked'], 'refSpan': e['ref_span'], 'hypSpan': e['hyp_span'] or '∅',
        'op': e['op'], 'hyp': single_error_hyp(e),  # only this error; all others corrected
    })

pairwise = []
for r in pairs:
    n, ctx, ref, a, b = r[:5]
    pairwise.append({'n': n, 'context': ctx.split('\n') if ctx else [], 'ref': ref, 'A': a, 'B': b})

used = set()
for s in severity:
    used.update([*s['before'], s['ref'], *s['after'], s['hyp']])
for p in pairwise:
    used.update([*p['context'], p['ref'], p['A'], p['B']])
missing = [s for s in used if s and s not in zh]
assert not missing, f'{len(missing)} strings lack a Chinese aid translation, e.g. {missing[:3]}'

rubric_zh = (ROOT / 'annotation/rubric_zh.md').read_text()


def section(text, start, end):
    body = text[text.index(start):text.index(end)]
    return body.split('\n', 1)[1].strip()


payload = {
    'severity': severity, 'pairwise': pairwise,
    'zh': {s: zh[s] for s in sorted(used) if s},
    'rubricZh': rubric_zh,
    'calibZh': section(rubric_zh, '## 2.', '## 3.'),
    'contentZh': section(rubric_zh, '## 3.', '## 4.'),
    'rubricVersion': '2.4',
}
payload['version'] = hashlib.sha256(json.dumps([ids, [p['n'] for p in pairwise]]).encode()).hexdigest()[:12]
OUT.mkdir(exist_ok=True)
(OUT / 'data.json').write_text(json.dumps(payload, ensure_ascii=False))
print(f"{OUT/'data.json'}: {len(severity)} severity, {len(pairwise)} pairwise, {len(payload['zh'])} translations, version {payload['version']}")
