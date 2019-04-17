import json
from pathlib import Path


BASE_DIR = Path(__file__).parent.resolve()
LOG_DIR = Path(BASE_DIR, 'log')
if not LOG_DIR.exists():
    LOG_DIR.mkdir()

CFG_DIR = Path(BASE_DIR, 'cfg')
if not CFG_DIR.exists():
    CFG_DIR.mkdir()
CFG_File = Path(CFG_DIR, 'default.cfg')
if not CFG_File.exists():
    # CFG_File.mkdir()
    with open(CFG_File, 'w') as fp:
        json.dump({}, fp)
COOKIE_DIR = Path(BASE_DIR, 'cookie')
if not COOKIE_DIR.exists():
    COOKIE_DIR.mkdir()
MESS_DIR = Path(BASE_DIR, 'mess')
if not MESS_DIR.exists():
    MESS_DIR.mkdir()
