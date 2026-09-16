#!/usr/bin/env python3
"""One-off tool used to migrate the 2004 Flash nav buttons to CSS.
Extracts Dreamweaver 'Flash Button'/'Flash Text' metadata embedded as
plain ASCII strings in each uncompressed .swf, and validates each
button's target against the actual files in this directory."""
import glob, json, os, re, sys

STRING_RE = re.compile(rb'[\x20-\x7e]{3,}')

def extract_strings(path):
    data = open(path, 'rb').read()
    return [m.decode('ascii') for m in (s.group() for s in STRING_RE.finditer(data))]

KNOWN_KEYS = {
    'dwType', 'Button Text', 'Button URL', 'Button Target', 'Button Font', 'Button Size',
    'text', 'color', 'font', 'size', 'url', 'window', 'rollovercolor',
    'shrinkwrap', 'alignment', 'bold', 'italic',
}

def value_after(strings_list, key, occurrence=0):
    idxs = [i for i, s in enumerate(strings_list) if s == key]
    if len(idxs) <= occurrence:
        return None
    i = idxs[occurrence]
    if i + 1 >= len(strings_list):
        return None
    nxt = strings_list[i + 1]
    # An empty Dreamweaver field leaves no string of its own; the "next"
    # string is really the following key, not this field's value.
    if nxt in KNOWN_KEYS:
        return None
    return nxt

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    existing = set(os.listdir(root))
    existing_lower = {e.lower(): e for e in existing}

    manifest = {}
    problems = []

    for path in sorted(glob.glob(os.path.join(root, '*.swf'))):
        fn = os.path.basename(path)
        s = extract_strings(path)
        dwtype = value_after(s, 'dwType')
        swt = next((x for x in s if x.endswith('.swt')), None)
        template = re.sub(r'.*Flash (?:Buttons|Text)/', '', swt) if swt else None

        if dwtype == 'Flash Button':
            entry = {
                'type': 'button',
                'template': template,
                'text': value_after(s, 'Button Text'),
                'url': value_after(s, 'Button URL'),
                'target': value_after(s, 'Button Target'),
                'font': value_after(s, 'Button Font'),
                'size': value_after(s, 'Button Size'),
            }
        elif dwtype == 'Flash Text':
            entry = {
                'type': 'text',
                'template': template,
                'text': value_after(s, 'text'),
                'color': value_after(s, 'color'),
                'font': value_after(s, 'font'),
                'size': value_after(s, 'size'),
                'url': value_after(s, 'url'),
                'target': value_after(s, 'window'),
                'rollovercolor': value_after(s, 'rollovercolor'),
                'bold': value_after(s, 'bold'),
                'italic': value_after(s, 'italic'),
            }
        else:
            entry = {'type': 'other'}

        manifest[fn] = entry

        url = entry.get('url')
        if url and not url.lower().startswith(('http:', 'https:', 'mailto:')):
            if url not in existing:
                if url.lower() in existing_lower:
                    problems.append(f"{fn}: URL {url!r} case-mismatch, actual file is {existing_lower[url.lower()]!r}")
                else:
                    problems.append(f"{fn}: URL {url!r} does NOT exist on disk")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out_dir, 'swf_manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"{len(manifest)} swf files parsed")
    print(f"{len(problems)} URL problems:")
    for p in problems:
        print(' -', p)

if __name__ == '__main__':
    main()
