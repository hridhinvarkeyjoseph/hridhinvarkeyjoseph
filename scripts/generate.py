#!/usr/bin/env python3
"""Draw the profile's two cards from GitHub's own data.

assets/upstream.svg  the header: every project I have sent a pull request to,
                     drawn as branches leaving my line and merging upstream.
assets/pulls.svg     the log: each pull request with its live status.

Standard library only. In GitHub Actions it reads GITHUB_TOKEN; locally,
PULLS_JSON=path/to/sample.json renders from a saved answer instead.
"""

import json
import math
import os
import urllib.request
from datetime import datetime
from html import escape
from pathlib import Path

USER = os.environ.get("PROFILE_USER", "hridhinvarkeyjoseph")
NAME = "Hridhin Varkey Joseph"
GOAL = 10  # the DevForge "10 PR Journey"
OUT = Path(__file__).resolve().parent.parent / "assets"

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
BG, PANEL, LINE, TEXT, MUTED = "#0a0d14", "#111622", "#1e2638", "#e6edf3", "#7d8aa3"
MINE = "#f5a623"  # my branch
STATUS = {"merged": "#a371f7", "open": "#3fb950", "closed": "#f85149"}


# ---------------------------------------------------------------- data

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
    pulls, stars = [], {}
    for it in items:
        repo = it["repository_url"].split("/repos/")[1]
        if repo not in stars:
            stars[repo] = api("repos/" + repo)["stargazers_count"]
        merged = it.get("pull_request", {}).get("merged_at")
        pulls.append({
            "repo": repo,
            "number": it["number"],
            "title": " ".join(it["title"].split()),
            "status": "merged" if merged else it["state"],
            "created": it["created_at"],
        })
    return pulls, stars


def load():
    sample = os.environ.get("PULLS_JSON")
    if sample:
        data = json.loads(Path(sample).read_text())
        return data["pulls"], data["stars"]
    return fetch()


# ---------------------------------------------------------------- helpers

def kstars(n):
    if n >= 1000:
        s = f"{n / 1000:.1f}".rstrip("0").rstrip(".")
        return s + "k"
    return str(n)


def clip(text, n):
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def svg(width, height, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>{body}</svg>\n"
    )


# ---------------------------------------------------------------- header

def upstream(pulls, stars):
    W, H = 900, 330
    repos = {}
    for p in pulls:
        r = repos.setdefault(p["repo"], {"n": 0, "merged": 0, "open": 0})
        r["n"] += 1
        r[p["status"]] = r.get(p["status"], 0) + 1
    order = sorted(repos, key=lambda r: -stars.get(r, 0))[:7]

    merged = sum(1 for p in pulls if p["status"] == "merged")
    reach = sum(stars.get(r, 0) for r in repos)

    o = [f"""<defs>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="{LINE}"/></pattern>
<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{MINE}" stop-opacity="0"/><stop offset=".08" stop-color="{MINE}"/><stop offset=".92" stop-color="{MINE}"/><stop offset="1" stop-color="{MINE}" stop-opacity="0"/></linearGradient>
<style>
.mono{{font-family:{MONO}}}
.flow{{stroke-dasharray:5 9;animation:flow 1.6s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-28}}}}
.pulse{{animation:pulse 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes pulse{{0%,100%{{opacity:.12;transform:scale(1)}}50%{{opacity:.32;transform:scale(1.3)}}}}
.cursor{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.rise{{opacity:0;animation:rise .6s ease-out forwards}}
@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
</style></defs>
<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>
<rect width="{W}" height="{H}" rx="14" fill="url(#dots)" opacity=".55"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LINE}"/>"""]

    # name block
    o.append(f"""<g class="mono">
<text x="40" y="52" font-size="13" fill="{MUTED}">~/{escape(USER)} <tspan fill="{MINE}">git</tspan> remote -v</text>
<text x="40" y="92" font-size="30" font-weight="700" fill="{TEXT}">{escape(NAME)}<tspan class="cursor" fill="{MINE}">_</tspan></text>
<text x="40" y="120" font-size="14" fill="{MUTED}">I read big codebases and send the fixes back upstream.</text>
</g>""")

    # stat chips, top right
    chips = [(str(len(pulls)), "pull requests"), (str(merged), "merged"),
             (str(len(repos)), "projects"), (kstars(reach) + "★", "combined reach")]
    cx = W - 40
    for i, (big, small) in enumerate(reversed(chips)):
        w = max(len(big) * 13, len(small) * 7.2) + 24
        cx -= w
        o.append(
            f'<g class="mono rise" style="animation-delay:{.15 * (3 - i):.2f}s">'
            f'<rect x="{cx:.0f}" y="36" width="{w:.0f}" height="58" rx="9" fill="{PANEL}" stroke="{LINE}"/>'
            f'<text x="{cx + 12:.0f}" y="63" font-size="20" font-weight="700" fill="{TEXT}">{escape(big)}</text>'
            f'<text x="{cx + 12:.0f}" y="82" font-size="11" fill="{MUTED}">{escape(small)}</text></g>'
        )
        cx -= 10

    # my line, and one branch merging into each project
    base = 292
    o.append(f'<line x1="30" y1="{base}" x2="{W - 30}" y2="{base}" stroke="url(#fade)" stroke-width="3"/>')
    o.append(f'<text x="40" y="{base + 22}" font-size="11" fill="{MINE}" class="mono">{escape(USER)}/main</text>')
    n = len(order)
    left, right = 120, W - 90
    step = (right - left) / max(n - 1, 1)
    for i, repo in enumerate(order):
        x = left + i * step if n > 1 else (left + right) / 2
        info = repos[repo]
        color = STATUS["merged"] if info.get("merged") else STATUS["open"]
        r = 7 + 2.2 * math.log10(max(stars.get(repo, 0), 1) + 1)
        y = 204 + (i % 2) * 30
        fork = x - 46
        path = f"M{fork:.0f},{base} C{fork:.0f},{base - 50} {x:.0f},{y + 60} {x:.0f},{y + r}"
        delay = .2 * i
        o.append(f'<circle cx="{fork:.0f}" cy="{base}" r="4.5" fill="{BG}" stroke="{MINE}" stroke-width="2"/>')
        o.append(f'<path d="{path}" fill="none" stroke="{LINE}" stroke-width="2"/>')
        o.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" class="flow" style="animation-delay:-{delay:.1f}s"/>')
        o.append(f'<circle cx="{x:.0f}" cy="{y}" r="{r + 4:.1f}" fill="{color}" class="pulse" style="animation-delay:{delay:.1f}s"/>')
        o.append(f'<circle cx="{x:.0f}" cy="{y}" r="{r:.1f}" fill="{BG}" stroke="{color}" stroke-width="2.5"/>')
        o.append(f'<text x="{x:.0f}" y="{y + 4}" font-size="11" font-weight="700" text-anchor="middle" fill="{color}" class="mono">{info["n"]}</text>')
        owner, name = repo.split("/")
        o.append(
            f'<g class="mono rise" style="animation-delay:{.4 + delay:.1f}s" text-anchor="middle">'
            f'<text x="{x:.0f}" y="{y - r * 1.3 - 24:.0f}" font-size="12" font-weight="700" fill="{TEXT}">{escape(clip(name, 16))}</text>'
            f'<text x="{x:.0f}" y="{y - r * 1.3 - 10:.0f}" font-size="10.5" fill="{MUTED}">{escape(kstars(stars.get(repo, 0)))}★ · {escape(clip(owner, 12))}</text></g>'
        )

    # legend
    lx = W - 300
    o.append(f'<g class="mono" font-size="11" fill="{MUTED}">'
             f'<circle cx="{lx}" cy="{base + 18}" r="4" fill="{STATUS["merged"]}"/><text x="{lx + 9}" y="{base + 22}">merged</text>'
             f'<circle cx="{lx + 80}" cy="{base + 18}" r="4" fill="{STATUS["open"]}"/><text x="{lx + 89}" y="{base + 22}">in review</text>'
             f'<text x="{lx + 170}" y="{base + 22}">number = PRs sent</text></g>')

    return svg(W, H, "".join(o), f"{NAME}: {len(pulls)} pull requests to {len(repos)} projects")


# ---------------------------------------------------------------- log

def log(pulls):
    W, ROW, TOP = 900, 30, 128
    rows = pulls[:12]
    H = TOP + ROW * len(rows) + 36
    merged = sum(1 for p in pulls if p["status"] == "merged")
    done = min(merged, GOAL)

    o = [f"""<defs><style>
.mono{{font-family:{MONO}}}
.row{{opacity:0;animation:in .45s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateX(-8px)}}to{{opacity:1;transform:none}}}}
.fill{{transform-box:fill-box;transform-origin:left;animation:grow 1.4s cubic-bezier(.2,.8,.2,1) forwards;transform:scaleX(0)}}
@keyframes grow{{to{{transform:scaleX(1)}}}}
</style></defs>
<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LINE}"/>
<g class="mono">
<circle cx="28" cy="26" r="6" fill="#ff5f57"/><circle cx="48" cy="26" r="6" fill="#febc2e"/><circle cx="68" cy="26" r="6" fill="#28c840"/>
<text x="{W / 2}" y="30" font-size="12" text-anchor="middle" fill="{MUTED}">upstream.log</text>
<line x1="0" y1="48" x2="{W}" y2="48" stroke="{LINE}"/>
<text x="32" y="78" font-size="13" fill="{TEXT}"><tspan fill="{MINE}">$</tspan> git log --author={escape(USER)} --upstream</text>
<text x="32" y="106" font-size="12" fill="{MUTED}">10 PR Journey</text>
</g>"""]

    # progress: one segment per PR of the goal
    seg_x, seg_w, gap = 150, 40, 6
    for i in range(GOAL):
        x = seg_x + i * (seg_w + gap)
        o.append(f'<rect x="{x}" y="96" width="{seg_w}" height="12" rx="3" fill="{PANEL}" stroke="{LINE}"/>')
        if i < done:
            o.append(f'<rect x="{x}" y="96" width="{seg_w}" height="12" rx="3" fill="{STATUS["merged"]}" class="fill" style="animation-delay:{.12 * i:.2f}s"/>')
    o.append(f'<text x="{seg_x + GOAL * (seg_w + gap) + 6}" y="106" font-size="12" fill="{TEXT}" class="mono">{done}/{GOAL} merged</text>')

    for i, p in enumerate(rows):
        y = TOP + i * ROW + 18
        color = STATUS.get(p["status"], MUTED)
        label = {"merged": "merged", "open": "review", "closed": "closed"}.get(p["status"], p["status"])
        date = datetime.strptime(p["created"][:10], "%Y-%m-%d").strftime("%b %d")
        repo = p["repo"].split("/")[1]
        o.append(
            f'<g class="mono row" font-size="12.5" style="animation-delay:{.3 + .07 * i:.2f}s">'
            f'<circle cx="38" cy="{y - 4}" r="4.5" fill="{color}"/>'
            f'<text x="54" y="{y}" fill="{MUTED}">{date}</text>'
            f'<rect x="112" y="{y - 15}" width="62" height="20" rx="10" fill="{color}" fill-opacity=".14" stroke="{color}" stroke-opacity=".5"/>'
            f'<text x="143" y="{y - 1}" font-size="11" text-anchor="middle" fill="{color}">{label}</text>'
            f'<text x="188" y="{y}" fill="{MINE}">{escape(clip(repo, 14))}</text>'
            f'<text x="306" y="{y}" fill="{MUTED}">#{p["number"]}</text>'
            f'<text x="368" y="{y}" fill="{TEXT}">{escape(clip(p["title"], 64))}</text></g>'
        )
    return svg(W, H, "".join(o), f"{len(pulls)} upstream pull requests, {merged} merged")


def main():
    pulls, stars = load()
    OUT.mkdir(exist_ok=True)
    (OUT / "upstream.svg").write_text(upstream(pulls, stars))
    (OUT / "pulls.svg").write_text(log(pulls))
    print(f"{len(pulls)} pull requests, {len(stars)} projects")


if __name__ == "__main__":
    main()
