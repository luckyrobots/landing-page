# Lucky Robots — landing page

The source for **[luckyrobots.com](https://luckyrobots.com)**.

- **One file owns all the content** → [`content.yaml`](./content.yaml)
- **Edit the YAML, commit, push, site updates automatically in about 60 seconds.** No HTML needed.
- Same content can render as **multiple designs** (framer, magazine, …).

---

## The 60-second overview

```
content.yaml          ─┐
(copy, people, jobs,   │
 logos, videos, ...)   │                            ┌─► luckyrobots.com
                       ├─► python build.py ─► HTML ─┼─► www.luckyrobots.com
templates/ (framer)    │       (via Jinja2)         └─► staging.landingpage…
designs/magazine/     ─┘
```

Push to `main` → GitHub Actions → fast integrity test → Cloudflare Pages deploy. Live in ~60s on all three domains.

---

## Edit the site (no code)

Everything visible on the site lives in [`content.yaml`](./content.yaml). Open it in the GitHub web editor (pencil icon), change a value, commit. That's it.

### Add a team member

```yaml
team:
  - { name: "Devrim",  role: "Founder & CEO" }
  - { name: "NewHire", role: "Senior Engineer" }   # ← add a line
```

### Remove a team member → delete the line.

### Add a job posting

```yaml
jobs_index:
  - title:    "Senior ML Engineer"
    type:     "Full Time"
    location: "Remote, Worldwide"
    url:      "./jobs/senior-ml-engineer"
```

### Add a full job detail page (at `/jobs/<slug>/`)

Easiest way — invoke the **`/add-a-job`** skill in Claude Code. It will
ask for title, type, location, slug, category, and the four body sections
(about / responsibilities / qualifications / bonus), then write the YAML,
update `content.yaml`, run a local build, and offer to commit + push.

Or do it by hand — create `content/jobs/<slug>.yaml`:

```yaml
slug: senior-ml-engineer
title: "Senior ML Engineer"
type: "Full Time"
location: "Remote, Worldwide"

about:
  - "One or more paragraphs about the role."

responsibilities:
  - "What the hire will do day-to-day"
  - "..."

qualifications:
  - "Required skill"
  - "..."

bonus:
  - "Nice-to-have"
  - "..."
```

`build.py` picks up every `content/jobs/*.yaml` and renders a full detail page at `/jobs/<slug>/` using `templates/job-detail.html`. You never touch HTML.

Also add the role's summary to `jobs_index` (or `jobs_aiml` / `jobs_engine`) in `content.yaml` so it appears on the homepage and /jobs listing.

### Swap the hero headline, subtitle, video, logos

Search `content.yaml` for the field. Change the string or URL. Commit.

### What happens next

1. Push triggers [GitHub Actions](https://github.com/luckyrobots/landing-page/actions)
2. CI runs tests — **if a video is broken, a link is dead, or an image returns a 16-byte Framer placeholder, the deploy is blocked.**
3. If green, [luckyrobots.com](https://luckyrobots.com) updates.

Broken push? `git revert HEAD && git push`, or instant rollback from the [Cloudflare Pages dashboard](https://dash.cloudflare.com/) (Deployments → `⋯` → Rollback).

---

## Preview locally

```bash
pip install pyyaml jinja2
python3 build.py
python3 -m http.server 8000
# → http://localhost:8000
# → http://localhost:8000/magazine.html
# → http://localhost:8000/designs.html   (picker)
```

Add `?switcher=true` to any URL to show the floating design switcher.

---

## Add a new design

Every design = one self-contained HTML file, rendered from the same YAML.

1. Create `designs/<name>/index.html` — a Jinja2 template. Reference any content.yaml key (`{{ hero.headline_line1 }}`, `{% for m in team %}…{% endfor %}`).
2. Register it in `build.py` — add to the `DESIGNS` list.
3. `python3 build.py` → outputs `<name>.html` at root + adds it to the switcher.

See [`designs/magazine/index.html`](./designs/magazine/index.html) for a worked example (editorial magazine, ~200 lines, zero deps beyond Google Fonts).

---

## Repository layout

```
content.yaml           ALL editable content (YOU EDIT THIS)
build.py               YAML → HTML renderer (Jinja2)
templates/             Framer-exported HTML, edit only if adding new content keys
designs/<name>/        Alternate designs
index.html, jobs.html, *.html   ← build output, regenerated on every push
assets/                images + videos + fonts (mirrored to Cloudflare R2)
jobs/<slug>/           job detail pages
contact/, enterprise/  contact + enterprise detail pages
.github/workflows/     CI: build → test → deploy
CLAUDE.md              deep architecture notes for engineers / future sessions
```

---

## How tests protect the site

Every push runs a fast integrity check against the built `_site/` directory:

- Every HTML file parses and has real content
- No unrendered Jinja tags escaped into output
- Every internal link (`/jobs/…`, `/contact`, …) returns 200
- Every asset URL on `landingpage.luckyrobots.com` returns 200 **and more than 100 bytes** — catches the 16-byte `{"message":null}` Framer placeholder that we've been bitten by before

If any check fails, the deploy step never runs. Current prod stays live.

See [`CLAUDE.md`](./CLAUDE.md) for the deep version.

---

## Need help?

- **Engineering notes / gotchas**: [`CLAUDE.md`](./CLAUDE.md)
- **CI logs**: [GitHub Actions](https://github.com/luckyrobots/landing-page/actions)
- **Deploys & rollbacks**: Cloudflare Pages dashboard, project `landing-page`
