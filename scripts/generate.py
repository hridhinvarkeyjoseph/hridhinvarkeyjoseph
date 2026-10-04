#!/usr/bin/env python3
"""Draw the profile's cards from GitHub's own data.

assets/hero.svg       an orbit of every project I have sent a pull request to,
                      a typed-out intro, live stats and a ticker of my PRs.
assets/telemetry.svg  what my PRs changed: lines by language, per project,
                      and how much of it is tests.
assets/timeline.svg   every PR as a capsule from opened to merged (or now).
assets/pulls.svg      the log: each PR, its status, size and time to merge.

Standard library only. In GitHub Actions it reads GITHUB_TOKEN; locally,
PULLS_JSON=sample.json renders from a saved answer instead.
"""

import json
import math
import os
import random
import re
import statistics
import urllib.request
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

USER = os.environ.get("PROFILE_USER", "hridhinvarkeyjoseph")
NAME = "Hridhin Varkey Joseph"
SCHOOL = "Newton School of Technology · S-VYASA"
GOAL = 10  # the DevForge "10 PR Journey"
OUT = Path(__file__).resolve().parent.parent / "assets"

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
BG, BG2, PANEL, LINE, TEXT, MUTED, DIM = (
    "#070a12", "#0c1220", "#101828", "#1f2a40", "#e6edf3", "#8592ad", "#4a5672")
MINE = "#f5a623"
ADD, DEL = "#3fb950", "#f85149"
STATUS = {"merged": "#a371f7", "open": "#3fb950", "closed": "#f85149"}
LANG_COLOR = {
    "Shell": "#89e051", "TypeScript": "#4d8eff", "JavaScript": "#f1e05a",
    "Markdown": "#9aa7c0", "JSON": "#ff8a3d", "Config": "#2dd4bf",
    "YAML": "#f472b6", "Python": "#60a5fa", "Other": "#64748b",
}


# ================================================================ data

def api(path):
    req = urllib.request.Request("https://api.github.com/" + path)
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch():
    q = f"author:{USER}+type:pr+-user:{USER}"
    items = api(f"search/issues?q={q}&sort=created&order=desc&per_page=100")["items"]
    repos, pulls = {}, []
    for it in items:
        repo = it["repository_url"].split("/repos/")[1]
        if repo not in repos:
            info = api("repos/" + repo)
            repos[repo] = {"stars": info["stargazers_count"], "language": info.get("language")}
        pr = api(f"repos/{repo}/pulls/{it['number']}")
        files = api(f"repos/{repo}/pulls/{it['number']}/files?per_page=100")
        pulls.append({
            "repo": repo,
            "number": it["number"],
            "title": it["title"],
            "status": "merged" if pr.get("merged_at") else pr["state"],
            "created": pr["created_at"],
            "merged": pr.get("merged_at"),
            "files": [[f["filename"], f["additions"], f["deletions"]] for f in files],
        })
    return {"repos": repos, "pulls": pulls, "now": None}


def load():
    sample = os.environ.get("PULLS_JSON")
    data = json.loads(Path(sample).read_text()) if sample else fetch()
    now = data.get("now")
    now = ts(now) if now else datetime.now(timezone.utc)
    for p in data["pulls"]:
        p["title"] = " ".join(p["title"].split())
        p["adds"] = sum(f[1] for f in p["files"])
        p["dels"] = sum(f[2] for f in p["files"])
    return data["pulls"], data["repos"], now


# ================================================================ helpers

def ts(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def kstars(n):
    if n >= 1000:
        return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    return str(n)


def clip(text, n):
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def span(hours):
    if hours < 1:
        return f"{max(1, round(hours * 60))}m"
    if hours < 48:
        return f"{hours:.0f}h"
    return f"{hours / 24:.0f}d"


def short(repo):
    return repo.split("/")[1]


TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec)/|\.(test|spec)\.|_test\.")
EXT = {
    "sh": "Shell", "bash": "Shell", "zsh": "Shell", "ts": "TypeScript", "tsx": "TypeScript",
    "js": "JavaScript", "mjs": "JavaScript", "cjs": "JavaScript", "jsx": "JavaScript",
    "md": "Markdown", "mdx": "Markdown", "json": "JSON", "yml": "YAML", "yaml": "YAML",
    "py": "Python", "example": "Config", "env": "Config", "toml": "Config",
}


def language(path, repo_lang):
    base = path.rsplit("/", 1)[-1]
    if "." not in base.lstrip("."):
        return "Shell" if repo_lang == "Shell" else "Other"
    return EXT.get(base.rsplit(".", 1)[1].lower(), "Other")


def svg(width, height, body, title, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><defs>{defs}</defs>{body}</svg>\n"
    )


def frame(W, H, label):
    """Card background, faint grid and a window bar."""
    return (
        f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>'
        f'<rect width="{W}" height="{H}" rx="14" fill="url(#grid)"/>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LINE}"/>'
        f'<g class="mono"><circle cx="24" cy="22" r="5" fill="#ff5f57"/><circle cx="41" cy="22" r="5" fill="#febc2e"/>'
        f'<circle cx="58" cy="22" r="5" fill="#28c840"/>'
        f'<text x="{W / 2}" y="26" font-size="11.5" text-anchor="middle" fill="{MUTED}">{escape(label)}</text></g>'
        f'<line x1="0" y1="42" x2="{W}" y2="42" stroke="{LINE}"/>'
    )


GRID = (f'<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<path d="M24 0H0V24" fill="none" stroke="{LINE}" stroke-width=".5" opacity=".45"/></pattern>')
BASE_CSS = f""".mono{{font-family:{MONO}}}
.in{{opacity:0;animation:in .6s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}"""


def summary(pulls, repos):
    merged = [p for p in pulls if p["status"] == "merged"]
    hours = [(ts(p["merged"]) - ts(p["created"])).total_seconds() / 3600 for p in merged if p.get("merged")]
    return {
        "n": len(pulls),
        "merged": len(merged),
        "repos": len({p["repo"] for p in pulls}),
        "reach": sum(r["stars"] for r in repos.values()),
        "adds": sum(p["adds"] for p in pulls),
        "dels": sum(p["dels"] for p in pulls),
        "files": len({(p["repo"], f[0]) for p in pulls for f in p["files"]}),
        "median": statistics.median(hours) if hours else None,
    }


# ================================================================ hero

def typed(x, y, text, start, size, fill, weight="400", per=0.045):
    """Text that types itself out, one character at a time."""
    out = [f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" class="mono">']
    for i, ch in enumerate(text):
        out.append(f'<tspan class="ch" style="animation-delay:{start + i * per:.3f}s">{escape(ch)}</tspan>')
    out.append("</text>")
    return "".join(out), start + len(text) * per


def hero(pulls, repos, now):
    W, H = 900, 420
    s = summary(pulls, repos)
    rng = random.Random(7)

    defs = GRID + f"""
<radialGradient id="glow" cx="72%" cy="42%" r="45%"><stop offset="0" stop-color="#1b2a55" stop-opacity=".9"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<radialGradient id="core" cx="40%" cy="35%"><stop offset="0" stop-color="#ffe2a8"/><stop offset=".45" stop-color="{MINE}"/><stop offset="1" stop-color="#b45309"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="{MINE}" stop-opacity=".55"/><stop offset="1" stop-color="{MINE}" stop-opacity="0"/></radialGradient>
<linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="{STATUS['merged']}"/><stop offset="1" stop-color="#e879f9"/></linearGradient>
<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="{BG}"/><stop offset=".06" stop-color="{BG}" stop-opacity="0"/><stop offset=".94" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<clipPath id="tick"><rect x="1" y="{H - 44}" width="{W - 2}" height="43"/></clipPath>
<style>{BASE_CSS}
.ch{{opacity:0;animation:show .01s linear forwards}}
@keyframes show{{to{{opacity:1}}}}
.cursor{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.tw{{animation:tw 3s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.9}}}}
.spin{{transform-box:fill-box;transform-origin:center;animation:spin 14s linear infinite}}
.spin.r{{animation-duration:22s;animation-direction:reverse}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.grow{{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:grow 1.6s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes grow{{to{{transform:scaleX(1)}}}}
.ticker{{animation:roll var(--d) linear infinite}}
@keyframes roll{{to{{transform:translateX(var(--l))}}}}
</style>"""

    o = [frame(W, H, f"~/{USER} — zsh — upstream"),
         f'<rect x="1" y="43" width="{W - 2}" height="{H - 88}" fill="url(#glow)"/>']

    # starfield
    for _ in range(70):
        x, y = rng.uniform(440, W - 10), rng.uniform(50, H - 52)
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.choice([.6, .8, 1, 1.3]):.1f}" fill="#c7d2fe" '
                 f'class="tw" style="animation-delay:{rng.uniform(0, 3):.2f}s"/>')

    # ---- left: the typed intro
    t, at = typed(36, 78, "~ $ whoami", .3, 13, MUTED)
    o.append(t)
    t, at = typed(36, 116, NAME, at + .25, 28, TEXT, "700", .05)
    o.append(t)
    o.append(f'<text x="{36 + len(NAME) * 16.9:.0f}" y="116" font-size="28" fill="{MINE}" class="mono cursor">▋</text>')
    o.append(f'<g class="mono in" style="animation-delay:{at + .1:.2f}s">'
             f'<text x="36" y="142" font-size="13" fill="{MINE}">CS student · {escape(SCHOOL)}</text>'
             f'<text x="36" y="163" font-size="12.5" fill="{MUTED}">I read big codebases and send fixes upstream.</text></g>')
    t, at2 = typed(36, 198, "~ $ git log --upstream --stat", at + .5, 13, MUTED, per=.03)
    o.append(t)

    # stat tiles, 2 x 2
    tiles = [
        (f"{s['merged']}/{GOAL}", "10 PR Journey merged", STATUS["merged"]),
        (str(s["n"]), f"PRs to {s['repos']} projects", ADD),
        (f"+{s['adds']}", f"lines in · −{s['dels']} out", ADD),
        (f"{kstars(s['reach'])}★", "stars on what I touched", MINE),
    ]
    for i, (big, small, color) in enumerate(tiles):
        x, y = 36 + (i % 2) * 196, 214 + (i // 2) * 74
        d = at2 + .1 + i * .12
        o.append(f'<g class="mono in" style="animation-delay:{d:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="184" height="62" rx="10" fill="{PANEL}" fill-opacity=".85" stroke="{LINE}"/>'
                 f'<rect x="{x}" y="{y}" width="3" height="62" rx="1.5" fill="{color}"/>'
                 f'<text x="{x + 16}" y="{y + 30}" font-size="22" font-weight="700" fill="{TEXT}">{escape(big)}</text>'
                 f'<text x="{x + 16}" y="{y + 49}" font-size="11" fill="{MUTED}">{escape(small)}</text></g>')
        if i == 0:  # journey progress inside the first tile
            w = 150 * min(s["merged"], GOAL) / GOAL
            o.append(f'<rect x="{x + 16}" y="{y + 54}" width="150" height="3" rx="1.5" fill="{LINE}"/>'
                     f'<rect x="{x + 16}" y="{y + 54}" width="{w:.0f}" height="3" rx="1.5" fill="url(#bar)" class="grow" style="animation-delay:{d + .3:.2f}s"/>')

    # ---- right: the orbit
    cx, cy = 690, 192
    stats = {}
    for p in pulls:
        r = stats.setdefault(p["repo"], {"n": 0, "merged": 0})
        r["n"] += 1
        r["merged"] += p["status"] == "merged"
    order = sorted(stats, key=lambda r: -repos.get(r, {}).get("stars", 0))[:8]
    rings = [(78, 20), (126, 32), (172, 46)]
    for rx, _ in rings:
        ry = rx * .40
        o.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry:.1f}" fill="none" stroke="{LINE}" stroke-width="1.2" stroke-dasharray="2 5"/>')

    # the core: me
    o.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="url(#halo)"/>')
    for k in range(3):
        o.append(f'<circle cx="{cx}" cy="{cy}" r="20" fill="none" stroke="{MINE}" stroke-width="1.2">'
                 f'<animate attributeName="r" from="22" to="70" dur="3.6s" begin="{k * 1.2}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" from=".7" to="0" dur="3.6s" begin="{k * 1.2}s" repeatCount="indefinite"/></circle>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="30" fill="none" stroke="{MINE}" stroke-width="1" stroke-dasharray="3 6" class="spin"/>'
             f'<circle cx="{cx}" cy="{cy}" r="36" fill="none" stroke="{MINE}" stroke-opacity=".4" stroke-width="1" stroke-dasharray="14 10" class="spin r"/>'
             f'<circle cx="{cx}" cy="{cy}" r="22" fill="url(#core)"/>'
             f'<text x="{cx}" y="{cy + 5}" font-size="13" font-weight="800" text-anchor="middle" fill="#1a1205" class="mono">HVJ</text>')

    for i, repo in enumerate(order):
        rx, dur = rings[2 - i % 3]
        ry = rx * .40
        phase = (i // 3) * .5 + (i % 3) * .29
        info, st = repos.get(repo, {"stars": 0}), stats[repo]
        color = STATUS["merged"] if st["merged"] == st["n"] else STATUS["open"]
        r = 5 + 2.1 * math.log10(info["stars"] + 1)
        path = f"M{cx - rx},{cy} a{rx},{ry:.1f} 0 1,0 {2 * rx},0 a{rx},{ry:.1f} 0 1,0 {-2 * rx},0"
        part = ""
        if 0 < st["merged"] < st["n"]:  # some merged, some in review: a split ring
            frac = st["merged"] / st["n"]
            c = 2 * math.pi * (r + 3)
            part = (f'<circle r="{r + 3:.1f}" fill="none" stroke="{STATUS["open"]}" stroke-width="2"/>'
                    f'<circle r="{r + 3:.1f}" fill="none" stroke="{STATUS["merged"]}" stroke-width="2" '
                    f'stroke-dasharray="{c * frac:.1f} {c:.1f}" transform="rotate(-90)"/>')
        o.append(
            f'<g><animateMotion dur="{dur}s" begin="-{phase * dur:.2f}s" repeatCount="indefinite" path="{path}"/>'
            f'<circle r="{r + 7:.1f}" fill="{color}" opacity=".16"/>{part}'
            f'<circle r="{r:.1f}" fill="{BG2}" stroke="{color}" stroke-width="2"/>'
            f'<text y="4" font-size="10" font-weight="700" text-anchor="middle" fill="{color}" class="mono">{st["n"]}</text>'
            f'<text y="{-r - 9:.0f}" font-size="10.5" font-weight="700" text-anchor="middle" fill="{TEXT}" class="mono">{escape(clip(short(repo), 15))}</text>'
            f'<text y="{r + 15:.0f}" font-size="9.5" text-anchor="middle" fill="{MUTED}" class="mono">{kstars(info["stars"])}★</text></g>'
        )

    o.append(f'<g class="mono" font-size="10.5" fill="{MUTED}">'
             f'<circle cx="{W - 236}" cy="{H - 62}" r="4" fill="{STATUS["merged"]}"/><text x="{W - 228}" y="{H - 58}">merged</text>'
             f'<circle cx="{W - 170}" cy="{H - 62}" r="4" fill="{STATUS["open"]}"/><text x="{W - 162}" y="{H - 58}">in review</text>'
             f'<text x="{W - 92}" y="{H - 58}">n = PRs</text></g>')

    # ---- bottom: a ticker of every PR
    items = []
    for p in pulls:
        mark = {"merged": "✔ merged", "open": "◷ review", "closed": "✕ closed"}.get(p["status"], p["status"])
        items.append((mark, STATUS.get(p["status"], MUTED), f'{short(p["repo"])}#{p["number"]}', clip(p["title"], 60)))
    chars = sum(len(a) + len(b) + len(c) + 12 for a, _, b, c in items)
    L = round(chars * 7.2)

    def strip(x0):
        parts = [f'<text x="{x0}" y="{H - 17}" font-size="12" class="mono" textLength="{L}" lengthAdjust="spacing">']
        for mark, color, ref, title in items:
            parts.append(f'<tspan fill="{color}">{escape(mark)}  </tspan><tspan fill="{MINE}">{escape(ref)}  </tspan>'
                         f'<tspan fill="{MUTED}">{escape(title)}   ✦   </tspan>')
        parts.append("</text>")
        return "".join(parts)

    o.append(f'<line x1="0" y1="{H - 44}" x2="{W}" y2="{H - 44}" stroke="{LINE}"/>'
             f'<rect x="1" y="{H - 43}" width="{W - 2}" height="42" fill="{BG2}"/>'
             f'<g clip-path="url(#tick)"><g class="ticker" style="--d:{L / 38:.0f}s;--l:-{L}px">{strip(24)}{strip(24 + L)}</g></g>'
             f'<rect x="1" y="{H - 43}" width="{W - 2}" height="42" fill="url(#edge)"/>'
             f'<rect x="12" y="{H - 33}" width="44" height="22" rx="5" fill="{MINE}"/>'
             f'<text x="34" y="{H - 18}" font-size="11" font-weight="800" text-anchor="middle" fill="#1a1205" class="mono">LIVE</text>')

    return svg(W, H, "".join(o), f"{NAME}: {s['n']} pull requests to {s['repos']} projects, {s['merged']} merged", defs)


# ================================================================ telemetry

def arc(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    big = 1 if a1 - a0 > math.pi else 0
    return f"M{x0:.1f},{y0:.1f} A{r},{r} 0 {big},1 {x1:.1f},{y1:.1f}"


def telemetry(pulls, repos):
    W, H = 900, 300
    s = summary(pulls, repos)
    langs, tests, per = {}, 0, {}
    for p in pulls:
        lang_of_repo = repos.get(p["repo"], {}).get("language")
        rp = per.setdefault(p["repo"], [0, 0])
        rp[0] += p["adds"]
        rp[1] += p["dels"]
        for path, a, d in p["files"]:
            lg = language(path, lang_of_repo)
            langs[lg] = langs.get(lg, 0) + a + d
            if TEST_PATH.search(path) or path.startswith("test/") or "/test/" in path:
                tests += a
    total = sum(langs.values()) or 1
    test_share = tests / (s["adds"] or 1)

    defs = GRID + f"""<style>{BASE_CSS}
.seg{{animation:draw 1.2s cubic-bezier(.3,.7,.2,1) forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
.grow{{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:grow 1.2s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes grow{{to{{transform:scaleX(1)}}}}
.needle{{transform-origin:792px 196px;animation:swing 1.8s cubic-bezier(.3,1.4,.4,1) forwards;transform:rotate(-90deg)}}
@keyframes swing{{to{{transform:rotate({-90 + 180 * test_share:.1f}deg)}}}}
</style>"""
    o = [frame(W, H, "git diff --stat upstream")]

    # section titles
    for x, label in [(36, "LINES CHANGED, BY LANGUAGE"), (380, "PER PROJECT"), (712, "HOW MUCH IS TESTS")]:
        o.append(f'<text x="{x}" y="70" font-size="10.5" letter-spacing="1.5" fill="{DIM}" class="mono">{label}</text>')

    # donut
    dx, dy, R = 118, 170, 68
    o.append(f'<circle cx="{dx}" cy="{dy}" r="{R}" fill="none" stroke="{PANEL}" stroke-width="18"/>')
    a = -math.pi / 2
    ranked = sorted(langs.items(), key=lambda kv: -kv[1])
    for i, (lg, n) in enumerate(ranked):
        frac = n / total
        a1 = a + frac * 2 * math.pi - 0.03
        length = R * max(a1 - a, 0.001)
        o.append(f'<path d="{arc(dx, dy, R, a, a1)}" fill="none" stroke="{LANG_COLOR.get(lg, LANG_COLOR["Other"])}" stroke-width="18" '
                 f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}" class="seg" style="animation-delay:{.2 + i * .18:.2f}s"/>')
        a += frac * 2 * math.pi
    o.append(f'<g class="mono" text-anchor="middle"><text x="{dx}" y="{dy - 2}" font-size="20" font-weight="700" fill="{ADD}">+{s["adds"]}</text>'
             f'<text x="{dx}" y="{dy + 18}" font-size="13" fill="{DEL}">−{s["dels"]}</text></g>')
    for i, (lg, n) in enumerate(ranked[:6]):
        y = 104 + i * 22
        o.append(f'<g class="mono in" font-size="11.5" style="animation-delay:{.3 + i * .1:.2f}s">'
                 f'<rect x="214" y="{y - 9}" width="10" height="10" rx="2" fill="{LANG_COLOR.get(lg, LANG_COLOR["Other"])}"/>'
                 f'<text x="232" y="{y}" fill="{TEXT}">{escape(lg)}</text>'
                 f'<text x="340" y="{y}" text-anchor="end" fill="{MUTED}">{100 * n / total:.0f}%</text></g>')

    # per project bars
    rows = sorted(per.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:6]
    peak = max((a + d for a, d in per.values()), default=1) or 1
    for i, (repo, (a_, d_)) in enumerate(rows):
        y = 100 + i * 28
        w_a, w_d = 150 * a_ / peak, 150 * d_ / peak
        o.append(f'<g class="mono" font-size="11.5"><text x="380" y="{y + 4}" fill="{MINE}">{escape(clip(short(repo), 14))}</text>'
                 f'<rect x="490" y="{y - 6}" width="150" height="12" rx="3" fill="{PANEL}"/>'
                 f'<rect x="490" y="{y - 6}" width="{max(w_a, 2):.1f}" height="12" rx="3" fill="{ADD}" class="grow" style="animation-delay:{.3 + i * .1:.2f}s"/>'
                 f'<rect x="{490 + w_a:.1f}" y="{y - 6}" width="{w_d:.1f}" height="12" rx="0" fill="{DEL}" class="grow" style="animation-delay:{.5 + i * .1:.2f}s"/>'
                 f'<text x="648" y="{y + 4}" font-size="10.5" fill="{MUTED}"><tspan fill="{ADD}">+{a_}</tspan> <tspan fill="{DEL}">−{d_}</tspan></text></g>')

    # test gauge
    gx, gy, gr = 792, 196, 66
    o.append(f'<path d="{arc(gx, gy, gr, math.pi, 2 * math.pi)}" fill="none" stroke="{PANEL}" stroke-width="14" stroke-linecap="round"/>')
    length = gr * math.pi * test_share
    o.append(f'<path d="{arc(gx, gy, gr, math.pi, 2 * math.pi)}" fill="none" stroke="{STATUS["merged"]}" stroke-width="14" stroke-linecap="round" '
             f'stroke-dasharray="{length:.1f} 999" stroke-dashoffset="{length:.1f}" class="seg" style="animation-delay:.4s"/>')
    for k in range(11):
        ang = math.pi + k * math.pi / 10
        x0, y0 = gx + (gr - 16) * math.cos(ang), gy + (gr - 16) * math.sin(ang)
        x1, y1 = gx + (gr - 11) * math.cos(ang), gy + (gr - 11) * math.sin(ang)
        o.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{DIM}"/>')
    o.append(f'<g class="needle"><line x1="{gx}" y1="{gy}" x2="{gx}" y2="{gy - gr + 22}" stroke="{TEXT}" stroke-width="2.5" stroke-linecap="round"/></g>'
             f'<circle cx="{gx}" cy="{gy}" r="6" fill="{TEXT}"/>'
             f'<g class="mono" text-anchor="middle"><text x="{gx}" y="{gy + 30}" font-size="24" font-weight="700" fill="{TEXT}">{100 * test_share:.0f}%</text>'
             f'<text x="{gx}" y="{gy + 48}" font-size="11" fill="{MUTED}">of added lines are tests</text></g>')

    # footer facts
    med = span(s["median"]) if s["median"] is not None else "—"
    facts = [f"{s['files']} files touched", f"median time to merge {med}", f"{s['repos']} codebases", f"{len(langs)} languages"]
    o.append(f'<line x1="24" y1="{H - 36}" x2="{W - 24}" y2="{H - 36}" stroke="{LINE}"/>')
    o.append(f'<text x="{W / 2}" y="{H - 14}" font-size="11.5" text-anchor="middle" fill="{MUTED}" class="mono">'
             + '<tspan fill="#3a4560">  ·  </tspan>'.join(escape(f) for f in facts) + "</text>")
    return svg(W, H, "".join(o), f"+{s['adds']} −{s['dels']} lines upstream, {100 * test_share:.0f}% tests", defs)


# ================================================================ timeline

def timeline(pulls, now):
    W, X0, X1 = 900, 170, 860
    by_repo = {}
    for p in sorted(pulls, key=lambda p: p["created"]):
        by_repo.setdefault(p["repo"], []).append(p)

    # pack each repo's PRs into as few rows as possible
    lanes = []
    for repo, ps in by_repo.items():
        rows = []
        for p in ps:
            start, end = ts(p["created"]), ts(p["merged"]) if p.get("merged") else now
            for row in rows:
                if row[-1][1] + timedelta(hours=6) < start:
                    row.append((p, end))
                    break
            else:
                rows.append([(p, end)])
        lanes.append((repo, rows))

    t0 = min(ts(p["created"]) for p in pulls).replace(hour=0, minute=0, second=0)
    t1 = max(now, t0 + timedelta(days=1))
    span_s = (t1 - t0).total_seconds()

    def X(t):
        return X0 + (X1 - X0) * (t - t0).total_seconds() / span_s

    top, rowh = 92, 22
    H = top + sum(len(r) * rowh + 14 for _, r in lanes) + 46

    defs = GRID + f"""
<pattern id="stripe" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="8" height="8" fill="{STATUS['open']}" fill-opacity=".18"/><rect width="3" height="8" fill="{STATUS['open']}" fill-opacity=".55"/>
<animateTransform attributeName="patternTransform" type="translate" from="0 0" to="8 0" dur="0.8s" additive="sum" repeatCount="indefinite"/></pattern>
<style>{BASE_CSS}
.grow{{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:grow 1s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes grow{{to{{transform:scaleX(1)}}}}
.ping{{transform-box:fill-box;transform-origin:center;animation:ping 1.8s ease-out infinite}}
@keyframes ping{{from{{opacity:.8;transform:scale(1)}}to{{opacity:0;transform:scale(3)}}}}
</style>"""
    o = [frame(W, H, "git log --graph --since=journey-start")]

    # day grid
    days = (t1 - t0).days + 1
    every = max(1, math.ceil(days / 12))
    for d in range(0, days + 1):
        t = t0 + timedelta(days=d)
        if t > t1:
            break
        x = X(t)
        o.append(f'<line x1="{x:.1f}" y1="{top - 18}" x2="{x:.1f}" y2="{H - 40}" stroke="{LINE}" stroke-width="{1 if d % every == 0 else .4}"/>')
        if d % every == 0:
            o.append(f'<text x="{x:.1f}" y="{top - 24}" font-size="10" text-anchor="middle" fill="{DIM}" class="mono">{t.strftime("%b %d")}</text>')

    y = top
    k = 0
    for li, (repo, rows) in enumerate(lanes):
        lane_h = len(rows) * rowh + 14
        if li % 2 == 0:
            o.append(f'<rect x="12" y="{y - 7}" width="{W - 24}" height="{lane_h}" rx="6" fill="{PANEL}" fill-opacity=".45"/>')
        o.append(f'<text x="28" y="{y + 4 + (len(rows) - 1) * rowh / 2 + 6:.0f}" font-size="12" fill="{MINE}" class="mono">{escape(clip(short(repo), 16))}</text>')
        for ri, row in enumerate(rows):
            cy = y + ri * rowh + 10
            for p, end in row:
                xa, xb = X(ts(p["created"])), X(end)
                w = max(xb - xa, 12)
                merged = p["status"] == "merged"
                fill = STATUS["merged"] if merged else "url(#stripe)"
                stroke = STATUS["merged"] if merged else STATUS["open"]
                o.append(f'<g class="mono"><rect x="{xa:.1f}" y="{cy - 7}" width="{w:.1f}" height="14" rx="7" fill="{fill}" '
                         f'stroke="{stroke}" class="grow" style="animation-delay:{.15 + k * .08:.2f}s"/>'
                         f'<circle cx="{xa:.1f}" cy="{cy}" r="3" fill="{TEXT}"/>')
                if merged:
                    o.append(f'<circle cx="{xa + w:.1f}" cy="{cy}" r="4.5" fill="{BG}" stroke="{STATUS["merged"]}" stroke-width="2"/>')
                hours = ((ts(p["merged"]) if merged else now) - ts(p["created"])).total_seconds() / 3600
                label = f'#{p["number"]} · {"merged in " if merged else "open "}{span(hours)}'
                lx = xa + w + 9
                anchor = "start"
                if lx + len(label) * 6.2 > W - 14:
                    lx, anchor = xa - 8, "end"
                o.append(f'<text x="{lx:.1f}" y="{cy + 4}" font-size="10.5" text-anchor="{anchor}" fill="{MUTED}">{escape(label)}</text></g>')
                k += 1
        y += lane_h

    nx = X(now)
    o.append(f'<line x1="{nx:.1f}" y1="{top - 14}" x2="{nx:.1f}" y2="{H - 40}" stroke="{MINE}" stroke-dasharray="3 3"/>'
             f'<circle cx="{nx:.1f}" cy="{top - 14}" r="4" fill="{MINE}" class="ping"/><circle cx="{nx:.1f}" cy="{top - 14}" r="4" fill="{MINE}"/>')
    o.append(f'<text x="{nx - 8:.1f}" y="{top - 24}" font-size="10" text-anchor="end" fill="{MINE}" class="mono" font-weight="700">now</text>')
    o.append(f'<g class="mono" font-size="10.5" fill="{MUTED}">'
             f'<rect x="28" y="{H - 27}" width="22" height="10" rx="5" fill="{STATUS["merged"]}"/><text x="58" y="{H - 18}">opened → merged</text>'
             f'<rect x="190" y="{H - 27}" width="22" height="10" rx="5" fill="url(#stripe)" stroke="{STATUS["open"]}"/><text x="220" y="{H - 18}">still in review</text></g>')
    return svg(W, H, "".join(o), "Timeline of my upstream pull requests", defs)


# ================================================================ log

def log(pulls, now):
    W, ROW, TOP = 900, 30, 112
    rows = pulls[:12]
    H = TOP + ROW * len(rows) + 30
    defs = GRID + f"""<style>{BASE_CSS}
.row{{opacity:0;animation:row .45s ease-out forwards}}
@keyframes row{{from{{opacity:0;transform:translateX(-10px)}}to{{opacity:1;transform:none}}}}
.cursor{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
</style>"""
    o = [frame(W, H, "upstream.log"),
         f'<text x="28" y="72" font-size="13" fill="{TEXT}" class="mono"><tspan fill="{MINE}">❯</tspan> gh pr list --author {escape(USER)} --upstream'
         f'<tspan fill="{MINE}" class="cursor"> ▋</tspan></text>']
    hdr = [(54, "OPENED"), (122, "STATE"), (196, "PROJECT"), (318, "PR"), (378, "TITLE"), (746, "DIFF"), (846, "TIME")]
    for x, t in hdr:
        anchor = "end" if t == "TIME" else "start"
        o.append(f'<text x="{x}" y="{TOP - 12}" font-size="10" letter-spacing="1.2" fill="{DIM}" text-anchor="{anchor}" class="mono">{t}</text>')
    peak = max((p["adds"] + p["dels"] for p in rows), default=1) or 1
    for i, p in enumerate(rows):
        y = TOP + i * ROW + 14
        color = STATUS.get(p["status"], MUTED)
        label = {"merged": "merged", "open": "review", "closed": "closed"}.get(p["status"], p["status"])
        merged = p["status"] == "merged" and p.get("merged")
        hours = ((ts(p["merged"]) if merged else now) - ts(p["created"])).total_seconds() / 3600
        when = ("✔ " if merged else "◷ ") + span(hours)
        wa = 56 * p["adds"] / peak
        wd = 56 * p["dels"] / peak
        o.append(
            f'<g class="mono row" font-size="12" style="animation-delay:{.2 + .06 * i:.2f}s">'
            f'<rect x="16" y="{y - 15}" width="{W - 32}" height="{ROW - 4}" rx="6" fill="{PANEL}" fill-opacity="{.6 if i % 2 == 0 else 0}"/>'
            f'<circle cx="38" cy="{y - 4}" r="4" fill="{color}"/>'
            f'<text x="54" y="{y}" fill="{MUTED}">{ts(p["created"]).strftime("%b %d")}</text>'
            f'<rect x="118" y="{y - 14}" width="64" height="19" rx="9.5" fill="{color}" fill-opacity=".14" stroke="{color}" stroke-opacity=".55"/>'
            f'<text x="150" y="{y - 1}" font-size="10.5" text-anchor="middle" fill="{color}">{label}</text>'
            f'<text x="196" y="{y}" fill="{MINE}">{escape(clip(short(p["repo"]), 14))}</text>'
            f'<text x="318" y="{y}" fill="{MUTED}">#{p["number"]}</text>'
            f'<text x="378" y="{y}" fill="{TEXT}">{escape(clip(p["title"], 50))}</text>'
            f'<rect x="746" y="{y - 9}" width="{max(wa, 1.5):.1f}" height="8" rx="2" fill="{ADD}"/>'
            f'<rect x="{746 + wa + 1:.1f}" y="{y - 9}" width="{wd:.1f}" height="8" rx="2" fill="{DEL}"/>'
            f'<text x="{846}" y="{y}" font-size="11" text-anchor="end" fill="{color}">{when}</text></g>'
        )
    return svg(W, H, "".join(o), f"{len(pulls)} upstream pull requests", defs)


def main():
    pulls, repos, now = load()
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero(pulls, repos, now))
    (OUT / "telemetry.svg").write_text(telemetry(pulls, repos))
    (OUT / "timeline.svg").write_text(timeline(pulls, now))
    (OUT / "pulls.svg").write_text(log(pulls, now))
    for old in ("upstream.svg",):
        (OUT / old).unlink(missing_ok=True)
    print(f"{len(pulls)} pull requests, {len(repos)} projects")


if __name__ == "__main__":
    main()
