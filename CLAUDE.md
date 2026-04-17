# CLAUDE.md

Project notes for future Claude sessions working on this repo.

## What this is

Static landing page for Lucky Robots (luckyrobots.com). Originally a Framer
export. Now **content-driven**: all copy, people, jobs, and media refs live
in `content.yaml`; a Python build step renders Jinja2 templates into static
HTML. Multiple designs render from the same YAML.

- Primary deploy: **Cloudflare Pages** project `landing-page` → custom domain
  `staging.landingpage.luckyrobots.com` (subdomain `landing-page-r4b.pages.dev`).
- Assets (images, videos, fonts): **Cloudflare R2** bucket
  `landing-page-assets` → `landingpage.luckyrobots.com` (public R2 domain,
  proxied through Cloudflare).
- No backend. Nothing runs at request time.

## Architecture

```
content.yaml          ──┐
                        ├─► build.py ─► index.html
templates/index.html  ──┤             ─► jobs.html
templates/jobs.html   ──┤             ─► magazine.html
designs/magazine/     ──┘             ─► designs.html (switcher)
```

- `content.yaml`: single source of truth for all editable content.
- `templates/`: Framer-exported HTML with `{{ }}` + `{% for %}` interpolation.
- `designs/<name>/index.html`: alternate designs (self-contained HTML/CSS).
- `build.py`: reads YAML, renders each template, injects a **design switcher**
  pill at `<body>` top, writes output to repo root.
- `_site/` (CI only): copy of root HTML for Pages deploy.
- `assets/{images,videos,fonts}/`: local mirrors of R2 assets. Only changed
  files under `assets/` get uploaded to R2 on push (see deploy.yml).

## Local dev

```bash
pip install pyyaml jinja2           # once
python3 build.py                    # renders all designs
python3 -m http.server 8000         # serve at http://localhost:8000
# → http://localhost:8000/           (Framer)
# → http://localhost:8000/magazine.html
# → http://localhost:8000/designs.html (picker)
```

The switcher pill is **hidden by default**. Append `?switcher=true` to any
URL (local or deployed) to show it — e.g. `http://localhost:8000/?switcher=true`
or `https://staging.../magazine.html?switcher=true`. The query param is
preserved when clicking between designs.

## Deploy

Git push to `main` → GitHub Actions (`.github/workflows/deploy.yml`):

1. Checkout + setup Python 3.12
2. `pip install pyyaml jinja2 && python build.py`
3. Diff `assets/` against previous commit, upload changed files to R2 via
   `wrangler r2 object put`
4. Copy all root `*.html` to `_site/`
5. `wrangler pages deploy _site --project-name=landing-page`

Live in ~60s. Visible at `https://staging.landingpage.luckyrobots.com/`.

## Secrets / tokens

`.env` is **gitignored**. Live tokens (as of 2026-04):
- `CLOUDFLARE_API_TOKEN` — Pages write + R2 write (narrow scope)
- `CLOUDFLARE_DNS_API_TOKEN` — DNS edit for luckyrobots.com zone
- GitHub Actions uses `secrets.CLOUDFLARE_API_TOKEN` + `secrets.CLOUDFLARE_ACCOUNT_ID`.

For cache purge or DNS ops locally: load `.env` with `set -a; source .env; set +a`.

Zone ID for luckyrobots.com: `f7dff3097f29554c906d053285f9a244`.

## Adding a new design

1. **Create template**: `designs/<name>/index.html`
   - Jinja2 template, self-contained (inline CSS + Google Fonts OK).
   - Reference any `content.yaml` key: `{{ hero.headline_line1 }}`,
     `{% for m in team %}...{% endfor %}`, etc.
   - Guard optional media with `is defined`:
     `{% if hero.video is defined %}<video ...>{% endif %}` — StrictUndefined
     will raise on missing keys.
   - Use `features.list` (not `features.items` — `items` collides with
     dict's `.items()` method in Jinja).

2. **Register in `build.py`** — append to `DESIGNS` list:
   ```python
   {"name": "newname", "label": "New Name", "dir": "designs/newname",
    "files": ["index.html"], "home": "/newname.html"}
   ```

3. **Test**: `python3 build.py && python3 -m http.server 8000`

4. **Switcher pill** picks up the new design automatically. Framer design
   stays at root (`/`); all others live at `/<name>.html`.

Every design = one self-contained HTML file at repo root after build.

## Adding / removing team members or jobs

Edit `content.yaml`. No HTML changes needed.

```yaml
team:
  - { name: "NewPerson", role: "Title" }   # add / remove / reorder freely
```

Rebuild local (`python3 build.py`) to preview, or just push — CI builds.

## Content map (content.yaml → which fold)

| YAML key                 | Where it appears                                |
|--------------------------|-------------------------------------------------|
| `site` / `media`         | `<head>` tags (title, favicons, OG)            |
| `nav`                    | Top nav links (index + jobs)                    |
| `hero`                   | Fold 1 headline + subtitle + video              |
| `terminal`               | Boot-log overlay in hero (9 events)             |
| `hero_command`           | Command composer overlay                        |
| `carousel`               | Fold 2 "real-world messiness" (6 slides)        |
| `robotgpt`               | Fold 3 natural-language demo                    |
| `features`               | Fold 4 grid (4 cards, title+body+icon)          |
| `robots_showcase`        | Fold 5 heading                                  |
| `team_section` / `team`  | Fold 6 "People Behind Lucky Robots" (20)        |
| `advisors_section` / `advisors` | Fold 7 (6 people, optional URL)          |
| `open_positions` / `jobs_index` | Fold 8 (5 highlighted roles)             |
| `final_cta`              | Fold 9 "Get your robots ready"                  |
| `enterprise`             | Fold 10 classified                              |
| `footer.links`           | Fold 11 social links                            |
| `jobs_page`, `jobs_aiml`, `jobs_engine`, `harrison_callout`, `yan_callout`, `jobs_hiring` | jobs.html sections |

## Framer gotchas

Framer export is ~350KB of auto-generated CSS classes (`framer-xzy`,
`framer-styles-preset-abc`). Don't try to clean it. Targeted find-and-replace
via the Python transform scripts is the pattern.

- **Duplicated HTML for breakpoints**: most sections have `ssr-variant
  hidden-m0kyxy` wrappers — same text appears twice (desktop + mobile). Use
  `str.replace()` (replace all) for single-line text, targeted regex for
  repeats, template loops for lists.
- **Whitespace**: Framer sometimes doubles spaces ("Cut costs without
  cutting corners" has two spaces). Match exact HTML or the replace silently
  no-ops.
- **`<!--$-->` / `<!--/$-->` markers**: React SSR hydration markers. Leave
  them alone — removing breaks hydration on some slides.
- **Carousel autoplay**: 3 index-carousel + 2 jobs-page videos shipped
  without `autoplay`. Fixed by adding `autoplay=""` in the transform. If
  another Framer export overwrites templates, re-run the fix.

## Asset / R2 gotchas

- **16-byte `{"message":null}` placeholders**: original `download-assets.sh`
  fetched some URLs that returned Framer's error JSON. These images and
  videos look "broken" on the page. Detect: `find assets -size -100c` or
  curl `Content-Length: 16`. Fix: redownload from
  `https://framerusercontent.com/images/<hash>.<ext>` and re-upload to R2.
- **Re-upload to R2** (after local asset fix):
  ```bash
  set -a; source .env; set +a
  npx wrangler r2 object put "landing-page-assets/images/X.png" \
    --file=assets/images/X.png --content-type=image/png --remote
  ```
- **Cloudflare cache purge** (required after R2 replace):
  ```bash
  curl -X POST "https://api.cloudflare.com/client/v4/zones/f7dff3097f29554c906d053285f9a244/purge_cache" \
    -H "X-Auth-Email: dvrmysr@gmail.com" \
    -H "X-Auth-Key: <global-key-from-assets/.env>" \
    -H "Content-Type: application/json" \
    --data '{"hosts":["landingpage.luckyrobots.com"]}'
  ```
  The narrow `CLOUDFLARE_API_TOKEN` lacks cache-purge scope. Global key sits
  in `~/Projects/assets/.env` as `CLOUDFLARE_GLOBAL_API_KEY`.

## Testing

Skill `/test-everything` lives at `~/.claude/skills/test-everything/SKILL.md`.
Runs:
1. Asset integrity (404 + 16-byte placeholder detection)
2. Video autoplay audit
3. External link check
4. Playwright responsive (375 / 393 / 768 / 1440)
5. Spelling (aspell + common-typo regex)
6. HTML structural (dup IDs, missing alt)

Emits a markdown report with screenshots in `/tmp/test-everything/`. Does
**not** auto-fix.

Run after any content push to catch regressions.

## Common tasks — quick commands

```bash
# Rebuild everything
python3 build.py

# Preview locally
python3 -m http.server 8000

# Re-run test suite
# (invoke /test-everything skill, or:)
URL=https://staging.landingpage.luckyrobots.com node /tmp/test-responsive.mjs

# Find broken local assets (16-byte placeholders)
find assets -size -100c -type f

# HEAD-check every referenced URL
python3 -c "import re,subprocess; [print(subprocess.run(['curl','-sIL',u],capture_output=True,text=True).stdout.split()[1],u) for u in set(re.findall(r'https://landingpage\.luckyrobots\.com/[^\"\'\s)]+', open('index.html').read()))]"
```

## File structure

```
.
├── CLAUDE.md                        # you are here
├── content.yaml                     # ALL editable content (edit this)
├── build.py                         # YAML → HTML renderer
├── templates/
│   ├── index.html                   # Framer template (Jinja2)
│   └── jobs.html
├── designs/
│   └── magazine/
│       └── index.html               # Morning Edition design
├── index.html, jobs.html,           # ← built output (do not edit by hand)
│   magazine.html, designs.html
├── assets/
│   ├── images/                      # mirrors R2 bucket
│   ├── videos/
│   └── fonts/
├── .github/workflows/deploy.yml     # GH Actions → CF Pages + R2
├── .env                             # tokens (gitignored)
├── download-assets.sh               # initial Framer asset scrape
└── luckyrobots-com/                 # original scraped site (reference)
```

## History / why-this-is-the-way-it-is

- Site started as a raw Framer export (`index.html`, `jobs.html` hand-placed).
- **2026-04**: swapped to YAML-driven templating so non-devs can add/remove
  team members by editing one YAML file. Framer HTML kept as-is; only the
  editable bits were turned into Jinja interpolation points.
- Magazine design added as a proof that the same YAML can drive a totally
  different visual (editorial/magazine vs Framer landing page).
- Staging cert for `staging.landingpage.luckyrobots.com` issued via Pages
  custom-domain + DNS CNAME → `landing-page-r4b.pages.dev`.

## When in doubt

1. `python3 build.py` — if this fails, fix YAML / template; everything else
   downstream is automated.
2. Check `/test-everything` output before pushing.
3. Don't modify `index.html` / `jobs.html` / `magazine.html` directly —
   those are build output. Edit `content.yaml` or `templates/` / `designs/`.
