#!/usr/bin/env python3
"""Cross-language execution with discovery, predeclared experiments, and acceptance."""
import argparse
import json
from pathlib import Path
import platform
import posixpath
import random
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'skills/software-resynthesis/scripts'))
import sre


def run(workspace):
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js 18+ required; no automatic installation')
    sre.initialize(workspace, 'Python posixpath.normpath: Unicode string paths', 'Portable JavaScript')
    workspace = Path(workspace).resolve()
    source_build = f'CPython {platform.python_version()}'
    manifests = {}
    for name in ('source', 'successor', 'mutant'):
        source = name == 'source'
        script = HERE / ('source_adapter.py' if source else 'successor_adapter.mjs')
        manifest = {'schema_version': 1, 'id': 'posix-' + name,
                    'kind': 'source-runtime' if source else 'successor-runtime',
                    'build': source_build if source else 'javascript-v1:' + name,
                    'argv': ['{python}' if source else node, str(script)] + (['--mutant'] if name == 'mutant' else []),
                    'build_files': [str(script)] + ([sys.executable, posixpath.__file__] if source else [str(HERE / 'normalize.mjs')])}
        manifests[name] = workspace / f'runs/{name}-adapter.json'
        sre.write_new(manifests[name], manifest)

    def execute(name, request, directory):
        request_file = workspace / f'runs/{directory}-request.json'
        sre.write_new(request_file, request)
        output = workspace / 'runs' / directory
        report = sre.run_adapter(manifests[name], request_file, output)
        if not report['passed']:
            raise RuntimeError(f'Adapter failed: {report}')
        return output / 'trace.json'

    # Exploratory observation is distinct from the later acceptance experiment.
    execute('source', {'schema_version': 1, 'scenario': 'discovery', 'fixture': {},
                      'actions': [{'normalize': 'a//b'}]}, 'discovery')
    project_path = workspace / 'project.json'
    project = sre.read(project_path)
    project.update({'request': 'Validate lexical POSIX Unicode string normalization across Python and JavaScript',
        'features': [{'id': 'normpath', 'description': 'Lexically normalize Unicode POSIX path strings',
                      'mode': 'preserve', 'status': 'implementing', 'acceptance': ['posix-normalize', 'node-execution']}],
        'validations': [
            {'id': 'posix-normalize', 'kind': 'differential', 'status': 'pending', 'features': ['normpath'], 'artifact': 'runs/comparison.json'},
            {'id': 'node-execution', 'kind': 'target', 'status': 'pending', 'features': ['normpath'], 'artifact': 'runs/target.json'}]})
    project_path.write_text(json.dumps(project, indent=2), encoding='utf-8')
    research = {'schema_version': 1, 'scope': {'claim': 'milestone',
        'description': 'Lexical normalization of Unicode POSIX paths only', 'source_build': source_build,
        'target': 'Node.js portable module', 'features': ['normpath']}, 'surveys': [],
        'questions': [{'id': 'double-slash', 'question': 'Are exactly two leading slashes preserved?',
          'feature': 'normpath', 'blocking': True, 'impact': 4,
          'hypotheses': [{'id': 'preserve', 'explanation': 'Keep exactly two leading slashes'},
                         {'id': 'collapse', 'explanation': 'Collapse all leading slashes to one'}],
          'experiments': [{'id': 'root', 'input': {'normalize': '//'}, 'cost': 1,
                          'predictions': {'preserve': '//', 'collapse': '/'}}]}]}
    for kind, source in (('docs', 'https://docs.python.org/3/library/os.path.html#os.path.normpath'),
                         ('runtime', 'runs/discovery/trace.json')):
        name = f'evidence/{kind}.json'
        sre.write_new(workspace / name, {'schema_version': 1, 'source_build': source_build, 'source': source,
            'scope_note': 'Curated lexical normalization scope; public docs may span a different Python release',
            'items': [{'id': 'normpath', 'label': 'Normalize string paths lexically', 'feature': 'normpath'}]})
        research['surveys'].append({'id': kind, 'kind': kind, 'required': True, 'status': 'complete', 'artifact': name})
    research_path = workspace / 'research.json'
    research_path.write_text(json.dumps(research, indent=2), encoding='utf-8')
    sre.sre_research.seal(workspace, 'research-baseline.json')
    plan = sre.sre_research.audit(workspace)
    if plan['research_ready'] or not plan['next_experiments']:
        raise RuntimeError('Unobserved blocking question should require a discriminating experiment')

    paths = ['', '.', '..', '/', '//', '///', '////', '//a/../b', 'a/../../b', '/../../a',
             'a//b/./c/..', '../a/..', '文件/../背包', 'a\\b/../c', 'a/.../b', 'a/', ' /../x']
    rng = random.Random(4217)
    pieces = ['a', 'b', '..', '.', '', '文件', 'x y', '...']
    paths.extend('/'.join(rng.choice(pieces) for _ in range(rng.randrange(1, 15))) for _ in range(400))
    request = {'schema_version': 1, 'scenario': 'posix-normalize', 'fixture': {},
               'actions': [{'normalize': p} for p in paths]}
    traces = {name: execute(name, request, name) for name in manifests}
    report_path = workspace / 'runs/comparison.json'
    report = sre.compare(traces['source'], traces['successor'], report_path)
    sre.write_new(report_path, report)
    mutant_path = workspace / 'runs/mutant-comparison.json'
    mutant = sre.compare(traces['source'], traces['mutant'], mutant_path)
    sre.write_new(mutant_path, mutant)
    passed = report['passed'] and not mutant['passed']
    node_version = subprocess.run([node, '--version'], text=True, encoding='utf-8', capture_output=True, check=True, timeout=10).stdout.strip()
    sre.write_new(workspace / 'runs/target.json', {'schema_version': 1, 'passed': passed,
        'environment': f'{platform.system()} / Node {node_version}',
        'command': 'node examples/posix-path/successor_adapter.mjs (adapter JSON on stdin)',
        'assertions': [f'{len(paths)} outputs match the running source', 'Double-leading-slash mutation detected'],
        'scope': 'Node execution only; browser and full-product acceptance not tested'})
    project['features'][0]['status'] = 'verified' if passed else 'implementing'
    project['validations'][0]['status'] = 'passed' if report['passed'] else 'failed'
    project['validations'][1]['status'] = 'passed' if passed else 'failed'
    project.update(stage='validation', next_action='Review limited scope; not a PZ or full-application benchmark.')
    project_path.write_text(json.dumps(project, indent=2), encoding='utf-8')
    research['questions'][0]['experiments'][0]['observation'] = {'artifact': 'runs/source/trace.json', 'pointer': '/steps/4/result/value'}
    research_path.write_text(json.dumps(research, indent=2), encoding='utf-8')
    result = sre.check(workspace)
    print(json.dumps({'cases': len(paths), 'differential_passed': report['passed'],
                      'first_difference': report['first_difference'], 'mutant_detected': not mutant['passed'],
                      'acceptance': result}, indent=2))
    return 0 if result['recorded_acceptance'] and not mutant['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, help='New output directory; must not exist')
    args = parser.parse_args()
    try:
        sys.exit(run(args.workspace))
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
