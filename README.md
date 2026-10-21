# FROST portal (preview)

Static website for **FROST — Fused Repository of Observations, Simulations, and Tests**, an AI-ready aircraft-icing dataset (Hui Hu, Suhas S. Jain, Ping He, Han Gao).

The site is plain HTML/CSS/JS with no server and no build step on GitHub. All links are relative, so it works at `https://hangaogroup.github.io/frost/` or on a custom domain. Every page carries `noindex, nofollow`.

## Edit and rebuild

All content lives in `tools/content.py`. Every number there comes from the FROST proposal or from the cited paper.

```bash
python3 tools/images.py   # re-export images from the proposal's figures/crops (only when images change)
python3 tools/pubs.py     # refresh data/publications.json from the proposal's references.bib
python3 tools/build.py    # regenerate every HTML page
```

`build.py` writes `index.html`, `datasets.html`, `datasets/*.html`, `record-s1223.html`, `benchmarks.html`, `ai.html`, `software.html`, `publications.html`, `team.html`, `access.html`, and `404.html`.

## Preview locally

```bash
cd .. && python3 -m http.server 8000   # then open http://localhost:8000/frost/
```

## Publish on GitHub Pages

1. Create an empty repository `frost` under the `HanGaoGroup` organization.
2. `git remote add origin https://github.com/HanGaoGroup/frost.git && git push -u origin main`
3. In the repository, go to Settings → Pages, choose "Deploy from a branch", and pick `main` and `/ (root)`.

Contact: hgao1@iastate.edu
