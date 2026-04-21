#!/usr/bin/env python3
"""Render all designs from content.yaml.

Outputs:
  index.html, jobs.html               — framer design (primary)
  magazine.html                        — editorial/magazine design
  designs.html                         — switcher landing

Each rendered page gets a floating design-switcher bar injected.
"""
import sys, pathlib, re
try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    sys.exit("pip install pyyaml jinja2")

ROOT = pathlib.Path(__file__).parent
DATA = yaml.safe_load((ROOT / "content.yaml").read_text())

# Load per-job YAML files from content/jobs/*.yaml
JOBS = []
jobs_dir = ROOT / "content" / "jobs"
if jobs_dir.exists():
    for f in sorted(jobs_dir.glob("*.yaml")):
        JOBS.append(yaml.safe_load(f.read_text()))
DATA["jobs"] = JOBS

# Registered designs: name → (template_dir, out_files)
DESIGNS = [
    {"name": "framer",   "label": "Framer",   "dir": "templates",        "files": ["index.html", "jobs.html"], "home": "/"},
    {"name": "main",     "label": "Main",     "dir": "designs/main",     "files": ["index.html"],               "home": "/main.html"},
    {"name": "magazine", "label": "Magazine", "dir": "designs/magazine", "files": ["index.html"],               "home": "/magazine.html"},
]

SWITCHER = """
<style>
.__design_switcher{display:none;position:fixed;top:12px;left:50%;transform:translateX(-50%);background:#111;color:#f7f2e8;padding:.35rem .5rem;border-radius:999px;font:500 13px/1 -apple-system,BlinkMacSystemFont,"Inter",sans-serif;z-index:2147483647;gap:.25rem;align-items:center;box-shadow:0 4px 16px rgba(0,0,0,.25)}
.__design_switcher.on{display:flex}
.__design_switcher>span{padding:.25rem .7rem;opacity:.55;letter-spacing:.08em;text-transform:uppercase;font-size:10px}
.__design_switcher a{color:inherit;text-decoration:none;padding:.35rem .8rem;border-radius:999px;transition:background .15s}
.__design_switcher a:hover{background:#2a2a2a}
.__design_switcher a.active{background:#f7f2e8;color:#111;font-weight:700}
</style>
<nav class="__design_switcher" id="__design_switcher">
  <span>Design</span>
  __LINKS__
</nav>
<script>(function(){if(new URLSearchParams(location.search).get('switcher')==='true'){var el=document.getElementById('__design_switcher');if(el){el.classList.add('on');document.querySelectorAll('#__design_switcher a').forEach(function(a){var u=new URL(a.href,location.origin);u.searchParams.set('switcher','true');a.href=u.pathname+u.search})}}})();</script>
""".strip()


def render_switcher(active_name):
    links = []
    for d in DESIGNS:
        cls = ' class="active"' if d["name"] == active_name else ""
        links.append(f'<a href="{d["home"]}"{cls}>{d["label"]}</a>')
    return SWITCHER.replace("__LINKS__", "\n  ".join(links))


def inject_switcher(html, active_name):
    """Insert switcher right after <body> (or <body ...>)."""
    snippet = render_switcher(active_name)
    m = re.search(r"<body[^>]*>", html)
    if not m:
        return snippet + html
    i = m.end()
    return html[:i] + "\n" + snippet + "\n" + html[i:]


def main():
    for d in DESIGNS:
        env = Environment(
            loader=FileSystemLoader(str(ROOT / d["dir"])),
            undefined=StrictUndefined,
            autoescape=False,
        )
        for fname in d["files"]:
            tpl = env.get_template(fname)
            out = tpl.render(**DATA)
            out = inject_switcher(out, d["name"])

            if d["name"] == "framer":
                dest = ROOT / fname            # root-level
            else:
                dest = ROOT / f'{d["name"]}.html'
            dest.write_text(out)
            print(f"  {d['name']:<9} → {dest.relative_to(ROOT)}  ({len(out):,} B)")

    # Job detail pages — render templates/job-detail.html once per YAML
    if JOBS:
        env = Environment(
            loader=FileSystemLoader(str(ROOT / "templates")),
            undefined=StrictUndefined,
            autoescape=False,
        )
        tpl = env.get_template("job-detail.html")
        for j in JOBS:
            ctx = dict(DATA)
            ctx["job"] = j
            ctx["other_jobs"] = [o for o in JOBS if o["slug"] != j["slug"]]
            out = tpl.render(**ctx)
            out = inject_switcher(out, "framer")
            dest = ROOT / "jobs" / j["slug"] / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(out)
            print(f"  job       → {dest.relative_to(ROOT)}  ({len(out):,} B)")

    # Switcher landing page
    cards = []
    for d in DESIGNS:
        cards.append(
            f'<a href="{d["home"]}" class="card"><div class="label">{d["label"]}</div></a>'
        )
    landing = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Designs — {DATA['site']['title']}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@900&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#f7f2e8;color:#111;font:18px/1.5 Inter,sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem;gap:3rem}}
h1{{font-family:Fraunces,serif;font-weight:900;font-size:clamp(3rem,8vw,6rem);letter-spacing:-.03em;text-align:center;margin:0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem;width:100%;max-width:960px}}
.card{{border:2px solid #111;padding:3rem 2rem;text-decoration:none;color:inherit;border-radius:12px;text-align:center;transition:transform .15s,background .15s}}
.card:hover{{transform:translateY(-2px);background:#111;color:#f7f2e8}}
.card .label{{font-family:Fraunces,serif;font-weight:900;font-size:2.2rem;letter-spacing:-.02em}}
</style>
</head>
<body>
<h1>Pick a design</h1>
<div class="grid">{''.join(cards)}</div>
</body>
</html>
"""
    (ROOT / "designs.html").write_text(landing)
    print(f"  landing   → designs.html")


if __name__ == "__main__":
    main()
