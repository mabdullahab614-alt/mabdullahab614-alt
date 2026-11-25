#!/usr/bin/env python3
"""
Builds the two SVGs used by the profile README.

  assets/hero.svg      name + photo + availability   (static)
  assets/activity.svg  live GitHub stats + 52-week bars

Live mode: GH_TOKEN set (GitHub Actions)   Demo mode: python scripts/generate.py --demo
"""
import base64, json, math, os, random, sys, urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "mabdullahab614-alt")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT, exist_ok=True)

CREAM, INK, CORAL, MUTED, GREEN = "#F4EFE6", "#141414", "#FF5A36", "#8A8378", "#2E9E5B"
SERIF = "Georgia,'Times New Roman',serif"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
LIVE_PROJECTS = 29


def fetch_live():
    q = """query($login:String!){user(login:$login){
      repositories(ownerAffiliations:OWNER,privacy:PUBLIC){totalCount}
      contributionsCollection{totalCommitContributions
        contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"})
    resp = json.load(urllib.request.urlopen(req))
    if not resp.get("data") or not resp["data"].get("user"):
        sys.exit("GitHub API error: " + json.dumps(resp)[:700])
    u = resp["data"]["user"]; cc = u["contributionsCollection"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]]
    return dict(weeks=weeks, total=cc["contributionCalendar"]["totalContributions"],
                commits=cc["totalCommitContributions"], repos=u["repositories"]["totalCount"])


def fetch_demo():
    r = random.Random(5)
    weeks = [[0 if r.random() > .3 + .6 * w / 52 else r.randint(1, 9) for _ in range(7)] for w in range(53)]
    return dict(weeks=weeks, total=sum(map(sum, weeks)), commits=1700, repos=39)


def streak(weeks):
    days = [c for w in weeks for c in w]
    tail = days[:-1] if days and days[-1] == 0 else days   # today may not be committed yet
    n = 0
    for c in reversed(tail):
        if not c: break
        n += 1
    return n


def save(name, s):
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(s)
    print("wrote", name, len(s) // 1024, "KB")


def hero():
    photo = ""
    p = os.path.join(OUT, "avatar-cutout.png")
    if os.path.exists(p):
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        photo = (f'<g clip-path="url(#card)"><image href="data:image/png;base64,{b64}" '
                 f'x="545" y="14" width="326" height="326"/></g>')
    else:  # fallback monogram if the cutout file is missing
        photo = (f'<text x="705" y="212" text-anchor="middle" font-family="{SERIF}" font-size="92" '
                 f'font-weight="700" fill="{CREAM}" letter-spacing="-3">AJ</text>')
    body = f'''<defs><clipPath id="card"><rect width="860" height="340" rx="22"/></clipPath></defs>
<rect width="860" height="340" rx="22" fill="{CREAM}"/>
<g clip-path="url(#card)">
<circle cx="706" cy="190" r="124" fill="{CORAL}"/>
<circle cx="706" cy="190" r="124" fill="none" stroke="{INK}" stroke-width="2" transform="translate(14 14)"/></g>
{photo}
<text x="56" y="76" font-family="{SANS}" font-size="13" font-weight="700" letter-spacing="3" fill="{MUTED}">AI &amp; ML ENGINEER  ·  LAHORE, PAKISTAN</text>
<text x="52" y="162" font-family="{SERIF}" font-size="84" font-weight="700" fill="{INK}" letter-spacing="-2">Abdullah</text>
<text x="52" y="242" font-family="{SERIF}" font-size="84" font-weight="700" fill="{INK}" letter-spacing="-2">Javid<tspan fill="{CORAL}">.</tspan></text>
<text x="56" y="280" font-family="{SANS}" font-size="17" fill="{INK}">I build AI products that ship, from model to live link.</text>
<g transform="translate(56 298)"><rect width="318" height="30" rx="15" fill="{INK}"/>
<circle cx="19" cy="15" r="5" fill="{GREEN}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>
<text x="34" y="20" font-family="{SANS}" font-size="13" font-weight="600" fill="{CREAM}">Available for freelance &amp; internships</text></g>'''
    save("hero-v2.svg", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 340" width="860" height="340">{body}</svg>')


def activity(d):
    wk = [sum(w) for w in d["weeks"]][-52:]
    mx = max(wk) or 1
    stats = [(f'{d["total"]:,}', "CONTRIBUTIONS / YEAR"), (f'{d["commits"]:,}', "COMMITS"),
             (str(streak(d["weeks"])), "DAY STREAK"), (str(d["repos"]), "PUBLIC REPOS")]
    top = "".join(
        f'<text x="{48 + i * 205}" y="76" font-family="{SERIF}" font-size="46" font-weight="700" fill="{CREAM}">{escape(v)}</text>'
        f'<text x="{50 + i * 205}" y="100" font-family="{SANS}" font-size="11" font-weight="700" letter-spacing="2" fill="{MUTED}">{l}</text>'
        for i, (v, l) in enumerate(stats))
    bars, bw, gap, base = "", 9.2, 6.2, 212
    for i, c in enumerate(wk):
        h = 4 if not c else 8 + 62 * math.sqrt(c / mx)
        col = MUTED if not c else (CREAM if i == len(wk) - 1 else CORAL)
        op = .35 if not c else 1
        bars += (f'<rect x="{48 + i * (bw + gap):.1f}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" rx="3" '
                 f'fill="{col}" opacity="{op}"/>')
    body = f'''<rect width="860" height="268" rx="22" fill="{INK}"/>{top}{bars}
<text x="48" y="248" font-family="{SANS}" font-size="11" letter-spacing="1.5" fill="{MUTED}">LAST 52 WEEKS  ·  UPDATED AUTOMATICALLY FROM GITHUB</text>'''
    save("activity.svg", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 268" width="860" height="268">{body}</svg>')


if __name__ == "__main__":
    demo = "--demo" in sys.argv or "GH_TOKEN" not in os.environ
    data = fetch_demo() if demo else fetch_live()
    print("mode:", "demo" if demo else "live", "| total", data["total"])
    hero(); activity(data)
