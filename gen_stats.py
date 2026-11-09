import os, json, html, urllib.request

USER = os.environ.get("GH_USER", "nopal2008")
FULL_NAME = os.environ.get("FULL_NAME", "Muhammad Fatih Nauval Azzidan")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DEMO = os.environ.get("DEMO") == "1"      # data contoh, tanpa internet
STATIC = os.environ.get("STATIC") == "1"  # tanpa animasi (untuk preview gambar)
OUT = os.environ.get("OUT_DIR", "stats")

BG, BAR, BORDER = "#0a0f0d", "#111a15", "#1f3a2b"
GREEN, DIM, CYAN, WHITE = "#00ff41", "#4f8f66", "#00f7ff", "#d7ffe3"
CW = 7.8  # lebar 1 karakter monospace 13px


def api(path):
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-stats")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    if DEMO:
        return dict(repos=12, stars=34, followers=21, following=15, commits=480, since="2023",
                    langs={"JavaScript": 52000, "PHP": 41000, "Vue": 30000, "CSS": 14000, "HTML": 9000, "Blade": 4000})
    u = api(f"/users/{USER}")
    repos, page = [], 1
    while page <= 5:
        chunk = api(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    langs = {}
    for r in own[:100]:
        try:
            for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
                langs[k] = langs.get(k, 0) + v
        except Exception as e:
            print("skip", r["name"], e)
    try:
        commits = api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]
    except Exception as e:
        print("commit count failed:", e)
        commits = 0
    return dict(repos=u["public_repos"], stars=stars, followers=u["followers"], following=u["following"],
                commits=commits, since=u["created_at"][:4], langs=langs)


def esc(s):
    return html.escape(str(s), quote=True)


def terminal_svg(d):
    W = 720
    prompt = f"{USER}@github:~$"
    p_len = len(prompt) * CW
    cmd_x = 24 + p_len + CW

    parts, y, t = [], 66, 0.4

    def fade(delay):
        return "" if STATIC else f' class="f" style="animation-delay:{delay:.2f}s"'

    def command(text):
        nonlocal y, t
        n = len(text)
        parts.append(f'<g{fade(t)}><text x="24" y="{y}" fill="{CYAN}" textLength="{p_len:.1f}" '
                     f'lengthAdjust="spacingAndGlyphs">{esc(prompt)}</text></g>')
        parts.append(f'<text x="{cmd_x:.1f}" y="{y}" fill="{GREEN}" textLength="{n*CW:.1f}" '
                     f'lengthAdjust="spacing">{esc(text)}</text>')
        if not STATIC:
            dur = max(0.5, n * 0.05)
            parts.append(f'<rect class="cv" x="{cmd_x-2:.1f}" y="{y-14}" width="{n*CW+6:.1f}" height="19" fill="{BG}" '
                         f'style="--w:{n*CW+6:.1f}px;animation:type {dur:.2f}s steps({n}) {t+0.25:.2f}s forwards"/>')
            t += 0.25 + dur + 0.25
        y += 24

    def out_row(key, val, color=WHITE):
        nonlocal y, t
        parts.append(f'<g{fade(t)}><text x="42" y="{y}" fill="{DIM}">{esc(key)}</text>'
                     f'<text x="200" y="{y}" fill="{color}" font-weight="700">{esc(val)}</text></g>')
        t += 0.14
        y += 22

    command("whoami")
    parts.append(f'<g{fade(t)}><text x="42" y="{y}" fill="{WHITE}" font-weight="700">{esc(FULL_NAME)}</text></g>')
    t += 0.3
    y += 32

    command(f"github-stats --user {USER}")
    for k, v in [("repositories", f"{d['repos']:,}"), ("total_stars", f"{d['stars']:,}"),
                 ("followers", f"{d['followers']:,}"), ("following", f"{d['following']:,}"),
                 ("total_commits", f"{d['commits']:,}"), ("member_since", d["since"])]:
        out_row(k, v, GREEN if k == "total_stars" else WHITE)
    y += 10

    top = sorted(d["langs"].items(), key=lambda x: -x[1])[:5]
    tot = sum(d["langs"].values()) or 1
    command("top-langs --limit 5")
    if not top:
        out_row("no_data", "-")
    for name, v in top:
        pct = v / tot * 100
        bw = 260
        fill_w = max(4.0, 260 * pct / 100)
        parts.append(f'<g{fade(t)}><text x="42" y="{y}" fill="{WHITE}">{esc(name)}</text>'
                     f'<rect x="200" y="{y-10}" width="{bw}" height="10" rx="2" fill="{BAR}" stroke="{BORDER}"/>'
                     f'<rect x="200" y="{y-10}" width="{fill_w:.1f}" height="10" rx="2" fill="{GREEN}" opacity=".85"/>'
                     f'<text x="478" y="{y}" fill="{GREEN}" font-weight="700">{pct:.1f}%</text></g>')
        t += 0.14
        y += 22
    y += 10

    command("")
    cursor_x = cmd_x
    parts.append(f'<rect class="cur" x="{cursor_x:.1f}" y="{y-36}" width="9" height="17" fill="{GREEN}"/>')

    H = y + 4
    css = f"""
    text{{font-family:'Fira Code','DejaVu Sans Mono',Menlo,Consolas,'Courier New',monospace;font-size:13px}}
    .f{{opacity:0;animation:fi .35s ease forwards}}
    @keyframes fi{{to{{opacity:1}}}}
    @keyframes type{{to{{transform:translateX(var(--w))}}}}
    .cur{{animation:bl 1.1s steps(1) infinite}}
    @keyframes bl{{50%{{opacity:0}}}}
    @media (prefers-reduced-motion:reduce){{.f{{animation:none;opacity:1}}.cv{{display:none}}.cur{{animation:none}}}}
    """
    if STATIC:
        css = css.replace(".cur{animation:bl 1.1s steps(1) infinite}", "")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="GitHub stats terminal for {esc(USER)}">'
           f'<style>{css}</style>'
           f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
           f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W-21}a10 10 0 0 1 10 10V34H.5z" fill="{BAR}"/>'
           f'<line x1=".5" y1="34.5" x2="{W-.5}" y2="34.5" stroke="{BORDER}"/>'
           f'<circle cx="22" cy="17.5" r="5.5" fill="#ff5f57"/><circle cx="42" cy="17.5" r="5.5" fill="#febc2e"/>'
           f'<circle cx="62" cy="17.5" r="5.5" fill="#28c840"/>'
           f'<text x="{W/2}" y="22" text-anchor="middle" fill="{DIM}" font-size="12">{esc(USER)} — bash — 80x24</text>'
           + "".join(parts) + "</svg>\n")
    return svg


if __name__ == "__main__":
    data = collect()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "terminal.svg"), "w", encoding="utf-8") as f:
        f.write(terminal_svg(data))
    print("ok", {k: v for k, v in data.items() if k != "langs"}, list(data["langs"])[:5])
