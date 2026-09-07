"""Explicitly refresh offline sources; no download occurs at clock startup."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

DATA = Path(__file__).resolve().parents[1] / 'src' / 'Data'
SOURCES = {
    'quran-arabic.json': 'https://raw.githubusercontent.com/risan/quran-json/master/dist/quran.json',
    'quran-de-bubenheim.json': 'https://raw.githubusercontent.com/fawazahmed0/quran-api/1/editions/deu-asfbubenheimand.json',
}


def main():
    prepared = {}
    for name, url in SOURCES.items():
        response = requests.get(url, timeout=(5, 30))
        response.raise_for_status()
        prepared[name] = response.content
    arabic = json.loads(prepared['quran-arabic.json'])
    german = json.loads(prepared['quran-de-bubenheim.json'])['quran']
    arabic_keys = {(s['id'], v['id']) for s in arabic for v in s['verses']}
    german_keys = {(v['chapter'], v['verse']) for v in german}
    if len(arabic) != 114 or len(arabic_keys) != 6236 or arabic_keys != german_keys:
        raise ValueError('Incomplete or mismatched source data; files not replaced')
    for name, content in prepared.items():
        temporary = DATA / (name + '.tmp')
        temporary.write_bytes(content)
        temporary.replace(DATA / name)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'files': {name: {'url': SOURCES[name], 'sha256': hashlib.sha256(content).hexdigest()}
                          for name, content in prepared.items()}}
    (DATA / 'quran-sources.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Validated 114 suras / 6236 matched Arabic and German verses.')


if __name__ == '__main__':
    main()
