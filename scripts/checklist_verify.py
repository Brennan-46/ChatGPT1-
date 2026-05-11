from pathlib import Path
import re
import sys

files = [Path('RELEASE_CHECKLIST.md'), Path('UAT_SIGNOFF.md')]
missing = []
for f in files:
    txt = f.read_text()
    unchecked = re.findall(r"- \[ \]", txt)
    if unchecked:
        missing.append((f, len(unchecked)))

if missing:
    for f, n in missing:
        print(f"{f}: {n} unchecked items")
    sys.exit(1)

print('All checklist and signoff items are checked.')
