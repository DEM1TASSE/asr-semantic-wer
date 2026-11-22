# -*- coding: utf-8 -*-
"""Build the official 50-item, rubric-v2.3 offline/hosted annotation page."""
import base64
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def read_sheet(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        result = []
        for row in sheet.findall('.//m:sheetData/m:row', NS):
            values = {}
            for c in row.findall('m:c', NS):
                ref = re.match(r'[A-Z]+', c.get('r')).group()
                value = c.find('m:v', NS)
                inline = c.find('m:is', NS)
                val = value.text if value is not None else ''.join(inline.itertext()) if inline is not None else ''
                values[ref] = shared[int(val)] if c.get('t') == 's' else val
            result.append(values)
        letters = list(result[0])
        return [[r.get(c, '') for c in letters] for r in result]

ids = (ROOT / 'outputs/pilot_ids.txt').read_text().splitlines()
errors_bytes = (ROOT / 'outputs/errors.jsonl').read_bytes()
errors = {e['error_id']: e for e in map(json.loads, errors_bytes.decode().splitlines())}
assert len(ids) == len(set(ids)) == 50
sheets = {who: read_sheet(ROOT / f'annotation/human_pilot_{who}.xlsx') for who in 'AB'}
for who, table in sheets.items():
    assert [r[table[0].index('error_id')] for r in table[1:]] == ids, 'Official Excel/ID list mismatch'
assert sheets['A'][0] == sheets['B'][0]
rubric_en = (ROOT / 'annotation/rubric.md').read_text()
version = hashlib.sha256(('\n'.join(ids) + '\n' + rubric_en).encode()).hexdigest()[:16]
zh = json.loads((ROOT / 'annotation/pilot_zh.json').read_text())['translations']
for eid in ids:
    e = errors[eid]
    assert all(t in zh for t in [*e['context_before'], e['ref'], *e['context_after'], e['hyp']])
payload = {'rubricVersion': '2.3', 'version': version, 'legacyVersion': hashlib.sha256(errors_bytes).hexdigest()[:12],
           'sourceCommit': subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip(),
           'ids': ids, 'errors': [errors[eid] for eid in ids], 'zh': zh,
           'rubricZh': (ROOT / 'annotation/rubric_zh.md').read_text(), 'rubricEn': rubric_en,
           'columns': sheets['A'][0], 'sheetRows': sheets['A'][1:],
           'templates': {who: base64.b64encode((ROOT / f'annotation/human_pilot_{who}.xlsx').read_bytes()).decode() for who in 'AB'}}
template = (ROOT / 'tools/viewer_v23.html').read_text()
html = template.replace('__PAYLOAD__', json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c'))
html = html.replace('__ZIPLIB__', (ROOT / 'tools/vendor/fflate.js').read_text())
html = html.replace('__APP__', (ROOT / 'tools/viewer_v23.js').read_text())
out = ROOT / 'annotation/viewer.html'
out.write_text(html)
print(f'{out}: official 50; rubric 2.3; dataset {version}; {out.stat().st_size:,} bytes')
