#!/usr/bin/env python3
"""Draw the profile's cards from GitHub's own data.

assets/hero.svg       a tilted 3D solar system: every project is a planet,
                      every PR a moon, plus my name and live stats.
assets/telemetry.svg  what my PRs changed: lines by language, per project,
                      and how much of it is tests.
assets/timeline.svg   a constellation of every PR, opened to merged (or now).
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
# Repos left off the cards: class / club exercises, not real upstream work.
SKIP = {"garv-sanveria/type-your-name-for-attendance-", "NST-DEVFORGE/workbook"}
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
SKY = ["#a78bfa", "#fbbf24", "#34d399", "#60a5fa", "#f472b6", "#38bdf8",
       "#f97316", "#facc15", "#c084fc", "#2dd4bf", "#fb7185", "#a3e635"]


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
        if repo in SKIP:
            continue
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
            "closed": pr.get("closed_at"),
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

def hero(pulls, repos, now):
    """Tilted 3D solar system: I am the sun, every project is a planet sized by
    its stars, and each PR is a moon coloured by what happened to it."""
    W, H = 900, 460
    cx, cy, T = 622, 248, .36
    RADII = [78, 112, 146, 180, 214, 248]
    LEFT_EDGE = 365
    s = summary(pulls, repos)
    rng = random.Random(11)
    CLOSED = STATUS["closed"]

    stats = {}
    for p in pulls:
        st = stats.setdefault(p["repo"], {"merged": 0, "open": 0, "closed": 0})
        if p["status"] in st:
            st[p["status"]] += 1
    order = sorted(stats, key=lambda r: -repos.get(r, {}).get("stars", 0))[:12]
    colour = {r: SKY[i % len(SKY)] for i, r in enumerate(order)}
    m_all = sum(v["merged"] for v in stats.values())
    o_all = sum(v["open"] for v in stats.values())
    c_all = sum(v["closed"] for v in stats.values())

    defs = [f"""
<radialGradient id="neb" cx="68%" cy="52%" r="55%"><stop offset="0" stop-color="#22184f" stop-opacity=".95"/><stop offset=".6" stop-color="#0d0f2a" stop-opacity=".6"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<radialGradient id="sun" cx="38%" cy="32%"><stop offset="0" stop-color="#fffbea"/><stop offset=".35" stop-color="#fcd34d"/><stop offset=".75" stop-color="{MINE}"/><stop offset="1" stop-color="#9a3412"/></radialGradient>
<radialGradient id="corona"><stop offset=".35" stop-color="{MINE}" stop-opacity=".55"/><stop offset=".6" stop-color="#f97316" stop-opacity=".18"/><stop offset="1" stop-color="#f97316" stop-opacity="0"/></radialGradient>
<linearGradient id="orbBack" x1="0" x2="1"><stop offset="0" stop-color="#2a3352" stop-opacity=".15"/><stop offset=".5" stop-color="#2a3352" stop-opacity=".55"/><stop offset="1" stop-color="#2a3352" stop-opacity=".15"/></linearGradient>
<linearGradient id="orbFront" x1="0" x2="1"><stop offset="0" stop-color="#3b4a72" stop-opacity=".25"/><stop offset=".5" stop-color="#5a6aa0" stop-opacity=".9"/><stop offset="1" stop-color="#3b4a72" stop-opacity=".25"/></linearGradient>
<filter id="soft" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="4"/></filter>
<style>{BASE_CSS}
.tw{{animation:tw 3s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.2}}50%{{opacity:.9}}}}
</style>"""]
    for i, r in enumerate(order):
        c = colour[r]
        defs.append(f'<radialGradient id="pl{i}" cx="32%" cy="28%" r="75%"><stop offset="0" stop-color="#fff" stop-opacity=".95"/>'
                    f'<stop offset=".25" stop-color="{c}"/><stop offset=".8" stop-color="{c}" stop-opacity=".55"/><stop offset="1" stop-color="#03040a"/></radialGradient>')

    o = [f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/><rect x="300" y="43" width="{W - 301}" height="{H - 44}" fill="url(#neb)"/>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LINE}"/>',
         f'<g class="mono"><circle cx="24" cy="22" r="5" fill="#ff5f57"/><circle cx="41" cy="22" r="5" fill="#febc2e"/><circle cx="58" cy="22" r="5" fill="#28c840"/>'
         f'<text x="{W / 2}" y="26" font-size="11.5" text-anchor="middle" fill="{MUTED}">~/{USER} — orbit.3d</text></g>'
         f'<line x1="0" y1="42" x2="{W}" y2="42" stroke="{LINE}"/>']
    for i in range(160):
        extra = f' class="tw" style="animation-delay:{rng.uniform(0, 3):.1f}s"' if i % 7 == 0 else f' opacity="{rng.uniform(.12, .7):.2f}"'
        o.append(f'<circle cx="{rng.uniform(330, W - 8):.0f}" cy="{rng.uniform(50, H - 8):.0f}" r="{rng.choice([.4, .6, .8, 1.1])}" fill="#dbe4ff"{extra}/>')

    # ---- left: name, PR breakdown, stat tiles
    o.append(f'<g class="mono in" style="animation-delay:.1s"><text x="36" y="86" font-size="12.5" fill="{MUTED}">~ $ whoami</text>'
             f'<text x="36" y="124" font-size="31" font-weight="800" fill="{TEXT}">{escape(NAME.split(" ", 1)[0])}</text>'
             f'<text x="36" y="160" font-size="31" font-weight="800" fill="{TEXT}">{escape(NAME.split(" ", 1)[-1])}</text>'
             f'<text x="36" y="188" font-size="12.5" fill="{MINE}">CS student · {escape(SCHOOL.split(" · ")[0])}</text>'
             f'<text x="36" y="207" font-size="12" fill="{MUTED}">I read big codebases and send fixes upstream.</text></g>')
    n = max(m_all + o_all + c_all, 1)
    bx, by, bw = 36, 250, 250
    bar = []
    x = bx
    for cnt, col in ((m_all, STATUS["merged"]), (o_all, STATUS["open"]), (c_all, CLOSED)):
        if cnt:
            w = bw * cnt / n
            bar.append(f'<rect x="{x:.1f}" y="{by + 10}" width="{max(w - 2, 2):.1f}" height="7" rx="3.5" fill="{col}"/>')
            x += w
    o.append(f'<g class="mono in" style="animation-delay:.4s">'
             f'<text x="{bx}" y="{by}" font-size="22" font-weight="800" fill="{TEXT}">{m_all}<tspan fill="{MUTED}" font-size="15">/{n}</tspan></text>'
             f'<text x="{bx + 70}" y="{by - 2}" font-size="11.5" fill="{MUTED}">PRs merged upstream</text>' + "".join(bar) +
             f'<text x="{bx}" y="{by + 34}" font-size="10.5"><tspan fill="{STATUS["merged"]}">● {m_all} merged</tspan>   '
             f'<tspan fill="{STATUS["open"]}">● {o_all} in review</tspan>   <tspan fill="{CLOSED}">● {c_all} closed</tspan></text></g>')
    tiles = [(str(s["repos"]), "open-source projects", ADD),
             (f"+{s['adds']}", f"lines in · −{s['dels']} out", ADD),
             (f"{kstars(s['reach'])}★", "stars on what I touched", MINE)]
    for i, (big, small, col) in enumerate(tiles):
        y = 316 + i * 44
        o.append(f'<g class="mono in" style="animation-delay:{.6 + i * .12:.2f}s">'
                 f'<rect x="36" y="{y}" width="250" height="36" rx="9" fill="{PANEL}" fill-opacity=".7" stroke="{LINE}"/>'
                 f'<rect x="36" y="{y}" width="3" height="36" rx="1.5" fill="{col}"/>'
                 f'<text x="50" y="{y + 24}" font-size="17" font-weight="800" fill="{TEXT}">{escape(big)}</text>'
                 f'<text x="130" y="{y + 23}" font-size="11" fill="{MUTED}">{escape(small)}</text></g>')

    # ---- place planets: each on its ring, at the angle that keeps it and its tag clear of the others
    def label_parts(r):
        st = stats[r]
        parts = [(short(r), TEXT)]
        if st["merged"]:
            parts.append((f"✔{st['merged']}", STATUS["merged"]))
        if st["open"]:
            parts.append((f"◷{st['open']}", STATUS["open"]))
        if st["closed"]:
            parts.append((f"✕{st['closed']}", CLOSED))
        return parts

    def geometry(i, r, a):
        rad = RADII[i % len(RADII)] + (i // len(RADII)) * 10
        x, y = cx + rad * math.cos(a), cy + rad * T * math.sin(a)
        pr = 5 + 1.9 * math.log10(repos.get(r, {}).get("stars", 0) + 1)
        parts = label_parts(r)
        wlen = sum(len(t) + (1 if j else 0) for j, (t, _) in enumerate(parts)) * 6.1 + 14
        return dict(a=a, rad=rad, x=x, y=y, pr=pr, wlen=wlen, parts=parts)

    def boxes(g):
        return [(g["x"] - g["pr"] - 10, g["y"] - g["pr"] - 8, g["x"] + g["pr"] + 10, g["y"] + g["pr"] + 6),
                (g["x"] - g["wlen"] / 2, g["y"] + g["pr"] + 7, g["x"] + g["wlen"] / 2, g["y"] + g["pr"] + 25)]

    def overlap(a, b):
        return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))

    sun_box = (cx - 48, cy - 44, cx + 48, cy + 44)
    placed, taken = [], []
    for i, r in enumerate(order):
        best = None
        for step in range(48):
            g = geometry(i, r, step * 2 * math.pi / 48 + i * .37)
            bx_ = boxes(g)
            cost = sum(overlap(b, t) for b in bx_ for t in taken) * 4 + sum(overlap(b, sun_box) for b in bx_) * 8
            cost += max(0, LEFT_EDGE - bx_[1][0]) * 40 + max(0, bx_[1][2] - (W - 8)) * 40
            if best is None or cost < best[0]:
                best = (cost, g)
        placed.append((i, r, best[1]))
        taken += boxes(best[1])

    def draw(i, r, g):
        """A planet that orbits its ring, with its moons and name tag riding along."""
        st, c, pr = stats[r], colour[r], g["pr"]
        a0, rad = g["a"], g["rad"]
        x0, y0 = g["x"], g["y"]
        x1, y1 = 2 * cx - x0, 2 * cy - y0
        path = f"M{x0:.1f},{y0:.1f} A{rad},{rad * T:.1f} 0 1,1 {x1:.1f},{y1:.1f} A{rad},{rad * T:.1f} 0 1,1 {x0:.1f},{y0:.1f}"
        dur = 120  # same period for every ring: the whole system turns together, so tags stay apart
        # nearer the viewer (lower on screen) = brighter; farther = dimmer
        shade = ";".join(f"{.55 + .45 * (math.sin(a0 + 2 * math.pi * k / 12) + 1) / 2:.2f}" for k in range(13))
        out = [f'<g><animateMotion dur="{dur:.0f}s" repeatCount="indefinite" path="{path}"/>'
               f'<animate attributeName="opacity" dur="{dur:.0f}s" repeatCount="indefinite" values="{shade}"/>'
               f'<g transform="translate({-x0:.1f},{-y0:.1f})"><g class="in" style="animation-delay:{.3 + .08 * i:.2f}s">']
        x, y = x0, y0
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr * 1.9:.1f}" fill="{c}" opacity=".22" filter="url(#soft)"/>')
        ringed = i == 0 or st["merged"] + st["open"] + st["closed"] >= 4
        if ringed:
            out.append(f'<path d="M{x - pr * 2.1:.1f},{y:.1f} A{pr * 2.1:.1f},{pr * .6:.1f} 0 0 1 {x + pr * 2.1:.1f},{y:.1f}" fill="none" stroke="#d6c4ff" stroke-opacity=".55" stroke-width="2"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr:.1f}" fill="url(#pl{i})"/>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr:.1f}" fill="none" stroke="#fff" stroke-opacity=".18"/>')
        if ringed:
            out.append(f'<path d="M{x - pr * 2.1:.1f},{y:.1f} A{pr * 2.1:.1f},{pr * .6:.1f} 0 0 0 {x + pr * 2.1:.1f},{y:.1f}" fill="none" stroke="#d6c4ff" stroke-opacity=".8" stroke-width="2"/>')
        moons = [STATUS["merged"]] * st["merged"] + [STATUS["open"]] * st["open"] + [CLOSED] * st["closed"]
        mr = pr + 7
        out.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{mr:.1f}" ry="{mr * .45:.1f}" fill="none" stroke="#fff" stroke-opacity=".10"/>')
        # moons circle their planet
        out.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {x:.1f} {y:.1f}" to="360 {x:.1f} {y:.1f}" dur="{14 + i:.0f}s" repeatCount="indefinite"/>')
        for k, col in enumerate(moons):
            ang = math.pi * 1.15 + k * (2 * math.pi / max(len(moons), 1))
            out.append(f'<circle cx="{x + mr * math.cos(ang):.1f}" cy="{y + mr * math.sin(ang):.1f}" r="3.1" fill="{col}" stroke="#05060f" stroke-width="1.2"/>')
        out.append('</g>')
        txt = "".join(f'<tspan fill="{col}">{" " if j else ""}{escape(t)}</tspan>' for j, (t, col) in enumerate(g["parts"]))
        ty = y + pr + 16
        # the tag fades out while the planet is on the far side of the sun, where the rings crowd together
        steps = 24
        fade = ";".join("1" if math.sin(a0 + 2 * math.pi * k / steps) > -.35 else "0" for k in range(steps + 1))
        out.append(f'<g><animate attributeName="opacity" dur="{dur:.0f}s" repeatCount="indefinite" calcMode="linear" values="{fade}"/>'
                   f'<rect x="{x - g["wlen"] / 2:.1f}" y="{ty - 9:.1f}" width="{g["wlen"]:.1f}" height="17" rx="8.5" fill="#0b1020" fill-opacity=".85" stroke="{c}" stroke-opacity=".45"/>'
                   f'<text x="{x:.1f}" y="{ty + 3.5:.1f}" font-size="10" text-anchor="middle" class="mono">{txt}</text></g></g></g></g>')
        return "".join(out)

    for rad in RADII:
        o.append(f'<path d="M{cx - rad},{cy} A{rad},{rad * T:.1f} 0 0 1 {cx + rad},{cy}" fill="none" stroke="url(#orbBack)" stroke-width="1.2"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="78" fill="url(#corona)"><animate attributeName="r" values="74;84;74" dur="5s" repeatCount="indefinite"/></circle>'
             f'<circle cx="{cx}" cy="{cy}" r="31" fill="url(#sun)"/>'
             f'<text x="{cx}" y="{cy + 5}" font-size="13.5" font-weight="800" text-anchor="middle" fill="#3b1d04" class="mono">HVJ</text>')
    for rad in RADII:
        o.append(f'<path d="M{cx - rad},{cy} A{rad},{rad * T:.1f} 0 0 0 {cx + rad},{cy}" fill="none" stroke="url(#orbFront)" stroke-width="1.3"/>')
    o += [draw(i, r, g) for i, r, g in placed]
    o.append(f'<g class="mono" font-size="10.5" fill="{MUTED}"><text x="{W - 400}" y="{H - 18}">each moon is a PR:</text>'
             f'<circle cx="{W - 262}" cy="{H - 22}" r="4" fill="{STATUS["merged"]}"/><text x="{W - 253}" y="{H - 18}">merged</text>'
             f'<circle cx="{W - 188}" cy="{H - 22}" r="4" fill="{STATUS["open"]}"/><text x="{W - 179}" y="{H - 18}">in review</text>'
             f'<circle cx="{W - 100}" cy="{H - 22}" r="4" fill="{CLOSED}"/><text x="{W - 91}" y="{H - 18}">closed</text></g>')
    return svg(W, H, "".join(o), f"{NAME}: {s['n']} pull requests to {s['repos']} projects, {m_all} merged, {o_all} in review, {c_all} closed", "".join(defs))


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

    for x, label in [(36, "LINES CHANGED, BY LANGUAGE"), (380, "PER PROJECT"), (712, "HOW MUCH IS TESTS")]:
        o.append(f'<text x="{x}" y="70" font-size="10.5" letter-spacing="1.5" fill="{DIM}" class="mono">{label}</text>')

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

    med = span(s["median"]) if s["median"] is not None else "—"
    facts = [f"{s['files']} files touched", f"median time to merge {med}", f"{s['repos']} codebases", f"{len(langs)} languages"]
    o.append(f'<line x1="24" y1="{H - 36}" x2="{W - 24}" y2="{H - 36}" stroke="{LINE}"/>')
    o.append(f'<text x="{W / 2}" y="{H - 14}" font-size="11.5" text-anchor="middle" fill="{MUTED}" class="mono">'
             + '<tspan fill="#3a4560">  ·  </tspan>'.join(escape(f) for f in facts) + "</text>")
    return svg(W, H, "".join(o), f"+{s['adds']} −{s['dels']} lines upstream, {100 * test_share:.0f}% tests", defs)


# ================================================================ timeline

def star_shape(x, y, r, color):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * .45
        pts.append(f"{x + rr * math.cos(a):.1f},{y + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{color}"/>'


def timeline(pulls, now):
    """A night sky: each project is a constellation in its own colour. Every PR
    is a faint dot on the day it was opened, linked to a star on the day it
    merged. PRs in review twinkle at today; closed ones end in a red cross."""
    W, H, X0, X1 = 900, 450, 170, 850
    CLOSED = STATUS["closed"]
    rng = random.Random(21)
    repos = []
    for p in sorted(pulls, key=lambda p: p["created"]):
        if p["repo"] not in repos:
            repos.append(p["repo"])
    color = {r: SKY[i % len(SKY)] for i, r in enumerate(repos)}
    t0 = min(ts(p["created"]) for p in pulls) - timedelta(days=1)
    X = lambda t: X0 + (X1 - X0) * (t - t0).total_seconds() / max((now - t0).total_seconds(), 1)

    def outcome(p):
        if p["status"] == "merged":
            return ts(p["merged"])
        if p["status"] == "closed":
            return ts(p.get("closed") or p["created"])
        return now

    defs = f"""
<radialGradient id="neb" cx="62%" cy="45%" r="60%"><stop offset="0" stop-color="#1a1440" stop-opacity=".9"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3.2"/></filter>
<style>{BASE_CSS}
.tw{{animation:tw 2.4s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
.bg{{animation:bgtw 4s ease-in-out infinite}}
@keyframes bgtw{{0%,100%{{opacity:.15}}50%{{opacity:.5}}}}
</style>"""
    o = [f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/><rect width="{W}" height="{H}" rx="14" fill="url(#neb)"/>'
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LINE}"/>']
    for i in range(90):
        cls = ' class="bg" style="animation-delay:%.1fs"' % rng.uniform(0, 4) if i % 6 == 0 else f' opacity="{rng.uniform(.1, .45):.2f}"'
        o.append(f'<circle cx="{rng.uniform(8, W - 8):.0f}" cy="{rng.uniform(8, H - 8):.0f}" r="{rng.choice([.4, .6, .8])}" fill="#fff"{cls}/>')
    ay = H - 22
    d = t0.replace(hour=0, minute=0, second=0)
    d += timedelta(days=(7 - d.weekday()) % 7)
    while d < now - timedelta(days=3):
        x = X(d)
        o.append(f'<line x1="{x:.1f}" y1="52" x2="{x:.1f}" y2="{ay - 14}" stroke="#ffffff" stroke-opacity=".04" stroke-dasharray="2 5"/>'
                 f'<text x="{x:.1f}" y="{ay}" font-size="9.5" text-anchor="middle" fill="{DIM}" class="mono">{d.strftime("%b %d")}</text>')
        d += timedelta(days=7)
    o.append(f'<text x="{X(now):.1f}" y="{ay}" font-size="9.5" text-anchor="end" fill="{MINE}" class="mono">today</text>')

    bands = {r: 78 + i * (H - 140) / max(len(repos) - 1, 1) for i, r in enumerate(repos)}
    pos = {}
    for r in repos:
        mine = sorted((p for p in pulls if p["repo"] == r), key=lambda p: p["created"])
        for k, p in enumerate(mine):
            yb = bands[r] + rng.uniform(-5, 5) + (k - (len(mine) - 1) / 2) * 7
            ya = yb + rng.uniform(-9, 9)
            xa = X(ts(p["created"]))
            xb = X(now) - 6 if p["status"] == "open" else X(outcome(p))
            pos[id(p)] = ((xa, ya), (max(xb, xa + 10), yb))

    for r in repos:
        c = color[r]
        mine = sorted((p for p in pulls if p["repo"] == r), key=lambda p: p["created"])
        for p in mine:
            (xa, ya), (xb, yb) = pos[id(p)]
            dash = ' stroke-dasharray="2 4"' if p["status"] == "open" else ""
            o.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{c}" '
                     f'stroke-opacity="{.22 if p["status"] == "open" else .4}"{dash}/>'
                     f'<circle cx="{xa:.1f}" cy="{ya:.1f}" r="1.8" fill="{c}" opacity=".8"/>')
        stars = [pos[id(p)][1] for p in mine if p["status"] == "merged"]
        for (xa, ya), (xb, yb) in zip(stars, stars[1:]):
            o.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{c}" stroke-opacity=".3"/>')
        (fx, fy), _ = pos[id(mine[0])]
        o.append(f'<text x="{fx - 10:.1f}" y="{fy + 3.5:.1f}" font-size="9.5" letter-spacing="1" text-anchor="end" '
                 f'fill="{c}" opacity=".85" class="mono">{escape(short(r).upper())}</text>')

    for i, p in enumerate(sorted(pulls, key=lambda p: p["created"])):
        _, (x, y) = pos[id(p)]
        c = color[p["repo"]]
        if p["status"] == "merged":
            days = (ts(p["merged"]) - ts(p["created"])).total_seconds() / 86400
            r = 4 + min(days, 8) * .55
            o.append(f'<g class="in" style="animation-delay:{.2 + .08 * i:.2f}s">'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 4:.1f}" fill="{c}" opacity=".55" filter="url(#glow)"/>'
                     + star_shape(x, y, r + 1.5, c) + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.4" fill="#fff"/></g>')
        elif p["status"] == "open":
            o.append(f'<g class="tw" style="animation-delay:{.3 * i:.1f}s"><circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{c}" opacity=".35" filter="url(#glow)"/>'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="none" stroke="{c}" stroke-width="1.5"/></g>')
        else:
            o.append(f'<text x="{x:.1f}" y="{y + 4.5:.1f}" font-size="13" font-weight="700" text-anchor="middle" fill="{CLOSED}" class="mono">✕</text>')

    merged = sum(p["status"] == "merged" for p in pulls)
    review = sum(p["status"] == "open" for p in pulls)
    closed = sum(p["status"] == "closed" for p in pulls)
    o.append(f'<text x="36" y="30" font-size="10.5" fill="#6b7899" class="mono">{len(pulls)} pull requests · {merged} merged · {review} in review · {closed} closed</text>')
    o.append(f'<g class="mono" font-size="10.5" fill="#6b7899">' + star_shape(W - 268, 26, 5, "#cbd5e1")
             + f'<text x="{W - 258}" y="30">merged</text>'
             f'<circle cx="{W - 192}" cy="26" r="4" fill="none" stroke="#cbd5e1" stroke-width="1.5"/><text x="{W - 184}" y="30">in review</text>'
             f'<text x="{W - 102}" y="31" fill="{CLOSED}" font-weight="700">✕</text><text x="{W - 89}" y="30">closed</text></g>')
    return svg(W, H, "".join(o), f"Constellation of {len(pulls)} pull requests across {len(repos)} projects: {merged} merged, {review} in review, {closed} closed", defs)


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
        closed = p["status"] == "closed"
        end = ts(p["merged"]) if merged else (ts(p.get("closed") or p["created"]) if closed else now)
        hours = (end - ts(p["created"])).total_seconds() / 3600
        when = ("✔ " if merged else "✕ " if closed else "◷ ") + span(hours)
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


# ================================================================ wall

def wall(pulls, repos):
    """Every project I have shipped code into, as badges: merged and in review."""
    W, CW, PAD, GAP, H_CHIP = 900, 7.6, 12, 12, 30
    counts = {}
    for p in pulls:
        c = counts.setdefault(p["repo"], {"merged": 0, "open": 0})
        if p["status"] in c:
            c[p["status"]] += 1
    order = sorted((r for r in counts if counts[r]["merged"] or counts[r]["open"]),
                   key=lambda r: (-counts[r]["merged"], -counts[r]["open"], -repos.get(r, {}).get("stars", 0)))
    chips, x, y = [], 36, 96
    for i, repo in enumerate(order):
        name, c = short(repo), counts[repo]
        segs = [(f"✔ {c['merged']}", STATUS["merged"])] if c["merged"] else []
        if c["open"]:
            segs.append((f"◷ {c['open']}", STATUS["open"]))
        wn = len(name) * CW + 2 * PAD
        ws = [len(t) * CW + 2 * PAD for t, _ in segs]
        w = wn + sum(ws)
        if x + w > W - 36:
            x, y = 36, y + H_CHIP + GAP
        g = [f'<g class="mono in" font-size="12.5" style="animation-delay:{.15 + .07 * i:.2f}s">',
             f'<clipPath id="chip{i}"><rect x="{x}" y="{y}" width="{w:.0f}" height="{H_CHIP}" rx="7"/></clipPath>',
             f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{H_CHIP}" rx="7" fill="{PANEL}"/>',
             f'<text x="{x + PAD}" y="{y + 19.5}" fill="{TEXT}">{escape(name)}</text>']
        sx = x + wn
        g.append(f'<g clip-path="url(#chip{i})">')
        for (t, color), sw in zip(segs, ws):
            g.append(f'<rect x="{sx:.0f}" y="{y}" width="{sw:.0f}" height="{H_CHIP}" fill="{color}"/>')
            g.append(f'<text x="{sx + PAD:.0f}" y="{y + 19.5}" font-weight="700" fill="#0b0f19">{t}</text>')
            sx += sw
        g.append("</g>")
        g.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{H_CHIP}" rx="7" fill="none" stroke="{LINE}"/></g>')
        chips.append("".join(g))
        x += w + GAP
    H = y + H_CHIP + 54
    defs = GRID + f"<style>{BASE_CSS}</style>"
    o = [frame(W, H, "git remote -v | upstream"),
         f'<text x="36" y="76" font-size="13" fill="{MUTED}" class="mono">code I have shipped into</text>']
    o += chips
    o.append(f'<g class="mono" font-size="11" fill="{MUTED}">'
             f'<circle cx="40" cy="{H - 24}" r="4" fill="{STATUS["merged"]}"/><text x="50" y="{H - 20}">merged</text>'
             f'<circle cx="116" cy="{H - 24}" r="4" fill="{STATUS["open"]}"/><text x="126" y="{H - 20}">in review</text></g>')
    total = sum(c["merged"] for c in counts.values())
    return svg(W, H, "".join(o), f"Code shipped into {len(order)} open-source projects, {total} pull requests merged", defs)


def main():
    pulls, repos, now = load()
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero(pulls, repos, now))
    (OUT / "wall.svg").write_text(wall(pulls, repos))
    (OUT / "telemetry.svg").write_text(telemetry(pulls, repos))
    (OUT / "timeline.svg").write_text(timeline(pulls, now))
    (OUT / "pulls.svg").write_text(log(pulls, now))
    for old in ("upstream.svg",):
        (OUT / old).unlink(missing_ok=True)
    print(f"{len(pulls)} pull requests, {len(repos)} projects")


if __name__ == "__main__":
    main()
