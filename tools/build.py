"""Build the static FROST portal.

Usage: python3 tools/build.py
Reads tools/content.py, data/publications.json and data/sources.json (refreshed from the
proposal bibliography when it is present next to this repo), writes HTML at the repo root.
All links are relative, so the site works at any base path (e.g. /frost/ on GitHub Pages).
"""
import html
import json
import os
import re
import sys
from collections import Counter, OrderedDict

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import content as C  # noqa: E402
import pubs as P  # noqa: E402

E = html.escape
YEAR = "2026"

# ------------------------------------------------------------------ data
PUBS = json.load(open(os.path.join(ROOT, "data", "publications.json"), encoding="utf-8"))


def load_sources():
    keys = sorted({k for d in C.DATASETS for k in d["sources"]})
    cache = os.path.join(ROOT, "data", "sources.json")
    if os.path.exists(P.DEFAULT_BIB):
        s = open(P.DEFAULT_BIB, encoding="utf-8").read()
        out = {}
        for e in re.split(r"\n(?=@)", s):
            m = re.match(r"@(\w+)\{([^,]+),", e)
            if not m or m.group(2).strip() not in keys:
                continue
            out[m.group(2).strip()] = {
                "title": P.clean(P.field(e, "title")), "authors": P.short_authors(P.field(e, "author")),
                "year": P.field(e, "year"), "venue": P.clean(P.field(e, "journal") or P.field(e, "booktitle")),
                "doi": P.field(e, "doi")}
        json.dump(out, open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return out
    return json.load(open(cache, encoding="utf-8"))


SRC = load_sources()
DS = {d["id"]: d for d in C.DATASETS}
COLL = {c["id"]: c for c in C.COLLECTIONS}
LAYER_HEX = {k: v[1] for k, v in C.LAYERS.items()}
LAYER_INK = {"exp": "#1d4fb0", "cfd": "#00706f", "gai": "#6a3cad", "app": "#a85508"}
ORIGIN = {"measured": "Measured", "simulation": "Simulation", "model": "Model output", "external": "External record"}
REL_CLASS = {"v0.5": "rel-v05", "v1.0": "rel-v10", "v2.0": "rel-v20"}
CAPTIONS = {}  # image name -> caption, filled from content below


def img_ar(name):
    p = os.path.join(ROOT, "assets", "img", "t", name + ".jpg")
    w, h = Image.open(p).size
    return w / h


def cite(k):
    s = SRC.get(k)
    if not s:
        return ""
    doi = f" https://doi.org/{s['doi']}" if s["doi"] else ""
    return f"{s['authors']} ({s['year']}). {s['title']}. {s['venue']}.{doi}"


# ------------------------------------------------------------------ icons
I = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "zoom": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M11 8v6M8 11h6"/>',
    "x": '<path d="M6 6l12 12M18 6 6 18"/>',
    "left": '<path d="m15 6-6 6 6 6"/>',
    "right": '<path d="m9 6 6 6-6 6"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "ext": '<path d="M14 4h6v6M20 4l-9 9M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "code": '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/>',
    "bot": '<rect x="4" y="8" width="16" height="11" rx="3"/><path d="M12 4v4M9 13h.01M15 13h.01M2 13v3M22 13v3"/>',
    "db": '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "shield": '<path d="M12 3 5 6v6c0 4.4 3 7.6 7 9 4-1.4 7-4.6 7-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a5.5 5.5 0 0 1 3.5 6"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/>',
    "flake": '<path d="M12 2v20M3.3 7l17.4 10M20.7 7 3.3 17M9 4l3 2.5L15 4M9 20l3-2.5 3 2.5"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
    "check": '<path d="m5 12 5 5 9-10"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>',
    "plane": '<path d="M10 14 3 12l1-2 7 1 4-7h2l-2 8 5 1 1-2h1.5l-1 4 1 4H22l-1-2-5 1 2 8h-2l-4-7z"/>',
}


def icon(name, cls=""):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{I[name]}</svg>')


def logo(uid):
    arms = ('<path d="M20 8.5v23M10 14.25l20 11.5M30 14.25l-20 11.5"/>'
            '<path d="M17.2 11.2 20 13.4l2.8-2.2M17.2 28.8 20 26.6l2.8 2.2"/>')
    return (f'<svg viewBox="0 0 40 40" aria-hidden="true"><defs><linearGradient id="lg{uid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#5b9dff"/><stop offset=".55" stop-color="#2b6fe3"/><stop offset="1" stop-color="#00a6a6"/></linearGradient></defs>'
            f'<path d="M20 1.8 35.8 10.9v18.2L20 38.2 4.2 29.1V10.9z" fill="url(#lg{uid})"/>'
            f'<path d="M20 1.8 35.8 10.9v18.2L20 38.2 4.2 29.1V10.9z" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="1"/>'
            f'<g stroke="#fff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" fill="none">{arms}'
            f'<g transform="rotate(60 20 20)"><path d="M17.2 11.2 20 13.4l2.8-2.2M17.2 28.8 20 26.6l2.8 2.2"/></g>'
            f'<g transform="rotate(120 20 20)"><path d="M17.2 11.2 20 13.4l2.8-2.2M17.2 28.8 20 26.6l2.8 2.2"/></g></g></svg>')


FAVICON = ("data:image/svg+xml," + re.sub(r"\s+", " ", logo("f")).replace('"', "'").replace("#", "%23")
           .replace("<", "%3C").replace(">", "%3E"))


# ------------------------------------------------------------------ chrome
def head(title, desc, r):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/css/frost.css">
</head>"""


def header(active, r):
    links = "".join(
        f'<a href="{r}{h}"{" aria-current=page" if h == active else ""}>{E(t)}</a>' for h, t in C.NAV)
    return f"""<div class="banner"><span class="dot"></span><strong>Preview of the FROST portal.</strong> Records are in curation; the first public release is FROST v0.5. Until then, the team shares data on request.</div>
<header class="site-header">
  <div class="container bar">
    <a class="brand" href="{r}index.html" aria-label="FROST home">{logo("h")}<span><span class="wm">FROST</span><span class="sub">AI-ready aircraft icing data</span></span></a>
    <nav class="nav" aria-label="Main">{links}</nav>
    <a class="btn btn-primary btn-sm header-cta" href="{r}access.html#request">Request access</a>
    <button class="menu-btn" aria-label="Menu" aria-expanded="false">{icon("menu")}</button>
  </div>
</header>"""


def footer(r):
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="foot">
      <div>
        <a class="brand" href="{r}index.html">{logo("f")}<span><span class="wm">FROST</span><span class="sub">{E(C.SITE['full'])}</span></span></a>
        <p style="margin-top:18px;max-width:380px">An AI-ready, governed community dataset of aircraft icing, built from two decades of icing-tunnel experiments and flight-test campaigns linked to validated simulation.</p>
        <p style="margin:0">Iowa State University · Georgia Institute of Technology</p>
      </div>
      <div><h4>Explore</h4><ul>
        <li><a href="{r}datasets.html">Datasets</a></li><li><a href="{r}record-s1223.html">Example record</a></li>
        <li><a href="{r}benchmarks.html">FROST-Bench</a></li><li><a href="{r}ai.html">AI &amp; Agents</a></li></ul></div>
      <div><h4>Project</h4><ul>
        <li><a href="{r}team.html">Team</a></li><li><a href="{r}publications.html">Publications</a></li>
        <li><a href="{r}software.html">Software</a></li><li><a href="{r}access.html">Access &amp; governance</a></li></ul></div>
      <div><h4>Contact</h4><ul>
        <li><a href="mailto:{C.SITE['email']}">{C.SITE['email']}</a></li>
        <li><a href="{r}access.html#request">Request data access</a></li>
        <li><a href="{r}access.html#contribute">Contribute data</a></li></ul></div>
    </div>
    <div class="fine"><span>Preview build · {C.SITE['updated']}. Images are from the team's own archives and publications unless credited otherwise.</span><span>Data licenses: CC-BY-4.0 for Open-tier releases · code under OSI licenses</span></div>
  </div>
</footer>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="Image viewer">
  <button class="x" aria-label="Close">{icon("x")}</button><button class="prev" aria-label="Previous">{icon("left")}</button><button class="next" aria-label="Next">{icon("right")}</button>
  <figure><img alt=""><figcaption></figcaption></figure>
</div>
<script src="{r}assets/js/frost.js"></script>"""


def page(fname, active, title, desc, body, dark=True, extra=""):
    r = "../" if "/" in fname else ""
    out = (head(title, desc, r) + f'\n<body{" data-dark-hero" if dark else ""}>\n' + header(active, r)
           + "\n<main>\n" + body.replace("{R}", r) + "\n</main>\n" + extra + footer(r) + "\n</body>\n</html>\n")
    path = os.path.join(ROOT, fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(out)


def page_hero(eyebrow, title, text, crumbs="", bg=None):
    bgh = f'<div class="bgimg" style="background-image:url({{R}}assets/img/{bg}.jpg)"></div>' if bg else ""
    return f"""<section class="page-hero">{bgh}
  <div class="container">
    {crumbs}
    <span class="eyebrow">{eyebrow}</span>
    <h1>{title}</h1>
    <p>{text}</p>
  </div>
</section>"""


def badge_rel(rel):
    return f'<span class="badge {REL_CLASS[rel]}">FROST {rel}</span>'


def badge_org(o):
    return f'<span class="badge org-{o}">{ORIGIN[o]}</span>'


def img(name, alt, cls="", thumb=True, r="{R}", lazy=True):
    path = f"{r}assets/img/{'t/' if thumb else ''}{name}.jpg"
    return f'<img src="{path}" alt="{E(alt)}"{" loading=lazy" if lazy else ""}{f" class={cls}" if cls else ""}>'


# ------------------------------------------------------------------ captions
CAPTIONS.update({
    "irt-facility": "The ISU Icing Research Tunnel (ISU-IRT)",
    "irt-iced-wing": "Iced wing model in the ISU-IRT",
    "irt-layout": "ISU-IRT layout with the S1223 model (chord 200 mm, span 400 mm)",
    "irt-glaze-horns": "Glaze horns on an airfoil in the ISU-IRT",
    "hs-airfoil": "High-speed imaging of ice growing on an airfoil leading edge",
    "dip-film": "DIP measurement of runback water-film thickness on an airfoil",
    "dip-fringe": "Projected fringe pattern used by Digital Image Projection",
    "dip-droplet": "DIP thickness map of an impinging droplet",
    "dip-film-sequence": "Time sequence of runback film thickness",
    "dip-rivulet": "Runback rivulet head, body, and front contact line (DIP)",
    "mtt-droplet": "Temperature inside a freezing droplet by molecular tagging thermometry",
    "dih-droplets": "Cloud droplets recorded by digital inline holography",
    "scan-airfoil": "3D scans of ice at four liquid water contents",
    "scan-s1223": "3D-scanned ice on the S1223 UAV wing, suction and pressure sides",
    "scan-propeller": "3D scan of an iced UAV propeller blade with extracted ice profiles",
    "scan-growth": "Time-resolved 3D scan of ice growth",
    "scan-roughness": "Laser-scanned ice roughness",
    "scan-rotor-sections": "Scanned rotor-blade ice with sectional profiles",
    "piv-propeller": "Phase-locked PIV vorticity behind an iced propeller blade",
    "piv-s1223": "PIV over the rime-iced S1223 replica; the shadow region below the wing is unmeasured",
    "cp-s1223": "Surface pressure on the clean and rime-iced airfoil",
    "ir-plasma": "IR thermography of DBD plasma actuators at increasing voltage",
    "plasma-glow": "DBD plasma discharge on a test article",
    "plasma-blade": "Plasma actuator glowing on a rotor blade",
    "coating-compare": "Ice accretion with and without a superhydrophobic coating",
    "coating-runback": "Runback and ice on a hydrophilic airfoil surface over time",
    "heater-ir": "Surface temperature during heated anti-icing",
    "rotor-ice-sequence": "Ice accretion on a rotating UAV propeller blade, from clean to lobster-tail ice",
    "rotor-heating": "Rotor blade icing with rotor-integrated heating at increasing power",
    "propeller-glaze": "Glaze ice on a UAV propeller",
    "engine-fan": "Ice on a rotating aero-engine fan and spinner",
    "cable-iced": "Scanned ice on a power-transmission conductor",
    "uav-iced": "Iced UAV after an icing flight (1.8 m span)",
    "uav-instrumented": "Instrumented UAV for icing flights: Pitot tube, camera, humidity sensor",
    "uav-inflight-ice": "Ice on the wing and vertical stabilizer after an icing flight",
    "uav-power": "UAV power draw in a mission with in-flight icing vs. one without",
    "uav-trajectory": "Flight trajectory of an icing mission",
    "wmles-leading-edge": "Wall-modeled LES over a rime-iced leading edge",
    "wmles-rime": "WMLES of a rime-iced airfoil",
    "wmles-stall": "Iced-airfoil stall (WMLES)",
    "crm65-surface-flow": "Surface flow on the iced CRM65 swept wing",
    "crm65-scans": "Ice shapes on the CRM65 swept wing",
    "naca-ice-shapes": "Laser-scanned IRT ice shapes on the NACA 23012",
    "wmles-cp-glaze": "WMLES vs. IRT surface pressure on glaze ice",
    "cht-les": "Conjugate-heat-transfer LES on scanned ice",
    "cht-vs-ir": "Surface temperature: simulation vs. IR experiment (cases s43, s55)",
    "cht-cases": "Simulated surface temperature for three roughness cases",
    "artificial-vs-real-ice": "Real (scanned) and artificial ice shapes",
    "wmles-roughness": "Flow over leading-edge ice roughness (LES)",
    "s1223-les-fields": "High-order LES of the rime-iced S1223: instantaneous fields",
    "s1223-les-mean": "High-order LES: mean velocity over the rime-iced S1223",
    "s1223-rans": "External RANS of a scanned S1223 shape",
    "s1223-les-3d": "High-order GPU LES of the rime-iced S1223 (346 M unknowns)",
    "irt402": "Ice shape, NASA IRT run 402: model ensemble vs. repeat runs",
    "irt403": "Ice shape, NASA IRT run 403: model ensemble vs. repeat runs",
    "irt405": "Ice shape, NASA IRT run 405: model ensemble vs. repeat runs",
    "ice-model-fields": "Agent-built ice-model fields: collection efficiency, heat-transfer coefficient, surface temperature",
    "ice-shape-band": "Predicted ice-shape ensemble against the NASA measurement",
    "physminer-vortices": "PhysMiner: agent-labeled K–H and hairpin vortices over a glaze-iced airfoil",
    "physminer-triple": "PhysMiner triple decomposition: rigid rotation, normal strain, pure shear",
    "physminer-arch": "PhysMiner architecture: literature track, data track, knowledge fusion, review",
    "physminer-session": "PhysMiner interactive session",
    "physminer-iddes": "IDDES of the glaze-iced airfoil",
    "convlstm-exp": "DIP measurement of runback film",
    "convlstm-pred": "ConvLSTM forecast of the same film",
    "uas-military": "Military UAS in cold weather. Photo: U.S. Marine Corps (public domain)",
    "community-uas": "Uncrewed aircraft. Photo: NASA (public domain)",
    "outreach-reu": "Undergraduates in the NSF LAUNCH-UAS REU program present their research (2022)",
    "outreach-lab": "Graduate students curate and use icing data in the ISU-IRT",
})


def cap(n):
    return CAPTIONS.get(n, "")


# ------------------------------------------------------------------ components
def ds_card(d, i, r="{R}"):
    c = COLL[d["collection"]]
    col = LAYER_HEX[c["layer"]]
    ink = LAYER_INK[c["layer"]]
    im = (img(d["images"][0], cap(d["images"][0]), r=r) if d["images"]
          else f'<div class="ph">{icon("db")}</div>')
    tags = "".join(f'<span class="chip">{E(m)}</span>' for m in d["modalities"][:3])
    years = [int(SRC[k]["year"]) for k in d["sources"] if k in SRC and SRC[k]["year"].isdigit()]
    text = " ".join([d["title"], d["summary"], " ".join(d["modalities"]), d["geometry"], " ".join(d["regime"]), c["name"], d["holder"]])
    return f"""<a class="ds" href="{r}datasets/{d['id']}.html" data-item data-order="{i}" data-title="{E(d['title'])}"
  data-collection="{d['collection']}" data-origin="{d['origin']}" data-release="{d['release']}" data-geometry="{E(d['geometry'])}"
  data-modality="{E('|'.join(d['modalities']))}" data-year="{max(years) if years else 2026}" data-text="{E(text.lower())}" style="--c:{col};--ci:{ink}">
  <div class="im">{im}<div class="tl">{badge_rel(d['release'])}{badge_org(d['origin'])}</div></div>
  <div class="bar"></div>
  <div class="bd"><span class="coll">{E(c['name'])}</span><h3>{E(d['title'])}</h3><p>{E(d['summary'])}</p><div class="tags">{tags}</div></div>
  <div class="ft"><span>{E(d['holder'])}</span><span><span class="status-dot"></span>&nbsp; In curation</span></div>
</a>"""


def src_item(k):
    s = SRC.get(k)
    if not s:
        return ""
    doi = (f'<a href="https://doi.org/{E(s["doi"])}" target="_blank" rel="noopener">doi:{E(s["doi"])} {icon("ext")}</a>'
           if s["doi"] else "")
    return f"""<li class="src"><div class="ti">{E(s['title'])}</div><div class="au">{E(s['authors'])} · <i>{E(s['venue'])}</i>, {E(s['year'])}</div>
  <div class="ac">{doi}<button class="copy" data-copy="{E(cite(k))}">Copy citation</button></div></li>"""


# ------------------------------------------------------------------ home
def build_home():
    wall_cols = [
        ["wmles-leading-edge", "rotor-ice-sequence", "scan-s1223", "irt-facility", "plasma-glow", "physminer-vortices"],
        ["s1223-les-3d", "uav-iced", "cht-les", "ir-plasma", "scan-airfoil", "crm65-surface-flow"],
        ["piv-propeller", "hs-airfoil", "engine-fan", "dip-film", "uav-instrumented", "irt402"],
    ]
    cols = ""
    for col in wall_cols:
        figs = ""
        for n in col + col:
            ar = min(max(img_ar(n), 0.8), 1.7)
            figs += f'<figure style="--ar:{ar:.3f}">{img(n, cap(n))}<figcaption>{E(cap(n))}</figcaption></figure>'
        cols += f'<div class="col">{figs}</div>'

    stats = [("~200", "TB", "aircraft-icing archive"), ("20", "yrs", "of tunnel and flight campaigns"),
             ("50+", "", "data products inventoried by agents"), ("68", "", "open-access papers read in the pilot"),
             ("100+", "", "UAV flight missions, 40+ in icing"), ("1.2", "B", "control volumes in validated LES")]
    stats_html = "".join(f'<div class="stat"><div class="n">{n}<small>{u}</small></div><div class="l">{E(l)}</div></div>' for n, u, l in stats)

    news = "".join(f"""<a class="news-card fade-in" href="{{R}}{n['href']}">
      <div class="im">{img(n['img'], n['title'])}</div>
      <div class="bd"><div class="meta"><span class="badge" style="background:{LAYER_HEX[n['color']]}1a;color:{LAYER_INK[n['color']]}">{E(n['tag'])}</span><span>{E(n['date'])}</span></div>
      <h3>{E(n['title'])}</h3><p>{E(n['text'])}</p></div></a>""" for n in C.NEWS)

    layers = [
        ("01", "exp", "Legacy experiments", "Objective 1 · Aims 1.1–1.2", "The only university-owned icing research tunnel in the U.S.; ~20 years, ~200 TB.", "validate · harmonize",
         [("irt-facility", "ISU Icing Research Tunnel"), ("irt-iced-wing", "Iced wing in the ISU-IRT"), ("uav-iced", "Iced UAV after an icing flight")]),
        ("02", "cfd", "Validated simulation", "Objective 1 · Aim 1.3", "Complete what experiments cannot measure, inside measurement uncertainty.", "augment · complete",
         [("wmles-rime", "WMLES, rime-iced airfoil"), ("crm65-surface-flow", "Surface flow, iced swept wing"), ("wmles-stall", "Iced-airfoil stall (WMLES)")]),
        ("03", "gai", "Generative AI + agents", "Objective 2 · Aims 2.1–2.2", "Curate, simulate, analyze, and generate with a human signing off every release.", "generate · discover",
         [("physminer-arch", "PhysMiner agent pipeline"), ("ice-model-fields", "Agent-built ice-model fields"), ("physminer-triple", "Agent-computed flow decomposition")]),
        ("04", "app", "Discovery + impact", "Objective 2 · Aim 2.3", "Ice-aware UAV planning, in-flight ice detection, and a first data-driven UAV icing envelope.", "safer all-weather flight",
         [("uas-military", "All-weather UAS · USMC photo"), ("uav-trajectory", "Mission trajectory in icing"), ("plasma-blade", "Plasma anti-icing on a rotor blade")]),
    ]
    layers_html = ""
    for num, k, name, obj, txt, verb, ims in layers:
        figs = "".join(f'<figure>{img(n, c)}<figcaption>{E(c)}</figcaption></figure>' for n, c in ims)
        layers_html += f"""<div class="layer fade-in" style="--c:{LAYER_HEX[k]}">
  <div class="lh"><span class="num">LAYER {num}</span><h3>{name}</h3><span class="aims">{obj}</span><p style="font-size:14px;margin:10px 0 14px;opacity:.95">{txt}</p><span class="verb">→ {verb}</span></div>
  <div class="imgs">{figs}</div></div>"""

    mods = "".join(f'<a class="mod fade-in" href="{{R}}datasets.html?q={E(t.split()[0].lower())}">{img(n, t)}<div class="t"><b>{E(t)}</b><span>{E(s)}</span></div></a>'
                   for t, s, n in C.MODALITIES)
    comms = "".join(f'<div class="comm fade-in">{img(n, t)}<div><h3>{E(t)}</h3><p>{E(s)}</p></div></div>' for t, s, n in C.COMMUNITIES)
    team = "".join(f"""<a class="pi fade-in" href="{{R}}team.html#{p['id']}" style="--c:{LAYER_HEX[p['layer']]};color:inherit">
  <div class="ph">{img(p['img'], cap(p['img']))}</div>
  <div class="bd"><span class="role">{E(p['role'])}</span><h3>{E(p['name'])}</h3><span class="inst">{E(p['inst'])}</span><span class="focus">{E(p['focus'])}</span></div></a>""" for p in C.PEOPLE)

    cov = {
        "series": [
            {"name": "Airfoils & wings", "shape": "circle", "color": "#2a78d6",
             "points": [[-8, 1.1], [-5, 2.0], [-15, 1.0], [-15, 0.5], [-8, 2.5], [-5, 3.0], [-5, 4.0], [-5, 0.3], [-5, 1.5]]},
            {"name": "Rotating: propellers & engine fans", "shape": "triangle", "color": "#eb6834",
             "points": [[-5, 0.5, "propeller"], [-5, 1.0, "propeller"], [-5, 2.0, "propeller"], [-15, 0.5, "propeller"], [-15, 1.0, "propeller"], [-15, 2.0, "propeller"], [-10, 1.0, "propeller"],
                        [-5, 2.4, "engine fan/spinner"], [-10, 1.1, "engine fan/spinner"], [-5, 2.0, "engine fan/spinner"], [-15, 0.5, "engine fan/spinner"], [-18, 0.3, "engine fan/spinner"]]},
            {"name": "Probes & cables", "shape": "square", "color": "#1baf7a",
             "points": [[-15, 0.5, "Pitot probe"], [-15, 1.0, "Pitot probe"], [-15, 1.5, "Pitot probe"], [-15, 2.0, "Pitot probe"], [-5, 0.5, "Pitot probe"], [-5, 1.0, "Pitot probe"], [-5, 1.5, "Pitot probe"], [-5, 2.0, "Pitot probe"],
                        [-15, 1.0, "power/bridge cable"], [-5, 2.0, "power/bridge cable"]]},
            {"name": "Field flights", "shape": "diamond", "color": "#4a3aa7", "points": [[-1.6, None, "natural cloud"], [-3.3, None, "natural cloud"]]},
        ],
        "plan": [[t, v] for v in (0.3, 0.45, 0.7, 1.4, 2.8, 4.2) for t in (-19, -17, -13, -11, -9, -7, -3, -1)],
    }
    shapes = {"circle": '<circle cx="7" cy="7" r="5.5"', "triangle": '<polygon points="7,1.2 13,12 1,12"',
              "square": '<rect x="2" y="2" width="10" height="10" rx="2"', "diamond": '<polygon points="7,0.8 13.2,7 7,13.2 0.8,7"'}
    legend = "".join(f'<span><svg viewBox="0 0 14 14">{shapes[s["shape"]]} fill="{s["color"]}"/></svg>{E(s["name"])}</span>' for s in cov["series"])
    legend += '<span><svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="2.6" fill="#c3cddb"/></svg>Planned LES augmentation</span>'
    rows = "".join(f"<tr><td>{E(s['name'])}{(' · ' + E(p[2])) if len(p) > 2 else ''}</td><td>{p[0]}</td><td>{p[1] if p[1] else 'natural cloud'}</td></tr>"
                   for s in cov["series"] for p in s["points"])

    body = f"""
<section class="hero">
  <svg class="crystals" viewBox="0 0 1440 800" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs><pattern id="hexes" width="56" height="97" patternUnits="userSpaceOnUse" patternTransform="scale(1.3)">
      <path d="M28 0 56 16.2v32.4L28 64.8 0 48.6V16.2zM28 64.8V97" fill="none" stroke="rgba(150,190,255,.07)" stroke-width="1"/></pattern>
      <radialGradient id="fadeh" cx="25%" cy="40%" r="70%"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
      <mask id="mh"><rect width="1440" height="800" fill="url(#fadeh)"/></mask></defs>
    <rect width="1440" height="800" fill="url(#hexes)" mask="url(#mh)"/>
  </svg>
  <div class="container hero-grid">
    <div class="hero-copy">
      <span class="eyebrow">{E(C.SITE['tagline'])}</span>
      <h1>FROST</h1>
      <div class="expand"><b>F</b>used <b>R</b>epository of <b>O</b>bservations, <b>S</b>imulations, and <b>T</b>ests</div>
      <p class="lead">Two decades of icing-tunnel experiments and UAV flight campaigns, linked to validated high-fidelity simulation and curated so that people, machine-learning models, and AI agents can learn icing physics from all of it at once.</p>
      <div class="ctas">
        <a class="btn btn-primary" href="{{R}}datasets.html">Explore the archive {icon("arrow")}</a>
        <a class="btn btn-glass" href="{{R}}record-s1223.html">See one FROST record</a>
      </div>
      <div class="note">{icon("flake")} Built on the ISU Icing Research Tunnel, the only university-owned icing research tunnel in the U.S.</div>
    </div>
    <div class="wall" aria-label="Images from the archive">{cols}</div>
  </div>
</section>
<div class="container stats-wrap"><div class="stats">{stats_html}</div></div>

<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Fresh on FROST</span><h2>What's new</h2><p>Recent results from the team that FROST is built on.</p></div>
    <div class="news">{news}</div>
  </div>
</section>

<section class="section section-ice">
  <div class="container">
    <div class="section-head"><span class="eyebrow">How FROST creates value</span><h2>One archive, four layers</h2>
      <p>Measurements validate and harmonize simulations; simulations complete what experiments cannot see; both train generative models and agents, which answer questions no single campaign was designed to answer.</p></div>
    <div class="layers">{layers_html}
      <div class="layer-base fade-in"><b>Objective 3 · Governed, sustained community infrastructure</b>
        <span class="chip">FAIR + Croissant metadata</span><span class="chip">W3C PROV lineage</span><span class="chip">SHA-256 per file</span><span class="chip">Access tiers</span><span class="chip">DataCite DOIs</span></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container feature">
    <div class="mosaic fade-in">
      <figure data-zoom="{{R}}assets/img/scan-s1223.jpg" data-cap="{E(cap('scan-s1223'))}">{img("scan-s1223", cap("scan-s1223"))}<figcaption>3D ice scan</figcaption></figure>
      <figure class="contain" data-zoom="{{R}}assets/img/piv-s1223.jpg" data-cap="{E(cap('piv-s1223'))}">{img("piv-s1223", cap("piv-s1223"))}<figcaption>Replica PIV</figcaption></figure>
      <figure data-zoom="{{R}}assets/img/s1223-les-3d.jpg" data-cap="{E(cap('s1223-les-3d'))}">{img("s1223-les-3d", cap("s1223-les-3d"))}<figcaption>ISU LES</figcaption></figure>
    </div>
    <div class="fade-in">
      <span class="eyebrow">Featured record</span>
      <h2 style="font-size:clamp(28px,3.2vw,40px);margin:14px 0 14px">One test case, five data products, one record</h2>
      <p class="lead-p">Ice grown on an S1223 UAV wing was scanned, 3D-printed, and re-tested; two independent simulations used the same scan. FROST links them into one machine-readable, provenance-tracked record, and fills the region below the wing that PIV cannot see with validated simulation.</p>
      <div class="record" style="margin:24px 0">
        <div class="rh"><i style="background:#e8453c"></i><i style="background:#f0a824"></i><i style="background:#21a85c"></i><span>frost://icing/airfoil/S1223/rime/aoa00</span></div>
<pre><span class="k">geometry  </span> S1223 UAV airfoil · c = 0.2 m · scan 150 µm
<span class="k">icing     </span> 20 m/s · −15 °C · 0.5 g/m³ · 463 s · <span class="s">rime</span>
<span class="k">test      </span> Re 2.65e5 · AoA 0/5° · Tu 3% <span class="c">← facility</span>
<span class="k">fields    </span> ice.stl <span class="ok">✓</span> loads <span class="ok">✓</span> Cp[42] <span class="ok">✓</span> PIV[500] <span class="ok">✓</span>
<span class="k">completed </span> lower-surface u, Cm <span class="c">← validated LES</span>
<span class="k">provenance</span> sha256 · W3C PROV · CC-BY-4.0 · <span class="w">DOI at release</span></pre>
      </div>
      <a class="btn btn-primary" href="{{R}}record-s1223.html">Open the record {icon("arrow")}</a>
    </div>
  </div>
</section>

<section class="section section-ice">
  <div class="container coverage">
    <div class="fade-in">
      <span class="eyebrow">Archive coverage</span>
      <h2 style="font-size:clamp(28px,3.2vw,40px);margin:14px 0 14px">The icing envelope, seen across geometries</h2>
      <p class="lead-p">Each mark is a tunnel campaign condition from the 37 aircraft- and UAV-icing papers inventoried in the pilot curation pass. ISU-IRT campaigns appear in 25 of them since 2016.</p>
      <p class="lead-p" style="margin:0">Gray dots mark where validated LES will augment the envelope around measured anchors (Aim 1.3), targeting at least four times more covered (T∞, LWC) cells per geometry family.</p>
    </div>
    <div class="chart-card fade-in">
      <h3>Archive coverage of the icing envelope</h3>
      <div class="sub">Tunnel and field conditions by test-article family. Dashed lines mark the rime and glaze reference isotherms.</div>
      <div class="legend">{legend}</div>
      <div class="chart" id="coverage-chart"></div>
      <button class="table-toggle" data-table-toggle>Show data table</button>
      <div id="coverage-table" hidden><table class="data-table"><thead><tr><th>Family</th><th>T∞ (°C)</th><th>LWC (g/m³)</th></tr></thead><tbody>{rows}</tbody></table></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Data modalities</span><h2>Every instrument, one physical description</h2>
      <p>The same icing physics measured by high-speed cameras, projected fringes, lasers, thermal cameras, holograms, load cells, and onboard sensors, harmonized into one similarity space.</p></div>
    <div class="mods">{mods}</div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Organized once, served three ways</span><h2>For people, ML users, and AI agents</h2>
      <p>Every record is served in open formats (HDF5/Zarr, STL/PLY, Parquet, MP4/TIFF) through a web portal, a Python API, and a Model Context Protocol server.</p></div>
    <div class="ways" data-tabs>
      <div class="way-list" role="tablist">
        <button class="way" role="tab" aria-selected="true" aria-controls="p-portal"><span class="ic">{icon("globe")}</span><span><b>Web portal</b><span>Search by condition, modality, origin tag, and access tier; results ranked by similarity in the harmonized space.</span></span></button>
        <button class="way" role="tab" aria-selected="false" aria-controls="p-python"><span class="ic">{icon("code")}</span><span><b>Python API</b><span>PyTorch and JAX loaders with FROST-Bench splits, so ML users never re-process raw data.</span></span></button>
        <button class="way" role="tab" aria-selected="false" aria-controls="p-mcp"><span class="ic">{icon("bot")}</span><span><b>MCP server for agents</b><span>Agents search, fetch, cite, and simulate records, built on the DAFoam MCP agents.</span></span></button>
      </div>
      <div>
        <div class="panel active" id="p-portal">
          <div class="portal-mock"><div class="pm-bar"><i style="background:#e8453c"></i><i style="background:#f0a824"></i><i style="background:#21a85c"></i><span>FROST portal · search</span></div>
            <div class="pm-body"><div class="pm-search">{icon("search")} glaze ice · airfoil · LWC 1–2 g/m³ · IR + 3D scan</div>
              <div class="pm-chips"><span class="chip">−15 to −5 °C</span><span class="chip">LWC 0.5–2 g/m³</span><span class="chip">modality: scan, IR</span><span class="chip">tag: measured</span><span class="chip">tier: Open</span></div>
              <div class="pm-res"><figure>{img("hs-airfoil", "High-speed video")}<figcaption>High-speed video</figcaption></figure><figure>{img("scan-airfoil", "3D ice scan")}<figcaption>3D ice scan</figcaption></figure><figure>{img("piv-propeller", "PIV")}<figcaption>PIV</figcaption></figure></div></div></div>
          <p style="margin-top:14px;font-size:14px;color:#8ea6c6">You are looking at the preview of the portal. <a href="{{R}}datasets.html" style="color:#8fb8f5">Browse the catalog →</a></p>
        </div>
        <div class="panel" id="p-python"><div class="code"><div class="ch"><span>python</span><span class="planned">Planned interface · v0.5</span></div>
<pre><span class="kw">import</span> frost

ds = frost.<span class="fn">load</span>(<span class="st">"ice-shape"</span>, version=<span class="st">"1.0"</span>,
                cond=<span class="fn">dict</span>(LWC=(<span class="st">0.5</span>, <span class="st">2.0</span>)),
                tags=[<span class="st">"measured"</span>])
loader = ds.<span class="fn">to_torch</span>(batch_size=<span class="st">32</span>)   <span class="cm"># or ds.to_jax()</span>
bench  = frost.<span class="fn">bench</span>(<span class="st">"T2-piv-shadow"</span>)       <span class="cm"># held-out split</span></pre></div></div>
        <div class="panel" id="p-mcp"><div class="code"><div class="ch"><span>mcp session</span><span class="planned">Planned interface · v0.5</span></div>
<pre><span class="ag">agent</span> → frost.<span class="fn">search</span>(<span class="st">"rime S1223 PIV"</span>)
<span class="fn">frost</span> → records with DOI, origin tag,
          uncertainty, and PROV lineage
<span class="ag">agent</span> → frost.<span class="fn">get</span>(id); frost.<span class="fn">cite</span>(id)
<span class="ag">agent</span> → frost.<span class="fn">simulate</span>(id)   <span class="cm"># via DAFoam</span></pre></div></div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Release roadmap</span><h2>From archive to community dataset</h2>
      <p>Each release is gated by integrity checks and curator sign-off, versioned, and preserved as a DOI snapshot. Months count from project start.</p></div>
    <div class="roadmap">
      <div class="milestone now fade-in"><div class="pin"></div><span class="when">Today</span><h3>Preview</h3><p>Archive inventoried by agents; pilot records drafted and curator-checked; this preview portal.</p></div>
      <div class="milestone fade-in" style="--c:#e8453c"><div class="pin"></div><span class="when">Month 9</span><h3>FROST v0.5</h3><p>The 25 pilot ISU-IRT campaigns and the S1223 and NASA IRT 401–405 benchmarks.</p></div>
      <div class="milestone fade-in" style="--c:#2b6fe3"><div class="pin"></div><span class="when">Month 18</span><h3>FROST v1.0</h3><p>All ISU-IRT, rotor, and UAV flight campaigns since 2016, with validated simulation completions.</p></div>
      <div class="milestone fade-in" style="--c:#8e5bd1"><div class="pin"></div><span class="when">Month 33</span><h3>FROST v2.0</h3><p>The full archive and the FROST-Gen generative benchmarks.</p></div>
    </div>
  </div>
</section>

<section class="section section-ice">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Who it serves</span><h2>Six communities with a documented need</h2></div>
    <div class="comms">{comms}</div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Team</span><h2>Four PIs, one record at a time</h2>
      <p>Experiments, high-fidelity simulation, AI agents, and generative AI, with overlapping expertise that ties the layers together.</p></div>
    <div class="team">{team}</div>
  </div>
</section>

<section class="section-tight" style="padding-bottom:104px">
  <div class="container"><div class="cta-band">
    <div><h2>Use FROST, or add to it</h2><p>Request early access to a collection, or bring your own icing data through the reviewed contribution path and earn a contributor DOI.</p></div>
    <div class="ctas"><a class="btn btn-light" href="{{R}}access.html#request">Request access</a><a class="btn btn-glass" href="{{R}}access.html#contribute">Contribute data</a></div>
  </div></div>
</section>
"""
    extra = f"\n<script>window.FROST_COVERAGE = {json.dumps(cov)};</script>"
    page("index.html", "index.html", "FROST · AI-ready aircraft icing data",
         "FROST, the Fused Repository of Observations, Simulations, and Tests: two decades of aircraft-icing experiments and flight tests, linked to validated simulation and made AI-ready.",
         body, extra=extra)


# ------------------------------------------------------------------ catalog
def facet(key, title, values, counts, labels=None, colors=None):
    opts = ""
    for v in values:
        dot = f'<i style="background:{colors[v]}"></i>' if colors and v in colors else ""
        opts += f'<button class="opt" data-key="{key}" data-val="{E(v)}" aria-pressed="false">{dot}{E((labels or {}).get(v, v))} <span class="n">{counts.get(v, 0)}</span></button>'
    return f'<div class="facet"><h4>{title}</h4><div class="opts">{opts}</div></div>'


def build_catalog():
    ds = C.DATASETS
    cnt = lambda f: Counter(x for d in ds for x in (d[f] if isinstance(d[f], list) else [d[f]]))
    coll_cards = "".join(f"""<button class="coll-card" data-key="collection" data-val="{c['id']}" aria-pressed="false" style="--c:{LAYER_HEX[c['layer']]}">
  {img(c['img'], c['name'])}<span class="t"><b>{E(c['name'])}</b><span>{cnt('collection')[c['id']]} records · {E(c['holder'])}</span></span></button>""" for c in C.COLLECTIONS)
    mods = [m for m, _ in cnt("modalities").most_common(12)]
    filters = (facet("collection", "Collection", [c["id"] for c in C.COLLECTIONS], cnt("collection"),
                     {c["id"]: c["name"] for c in C.COLLECTIONS}, {c["id"]: LAYER_HEX[c["layer"]] for c in C.COLLECTIONS})
               + facet("origin", "Origin", list(ORIGIN), cnt("origin"), ORIGIN,
                       {"measured": "#2b6fe3", "simulation": "#00a0a0", "model": "#8e5bd1", "external": "#f08a24"})
               + facet("release", "Planned release", ["v0.5", "v1.0", "v2.0"], cnt("release"), {"v0.5": "FROST v0.5", "v1.0": "FROST v1.0", "v2.0": "FROST v2.0"})
               + facet("geometry", "Geometry", [g for g, _ in cnt("geometry").most_common()], cnt("geometry"))
               + facet("modality", "Modality", mods, cnt("modalities")))
    cards = "".join(ds_card(d, i) for i, d in enumerate(ds))
    body = page_hero("Datasets", "Explore the archive",
                     f"{len(ds)} records across six collections: icing-tunnel and rotor experiments, UAV flight campaigns, validated simulations, and linked external records. Every record is in curation for a planned FROST release.",
                     bg="scan-airfoil") + f"""
<div data-filter-root>
<div class="container"><div class="coll-strip">{coll_cards}</div></div>
<section class="section" style="padding-top:56px">
  <div class="container catalog">
    <aside class="filters" aria-label="Filters">
      <label class="search"><span class="sr-only">Search datasets</span>{icon("search")}<input type="search" placeholder="Search: glaze, PIV, propeller…" data-search></label>
      {filters}
      <button class="clear" data-clear>Clear all filters</button>
    </aside>
    <div>
      <div class="results-bar"><span class="count"><b data-count>{len(ds)}</b> records</span>
        <label>Sort&nbsp; <select class="sort" data-sort><option value="rec">Recommended</option><option value="release">Planned release</option><option value="newest">Newest source paper</option><option value="az">Name A–Z</option></select></label></div>
      <div class="ds-grid" data-list>{cards}</div>
      <div class="empty">No records match these filters. <button class="clear" data-clear>Clear filters</button></div>
    </div>
  </div>
</section>
</div>"""
    page("datasets.html", "datasets.html", "Datasets · FROST", "Browse the FROST archive of aircraft-icing experiments, flight tests, and validated simulations.", body)


FORMATS = {"High-speed video": "MP4/TIFF", "3D ice scan": "STL/PLY", "PIV": "HDF5/Zarr", "Phase-locked PIV": "HDF5/Zarr",
           "Loads": "Parquet", "Surface pressure": "Parquet", "DIP film thickness": "HDF5", "IR thermography": "HDF5/TIFF",
           "Holography": "TIFF + Parquet", "MTT temperature": "HDF5", "Flight logs": "Parquet", "Onboard video": "MP4",
           "LES fields": "HDF5/Zarr", "IDDES fields": "HDF5/Zarr", "RANS fields": "HDF5/Zarr", "CFD fields": "HDF5/Zarr",
           "Lagrangian particles": "HDF5", "Ice shapes": "STL/CSV", "Model fields": "HDF5", "Agent annotations": "JSON-LD",
           "Surface temperature": "HDF5"}
TAG = {"measured": "measured", "simulation": "synthetic-validated (after the Aim 1.3 gate)", "model": "derived / generated (labeled)", "external": "measured (external, linked)"}


def build_details():
    for d in C.DATASETS:
        c = COLL[d["collection"]]
        col = LAYER_HEX[c["layer"]]
        if d["images"]:
            first = d["images"][0]
            thumbs = "".join(f'<button aria-current="{"true" if i == 0 else "false"}" data-full="../assets/img/{n}.jpg" data-cap="{E(cap(n))}">{img(n, cap(n))}</button>'
                             for i, n in enumerate(d["images"])) if len(d["images"]) > 1 else ""
            gallery = f"""<div class="gallery"><div class="main">{img(first, cap(first), thumb=False, lazy=False)}<span class="zoom">{icon("zoom")} Enlarge</span></div>
  <div class="cap">{E(cap(first))}</div><div class="thumbs">{thumbs}</div></div>"""
        else:
            gallery = f'<div class="no-gallery"><div>{icon("image")}<b style="display:block;color:#fff;font-family:var(--font-display);font-size:18px">Figures will appear at release</b><span style="font-size:14px">See the source publications below for figures from this dataset.</span></div></div>'
        facts = [("Collection", c["name"]), ("Holder", d["holder"]), ("Geometry", d["geometry"])]
        if d["regime"]:
            facts.append(("Regime", ", ".join(d["regime"])))
        facts.append(("Modalities", ", ".join(d["modalities"])))
        facts += d["facts"]
        facts_html = "".join(f"<div><dt>{E(a)}</dt><dd>{E(b)}</dd></div>" for a, b in facts)
        srcs = "".join(src_item(k) for k in d["sources"])
        if d["id"] == "irt-401-405":
            srcs = ('<li class="src"><div class="ti">Agent-directed development of a zero-calibration three-dimensional ice-accretion model</div>'
                    '<div class="au">H. Gao, Y. Sheng, H. Hu · unpublished results</div></li>') + srcs
        if d["id"] == "s1223-dg-les":
            srcs = '<li class="src"><div class="ti">High-order discontinuous-Galerkin LES of the rime-iced S1223</div><div class="au">H. Gao · preliminary results; linked to the S1223 tunnel record</div></li>'
        if d["id"] == "s1223-rans":
            srcs = '<li class="src"><div class="ti">RANS of the scanned S1223 ice shapes</div><div class="au">University of Tokyo · shapes from the ISU-IRT S1223 campaign</div></li>' + src_item("wang2026experimental")
        fmts = sorted({FORMATS.get(m, "HDF5") for m in d["modalities"]})
        rid = f"frost://{d['collection']}/{d['id']}"
        planned = (f'<span class="k">id        </span> {rid}\n<span class="k">origin    </span> {TAG[d["origin"]]}\n'
                   f'<span class="k">formats   </span> {", ".join(fmts)}\n<span class="k">metadata  </span> Croissant + icing vocabulary: (V∞, T∞, LWC, MVD, t_ice, α, Ω, Re)\n'
                   f'<span class="k">integrity </span> SHA-256 per file · W3C PROV lineage · curator-signed\n'
                   f'<span class="k">access    </span> Open tier expected (CC-BY-4.0), subject to export-control screening\n'
                   f'<span class="k">release   </span> FROST {d["release"]} · DataCite DOI minted at release')
        rec_link = (f'<div class="callout" style="margin-top:22px">This dataset is part of a fully linked FROST record. <a href="../{d["record"]}">See the S1223 record →</a></div>'
                    if d.get("record") else "")
        related = [x for x in C.DATASETS if x["collection"] == d["collection"] and x["id"] != d["id"]][:3]
        if len(related) < 3:
            related += [x for x in C.DATASETS if x["id"] != d["id"] and x not in related and x["geometry"] == d["geometry"]][:3 - len(related)]
        rel_html = "".join(ds_card(x, 0, r="../") for x in related)
        crumbs = f'<nav class="crumbs"><a href="../datasets.html">Datasets</a> / <a href="../datasets.html?collection={c["id"]}">{E(c["name"])}</a></nav>'
        hero = page_hero(E(c["name"]), E(d["title"]), E(d["summary"]), crumbs, bg=d["images"][0] if d["images"] else c["img"])
        hero = hero.replace("</p>\n  </div>", f'</p>\n    <div class="detail-head">{badge_rel(d["release"])}{badge_org(d["origin"])}<span class="badge" style="background:rgba(255,255,255,.1);color:#fff"><span class="status-dot"></span>&nbsp;In curation</span></div>\n  </div>')
        mailto = f"../access.html?coll={d['collection']}#request"
        body = hero + f"""
<section class="section" style="padding-top:56px">
  <div class="container detail">
    <div class="prose">
      {gallery}
      <h2 style="margin-top:40px">What this dataset contains</h2>
      <p>{E(d['summary'])}</p>
      <div style="display:flex;flex-wrap:wrap;gap:6px">{''.join(f'<span class="chip"><i style="background:{col}"></i>{E(m)}</span>' for m in d['modalities'])}{''.join(f'<span class="chip">{E(x)}</span>' for x in d['regime'])}</div>
      {rec_link}
      <h2>Source publications</h2>
      <ul class="srcs">{srcs or '<li class="src"><div class="ti">Source publications will be listed at release.</div></li>'}</ul>
      <h2>How it will appear in FROST</h2>
      <p>Every FROST record carries its conditions, instruments, uncertainty, and provenance. This is the planned record header for this dataset.</p>
      <div class="planned-record">{planned}</div>
    </div>
    <aside class="side">
      <div class="box"><h3>{icon("layers")} At a glance</h3><dl class="facts">{facts_html}</dl></div>
      <div class="box status-box"><h3><span class="status-dot"></span> Status: in curation</h3><div class="in">
        <p>Planned for <b>FROST {d['release']}</b>. Today: <b>{E(c['today'])}</b>. Cite the source papers now; a dataset DOI is minted at release.</p>
        <a class="btn btn-primary btn-sm" href="{mailto}">{icon("mail")} Request access</a></div></div>
    </aside>
  </div>
</section>
<section class="section section-ice section-tight"><div class="container"><h2 style="font-size:26px;margin-bottom:22px">Related records</h2><div class="related">{rel_html}</div></div></section>"""
        page(f"datasets/{d['id']}.html", "datasets.html", f"{d['title']} · FROST", d["summary"], body)


# ------------------------------------------------------------------ record page
def build_record():
    prods = [
        ("1", "exp", "ISU-IRT icing run + 3D scan", "irt-layout", "S1223, c = 200 mm, b = 400 mm; ice laser-scanned to an STL."),
        ("2", "exp", "Replica loads · Cp · PIV", "piv-s1223", "Re = 2.65×10⁵, AoA 0° and 5°; load cell, 42 taps, 500 PIV pairs per case."),
        ("3", "exp", "Surface pressure", "cp-s1223", "Clean vs. rime-iced pressure distributions from the 3D-printed replica."),
        ("4", "cfd", "External RANS", "s1223-rans", "RANS of every scan, 7.9–11.8 M cells, under 1 h per case (University of Tokyo)."),
        ("5", "gai", "ISU wall-resolved LES", "s1223-les-3d", "346 M unknowns on one GPU, filling the region PIV cannot see."),
    ]
    ph = "".join(f"""<div class="product fade-in" style="--c:{LAYER_HEX[k]}"><div class="im" data-zoom="{{R}}assets/img/{n}.jpg" data-cap="{E(cap(n))}">{img(n, cap(n))}</div>
  <div class="bd"><span class="n">PRODUCT {i}</span><h3>{E(t)}</h3>{E(s)}</div></div>""" for i, k, t, n, s in prods)
    body = page_hero("Featured record", "One test case, five data products, one FROST record",
                     "Rime and glaze ice grown on an S1223 UAV wing in the ISU-IRT, followed through every product it has generated, and linked into a single machine-readable record.",
                     '<nav class="crumbs"><a href="datasets.html">Datasets</a> / <a href="datasets/s1223-uav-wing.html">S1223 UAV wing</a></nav>', bg="scan-s1223") + f"""
<section class="section" style="padding-top:64px">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Today: five separate products</span><h2>Scattered across papers, folders, and groups</h2>
      <p>Together these describe the ice, its aerodynamic penalty, and the airflow more completely than any one of them. Today they live in separate places.</p></div>
    <div class="products">{ph}</div>
  </div>
</section>
<section class="section section-dark">
  <div class="container split">
    <div>
      <span class="eyebrow">In FROST: one record</span>
      <h2 style="font-size:clamp(28px,3.2vw,40px);margin:14px 0 16px">Linked, harmonized, and completed</h2>
      <p>A pilot pass by LLM agents, the prototype of Aim 1.1, has already assembled this case into one machine-readable record. Linking does more than collect files:</p>
      <ul style="padding-left:20px;line-height:1.8">
        <li>The tunnel's ~3% inflow turbulence becomes metadata available to every simulation that uses the data.</li>
        <li>The region below the wing that PIV cannot see is completed by validated simulation, tagged as synthetic, with uncertainty.</li>
        <li>The solver's own validation record travels with it: WMLES surface pressure matches IRT measurements on scanned glaze ice.</li>
        <li>Every file is hashed, every derived value has W3C PROV lineage, and a curator signs the release.</li>
      </ul>
      <div style="display:flex;gap:14px;align-items:center;margin-top:22px">
        <img src="{{R}}assets/img/t/wmles-cp-glaze.jpg" alt="{E(cap('wmles-cp-glaze'))}" style="width:150px;border-radius:10px;background:#fff" data-zoom="{{R}}assets/img/wmles-cp-glaze.jpg" data-cap="{E(cap('wmles-cp-glaze'))}">
        <span style="font-size:14px;color:#a9bbd5">Linked solver validation: WMLES vs. IRT Cp on glaze ice.</span></div>
    </div>
    <div class="record">
      <div class="rh"><i style="background:#e8453c"></i><i style="background:#f0a824"></i><i style="background:#21a85c"></i><span>frost://icing/airfoil/S1223/rime/aoa00 · v1.0</span></div>
<pre><span class="k">geometry  :</span> S1223 UAV airfoil · c = 0.200 m
            3D ice scan (150 µm) linked
<span class="k">icing     :</span> V = 20 m/s · T = −15 °C · LWC = 0.5 g/m³
            t = 463 s · regime = <span class="s">rime</span>
<span class="k">test      :</span> Re = 2.65e5 · AoA = 0/5° · Tu = 3%
            <span class="c">← linked facility record</span>
<span class="k">fields    :</span> ice.stl <span class="ok">✓</span>  loads(CL, CD) <span class="ok">✓</span>  Cp[42] <span class="ok">✓</span>
            PIV[500 pairs, shadow-masked] <span class="ok">✓</span>
<span class="k">completed :</span> lower-surface u, Cm
            <span class="c">← validated LES, tagged synthetic</span>
<span class="k">links     :</span> ISU-LES · UTokyo-RANS
            doi:10.2514/6.2026-0887
<span class="k">provenance:</span> sha256 per file · W3C-PROV chain
            CC-BY-4.0 · curator-signed
            <span class="w">DataCite DOI at release</span></pre>
    </div>
  </div>
</section>
<section class="section">
  <div class="container split">
    <div class="code" style="box-shadow:var(--shadow-2)"><div class="ch"><span>python</span><span class="planned">Planned interface · v0.5</span></div>
<pre><span class="kw">import</span> frost

rec = frost.<span class="fn">get</span>(<span class="st">"icing/airfoil/S1223/rime/aoa00"</span>)
rec.ice.<span class="fn">to_mesh</span>()             <span class="cm"># scanned STL</span>
rec.piv.u, rec.piv.mask          <span class="cm"># shadow never mistaken for data</span>
rec.completed.u.origin          <span class="cm"># "synthetic-validated"</span>
frost.<span class="fn">cite</span>(rec)                  <span class="cm"># DOI + source papers</span></pre></div>
    <div>
      <span class="eyebrow">Benchmark in v0.5</span>
      <h2 style="font-size:clamp(26px,3vw,36px);margin:14px 0 14px">A benchmark, not just a record</h2>
      <p class="lead-p">The S1223 record anchors FROST-Bench task T2: complete the PIV shadow from partial observations, with calibrated uncertainty.</p>
      <div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn btn-primary" href="{{R}}benchmarks.html">FROST-Bench {icon("arrow")}</a><a class="btn btn-ghost" href="{{R}}datasets/s1223-uav-wing.html">Dataset page</a></div>
    </div>
  </div>
</section>"""
    page("record-s1223.html", "datasets.html", "S1223 record · FROST",
         "One test case, five data products, one FROST record: the S1223 UAV wing.", body)


# ------------------------------------------------------------------ bench
def build_bench():
    tasks = "".join(f"""<div class="task fade-in">{img(t['img'], t['name'])}<div class="bd"><span class="id">{t['id']}</span><h3>{E(t['name'])}</h3><p>{E(t['text'])}</p>
  <div class="metric"><b>Metric:</b> {E(t['metric'])}</div></div></div>""" for t in C.BENCH)
    bsets = "".join(ds_card(DS[k], 0) for k in ["s1223-uav-wing", "irt-401-405", "nasa-irt-401-405"])
    body = page_hero("FROST-Bench", "Benchmarks built on measured icing physics",
                     "Fluid dynamics has large AI-ready simulation collections, but none with measured icing physics. FROST-Bench poses four tasks with held-out splits, partial observations, and calibrated-uncertainty metrics.",
                     bg="irt402") + f"""
<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Four tasks</span><h2>T1–T4</h2><p>Each benchmark ships as a dataset card with held-out splits. Generated samples are released only as labeled benchmarks, never as data.</p></div>
    <div class="tasks">{tasks}</div>
  </div>
</section>
<section class="section section-ice">
  <div class="container">
    <div class="section-head"><span class="eyebrow">First benchmarks · FROST v0.5</span><h2>Benchmark records</h2></div>
    <div class="related">{bsets}</div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Leaderboard</span><h2>Submissions open with v0.5</h2></div>
    <div class="table-scroll"><table class="board"><thead><tr><th>Rank</th><th>Method</th><th>Task</th><th>Score</th><th>Uncertainty coverage</th><th>Submitted</th></tr></thead>
      <tbody><tr class="opens"><td colspan="6">{icon("spark", "")} <b style="color:var(--ink)">The leaderboard opens with FROST v0.5.</b><br>The public FROST-Bench challenge covers ice-shape generation, completion of PIV shadow regions, and in-flight ice inference.</td></tr></tbody></table></div>
    <div class="grid-3" style="margin-top:36px">
      <div class="card"><div class="ic">{icon("users")}</div><h3>Annual workshop and hackathon</h3><p>Co-located with the AIAA AVIATION Forum, where the icing community already meets.</p></div>
      <div class="card"><div class="ic">{icon("plane")}</div><h3>AIAA Ice Prediction Workshop</h3><p>Curated FROST cases offered to the <a href="https://icepredictionworkshop.wordpress.com/" target="_blank" rel="noopener">Ice Prediction Workshop</a>, where predicted heat-transfer coefficients once spanned 200–950 W/(m²K).</p></div>
      <div class="card"><div class="ic">{icon("shield")}</div><h3>Certified envelope</h3><p>FROST-Gen refuses queries outside its certified envelope rather than extrapolating, and every generated field is tagged.</p></div>
    </div>
  </div>
</section>"""
    page("benchmarks.html", "benchmarks.html", "FROST-Bench · FROST", "FROST-Bench: four benchmark tasks on measured aircraft-icing physics.", body)


# ------------------------------------------------------------------ AI
def build_ai():
    agents = [("Readiness", "exp", "Crawl legacy storage; type and hash files; score metadata completeness; rank for curation.", "readiness queue"),
              ("Curation", "exp", "Run feature extractors and metadata agents; link records; check consistency.", "linked records"),
              ("Simulation", "cfd", "Scanned shape + condition vector → meshed, configured, validated case.", "validated case"),
              ("Analysis", "gai", "Triple decomposition; flow fingerprints; similar-case retrieval across FROST.", "fingerprints"),
              ("Review", "app", "Dimensional, physical, and literature consistency; escalate failures to a human.", "pass or escalate")]
    ag = "".join(f'<div class="agent fade-in" style="--c:{LAYER_HEX[k]}"><b>{n} agent</b><p>{E(t)}</p><span class="out">→ {E(o)}</span></div>' for n, k, t, o in agents)
    views = [("view-tensor", "Grids & video", "ℝ^(T×C×H×W)", "Tensors for CNNs and diffusion models."),
             ("view-vector", "Vector → vector", "c ∈ ℝ⁸ → y ∈ ℝ⁴⁴", "Condition-to-QoI pairs for MLPs and neural operators."),
             ("view-graph", "Surface graph", "G = (V, E)", "Scanned ice as a graph for GNNs."),
             ("view-sdf", "Neural implicit field", "φ(x; c): ℝ³ → ℝ", "Signed-distance fields for implicit models."),
             ("view-tokens", "Sequences & tokens", "[c | g | p₁…pₙ | t₁…tₘ]", "Token streams for transformers."),
             ("view-record", "JSON-LD record", "Croissant + PROV", "Machine-readable records for LLM agents.")]
    vw = "".join(f'<div class="view fade-in">{img(n, t)}<div class="bd"><b>{E(t)}</b><code>{E(m)}</code><p>{E(p)}</p></div></div>' for n, t, m, p in views)
    body = page_hero("AI & Agents", "Agents curate it. Generative models learn from it.",
                     "AI systems are becoming the first consumers of scientific data. In FROST, agents are also its first curators, under human supervision, and generative models are its proof of value.",
                     bg="physminer-vortices") + f"""
<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Aim 2.1 · Agentic data pipelines</span><h2>Five agents, one human sign-off</h2>
      <p>Five cooperating agents carry records from legacy storage to a validated, analyzed, consistency-checked state. Every agent action becomes a W3C PROV record: prompt, model, inputs and outputs with SHA-256, tool calls, cost, and the human decision.</p></div>
    <div class="pipeline">{ag}<div class="release-node fade-in">Curator sign-off<br>→ FROST release</div></div>
  </div>
</section>
<section class="section section-ice" id="curation">
  <div class="container split">
    <div>
      <span class="eyebrow">Pilot curation pass</span>
      <h2 style="font-size:clamp(28px,3.2vw,40px);margin:14px 0 14px">Agents have already read the archive's papers</h2>
      <p class="lead-p">LLM agents read the PI's open-access papers, slide decks, and internal reports and drafted machine-readable records with conditions, instruments, and stated volumes. A curator checked every drafted value against its source before it was used.</p>
      <div class="kpis" style="margin-top:22px">
        <div class="kpi"><div class="n">68</div><div class="l">open-access papers</div></div><div class="kpi"><div class="n">4</div><div class="l">slide decks</div></div>
        <div class="kpi"><div class="n">3</div><div class="l">internal reports</div></div><div class="kpi"><div class="n">50+</div><div class="l">data products drafted</div></div></div>
    </div>
    <div class="card" style="padding:26px">
      <h3>Agent output is a draft, never data</h3>
      <p style="margin-bottom:12px">Five safeguards make every value checkable:</p>
      <ol style="padding-left:20px;color:var(--ink-2);font-size:14.5px;line-height:1.7;margin:0">
        <li>Each value points to the page, table, or file it came from.</li>
        <li>Physics checks reject values that violate conservation or the facility envelope.</li>
        <li>A domain curator signs off every record before release.</li>
        <li>Agent precision and recall are measured on a curator-labeled test set and published with every release.</li>
        <li>A second curator blind-audits a random 5% of signed-off records.</li></ol>
    </div>
  </div>
</section>
<section class="section" id="physminer">
  <div class="container">
    <div class="section-head"><span class="eyebrow">PhysMiner · open source</span><h2>Agents that read a flow field</h2>
      <p>PhysMiner splits the velocity-gradient tensor into rigid rotation, pure shear, and normal straining, then four agents reason over the result, the literature, and a library of six reference flows that includes an iced airfoil and a propeller wake.</p></div>
    <div class="grid-2" style="align-items:start">
      <div class="card" style="padding:24px">
        <h3 style="margin-bottom:16px">Session replay · glaze-iced GLC305 airfoil (IDDES)</h3>
        <div class="chat">
          <div class="msg u"><small>Researcher</small>Investigate the flow over the iced airfoil with Cauchy–Stokes and triple decomposition.</div>
          <div class="msg a"><small>PhysMiner</small>Report: literature, statistics, decompositions, and a new reading of the separating shear layer.</div>
          <div class="msg u"><small>Researcher</small>Label the K–H instability and the hairpin vortices.</div>
          <div class="msg a"><small>PhysMiner</small>Annotated flow structures, with shear separated from true rotation.</div>
        </div>
        <div class="kpis" style="margin-top:20px;grid-template-columns:repeat(4,1fr)">
          <div class="kpi"><div class="n">5/5</div><div class="l">end-to-end runs</div></div><div class="kpi"><div class="n">3.2M</div><div class="l">tokens, mean</div></div>
          <div class="kpi"><div class="n">$3.89</div><div class="l">per run, mean</div></div><div class="kpi"><div class="n">53 min</div><div class="l">per run, mean</div></div></div>
        <p style="font-size:13px;color:var(--ink-3);margin:10px 0 0">Run statistics from the periodic-hill benchmark, where PhysMiner also proposed a turbulence-model correction that improved agreement with experiment.</p>
      </div>
      <div style="display:flex;flex-direction:column;gap:16px">
        <figure style="margin:0" class="img-card" data-zoom="{{R}}assets/img/physminer-vortices.jpg" data-cap="{E(cap('physminer-vortices'))}">{img("physminer-vortices", cap("physminer-vortices"))}<div class="bd"><p>{E(cap("physminer-vortices"))}</p></div></figure>
        <figure style="margin:0" class="img-card" data-zoom="{{R}}assets/img/physminer-triple.jpg" data-cap="{E(cap('physminer-triple'))}">{img("physminer-triple", cap("physminer-triple"))}<div class="bd"><p>{E(cap("physminer-triple"))}</p></div></figure>
        <div style="display:flex;gap:10px"><a class="btn btn-primary btn-sm" href="https://github.com/iDesign-Lab/PhysMiner" target="_blank" rel="noopener">GitHub {icon("ext")}</a><a class="btn btn-ghost btn-sm" href="https://arxiv.org/abs/2607.04009" target="_blank" rel="noopener">arXiv:2607.04009 {icon("ext")}</a></div>
      </div>
    </div>
  </div>
</section>
<section class="section section-dark">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Aim 2.2 · FROST-Gen</span><h2>A physics-guided generative model for icing</h2>
      <p>Conditional diffusion and flow-matching models, pretrained on validated simulation and tuned on measurements, generate ice, water-film, temperature, and flow fields with calibrated uncertainty, inside a certified envelope.</p></div>
    <div class="grid-3">
      <div class="img-card" style="background:#0f213d;border-color:#1d3253"><div style="display:grid;grid-template-columns:1fr 1fr;gap:2px;background:#fff">{img("convlstm-exp", cap("convlstm-exp"))}{img("convlstm-pred", cap("convlstm-pred"))}</div>
        <div class="bd"><h3>0.008 mm</h3><p style="color:#a9bbd5">Median absolute error of a ConvLSTM forecast of runback film thickness trained on ISU-IRT DIP data, on the order of the 0.02 mm measurement uncertainty.</p></div></div>
      <div class="img-card" style="background:#0f213d;border-color:#1d3253">{img("irt402", cap("irt402"))}
        <div class="bd"><h3>0.9–2.1 mm</h3><p style="color:#a9bbd5">Mean ice-thickness error of an agent-developed accretion model over NASA IRT runs 401–405, with no fitted coefficients.</p></div></div>
      <div class="img-card" style="background:#0f213d;border-color:#1d3253">{img("s1223-les-mean", cap("s1223-les-mean"))}
        <div class="bd"><h3>5–6 orders</h3><p style="color:#a9bbd5">Closer match to PIV-like cell averages from exact spectral-projection guidance than from gradient-based diffusion posterior sampling (under review).</p></div></div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">AI-native views</span><h2>Six views, one ID</h2>
      <p>Each harmonized record is exported as six views, so ML users pick the representation that fits their architecture. Every sample carries a measurement mask, uncertainty, origin tag, and provenance.</p></div>
    <div class="view-grid">{vw}</div>
  </div>
</section>"""
    page("ai.html", "ai.html", "AI & Agents · FROST", "Agentic curation, PhysMiner, and the FROST-Gen generative model.", body)


# ------------------------------------------------------------------ software
def build_software():
    cats = OrderedDict()
    for s in C.SOFTWARE:
        cats.setdefault(s["cat"], []).append(s)
    colors = {"FROST tooling": "#1e3557", "AI agents": "#8e5bd1", "Simulation & optimization": "#00a0a0", "Scientific machine learning": "#2b6fe3"}
    order = ["FROST tooling", "AI agents", "Simulation & optimization", "Scientific machine learning"]
    groups = ""
    for cname in order:
        cards = ""
        for s in cats.get(cname, []):
            links = ""
            if s["url"]:
                links += f'<a href="{s["url"]}" target="_blank" rel="noopener">{"Repository" if "github" in s["url"] else "Website"} {icon("ext")}</a>'
            if s.get("docs"):
                links += f'<a href="{s["docs"]}" target="_blank" rel="noopener">{"Paper" if "arxiv" in s["docs"] else "Docs"} {icon("ext")}</a>'
            st = s["status"]
            stc = "rel-v05" if st.startswith("Planned") else ("org-simulation" if st.startswith("Open") else "rel-v20")
            initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", s["name"])[:2]).upper()
            cards += f"""<div class="sw fade-in" style="--c:{colors[cname]}"><div class="top"><span class="mono-ic">{initials}</span><span class="badge {stc}">{E(st)}</span></div>
  <h3>{E(s['name'])}</h3><span class="who">{E(s['who'])}</span><p>{E(s['text'])}</p><div class="links">{links}</div></div>"""
        groups += f'<div class="sw-group"><h2><span style="width:12px;height:12px;border-radius:4px;background:{colors[cname]};display:inline-block"></span>{E(cname)}</h2><div class="grid-3">{cards}</div></div>'
    body = page_hero("Software", "Open code behind FROST",
                     "The solvers, agents, and learning frameworks the team brings to FROST, and the FROST tooling that will ship with the first release. Data are released under CC-BY-4.0; code under OSI licenses.",
                     bg="crm65-surface-flow") + f'<section class="section"><div class="container">{groups}</div></section>'
    page("software.html", "software.html", "Software · FROST", "Open-source solvers, agents, and machine-learning code behind FROST.", body)


# ------------------------------------------------------------------ publications
def build_pubs():
    names = {"Hu": "Hui Hu", "Jain": "Suhas S. Jain", "He": "Ping He", "Gao": "Han Gao"}
    pcol = {p["id"]: LAYER_HEX[p["layer"]] for p in C.PEOPLE}
    cnt_pi = Counter(x for p in PUBS for x in p["pis"])
    cnt_t = Counter(x for p in PUBS for x in p["topics"])
    cnt_ty = Counter(p["type"] for p in PUBS)
    filters = (facet("pi", "PI", ["Hu", "Jain", "He", "Gao"], cnt_pi, names, {k: pcol[k.lower()] for k in names})
               + facet("topic", "Topic", [t for t, _ in cnt_t.most_common() if t != "Other"] + ["Other"], cnt_t)
               + facet("type", "Type", ["Journal", "Conference", "Preprint"], cnt_ty))
    by_year = OrderedDict()
    for p in PUBS:
        by_year.setdefault(p["year"], []).append(p)
    groups = ""
    for y, ps in by_year.items():
        items = ""
        for p in ps:
            doi = f'<a href="https://doi.org/{E(p["doi"])}" target="_blank" rel="noopener">DOI {icon("ext")}</a>' if p["doi"] else ""
            c = f'{p["authors"]} ({p["year"]}). {p["title"]}. {p["venue"]}.' + (f' https://doi.org/{p["doi"]}' if p["doi"] else "")
            tg = "".join(f'<span class="chip"><i style="background:{pcol[x.lower()]}"></i>{E(names[x])}</span>' for x in p["pis"]) + "".join(f'<span class="chip">{E(t)}</span>' for t in p["topics"])
            items += f"""<div class="pub" data-item data-pi="{'|'.join(p['pis'])}" data-topic="{E('|'.join(p['topics']))}" data-type="{p['type']}" data-text="{E((p['title'] + ' ' + p['authors'] + ' ' + p['venue']).lower())}">
  <div><div class="ti">{E(p['title'])}</div><div class="au">{E(p['authors'])}</div><div class="ve">{E(p['venue'])}</div><div class="tg">{tg}</div></div>
  <div class="ac">{doi}<button class="copy" data-copy="{E(c)}">Copy citation</button></div></div>"""
        groups += f'<div data-group><div class="pub-year">{y}<span data-group-count>{len(ps)} papers</span></div>{items}</div>'
    body = page_hero("Publications", "The papers behind the archive",
                     f"{len(PUBS)} journal articles, conference papers, and preprints by the four PIs on icing physics, measurement, simulation, and AI. Each FROST record links back to the papers that report it.",
                     bg="hs-airfoil") + f"""
<section class="section" style="padding-top:56px" data-filter-root>
  <div class="container catalog">
    <aside class="filters" aria-label="Filters">
      <label class="search"><span class="sr-only">Search publications</span>{icon("search")}<input type="search" placeholder="Search title, author, journal…" data-search></label>
      {filters}
      <button class="clear" data-clear>Clear all filters</button>
    </aside>
    <div>
      <div class="results-bar"><span class="count"><b data-count>{len(PUBS)}</b> publications</span></div>
      <div class="pubs">{groups}</div>
      <div class="empty">No publications match these filters.</div>
    </div>
  </div>
</section>"""
    page("publications.html", "publications.html", "Publications · FROST", "Publications by the FROST team.", body)


# ------------------------------------------------------------------ team
def build_team():
    cards = ""
    for p in C.PEOPLE:
        links = "".join(f'<a class="btn btn-ghost btn-sm" href="{u}" target="_blank" rel="noopener">{E(t)} {icon("ext")}</a>' for t, u in p["links"])
        leads = "".join(f"<li>{E(x)}</li>" for x in p["leads"])
        col = LAYER_HEX[p["layer"]]
        cards += f"""<article class="card fade-in" id="{p['id']}" style="display:grid;grid-template-columns:220px 1fr;gap:28px;padding:24px;border-top:5px solid {col}">
  <img src="assets/img/t/{p['img']}.jpg" alt="{E(cap(p['img']))}" style="width:220px;height:220px;object-fit:cover;border-radius:14px">
  <div><span style="font:600 12px/1 var(--font-body);letter-spacing:.08em;text-transform:uppercase;color:{col}">{E(p['role'])} · {E(p['focus'])}</span>
    <h2 style="font-size:30px;margin:8px 0 4px">{E(p['name'])}</h2>
    <div style="color:var(--ink-3);font-size:15px">{E(p['title'])} · {E(p['inst'])}</div>
    <p style="margin:14px 0 10px;color:var(--ink-2)">{E(p['bio'])}</p>
    <div style="font-size:14px;color:var(--ink-2)"><b style="color:var(--ink)">Leads in FROST</b><ul style="margin:6px 0 14px;padding-left:18px">{leads}</ul></div>
    <div style="display:flex;flex-wrap:wrap;gap:8px">{links}</div></div></article>"""
    body = page_hero("Team", "Experiments, simulation, agents, and generative AI",
                     "Four PIs at Iowa State University and Georgia Tech, each leading one layer of FROST, with overlapping expertise that ties the aims together.",
                     bg="irt-facility") + f"""
<section class="section"><div class="container" style="display:flex;flex-direction:column;gap:22px">{cards}</div></section>
<section class="section section-ice">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Where the expertise overlaps</span><h2>A team that already works together</h2></div>
    <div class="grid-3">
      <div class="card"><h3>Hu × Jain</h3><p>Scanned ice and IRT data validate LES; a neural operator for icing water films (JFM, 2026).</p></div>
      <div class="card"><h3>Jain × He</h3><p>LES and DAFoam simulations; agents set up validated cases.</p></div>
      <div class="card"><h3>He × Gao</h3><p>PhysMiner agents, co-developed; AI-driven design.</p></div>
      <div class="card"><h3>Hu × He</h3><p>A shared NSF icing award and machine-learning studies of wind-driven runback.</p></div>
      <div class="card"><h3>Gao × Hu</h3><p>A shared study of the icing-induced penalty on the S1223 UAV wing, and the NASA IRT 401–405 ice-accretion model.</p></div>
      <div class="card"><h3>Governance</h3><p>A Steering Committee of the four PIs plus external members from aircraft icing, UAS operations, certification, and AI for science; a Data Curation Board reviews releases.</p></div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Training & outreach</span><h2>Students at the center</h2>
      <p>Undergraduates in AI-driven use of scientific data, course modules at ISU and Georgia Tech, and K–12 tours of the icing tunnel with a FROST station where an AI model predicts the ice shape before the tunnel grows it.</p></div>
    <div class="grid-2">
      <div class="img-card">{img("outreach-reu", cap("outreach-reu"))}<div class="bd"><p>{E(cap("outreach-reu"))}</p></div></div>
      <div class="img-card">{img("outreach-lab", cap("outreach-lab"))}<div class="bd"><p>{E(cap("outreach-lab"))}</p></div></div>
    </div>
  </div>
</section>"""
    page("team.html", "team.html", "Team · FROST", "The four PIs behind FROST.", body)


# ------------------------------------------------------------------ access
def build_access():
    tags = [("measured", "#2b6fe3", "Measured", "Raw or processed measurement, hash-locked, with facility, instrument, and uncertainty."),
            ("derived", "#00a0a0", "Derived", "Computed from measurements, such as features extracted from video or scans."),
            ("synthetic-validated", "#8e5bd1", "Synthetic-validated", "Simulation that passed the validation gate, with its validation error attached."),
            ("generated", "#f08a24", "Generated", "Model output; released only as labeled benchmarks, never used as truth.")]
    tg = "".join(f'<div class="tag4" style="border-top:4px solid {c}"><code style="color:{c}">{t}</code><p>{E(d)}</p></div>' for t, c, n, d in tags)
    gates = [("1 Ingest", "SHA-256 hash", "#2b6fe3"), ("2 Curate", "agents, extractors", "#2b6fe3"), ("3 Check", "physics, similarity", "#00a0a0"),
             ("4 Review", "curator sign-off", "#8e5bd1"), ("5 Release", "signed, DOI", "#1e3557")]
    gt = "".join(f'<div class="gate" style="background:{c}"><b>{a}</b><span>{b}</span></div>' for a, b, c in gates)
    coll_opts = "".join(f'<option value="{c["id"]}">{E(c["name"])}</option>' for c in C.COLLECTIONS)
    body = page_hero("Access & governance", "Open by default, governed by design",
                     "Integrity is a property of every record, not just of the repository. Every value carries its lineage and an origin tag, and every release is gated, signed, and DOI'd.",
                     bg="irt-iced-wing") + f"""
<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Access tiers</span><h2>Who can access what</h2>
      <p>Before any data enter FROST, ISU's export-control office screens them against the EAR and ITAR. Most of the archive is fundamental research already published in the open literature and is expected to enter the Open tier.</p></div>
    <div class="tiers">
      <div class="tier fade-in" style="--c:#21a85c"><span class="who">Anyone · no login</span><h3>Open</h3><ul><li>CC-BY-4.0</li><li>Fundamental research, published or publishable by the team</li><li>Web portal, Python API, MCP server</li></ul></div>
      <div class="tier fade-in" style="--c:#2b6fe3"><span class="who">ORCID login</span><h3>Registered</h3><ul><li>Large raw imagery and attribution-tracked data</li><li>Usage logged for credit and reporting</li><li>Opens with FROST v0.5</li></ul></div>
      <div class="tier fade-in" style="--c:#e8453c"><span class="who">Approved request</span><h3>{icon("lock")} Controlled</h3><ul><li>Sponsor and industry flight-test data</li><li>Approved, logged, rate-limited</li><li>No bulk export</li></ul></div>
    </div>
  </div>
</section>
<section class="section section-ice">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Integrity</span><h2>Every value carries its lineage and origin</h2>
      <p>Every file is SHA-256 hashed at ingest. Every derived product carries a W3C PROV lineage to the raw files, code, solver settings, agent prompts and models, and curator decisions behind it. AI pipelines can never silently train on model output as if it were measurement.</p></div>
    <div class="gates" style="margin-bottom:26px">{gt}</div>
    <div class="tags4">{tg}</div>
    <div class="planned-record" style="margin-top:22px"><span class="k">prov:</span> frost:cht/s43 wasDerivedFrom frost:scan/s43; wasGeneratedBy cht-les@2.1
<span class="k">tag:</span> synthetic-validated   <span class="k">err:</span> ±1.4 K vs. IR   <span class="k">sha256:</span> 9f2c…e41   <span class="k">lic:</span> CC-BY-4.0</div>
  </div>
</section>
<section class="section">
  <div class="container split" style="align-items:start">
    <div>
      <span class="eyebrow">Policies</span>
      <h2 style="font-size:clamp(28px,3vw,38px);margin:14px 0 16px">Written, public, and enforced</h2>
      <ul style="padding-left:20px;color:var(--ink-2);line-height:1.8">
        <li><b>Licensing:</b> CC-BY-4.0 for data; an OSI license for code.</li>
        <li><b>Citation and credit:</b> dataset DOIs and CRediT roles; contributors earn authorship on dataset descriptors.</li>
        <li><b>Embargo:</b> at most 12 months for contributors' unpublished work.</li>
        <li><b>Retirement:</b> a superseded or erroneous record is deprecated with a tombstone that keeps its DOI resolvable and states the reason. It is never silently deleted.</li>
        <li><b>Privacy:</b> no human-subjects data; incidental faces and plates in field imagery are blurred.</li>
        <li><b>Audit:</b> an annual external audit samples 5% of records and must find zero untagged synthetic values.</li>
      </ul>
    </div>
    <div id="contribute">
      <span class="eyebrow">Contribute</span>
      <h2 style="font-size:clamp(28px,3vw,38px);margin:14px 0 16px">Bring your icing data</h2>
      <p class="lead-p">Outside groups contribute through a documented path, with a median review time under 30 days.</p>
      <div class="steps" style="grid-template-columns:1fr">
        <div class="step"><b>Submit</b><p>A package with Croissant metadata and a FROST datasheet.</p></div>
        <div class="step"><b>Automated checks</b><p>Format, completeness, physics consistency, and duplicate detection by the readiness and review agents.</p></div>
        <div class="step"><b>Quarantine</b><p>Held apart until reviewed, so poisoning and mislabeling cannot reach a release.</p></div>
        <div class="step"><b>Expert review</b><p>By the Data Curation Board.</p></div>
        <div class="step"><b>Release with DOI credit</b><p>A contributor DOI and authorship on the dataset descriptor.</p></div>
      </div>
    </div>
  </div>
</section>
<section class="section section-ice" id="request">
  <div class="container split" style="align-items:start">
    <div>
      <span class="eyebrow">Request access</span>
      <h2 style="font-size:clamp(28px,3vw,38px);margin:14px 0 16px">Get data before the first release</h2>
      <p class="lead-p">Registration opens with FROST v0.5. Until then, the team shares data on request. Tell us what you need and how you will use it; the form opens an email to the team.</p>
      <p style="color:var(--ink-3);font-size:14.5px">Or write directly to <a href="mailto:{C.SITE['email']}">{C.SITE['email']}</a>.</p>
    </div>
    <form class="form card" id="access-form" data-to="{C.SITE['email']}" style="padding:24px">
      <label>Name<input name="name" required autocomplete="name"></label>
      <label>Email<input name="email" type="email" required autocomplete="email"></label>
      <label class="full">Affiliation<input name="aff" autocomplete="organization"></label>
      <label>Interested in<select name="tier"><option>Open-tier data</option><option>Registered-tier raw imagery</option><option>Benchmarks (FROST-Bench)</option><option>Contributing data</option></select></label>
      <label>Collection<select name="coll"><option value="">Any</option>{coll_opts}</select></label>
      <label class="full">Intended use<textarea name="use" placeholder="Research question, model, or course"></textarea></label>
      <div class="full"><button class="btn btn-primary" type="submit">{icon("mail")} Send request</button></div>
    </form>
  </div>
</section>
<script>(function(){{var p=new URLSearchParams(location.search).get("coll");var s=document.querySelector('select[name=coll]');if(p&&s)s.value=p;}})();</script>"""
    page("access.html", "access.html", "Access & governance · FROST", "Access tiers, integrity, governance, and how to request or contribute FROST data.", body)


def build_404():
    body = page_hero("Not found", "This record isn't here", "The page may have moved. Try the catalog.", "") + \
        '<section class="section"><div class="container"><a class="btn btn-primary" href="{R}datasets.html">Browse datasets</a></div></section>'
    page("404.html", "", "Not found · FROST", "Page not found.", body)


def main():
    build_home()
    build_catalog()
    build_details()
    build_record()
    build_bench()
    build_ai()
    build_software()
    build_pubs()
    build_team()
    build_access()
    build_404()
    open(os.path.join(ROOT, ".nojekyll"), "w").close()
    n = sum(1 for _ in os.scandir(os.path.join(ROOT, "datasets")))
    print(f"built 11 pages + {n} dataset pages")


if __name__ == "__main__":
    main()
