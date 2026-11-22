"""Create a reproducible proposed dev set; preserve all legacy annotations."""
import csv
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = '751'
source = ROOT / 'annotation/human_pilot_A.csv'
with source.open() as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    pilot = list(reader)
errors = {e['error_id']: e for e in map(json.loads, (ROOT / 'outputs/errors.jsonl').read_text().splitlines())}
by_system = defaultdict(list)
for row in pilot:
    by_system[errors[row['error_id']]['system']].append(row['error_id'])
selected = set()
quotas = {}
for system, ids in sorted(by_system.items()):
    groups = defaultdict(list)
    for eid in ids:
        groups[errors[eid]['op']].append(eid)
    base = {op: 25 * len(g) // len(ids) for op, g in groups.items()}
    remainders = sorted(groups, key=lambda op: (-(25 * len(groups[op]) % len(ids)), op))
    for op in remainders[:25 - sum(base.values())]:
        base[op] += 1
    quotas[system] = base
    for op, group in groups.items():
        ordered = sorted(group, key=lambda eid: hashlib.sha256((SEED + '|' + eid).encode()).hexdigest())
        selected.update(ordered[:base[op]])
# Retain legacy display order so earlier and later page positions can be matched.
rows = [r for r in pilot if r['error_id'] in selected]
assert len(rows) == 50
ids = [r['error_id'] for r in rows]
manifest = {'status': 'candidate_pending_team_confirmation', 'seed': SEED,
            'source': 'annotation/human_pilot_A.csv',
            'method': '25 spans per ASR system; proportional allocation by alignment op using largest remainders; SHA256(seed|error_id) ordering within each stratum; no LLM or human labels used',
            'quotas': quotas, 'ids': ids,
            'legacy_positions': [i + 1 for i, r in enumerate(pilot) if r['error_id'] in selected]}
p = ROOT / 'annotation/dev50_candidate_manifest.json'
if p.exists():
    assert json.loads(p.read_text()) == manifest, 'Candidate manifest changed; refusing to replace an existing split'
else:
    p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
for who in 'AB':
    out = ROOT / f'annotation/human_dev50_candidate_{who}.csv'
    if not out.exists():
        with out.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for r in rows:
                writer.writerow({**r, **dict.fromkeys(['severity','content_type','error_form','flag','note'], '')})
(ROOT / 'outputs/dev50_candidate_ids.txt').write_text('\n'.join(ids) + '\n')
summary = '# Dev 50 candidate (pending team confirmation)\n\n'
summary += 'The upstream repository has no official 50-item ID list as of 2026-11-09. This is a proposed subset of the legacy 80, not a team-confirmed split. Keep legacy files and annotations. Both annotators should use identical IDs after agreeing on this manifest. The final 200-item test set is not selected here.\n\n'
summary += '25 per ASR system; stratified by alignment operation (not severity or LLM error-form labels). Fixed seed 751; exact selection is recorded in dev50_candidate_manifest.json. All 50 retain the existing Chinese helper translations.\n\n'
summary += '| Dev row | Legacy 80 row | Reference span | ASR span | error_id |\n|---|---|---|---|---|\n'
for i, r in enumerate(rows):
    e = errors[r['error_id']]
    summary += f"| {i+1} | {manifest['legacy_positions'][i]} | {e['ref_span'] or '∅'} | {e['hyp_span'] or '∅'} | `{e['error_id']}` |\n"
(ROOT / 'annotation/dev50_candidate.md').write_text(summary)
print('Legacy positions:', manifest['legacy_positions'])
print('Quotas:', quotas)
