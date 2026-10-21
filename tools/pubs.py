"""Extract the four PIs' papers from the proposal bibliography into data/publications.json.

Usage: python3 tools/pubs.py [path/to/references.bib]
Only entries with a venue or a DOI are kept (unpublished manuscripts are skipped).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_BIB = os.path.join(
    os.path.dirname(ROOT),
    "NSF-26-512-Unlocking-Dataset-Value-for-AI-Enabled-Scientific-Discovery-AI-Datasets-",
    "references.bib")

PIS = {
    "Hu": re.compile(r"\bHu,\s*Hui\b|\bHu,\s*H\.(?!\s*[a-z])"),
    "Jain": re.compile(r"\bJain,\s*S(uhas|\.)"),
    "He": re.compile(r"\bHe,\s*P(ing|\.)"),
    "Gao": re.compile(r"\bGao,\s*Han\b|\bGao,\s*H\.(?!\s*[a-z])"),
}

TOPICS = [
    ("Anti-/de-icing", r"anti-?ic|de-?ic|plasma|coating|superhydrophobic|icephobic|heating|hot-air|slippery|mitigat|protection"),
    ("Runback & water films", r"runback|water film|rivulet|film flow|surface water"),
    ("UAV & rotorcraft", r"\bUAV|propeller|rotor|drone|multirotor|unmanned|flight-testing|aeroengine|fan blade"),
    ("Measurement techniques", r"thermometry|holograph|velocimetry|\bPIV\b|imaging|ultrasonic|image projection|molecular tagging|measurement"),
    ("Icing physics", r"\bice\b|icing|accretion|freez|glaze|rime|supercooled"),
    ("LES & multiphase CFD", r"large-eddy|\bLES\b|phase-field|phase field|diffuse-interface|two-phase|multiphase|droplet|bubble|turbulen|wall-modeled"),
    ("Generative AI & ML", r"diffusion|generative|neural|learning|transformer|physics-informed|surrogate|super-resolution|reduced-order|model reduction|machine"),
    ("Agents & design optimization", r"agent|agentic|optimi[sz]ation|adjoint|DAFoam|design"),
]

LATEX = [(r"\\&", "&"), (r"--", "–"), (r"\\'e", "é"), (r"\\'a", "á"), (r'\\"o', "ö"), (r'\\"u', "ü"),
         (r"\\'\{e\}", "é"), (r"\\textendash", "–"), (r"\\textemdash", "—"), (r"~", " ")]


def field(e, k):
    m = re.search(r"\b" + k + r"\s*=\s*\{", e, re.I)
    if not m:
        m2 = re.search(r"\b" + k + r'\s*=\s*"([^"]*)"', e, re.I)
        return m2.group(1) if m2 else ""
    i, d, j = m.end(), 1, m.end()
    while d:
        d += {"{": 1, "}": -1}.get(e[j], 0)
        j += 1
    return re.sub(r"\s+", " ", e[i:j - 1]).strip()


def clean(s):
    for a, b in LATEX:
        s = re.sub(a, b, s)
    s = re.sub(r"\$([^$]*)\$", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    return s.replace("{", "").replace("}", "").strip()


def short_authors(a):
    names = [n.strip() for n in clean(a).split(" and ") if n.strip()]
    out = []
    for n in names:
        if n.lower() == "others":
            continue
        if "," in n:
            last, first = [x.strip() for x in n.split(",", 1)]
        else:
            parts = n.split()
            last, first = parts[-1], " ".join(parts[:-1])
        initials = "".join(p[0] + "." for p in re.split(r"[\s\-]+", first) if p and p[0].isalpha())
        out.append(f"{initials} {last}".strip())
    if len(out) > 8:
        out = out[:7] + ["et al."]
    return ", ".join(out)


def main():
    bib = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BIB
    s = open(bib, encoding="utf-8").read()
    pubs = []
    for e in re.split(r"\n(?=@)", s):
        m = re.match(r"@(\w+)\{([^,]+),", e)
        if not m:
            continue
        authors = field(e, "author")
        pis = [k for k, rx in PIS.items() if rx.search(authors)]
        if not pis:
            continue
        venue = clean(field(e, "journal") or field(e, "booktitle"))
        doi = field(e, "doi")
        if not venue and not doi:
            continue
        title = clean(field(e, "title"))
        kind = m.group(1).lower()
        typ = "Preprint" if "arxiv" in (venue + doi).lower() else (
            "Conference" if kind in ("inproceedings", "conference") or "forum" in venue.lower()
            or "meeting" in venue.lower() or "conference" in venue.lower() else "Journal")
        topics = [t for t, rx in TOPICS if re.search(rx, title, re.I)] or ["Other"]
        pubs.append({
            "key": m.group(2).strip(), "title": title, "authors": short_authors(authors),
            "year": int(re.sub(r"\D", "", field(e, "year")) or 0), "venue": venue or "arXiv",
            "doi": doi, "pis": pis, "topics": topics, "type": typ,
        })
    pubs.sort(key=lambda p: (-p["year"], p["title"]))
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "publications.json"), "w", encoding="utf-8") as f:
        json.dump(pubs, f, ensure_ascii=False, indent=1)
    from collections import Counter
    print(len(pubs), "publications;", dict(Counter(p for x in pubs for p in x["pis"])),
          dict(Counter(x["type"] for x in pubs)))


if __name__ == "__main__":
    main()
