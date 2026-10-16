"""Append-only project records and evidence-linked progress reports.

These records describe work; they never satisfy fidelity/acceptance obligations.
Hashes detect drift relative to a record, not authenticity of its author.
"""
from datetime import datetime, timezone
from pathlib import Path
import re
from sre_common import read, write_new, digest, require, text, object_v1


def validate(entry):
    object_v1(entry)
    require(text(entry.get('id')) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', entry['id']), 'Invalid journal ID')
    for field in ('title', 'objective', 'result', 'next_action'):
        require(text(entry.get(field)), f'Missing journal {field}')
    require(entry.get('outcome') in {'progress', 'failed', 'blocked', 'verified'}, 'Invalid journal outcome')
    for field in ('actions', 'difficulties', 'resolutions', 'limitations'):
        require(isinstance(entry.get(field), list) and all(text(v) for v in entry[field]), f'Invalid journal {field}')
    require(entry['actions'], 'Journal must record actions')
    require(isinstance(entry.get('evidence'), list), 'Invalid journal evidence')
    for item in entry['evidence']:
        require(isinstance(item, dict) and text(item.get('path')) and text(item.get('description')), 'Invalid journal evidence item')
    require(entry['outcome'] != 'verified' or entry['evidence'], 'Verified journal entry requires evidence; does not establish acceptance')


def artifact(root, relative):
    require(not Path(relative).is_absolute(), 'Journal evidence must be relative to workspace')
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'Journal evidence escapes workspace')
    require(path.is_file(), f'Missing journal evidence: {relative}')
    return path


def record(workspace, entry_file):
    root = Path(workspace).resolve()
    object_v1(read(root / 'project.json'))
    entry = read(entry_file)
    validate(entry)
    # Fingerprint explicitly selected files only; never crawl or embed raw source.
    for item in entry['evidence']:
        item['sha256'] = digest(artifact(root, item['path']))
    entry['recorded_at'] = datetime.now(timezone.utc).isoformat()
    folder = root / 'journal'
    require(not folder.is_symlink(), 'Journal directory must not be a symlink')
    folder.mkdir(exist_ok=True)
    dest = folder / f"{entry['id']}.json"
    write_new(dest, entry)
    return {'schema_version': 1, 'entry': str(dest), 'id': entry['id'], 'acceptance_evidence': False}


def report(workspace):
    root = Path(workspace).resolve()
    project = read(root / 'project.json')
    object_v1(project)
    folder = root / 'journal'
    require(not folder.is_symlink(), 'Journal directory must not be a symlink')
    entries, problems = [], []
    for path in sorted(folder.glob('*.json')):
        require(path.resolve().is_relative_to(root), 'Journal entry escapes workspace')
        entry = read(path); validate(entry)
        for item in entry['evidence']:
            try:
                require(digest(artifact(root, item['path'])) == item.get('sha256'), 'Missing/stale evidence digest')
            except (ValueError, OSError) as exc:
                problems.append(f"{entry['id']}: {item['path']}: {exc}")
        entries.append(entry)
    entries.sort(key=lambda e:(e.get('recorded_at',''),e['id']))
    lines = ['# Resynthesis work record', '', f"Original request: {project.get('request','')}", '',
             'This is a progress record, not a fidelity or acceptance certificate.', '',
             '## Current feature inventory', '']
    for feature in project.get('features', []):
        lines.append(f"- {feature['id']}: {feature['status']} — {feature['description']}")
    for entry in entries:
        lines.extend(['', f"## {entry['id']} — {entry['title']}", '',
                      f"Recorded: {entry.get('recorded_at','unrecorded')} | Outcome: {entry['outcome']}", '', entry['objective']])
        for field in ('actions','difficulties','resolutions','limitations'):
            lines.extend(['',f'### {field.replace("_"," ").title()}',''])
            lines.extend(f'- {v}' for v in entry[field])
            if not entry[field]: lines.append('None recorded.')
        lines.extend(['','### Result','',entry['result'],'','### Evidence',''])
        lines.extend(f"- `{e['path']}` — {e['description']} (SHA-256 `{e.get('sha256', 'MISSING')}`)" for e in entry['evidence'])
        lines.extend(['',f"Next: {entry['next_action']}"])
    lines.extend(['','## Evidence integrity',''])
    lines.extend(f'- {p}' for p in problems)
    if not problems: lines.append('Recorded evidence hashes match. This does not authenticate captures or prove completeness.')
    return '\n'.join(lines)+'\n', problems
