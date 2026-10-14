"""Read original or losslessly retained geometry without expanding on disk."""
from pathlib import Path
from functools import lru_cache
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def _decoder():
    spec = importlib.util.spec_from_file_location('rainee_lean_decoder', ROOT/'serve.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entries = json.loads((ROOT/'data/asset-map.json').read_text(encoding='utf-8'))['assets']
    return module, entries

def read_retained_asset(filename):
    filename = Path(filename).resolve()
    route = filename.relative_to(ROOT).as_posix()
    if (ROOT/'data/asset-map.json').exists():
        module, entries = _decoder()
        if route in entries:
            return module.decode(ROOT, entries[route], entries)
    return filename.read_bytes()
