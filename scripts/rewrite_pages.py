#!/usr/bin/env python3
"""One-off migration script: rewrites the 2004 FGOAC HTML pages so they run
without the Flash plugin, and flattens them into public/.

What it does, in order, per .htm/.html file:
  1. Replaces every <object>...<embed src="X.swf">...</object> block whose
     swf is a Dreamweaver "Flash Button"/"Flash Text" template (see
     extract_swf_manifest.py / swf_manifest.json) with an equivalent <a>
     styled by fgoac-buttons.css, preserving text/link/target/size.
  2. Strips the "../pages/" prefix (the site was deployed with its HTML
     inside a `pages/` folder, so this prefix always pointed back at the
     same flat directory as the HTML itself -- see README "Known gaps").
  3. Fixes the one case-sensitivity mismatch (Money.jpg -> Money.JPG).
  4. Renames index.htm -> index.html (static hosts serve index.html by
     default, not index.htm) and rewrites internal links/targets to match.
  5. Replaces the two embedded Targets_email_intro.swf players (a genuine
     hand-animated splash, not a template button) with a static fallback.
  6. Links the stylesheet into <head>.

Leaves table layouts, <font> tags, and everything else untouched by design.
"""
import json, os, re, shutil, sys

SRC = sys.argv[1]
DST = sys.argv[2]
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swf_manifest.json')

TEMPLATE_CLASS = {
    'Beveled Rect-Blue.swt': 'fbtn-blue',
    'Beveled Rect-Green.swt': 'fbtn-green',
    'Beveled Rect-Bronze.swt': 'fbtn-bronze',
    'Glass-Silver.swt': 'fbtn-silver',
    'Soft-LimeGreen.swt': 'fbtn-lime',
    'eCommerce-Generic.swt': 'fbtn-generic',
    'eCommerce-Checkout.swt': 'fbtn-checkout',
    'eCommerce-Cash.swt': 'fbtn-cash',
    'Slider.swt': 'fbtn-misc',
    'Blip Arrow.swt': 'fbtn-misc',
    'Navigation-Previous (Green).swt': 'fbtn-misc',
}

TEXT_FALLBACK = {
    'bck2gmes.swf': 'Back',
}

OBJECT_BLOCK_RE = re.compile(
    r'<object\b[^>]*?width="(?P<w>\d+)"\s+height="(?P<h>\d+)"[^>]*>.*?</object>\s*',
    re.IGNORECASE | re.DOTALL,
)
MOVIE_RE = re.compile(r'value="([^"]+\.swf)"', re.IGNORECASE)


def esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def build_replacement(fn, entry, w, h):
    if fn == 'Targets_email_intro.swf':
        return (
            '<div class="legacy-flash-note" '
            f'style="width:{w}px;max-width:100%;border:2px dashed #888;padding:12px;'
            'text-align:center;font-family:Verdana,Arial,sans-serif;font-size:13px;'
            'background:#f4f4f4;color:#333;box-sizing:border-box;">'
            'This page originally opened with a hand-animated Flash intro. '
            'The original movie is preserved for reference: '
            '<a href="Targets_email_intro.swf">Targets_email_intro.swf</a>.'
            '</div>'
        )

    text = entry.get('text') or TEXT_FALLBACK.get(fn, fn)
    url = entry.get('url') or '#'
    target = entry.get('target') or '_self'
    if url.lower() == 'index.htm':
        url = 'index.html'
    # Cap at 15px: some templates (e.g. eCommerce-Generic, 93x33) pair a tall
    # box with longer text ("Comic #164"), and height-9 alone would clip it.
    font_size = min(max(9, int(h) - 9), 15)

    if entry['type'] == 'text':
        style = (
            f'min-width:{w}px;min-height:{h}px;font-size:{font_size}px;'
            f'--fg:{entry.get("color") or "#0000FF"};--hover:{entry.get("rollovercolor") or "#0000FF"};'
        )
        return (
            f'<a class="ftext" href="{esc(url)}" target="{esc(target)}" style="{style}">{esc(text)}</a>'
        )

    css_class = TEMPLATE_CLASS.get(entry.get('template'), 'fbtn-blue')
    style = f'min-width:{w}px;min-height:{h}px;font-size:{font_size}px;'
    return (
        f'<a class="fbtn {css_class}" href="{esc(url)}" target="{esc(target)}" style="{style}">{esc(text)}</a>'
    )


def rewrite_objects(html, manifest, stats):
    def repl(m):
        block = m.group(0)
        mv = MOVIE_RE.search(block)
        if not mv:
            return block
        fn = mv.group(1)
        # normalize possible "../pages/X.swf" movie refs
        fn = fn.split('/')[-1]
        entry = manifest.get(fn)
        if entry is None:
            stats['unknown_swf'].add(fn)
            return block
        stats['converted'] += 1
        return build_replacement(fn, entry, m.group('w'), m.group('h'))

    return OBJECT_BLOCK_RE.sub(repl, html)


def fix_paths(html):
    html = html.replace('../pages/', '')
    html = html.replace('Money.jpg', 'Money.JPG')
    html = re.sub(r'(href|src)="index\.htm"', r'\1="index.html"', html, flags=re.IGNORECASE)
    return html


def ensure_stylesheet_linked(html):
    if 'fgoac-buttons.css' in html:
        return html
    link = '<link rel="stylesheet" href="fgoac-buttons.css">\n'
    if re.search(r'</head>', html, re.IGNORECASE):
        return re.sub(r'</head>', link + '</head>', html, count=1, flags=re.IGNORECASE)
    return link + html


def main():
    manifest = json.load(open(MANIFEST_PATH))
    os.makedirs(DST, exist_ok=True)
    stats = {'converted': 0, 'unknown_swf': set(), 'files': 0}

    for name in sorted(os.listdir(SRC)):
        src_path = os.path.join(SRC, name)
        if not os.path.isfile(src_path):
            continue
        base, ext = os.path.splitext(name)
        if ext.lower() not in ('.htm', '.html'):
            continue

        html = open(src_path, encoding='latin-1').read()
        html = rewrite_objects(html, manifest, stats)
        html = fix_paths(html)
        html = ensure_stylesheet_linked(html)
        stats['files'] += 1

        out_name = 'index.html' if name.lower() == 'index.htm' else name
        with open(os.path.join(DST, out_name), 'w', encoding='latin-1') as f:
            f.write(html)

    print(f"Rewrote {stats['files']} html files, converted {stats['converted']} swf embeds")
    if stats['unknown_swf']:
        print(f"{len(stats['unknown_swf'])} swf(s) left as-is (no manifest entry / not a template button):")
        for fn in sorted(stats['unknown_swf']):
            print(' -', fn)


if __name__ == '__main__':
    main()
