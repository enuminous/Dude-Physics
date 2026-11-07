#!/usr/bin/env python3
"""Build the offline archive from its canonical catalog and Markdown essays.

Only Python's standard library is required. --check is read-only.
The Markdown renderer implements the limited subset used by these source files;
it is not a general-purpose Markdown parser.
"""
from pathlib import Path
import argparse
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
CHAPTERS = [
    ('DUDE_PHYSICS.md', 'essay', 'Dude Physics', 'The full essay: identity, coherence, comedy and the burden of proof.'),
    ('THE_ROOM.md', 'the-room', 'The room', 'A walk through three workspaces and their shared floor.'),
    ('EMERGENT_DUDEISM.md', 'origin-story', 'Emergent dudeism', 'The recorded sequence, from image prompt to shared joke.'),
    ('RUG_THEORY.md', 'rug-theory', 'Rug Theory', 'Explicit satire, mock laws and a fictional peer review.'),
    ('EFMW.md', 'efmw-guide', 'EFMW in this room', 'The research program and the evidence each kind of claim needs.'),
    ('CLAIMS.md', 'claims', 'The claim ledger', 'Observations, interpretations, open questions and jokes.'),
    ('PROVENANCE.md', 'provenance', 'Provenance', 'Images, catalog, authorship and source history.'),
    ('SOURCES.md', 'sources', 'Primary sources', 'Inspected research documents and their exact blob identifiers.'),
    ('LICENSE_NOTICE.md', 'rights', 'Rights and attribution', 'The package’s current rights and licensing boundaries.'),
]
CHAPTER_IDS = {filename: anchor for filename, anchor, _, _ in CHAPTERS}


def esc(value):
    return html.escape(str(value), quote=True)


def inline(text):
    """Escape first, then handle trusted-source inline links/emphasis/code."""
    text = esc(text)
    protected = []

    def hold(match):
        protected.append('<code>' + match.group(1) + '</code>')
        return '\x00' + str(len(protected) - 1) + '\x00'

    text = re.sub(r'`([^`]+)`', hold, text)

    def link(match):
        label, destination = match.groups()
        raw = html.unescape(destination)
        if raw in CHAPTER_IDS:
            destination = '#' + CHAPTER_IDS[raw]
        if re.match(r'(?i)^(javascript|data):', raw):
            raise ValueError('Unsupported link scheme')
        return f'<a href="{destination}">{label}</a>'

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    for i, item in enumerate(protected):
        text = text.replace('\x00' + str(i) + '\x00', item)
    return text


def markdown(source):
    lines = source.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith('```'):
            block, i = [], i + 1
            while i < len(lines) and not lines[i].startswith('```'):
                block.append(lines[i]); i += 1
            out.append('<pre><code>' + esc('\n'.join(block)) + '</code></pre>')
            i += 1
        elif re.match(r'^#{1,6} ', line):
            marker, title = line.split(' ', 1)
            level = min(len(marker) + 1, 6)
            out.append(f'<h{level}>{inline(title)}</h{level}>'); i += 1
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [cell.strip() for cell in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', cell) for cell in cells):
                    rows.append(cells)
                i += 1
            out.append('<table><thead><tr>' + ''.join('<th scope="col">' + inline(c) + '</th>' for c in rows[0]) + '</tr></thead><tbody>')
            for row in rows[1:]:
                out.append('<tr>' + ''.join('<td>' + inline(c) + '</td>' for c in row) + '</tr>')
            out.append('</tbody></table>')
        elif line.startswith('>'):
            quote = []
            while i < len(lines) and lines[i].startswith('>'):
                quote.append(lines[i][1:].lstrip()); i += 1
            out.append('<blockquote>' + markdown('\n'.join(quote)) + '</blockquote>')
        elif re.match(r'^(?:- |\d+\. )', line):
            ordered = bool(re.match(r'^\d+\. ', line))
            tag = 'ol' if ordered else 'ul'
            out.append('<' + tag + '>')
            while i < len(lines) and re.match(r'^(?:- |\d+\. )', lines[i]):
                item = re.sub(r'^(?:- |\d+\. )', '', lines[i]); i += 1
                while i < len(lines) and lines[i].startswith('  '):
                    item += ' ' + lines[i].strip(); i += 1
                out.append('<li>' + inline(item) + '</li>')
            out.append('</' + tag + '>')
        else:
            paragraph = [line]; i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6} |>|\||```|- |\d+\. )', lines[i]):
                paragraph.append(lines[i]); i += 1
            out.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n'.join(out)


def outputs():
    items = json.loads((ROOT / 'inventory.json').read_text())
    categories = sorted({item['category'] for item in items})
    cards = []
    for item in items:
        rug = ' is-rug' if item['id'] == 66 else ''
        cards.append(f'''<article class="artifact{rug}" id="artifact-{item['id']}" data-id="{item['id']}">
<span class="artifact-id">{item['id']:02d}</span><h3>{esc(item['name'])}</h3>
<p>{esc(item['connection'])}</p><div class="artifact-meta"><span>{esc(item['category'])}</span><span>{esc(item['reading'])}</span></div></article>''')
    links = []
    for n, (_, anchor, title, description) in enumerate(CHAPTERS, 1):
        links.append(f'<a href="reading.html#{anchor}"><span class="number">{n:02d}</span><h3>{esc(title)}</h3><p>{esc(description)}</p><span class="arrow" aria-hidden="true">↗</span></a>')
    page = (ROOT / 'index.template.html').read_text()
    tokens = {'COUNT': str(len(items)), 'CATEGORY_OPTIONS': ''.join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in categories), 'CATALOG': '\n'.join(cards), 'READING_LINKS': '\n'.join(links)}
    for key, value in tokens.items():
        page = page.replace('{{' + key + '}}', value)
    if re.search(r'\{\{[A-Z_]+\}\}', page):
        raise ValueError('Unresolved template variable')
    js = '/* Generated by build.py; edit inventory.json. */\n' + 'globalThis.DUDE_INVENTORY = ' + json.dumps(items, ensure_ascii=False, indent=2) + ';\n'
    md = '# The complete 72-entry room inventory\n\nGenerated from `inventory.json`. Numbers preserve the conversational catalog.\nThese are entries, not a count of individual objects or real possessions.\n\n**Visible:** direct visual reading. **Grouped:** several things in one entry.\n**Interpretive:** less certain identification or meaning.\n\n| No. | Artifact | Collection | Connection | Reading |\n|---:|---|---|---|---|\n'
    for item in items:
        md += '| ' + ' | '.join(str(item[k]).replace('|', '\\|') for k in ('id', 'name', 'category', 'connection', 'reading')) + ' |\n'
    nav = '\n'.join(f'<a href="#{anchor}">{esc(title)}</a>' for _, anchor, title, _ in CHAPTERS)
    chapters = '\n'.join(f'<article class="chapter" id="{anchor}"><p class="source-link"><a href="{filename}">Markdown source ↗</a></p>\n{markdown((ROOT / filename).read_text())}\n</article>' for filename, anchor, _, _ in CHAPTERS)
    reader = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>The writing · Dude Physics</title><link rel="stylesheet" href="styles.css"></head>
<body><a class="skip" href="#chapters">Skip to the writing</a><header class="site-header"><a class="wordmark" href="index.html">DP<span> / field notes</span></a><nav aria-label="Main navigation"><a href="index.html">← Return to the room</a><a href="INVENTORY.md">72-entry catalog</a></nav></header>
<div class="reader-header wrap"><p class="eyebrow">Dude Physics / The complete writing</p><h1>A place to <em>read.</em></h1><p>Essays, evidence, satire. Keep the labels attached.</p></div>
<main class="reader-layout wrap"><nav class="contents" aria-label="Chapters">{nav}</nav><div id="chapters">{chapters}</div></main>
<footer class="site-footer wrap"><p><a href="index.html">Return to the room</a> · Prepared for Matthew Chenoweth Wright with AI assistance · 2026-11-07</p></footer></body></html>
'''
    return {'index.html': page, 'inventory.js': js, 'INVENTORY.md': md, 'reading.html': reader}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for name, content in outputs().items():
        destination = ROOT / name
        if args.check:
            if not destination.exists() or destination.read_text() != content:
                stale.append(name)
        else:
            destination.write_text(content, encoding='utf-8')
    if stale:
        print('FAIL: generated files are stale: ' + ', '.join(stale), file=sys.stderr)
        return 1
    print('PASS: 4 generated files are current' if args.check else 'Built index.html, reading.html, inventory.js and INVENTORY.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
