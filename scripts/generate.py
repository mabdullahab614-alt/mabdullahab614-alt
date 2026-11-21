#!/usr/bin/env python3
"""
Generates the animated SVGs for Abdullah Javid's GitHub profile README.

  assets/name3d.svg    3D animated name
  assets/city.svg      isometric Contribution City  (1 block = 1 day, 1 row = 1 week)
  assets/skyline.svg   neon skyline                 (1 tower = 1 week of commits)
  assets/pet.svg       Code Pet that grows with total contributions
  assets/holocard.svg  holographic collector card with live stats

Live mode : GH_TOKEN env var set (GitHub Actions provides it)  -> real data
Demo mode : python scripts/generate.py --demo                  -> fake data
"""
import base64, json, math, os, random, sys, urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "mabdullahab614-alt")
NAME = "ABDULLAH JAVID"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT, exist_ok=True)

CYAN, PURPLE, PINK, GREEN, BG = "#00d9ff", "#9d4edd", "#ff006e", "#00ff88", "#0a0e27"


# ───────────────────────── data ─────────────────────────
def fetch_live():
    q = """query($login:String!){user(login:$login){
      followers{totalCount}
      repositories(ownerAffiliation:OWNER,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount}}
      contributionsCollection{totalCommitContributions totalPullRequestContributions
        contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"},
    )
             resp = json.load(urllib.request.urlopen(req))
    if not resp.get("data") or not resp["data"].get("user"):
        sys.exit("GitHub API error: " + json.dumps(resp)[:700])
    u = resp["data"]["user"]
    cc = u["contributionsCollection"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]]
    dates = [d["date"] for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return dict(
        weeks=weeks, dates=dates,
        total=cc["contributionCalendar"]["totalContributions"],
        commits=cc["totalCommitContributions"], prs=cc["totalPullRequestContributions"],
        repos=u["repositories"]["totalCount"], followers=u["followers"]["totalCount"],
        stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
    )


def fetch_demo():
    r = random.Random(7)
    weeks = []
    for w in range(53):
        busy = 0.35 + 0.65 * (w / 52)
        weeks.append([0 if r.random() > busy * 0.8 else int(r.random() ** 2 * 14 * busy) + 1 for _ in range(7)])
    total = sum(map(sum, weeks))
    return dict(weeks=weeks, dates=[], total=total, commits=int(total * .85), prs=18, repos=34, followers=12, stars=9)


def streak(weeks):
    days = [c for w in weeks for c in w]
    best = cur = 0
    for c in days:
        cur = cur + 1 if c else 0
        best = max(best, cur)
    tail = days[:-1] if days and days[-1] == 0 else days  # today may not be committed yet
    now = 0
    for c in reversed(tail):
        if not c: break
        now += 1
    return now, best


# ───────────────────────── helpers ─────────────────────────
def svg(w, h, body, defs="", style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}"><defs>{defs}</defs><style>{style}</style>{body}</svg>')


def save(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", name, f"({len(content)//1024} KB)")


def shade(hex_, f):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))


def level_color(c, mx):
    if c == 0: return "#161b3a"
    t = c / max(mx, 1)
    return CYAN if t < .25 else GREEN if t < .5 else PURPLE if t < .75 else PINK


# ───────────────────────── 1. 3D name ─────────────────────────
def name3d():
    layers = ""
    for k in range(16, 0, -1):
        c = shade("#2a0f5c", 0.45 + 0.55 * (1 - k / 16))
        layers += (f'<text x="{60 + k * 1.1:.1f}" y="{112 + k * 1.1:.1f}" fill="{c}" textLength="780" '
                   f'lengthAdjust="spacingAndGlyphs">{NAME}</text>')
    defs = (f'<linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/>'
            f'<stop offset=".5" stop-color="#ffffff"/><stop offset="1" stop-color="{PINK}"/>'
            f'<animate attributeName="x1" values="0;1;0" dur="6s" repeatCount="indefinite"/></linearGradient>'
            f'<filter id="g" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>')
    body = (f'<g transform="translate(450 0)"><g><animateTransform attributeName="transform" type="skewX" '
            f'values="-4;4;-4" dur="7s" repeatCount="indefinite"/><g transform="translate(-450 0)" '
            f'font-family="Impact,\'Arial Black\',sans-serif" font-size="104" font-weight="900">'
            f'<text x="62" y="114" fill="{PINK}" opacity=".55" filter="url(#g)" textLength="780" lengthAdjust="spacingAndGlyphs">{NAME}</text>'
            f'{layers}<text x="60" y="112" fill="url(#f)" stroke="#fff" stroke-width="1.2" textLength="780" '
            f'lengthAdjust="spacingAndGlyphs">{NAME}</text></g></g></g>')
    save("name3d.svg", svg(900, 170, body, defs))


# ───────────────────────── 2. Contribution City ─────────────────────────
def city(d):
    weeks = d["weeks"]
    mx = max(max(w) for w in weeks) or 1
    a, b = 13, 6.2
    ox, oy = 110, 150
    parts = []
    cells = [(i, j, c) for i, w in enumerate(weeks) for j, c in enumerate(w)]
    cells.sort(key=lambda t: (t[0] + t[1], t[0]))
    for i, j, c in cells:
        x, y = ox + (i - j) * a, oy + (i + j) * b
        h = 2 if c == 0 else 6 + 100 * math.sqrt(c / mx)
        col = level_color(c, mx)
        s = .88
        A, B = a * s, b * s
        top = f"{x},{y - h - B} {x + A},{y - h} {x},{y - h + B} {x - A},{y - h}"
        lef = f"{x - A},{y - h} {x},{y - h + B} {x},{y + B} {x - A},{y}"
        rig = f"{x},{y - h + B} {x + A},{y - h} {x + A},{y} {x},{y + B}"
        delay = f"{(i * 0.03 + j * 0.01):.2f}"
        parts.append(
            f'<g class="b" style="animation-delay:{delay}s"><polygon points="{lef}" fill="{shade(col, .55)}"/>'
            f'<polygon points="{rig}" fill="{shade(col, .8)}"/><polygon points="{top}" fill="{col}"/></g>')
    style = (".b{transform-box:fill-box;transform-origin:50% 100%;animation:rise 1.2s ease-out both}"
             "@keyframes rise{from{transform:scaleY(0);opacity:0}to{transform:scaleY(1);opacity:1}}"
             ".t{font:600 14px 'Courier New',monospace;fill:#00d9ff}.s{font:12px 'Courier New',monospace;fill:#8b949e}")
    body = (f'<rect width="860" height="540" fill="{BG}"/>' + "".join(parts) +
            f'<text x="24" y="34" class="t">// CONTRIBUTION CITY</text>'
            f'<text x="24" y="54" class="s">{d["total"]} contributions · 1 block = 1 day · taller = more commits</text>')
    save("city.svg", svg(860, 540, body, style=style))


# ───────────────────────── 3. Neon skyline ─────────────────────────
def skyline(d):
    wk = [sum(w) for w in d["weeks"]][-52:]
    mx = max(wk) or 1
    r = random.Random(3)
    W, H, tw, gap = 900, 300, 14, 3.2
    x0 = (W - len(wk) * (tw + gap)) / 2
    base = H - 50
    stars = "".join(f'<circle cx="{r.randint(0, W)}" cy="{r.randint(5, 150)}" r="{r.random() * 1.2 + .3:.1f}" '
                    f'fill="#fff" class="tw" style="animation-delay:{r.random() * 3:.1f}s"/>' for _ in range(60))
    towers, wins = "", ""
    palette = [CYAN, PURPLE, PINK, GREEN]
    for i, c in enumerate(wk):
        h = 8 + 170 * math.sqrt(c / mx) if c else 5
        x = x0 + i * (tw + gap)
        col = palette[i % 3] if c else "#2a2f5a"
        towers += (f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{tw}" height="{h:.1f}" fill="#0d1130" stroke="{col}" '
                   f'stroke-width="1.4" filter="url(#n)" class="tower" style="animation-delay:{i * .04:.2f}s"/>')
        if c:
            for wy in range(int(base - h + 6), int(base - 4), 9):
                if r.random() < .55:
                    wins += (f'<rect x="{x + 3 + (r.random() > .5) * 5:.1f}" y="{wy}" width="3" height="4" fill="{col}" '
                             f'class="w" style="animation-delay:{r.random() * 4:.1f}s"/>')
    style = (".tw{animation:tw 3s infinite}@keyframes tw{50%{opacity:.15}}"
             ".w{animation:w 4s infinite}@keyframes w{0%,100%{opacity:1}50%{opacity:.15}}"
             ".tower{transform-box:fill-box;transform-origin:50% 100%;animation:up 1s ease-out both}"
             "@keyframes up{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
             ".t{font:600 14px 'Courier New',monospace;fill:#00d9ff}.s{font:12px 'Courier New',monospace;fill:#8b949e}")
    defs = (f'<filter id="n" x="-50%" y="-20%" width="200%" height="140%"><feGaussianBlur stdDeviation="1.6" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05071a"/>'
            f'<stop offset=".75" stop-color="#1a0b3d"/><stop offset="1" stop-color="#3a0b4d"/></linearGradient>')
    body = (f'<rect width="{W}" height="{H}" fill="url(#sky)"/>{stars}'
            f'<circle cx="810" cy="60" r="22" fill="#ffd6f2" opacity=".9" filter="url(#n)"/>'
            f'{towers}{wins}<rect x="0" y="{base}" width="{W}" height="2" fill="{PINK}" filter="url(#n)"/>'
            f'<text x="24" y="28" class="t">// NEON SKYLINE</text>'
            f'<text x="{W / 2}" y="{H - 18}" text-anchor="middle" class="s">each tower = 1 week of commits · last 52 weeks</text>')
    save("skyline.svg", svg(W, H, body, defs, style))


# ───────────────────────── 4. Code Pet ─────────────────────────
SPRITES = {  # half-rows, mirrored horizontally. o body, d outline, e eye, p pupil, c accent, b belly, y gold
    "egg": ["....dd", "..ddoo", ".dooco", ".doooo", "dooooo", "docooo", "dooooc", "dooooo", ".doooo", ".ddooo", "..dddd"],
    "baby": ["......d", "....ddd", "..ddooo", ".dooooo", ".dooooo", "doeeooo", "doepooo", "doooooc", "doooooo", ".dooooo", "..ddooo", "...d.dd"],
    "teen": [".c......", ".coc....", ".cooddd.", "..dooooo", ".doooooo", ".doeeooo", ".doepooo", ".dooooco", "dooooooo", ".dobbbbb", ".dobbbbb", "..dooooo", "..dd.ddd"],
    "adult": ["...c......", "...cd.....", "cc.dooooo.", "ccdooooooo", "cccdoooooo", "ccdoeeoooo", "cdoepooooo", "cdooooooco", ".dobbbbbbb", ".dobbbbbbb", "..dooooooo", "..dd.ddddd"],
    "legend": ["...y.y.y.y", "...yyyyyyy", "...c......", "...cd.....", "cc.dooooo.", "ccdooooooo", "cccdoooooo", "ccdoeeoooo", "cdoepooooo", "cdooooooco", ".dobbbbbbb", ".dobbbbbbb", "..dooooooo", "..dd.ddddd"],
}
PALETTE = {
    "egg": dict(o="#f4f1de", d="#3d405b", c="#9d4edd"),
    "baby": dict(o="#00d9ff", d="#06324a", e="#ffffff", p="#0a0e27", c="#ff006e"),
    "teen": dict(o="#00ff88", d="#064d2e", e="#ffffff", p="#0a0e27", c="#ff006e", b="#c9ffe6"),
    "adult": dict(o="#9d4edd", d="#2a0f5c", e="#ffffff", p="#0a0e27", c="#00d9ff", b="#e0c3fc"),
    "legend": dict(o="#ff006e", d="#4a0020", e="#ffffff", p="#0a0e27", c="#00d9ff", b="#ffc2d9", y="#ffd60a"),
}
STAGES = [("egg", "Code Egg", 0), ("baby", "Bit Hatchling", 30), ("teen", "Byte Runner", 150),
          ("adult", "Neural Dragon", 500), ("legend", "Singularity Lord", 1200)]


def pet(d):
    total = d["total"]
    idx = max(i for i, s in enumerate(STAGES) if total >= s[2])
    key, title, lo = STAGES[idx]
    nxt = STAGES[idx + 1][2] if idx + 1 < len(STAGES) else None
    pct = 1.0 if nxt is None else (total - lo) / (nxt - lo)
    last7 = sum(c for w in d["weeks"] for c in w)  # fallback
    flat = [c for w in d["weeks"] for c in w]
    last7 = sum(flat[-7:])
    mood = "STARVING · feed me commits!" if last7 == 0 else "HAPPY" if last7 < 10 else "HYPED 🔥"
    level = int(math.sqrt(total / 10)) + 1
    px = 11
    rows = SPRITES[key]
    pal = PALETTE[key]
    rects, eyes = "", ""
    for ry, half in enumerate(rows):
        row = half + half[::-1]
        for rx, ch in enumerate(row):
            if ch == ".": continue
            r_ = f'<rect x="{rx * px}" y="{ry * px}" width="{px}" height="{px}" fill="{pal[ch]}"/>'
            if ch in "ep": eyes += r_
            else: rects += r_
    sw, sh = len(rows[0]) * 2 * px, len(rows) * px
    tx, ty = 40 + (240 - sw) / 2, 50 + (150 - sh)
    sprite = (f'<g transform="translate({tx} {ty})"><g class="bob">{rects}<g class="blink">{eyes}</g></g></g>')
    if key == "legend":
        sprite += "".join(f'<text x="{x}" y="{y}" fill="{PINK}" class="sp" style="animation-delay:{dl}s">✦</text>'
                          for x, y, dl in [(50, 70, 0), (260, 90, 1), (80, 170, .5), (240, 40, 1.5)])
    style = (".bob{animation:bob 1.6s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-8px)}}"
             ".blink{transform-box:fill-box;transform-origin:50% 50%;animation:bl 4s infinite}"
             "@keyframes bl{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}"
             ".sp{font:16px sans-serif;animation:tw 2s infinite}@keyframes tw{50%{opacity:.1}}"
             ".t{font:600 14px 'Courier New',monospace;fill:#00d9ff}.m{font:13px 'Courier New',monospace;fill:#c9d1d9}"
             ".h{font:700 18px 'Courier New',monospace;fill:#fff}")
    bar = 440
    body = (f'<rect width="860" height="250" rx="14" fill="{BG}" stroke="{PURPLE}" stroke-width="1.5"/>'
            f'<text x="24" y="30" class="t">// CODE PET</text>'
            f'<rect x="30" y="44" width="260" height="170" rx="10" fill="#0d1130" stroke="#222a5c"/>'
            f'<g transform="translate(0 0)">{sprite}</g>'
            f'<text x="330" y="82" class="h">{escape(title)}  ·  LV {level}</text>'
            f'<text x="330" y="112" class="m">Mood : {mood}</text>'
            f'<text x="330" y="136" class="m">Food : {last7} contributions in the last 7 days</text>'
            f'<text x="330" y="160" class="m">XP   : {total} contributions this year</text>'
            f'<rect x="330" y="178" width="{bar}" height="14" rx="7" fill="#161b3a"/>'
            f'<rect x="330" y="178" width="{bar * min(pct, 1):.0f}" height="14" rx="7" fill="url(#xp)"><animate attributeName="opacity" values=".7;1;.7" dur="2s" repeatCount="indefinite"/></rect>'
            f'<text x="330" y="212" class="m">{"MAX LEVEL reached" if nxt is None else f"Evolves into {STAGES[idx + 1][1]} at {nxt} contributions"}</text>')
    defs = f'<linearGradient id="xp"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>'
    save("pet.svg", svg(860, 250, body, defs, style))


# ───────────────────────── 5. Holo card ─────────────────────────
def holocard(d):
    cur, best = streak(d["weeks"])
    total = d["total"]
    stars = 1 + sum(total >= t for t in (50, 200, 600, 1200))
    photo = ""
    p = os.path.join(OUT, "avatar.jpg")
    if os.path.exists(p):
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        photo = (f'<clipPath id="cp"><rect x="40" y="86" width="280" height="200" rx="10"/></clipPath>'
                 f'<image href="data:image/jpeg;base64,{b64}" x="40" y="86" width="280" height="200" '
                 f'preserveAspectRatio="xMidYMin slice" clip-path="url(#cp)"/>')
    stats = [("HP", f'{d["commits"]}', "commits"), ("ATK", f'{d["prs"]}', "pull requests"),
             ("DEF", f'{d["repos"]}', "public repos"), ("SPD", f"{cur}d / {best}d", "streak now / best")]
    st = "".join(f'<text x="44" y="{322 + i * 26}" class="k">{k}</text><text x="100" y="{322 + i * 26}" class="v">{escape(v)}</text>'
                 f'<text x="196" y="{322 + i * 26}" class="d">{escape(l)}</text>' for i, (k, v, l) in enumerate(stats))
    sp = "".join(f'<polygon points="0,-7 2,-2 7,0 2,2 0,7 -2,2 -7,0 -2,-2" fill="#fff" transform="translate({x} {y})" class="sp" '
                 f'style="animation-delay:{dl}s"/>' for x, y, dl in [(300, 70, 0), (60, 300, .7), (320, 250, 1.4), (180, 60, 2)])
    defs = (f'<linearGradient id="holo" x1="0" y1="0" x2="1" y2="1" gradientUnits="objectBoundingBox">'
            f'<stop offset="0" stop-color="#ff006e"/><stop offset=".25" stop-color="#ffd60a"/><stop offset=".5" stop-color="#00ff88"/>'
            f'<stop offset=".75" stop-color="#00d9ff"/><stop offset="1" stop-color="#9d4edd"/>'
            f'<animateTransform attributeName="gradientTransform" type="rotate" from="0 .5 .5" to="360 .5 .5" dur="8s" repeatCount="indefinite"/></linearGradient>'
            f'<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="card"><rect x="8" y="8" width="344" height="504" rx="22"/></clipPath>')
    style = (".n{font:900 26px Impact,'Arial Black',sans-serif;fill:#fff;letter-spacing:1px}"
             ".r{font:600 12px 'Courier New',monospace;fill:#0a0e27}"
             ".k{font:700 14px 'Courier New',monospace;fill:#00d9ff}.v{font:700 14px 'Courier New',monospace;fill:#fff}"
             ".d{font:12px 'Courier New',monospace;fill:#8b949e}.mv{font:12px 'Courier New',monospace;fill:#e0c3fc}"
             ".sp{animation:tw 2.2s infinite}@keyframes tw{0%,100%{opacity:0;transform:scale(.3)}50%{opacity:1}}")
    body = (f'<rect x="2" y="2" width="356" height="516" rx="26" fill="url(#holo)"/>'
            f'<rect x="8" y="8" width="344" height="504" rx="22" fill="#0b0f2e"/>'
            f'<g clip-path="url(#card)">'
            f'<rect x="8" y="8" width="344" height="504" fill="url(#holo)" opacity=".18"/>'
            f'<rect x="-200" y="0" width="140" height="520" fill="url(#shine)" transform="skewX(-20)">'
            f'<animate attributeName="x" values="-200;520;-200" dur="4.5s" repeatCount="indefinite"/></rect></g>'
            f'<text x="28" y="48" class="n">{NAME}</text>'
            f'<text x="332" y="48" text-anchor="end" fill="#ffd60a" font-size="14">{"★" * stars}</text>'
            f'<text x="28" y="70" class="d">AI ENGINEER · ML · BUILDER + DEPLOYER</text>'
            f'<rect x="36" y="82" width="288" height="208" rx="12" fill="url(#holo)"/>'
            f'<rect x="40" y="86" width="280" height="200" rx="10" fill="#0d1130"/>{photo}'
            f'<rect x="40" y="86" width="280" height="200" rx="10" fill="url(#holo)" opacity=".22"/>'
            f'<rect x="28" y="296" width="304" height="1" fill="#2a3070"/>{st}'
            f'<rect x="28" y="428" width="304" height="1" fill="#2a3070"/>'
            f'<text x="28" y="450" class="mv">⚡ Train Model  — ship it to Hugging Face</text>'
            f'<text x="28" y="470" class="mv">🚀 Deploy      — 30+ live projects</text>'
            f'<text x="28" y="496" class="d">BS AI · UMT Lahore · Lahore, PK · {date.today().year}</text>{sp}')
    save("holocard.svg", svg(360, 520, body, defs, style))


# ───────────────────────── main ─────────────────────────
if __name__ == "__main__":
    data = fetch_demo() if ("--demo" in sys.argv or "GH_TOKEN" not in os.environ) else fetch_live()
    print("mode:", "demo" if "--demo" in sys.argv or "GH_TOKEN" not in os.environ else "live", "· total", data["total"])
    name3d(); city(data); skyline(data); pet(data); holocard(data)
