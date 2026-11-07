#!/usr/bin/env python3
"""Check sources, refresh release hashes, validate and write a flat-root ZIP."""
from pathlib import Path
import argparse
import hashlib
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRS = {'.git', '__pycache__', 'node_modules', '.venv'}


def release_files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file()
                  and not EXCLUDED_DIRS.intersection(p.relative_to(ROOT).parts)
                  and p.suffix not in {'.zip', '.pyc'}
                  and p.name not in {'.DS_Store', 'verification-output.txt'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'Dude_Physics_GitHub_Flat_2026-11-07.zip')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.suffix != '.zip':
        parser.error('--output must be a .zip path')
    subprocess.run([sys.executable, 'build.py', '--check'], cwd=ROOT, check=True)
    files = [p for p in release_files() if p.name != 'SHA256SUMS']
    sums = ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(ROOT).as_posix() + '\n' for p in files)
    (ROOT / 'SHA256SUMS').write_text(sums)
    subprocess.run([sys.executable, 'verify.py'], cwd=ROOT, check=True)
    files = release_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert 'index.html' in archive.namelist() and 'README.md' in archive.namelist()
        assert len(archive.namelist()) == len(files)
        assert all(not name.startswith(('/', '../')) for name in archive.namelist())
    print(f'PASS: flat-root ZIP, {len(files)} files, {output.stat().st_size} bytes')
    print('ZIP SHA-256:', hashlib.sha256(output.read_bytes()).hexdigest())
    print('Archive:', output)


if __name__ == '__main__':
    main()
