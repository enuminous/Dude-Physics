#!/usr/bin/env python3
"""Validate the local Dude Physics package. This does not execute Lean or test physics."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.links, self.scripts, self.images, self.articles = [], [], [], [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        for attr in ('href', 'src'):
            if attr in values:
                self.links.append((tag, values[attr]))
        if tag == 'script' and 'src' in values:
            self.scripts.append(values['src'])
        if tag == 'img':
            self.images.append(values)
        if tag == 'article' and 'data-id' in values:
            self.articles.append(int(values['data-id']))


def main():
    require(sys.version_info >= (3, 10), 'Python 3.10+ required')
    node_version = subprocess.check_output(['node', '--version'], text=True).strip()
    require(int(node_version.lstrip('v').split('.')[0]) >= 20, 'Node.js 20+ required')
    items = json.loads((ROOT / 'inventory.json').read_text())
    require([x['id'] for x in items] == list(range(1, 73)), 'IDs must be 1–72 in order')
    for item in items:
        require(set(item) == {'id', 'name', 'category', 'connection', 'reading'}, 'Catalog schema mismatch')
        require(all(isinstance(item[k], str) and item[k].strip() for k in ('name', 'category', 'connection', 'reading')), 'Blank catalog field')
        require(item['reading'] in {'visible', 'grouped', 'interpretive'}, 'Unknown reading label')
    require('rug' in items[65]['name'].lower(), 'Item 66 must remain the rug')
    print('PASS: 72 catalog entries, stable IDs, reading labels and rug 66', flush=True)
    subprocess.run([sys.executable, 'build.py', '--check'], cwd=ROOT, check=True)

    docs = {p.name: Document(p.read_text()) for p in ROOT.glob('*.html') if '.template.' not in p.name}
    for name, doc in docs.items():
        require(len(doc.ids) == len(set(doc.ids)), f'Duplicate HTML IDs in {name}')
        for tag, target in doc.links:
            parsed = urlsplit(target)
            if parsed.scheme:
                require(parsed.scheme in {'http', 'https', 'mailto'}, f'Unexpected URI scheme: {target}')
                require(tag == 'a', f'External runtime dependency: {target}')
                continue
            require(not parsed.netloc, f'Protocol-relative dependency: {target}')
            path = unquote(parsed.path) or name
            require((ROOT / path).is_file(), f'Missing target from {name}: {target}')
            if parsed.fragment and path in docs:
                require(parsed.fragment in docs[path].ids, f'Missing fragment from {name}: {target}')
        for img in doc.images:
            require(bool(img.get('alt')), f'Missing image alternative text in {name}')
    require(docs['index.html'].articles == list(range(1, 73)), 'Static HTML catalog is incomplete')
    require(docs['index.html'].scripts == ['inventory.js', 'app.js'], 'Script ordering changed')
    for p in ROOT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            parsed = urlsplit(target)
            if not parsed.scheme and parsed.path:
                require((ROOT / unquote(parsed.path)).is_file(), f'Missing Markdown link in {p.name}: {target}')
    print('PASS: local HTML/Markdown links, anchors, 72 static entries and offline assets', flush=True)

    manifest = json.loads((ROOT / 'source-manifest.json').read_text())
    for image in manifest['images']:
        actual = hashlib.sha256((ROOT / image['file']).read_bytes()).hexdigest()
        require(actual == image['sha256'], f'Image bytes changed: {image["file"]}')
    require(len(manifest['images']) == 2, 'Both source and generated room must be preserved')
    print('PASS: both preserved image SHA-256 hashes', flush=True)
    subprocess.run(['node', 'test.cjs'], cwd=ROOT, check=True)
    sums = ROOT / 'SHA256SUMS'
    if sums.exists():
        listed = set()
        for line in sums.read_text().splitlines():
            expected, filename = line.split('  ', 1)
            require((ROOT / filename).is_file(), f'Missing file in SHA256SUMS: {filename}')
            require(hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == expected, f'Integrity mismatch: {filename}')
            require(filename not in listed, 'Duplicate hash entry')
            listed.add(filename)
        print(f'PASS: {len(listed)} release file hashes', flush=True)
    else:
        print('INFO: release SHA256SUMS not yet generated', flush=True)
    print(f'PASS: Dude Physics package checks (Python {sys.version.split()[0]}, Node {node_version})')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
