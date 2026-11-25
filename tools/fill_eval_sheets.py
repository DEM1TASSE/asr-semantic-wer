# -*- coding: utf-8 -*-
"""Fill the human-eval Excel sheets with labels collected on the Chinese eval site.

Input, either or both:
  --db DIR       a database dump of the site: DIR/sev1/<n>.json, DIR/pair1/<n>.json, DIR/sev2/..., DIR/pair2/...
                 (one JSON object per item, as saved by annotation/eval_site/index.html)
  --backup FILE  a JSON backup exported from the site's "导出备份" button (one rater; may be repeated)

Rater 1 -> human_test_A.xlsx + pairwise_rater1.xlsx (+ relabel: submissions/human_test_A_relabel57.xlsx),
rater 2 -> human_test_B.xlsx + pairwise_rater2.xlsx.
The templates stay untouched; filled copies go to --out (default annotation/submissions/).
"""
import argparse
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SEV = {'1': 'human_test_A.xlsx', '2': 'human_test_B.xlsx'}
PAIR = {'1': 'pairwise_rater1.xlsx', '2': 'pairwise_rater2.xlsx'}
RELAB = {'1': 'submissions/human_test_A_relabel57.xlsx'}  # blind relabel of 57 display-affected items
CONTENT = {'disfluency', 'function_word', 'content_word', 'named_entity', 'number', 'negation', 'other'}
FLAGS = {'ref_issue', 'crosstalk', 'uncertain', 'multi_issue'}


def load_db(d):
    out = {}
    for kind in ('sev', 'pair', 'relab'):
        for r in '12':
            folder = Path(d) / f'{kind}{r}'
            if folder.is_dir():
                out[(kind, r)] = {f.stem: json.loads(f.read_text()) for f in folder.glob('*.json')}
    return out


def load_backup(f):
    b = json.loads(Path(f).read_text())
    r = str(b['rater'])
    return {('sev', r): b.get('severity', {}), ('pair', r): b.get('pairwise', {}), ('relab', r): b.get('relabel', {})}


def newer(a, b):
    return a if (a.get('updated') or '') >= (b.get('updated') or '') else b


def fill(template, labels, kind, out_dir):
    wb = openpyxl.load_workbook(ROOT / 'annotation' / template)
    ws = wb.active
    head = [c.value for c in ws[1]]
    col = {name: head.index(name) + 1 for name in head if name}
    n_rows = ws.max_row - 1
    filled, problems = 0, []
    for row in range(2, ws.max_row + 1):
        n = str(ws.cell(row, 1).value)
        a = labels.get(n)
        if not a:
            continue
        if kind in ('sev', 'relab'):
            sev, ct = a.get('severity'), a.get('content_type')
            flags = [f for f in a.get('flag') or [] if f in FLAGS]
            if sev not in (1, 2, 3, 4, 5):
                problems.append(f'#{n}: severity missing or invalid ({sev!r})')
            else:
                ws.cell(row, col['severity']).value = sev
            if ct in CONTENT:
                ws.cell(row, col['content_type']).value = ct
            else:
                problems.append(f'#{n}: content_type missing')
            ws.cell(row, col['flag']).value = ','.join(flags) or None
            done = sev in (1, 2, 3, 4, 5) and ct in CONTENT
        else:
            choice = a.get('choice')
            target = col['which keeps the meaning better?']
            if choice in ('A', 'B', 'Same'):
                ws.cell(row, target).value = choice
            else:
                problems.append(f'#{n}: choice missing')
            done = choice in ('A', 'B', 'Same')
        ws.cell(row, col['note']).value = (a.get('note') or '').strip() or None
        filled += done
    out = out_dir / Path(template).name.replace('.xlsx', '_filled.xlsx')
    wb.save(out)
    return out, filled, n_rows, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db')
    ap.add_argument('--backup', action='append', default=[])
    ap.add_argument('--out', default=str(ROOT / 'annotation/submissions'))
    args = ap.parse_args()
    labels = {}
    sources = ([load_db(args.db)] if args.db else []) + [load_backup(f) for f in args.backup]
    for src in sources:
        for key, items in src.items():
            merged = labels.setdefault(key, {})
            for n, a in items.items():
                merged[str(n)] = newer(a, merged[str(n)]) if str(n) in merged else a
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for (kind, r), items in sorted(labels.items()):
        if not items:
            continue
        template = {'sev': SEV, 'pair': PAIR, 'relab': RELAB}[kind][r]
        out, filled, total, problems = fill(template, items, kind, out_dir)
        print(f'{out}: {filled}/{total} complete')
        for p in problems:
            print('  ', p)


if __name__ == '__main__':
    main()
