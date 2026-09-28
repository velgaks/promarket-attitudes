"""Download original public sources, preserving checksums and acquisition metadata."""
from pathlib import Path
import hashlib
import json
import ssl
import sys
import tempfile
from datetime import datetime, timezone
import requests

ROOT = Path(__file__).resolve().parents[1]

def session():
    s = requests.Session()
    # Requests' bundled CA list may omit locally trusted enterprise roots on Windows.
    # Keep TLS verification enabled and supplement the public CA bundle.
    if sys.platform == "win32":
        certs = ''.join(ssl.DER_cert_to_PEM_cert(c) for c, enc, _ in ssl.enum_certificates('ROOT') if enc == 'x509_asn')
        ca = ROOT / 'tmp' / 'windows-roots.pem'
        ca.parent.mkdir(exist_ok=True)
        bundle = certs + Path(requests.certs.where()).read_text()
        # Concurrent downloads must never see a partially written CA bundle.
        if not ca.exists() or ca.read_text() != bundle:
            with tempfile.NamedTemporaryFile(mode='w', dir=ca.parent, delete=False) as f:
                f.write(bundle)
                pending = Path(f.name)
            pending.replace(ca)
        s.verify = str(ca)
    return s

def download(url, relative_path, label='', params=None):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    fetched = not path.exists()
    if fetched:
        with session().get(url, params=params, stream=True, timeout=(30, 180)) as r:
            r.raise_for_status()
            partial = path.with_suffix(path.suffix + '.part')
            with partial.open('wb') as f:
                for block in r.iter_content(1024 * 1024):
                    f.write(block)
            validate_file(partial, path.suffix)
            partial.replace(path)
    validate_file(path, path.suffix)
    item = dict(path=relative_path, url=url, params=params, label=label,
                retrieved_utc=datetime.now(timezone.utc).isoformat(),
                bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    # Each source has its own manifest fragment, so independent downloads are safe.
    manifest = ROOT / 'data' / 'source_manifests'
    manifest.mkdir(parents=True, exist_ok=True)
    target = manifest / (path.name + '.json')
    # Rerunning acquisition must not invent a new acquisition timestamp.
    if fetched or not target.exists():
        target.write_text(json.dumps(item, indent=2), encoding='utf8')
    print(relative_path, item['bytes'], flush=True)
    return path

def validate_file(path, suffix):
    with path.open('rb') as f:
        prefix = f.read(512)
    if len(prefix.strip()) < 16 or prefix.lstrip().lower().startswith((b'<!doctype html', b'<html')):
        raise ValueError(f'Empty or HTML response instead of data: {path}')
    if suffix.lower() == '.pdf' and not prefix.startswith(b'%PDF'):
        raise ValueError(f'Invalid PDF: {path}')
    if suffix.lower() in ['.zip', '.xlsx'] and not prefix.startswith(b'PK'):
        raise ValueError(f'Invalid ZIP container: {path}')

if __name__ == '__main__':
    download(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else '')
