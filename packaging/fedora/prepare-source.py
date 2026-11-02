#!/usr/bin/env python3
"""Prepare a vendored Linux source archive from working files, without Git writes."""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import tarfile
import tempfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=pathlib.Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
version = tomllib.loads((ROOT / 'Cargo.toml').read_text())['workspace']['package']['version']
spec = (ROOT / 'packaging/fedora/openlogi.spec').read_text()
(output / 'openlogi.spec').write_text(re.sub(r'^Version:.*$', f'Version:        {version}', spec, flags=re.MULTILINE))
with tempfile.TemporaryDirectory(prefix='openlogi-source-') as temporary:
    source = pathlib.Path(temporary) / f'openlogi-{version}'
    source.mkdir()
    # Read the index only; include new packaging files before the user commits them.
    files = subprocess.check_output(['git', '-c', f'safe.directory={ROOT}', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
    for name in set(files.decode().split('\0')) - {''}:
        relative = pathlib.Path(name)
        if '__pycache__' in relative.parts or relative.suffix == '.pyc' or relative.parts[0] in {'design', '.git', '.agents', '.claude', '.codex'}:
            continue
        original = ROOT / relative
        if original.is_symlink() or not original.is_file():
            continue
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, destination)
    # Preserve compile-time paths while replacing all restricted branding.
    icon_dir = source / 'design/icon'
    icon_dir.mkdir(parents=True)
    artwork = ROOT / 'packaging/fedora/assets'
    shutil.copy2(artwork / 'LICENSE', source / 'design/LICENSE')
    for size in (16, 32, 48, 64, 128, 256, 512, 1024):
        filename = 'openlogi.png' if size == 1024 else f'openlogi-{size}.png'
        subprocess.run(['magick', '-background', 'none', str(artwork / 'openlogi.svg'), '-resize', f'{size}x{size}', str(icon_dir / filename)], check=True)
    for name in ('tray-icon@2x.png', 'tray-icon-prism@2x.png', 'tray-icon-white@2x.png'):
        subprocess.run(['magick', '-background', 'none', str(artwork / 'tray.svg'), '-resize', '64x64', str(source / 'crates/openlogi-agent/assets' / name)], check=True)
    original_metadata = json.loads(subprocess.check_output(
        ['cargo', 'metadata', '--locked', '--format-version', '1'], cwd=ROOT, text=True))
    component = next(p for p in original_metadata['packages'] if p['name'] == 'gpui-component')
    manifest = pathlib.Path(component['manifest_path'])
    themes = next(parent / 'themes' for parent in manifest.parents
                  if (parent / 'themes/catppuccin.json').is_file())
    shutil.copytree(themes, source / 'upstream-themes')
    config = subprocess.check_output(['cargo', 'vendor', '--locked', 'vendor'], cwd=source, text=True)
    with (source / '.cargo/config.toml').open('a') as stream:
        stream.write('\n' + config)
    metadata = json.loads(subprocess.check_output(
        ['cargo', 'metadata', '--frozen', '--format-version', '1'], cwd=source, text=True))
    inventory = [{'name': p['name'], 'version': p['version'], 'license': p.get('license'),
                  'license_file': p.get('license_file')} for p in metadata['packages']]
    (source / 'bundled-licenses.json').write_text(json.dumps(inventory, indent=2) + '\n')
    notices = source / 'bundled-licenses'
    notices.mkdir()
    for package in (source / 'vendor').iterdir():
        if not package.is_dir():
            continue
        for item in package.rglob('*'):
            if item.is_file() and item.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'NOTICE', 'COPYRIGHT')):
                destination = notices / package.name / item.relative_to(package)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destination)
    archive = output / f'openlogi-{version}.tar.gz'
    with tarfile.open(archive, 'w:gz') as bundle:
        bundle.add(source, arcname=source.name)
    print(archive)
