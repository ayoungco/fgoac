# FGOAC (2004)

The source for the FGOAC (Funny Guy Organized Association of Comics) website —
the first site Adam Young ever built, in Macromedia Dreamweaver MX 2004, for
his [funnyguycomics](https://github.com/ayoungco/funnyguycomics) FGOAC-era
webcomic. It's the successor to the original fgcomics.com incarnation
(`fgcomics2006`) after the FGCI → FGOAC rename described in
[`funnyguycomics`'s history page](https://github.com/ayoungco/funnyguycomics/blob/main/content/history.md).

Static HTML pages (character bios, a store, a FAQ, comic pages, forums
link-out, FGRPG game promotion) wired together by a Flash-based nav bar. No
server-side code — this was a purely static site.

## Layout

- **`public/`** — the site as deployed. Every `.htm`/`.html` page, every
  image, and the archived `.swf` originals live here flat, matching how the
  2004 site was actually hosted (see "Why the paths are flat" below).
- **`scripts/`** — the one-off tools used to migrate the site off Flash (see
  below). Not needed to run the site; kept for provenance/re-running if more
  source images turn up.
- **`.github/workflows/pages.yml`** — deploys `public/` to GitHub Pages on
  every push to `master`.

## Local preview

```
cd public && python3 -m http.server 8000
```

then open `http://localhost:8000/`.

## Flash → CSS

The original site used ~85 `.swf` movies for its nav bar and buttons. Nearly
all of them (84 of 85) turned out to be stock Dreamweaver "Flash
Button"/"Flash Text" objects — Dreamweaver bakes the button's text, target
URL, link target, font, and size into the `.swf` as plain strings alongside
the vector art. `scripts/extract_swf_manifest.py` pulls that metadata out of
every `.swf` into `scripts/swf_manifest.json`, and
`scripts/rewrite_pages.py` uses it to replace each `<object>/<embed>` block
with a real `<a>` styled by `public/fgoac-buttons.css` to match the original
button's color family (blue/green/bronze/silver/lime, per the Dreamweaver
`.swt` template it came from). Real links, keyboard/screen-reader
accessible, no Flash plugin or emulator needed.

The one exception is `Targets_email_intro.swf`, a genuine hand-animated
600×450 splash (embedded in `Email.htm`) — not a template button, so it
wasn't auto-convertible. It's preserved as a downloadable file with a note
in its place; recreating the animation itself was out of scope for this
pass.

Re-run the pipeline (e.g. after editing a source `.htm`) with:

```
python3 scripts/extract_swf_manifest.py .
python3 scripts/rewrite_pages.py . public
```

## Known gaps

**72 of ~150 referenced images are missing** — mostly character bio
portraits (`Razor.PNG`, `yoda.PNG`, `mrevil.PNG`, ...), page backgrounds
(`Falls.jpg`, `SoapBubbles.PNG`, ...), and comic preview thumbnails
(`OwzersC164.JPG`, `TelethonC187.JPG`, ...). Full list in
`scripts/missing_images.txt`. Checked and ruled out as sources: this repo's
own history, a portfolio mirror and a recycle-bin backup found on disk (both
turned out to be the same incomplete flat export), and the Wayback Machine
(which only ever crawled the homepage at `freehostz.com/fgoac/pages/`, never
the image assets under it — `fgoac.com` itself was never archived at all).
If a backup of the original Dreamweaver "Local Site" folder turns up (old
external drive, burned disc, etc.), drop the images in flat into `public/`
by their original filenames and they'll resolve automatically — nothing
else needs to change.

**`Sponsors.htm`** is a stub added in 2026. The original nav bar linked to
it from every single page, but the page was never written back in 2004
either — it 404'd on the live site too.

### Why the paths are flat

Pages reference images as `../pages/Whatever.jpg`. That's not a broken
relative path — the original site's HTML lived *inside* a `pages/` folder
(`http://www.freehostz.com/fgoac/pages/`, confirmed by a hit-counter URL
embedded in `index.htm`), so `../pages/X` resolved back to the same flat
folder the HTML was already in. `scripts/rewrite_pages.py` strips that
prefix so the same flat layout works unmodified as `public/`.

## Deploying as fgoac.ayoung.ai

Deployed via GitHub Pages, built by `.github/workflows/pages.yml` from
`public/`. `public/CNAME` already contains `fgoac.ayoung.ai`.

One-time setup (needs a repo admin, done once):

1. In the GitHub repo settings → Pages, set **Source** to "GitHub Actions"
   (the workflow handles the rest on every push to `master`).
2. In the `ayoung.ai` DNS zone (Squarespace, formerly Google Domains — the
   apex domain currently points at Squarespace's site builder, but
   subdomains can point elsewhere independently), add:

   ```
   CNAME   fgoac   ayoungco.github.io.
   ```

3. Back in GitHub Pages settings, set the custom domain to
   `fgoac.ayoung.ai` and enable "Enforce HTTPS" once DNS has propagated and
   GitHub has issued the certificate.

That's the only step that needed doing outside this repo — DNS record
creation requires access to the Squarespace domain panel, which isn't
available from here.

## Notes

- Contact addresses embedded in the original pages (`adamyoung@suscom.net`,
  `thefgs@nexuswebs.net`) were on now-defunct ISP/mail domains. They're kept
  struck-through for historical accuracy, with a current address
  (`adam@ayoung.co`) added alongside.
- The table-soup markup, `<font>` tags, and Dreamweaver-generated JS
  (`MM_preloadImages`) are left exactly as they were in 2004. Only the Flash
  embeds, the `../pages/` paths, one case-sensitivity mismatch
  (`Money.jpg` → `Money.JPG`), and the `index.htm` → `index.html` rename
  (static hosts don't serve `.htm` as a default document) were touched.
- The Google SiteSearch form, the `freehitcounters.net`/`oursql.net` hit
  counter, and other period third-party embeds on `index.htm` are left as
  historical artifacts — most no longer function, and that's fine.
