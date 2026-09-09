# pzhoumath.github.io

Source for https://pzhoumath.github.io/, built with [Hugo](https://gohugo.io)
using hand-written layouts (no theme).

## Structure

- `content/research/` — research statement (`_index.md`) plus one page per
  theme (homological mirror symmetry, Fukaya categories, ...).
- `content/blog/` — dated notes. New post: `content/blog/YYYY-MM-DD-slug.md`
  with `title`, `date`, `tags` front matter.
- `content/publications/` — the `/publications/` page itself is just a
  stub; the actual list is generated from `bibliography/publications.bib`
  (see below).
- `layouts/` — custom templates: `_default/` (base wrapper, generic
  single/list), plus per-section overrides in `research/`, `blog/`,
  `publications/`.
- `assets/css/main.css` — the site's one stylesheet (processed with Hugo
  Pipes: minified + fingerprinted at build time).

## Publications

Publications are driven by `bibliography/publications.bib`: paste BibTeX
entries exported from Google Scholar (or arXiv, MathSciNet, ...) directly
into that file. Two extra fields are recognized on top of standard BibTeX:

```bibtex
@article{zhou2024example,
  title   = {A Paper Title},
  author  = {Zhou, Peng and Coauthor, Jane},
  journal = {arXiv preprint arXiv:2401.01234},
  year    = {2024},
  tags    = {Fukaya categories, mirror symmetry},
  pdf     = {https://arxiv.org/pdf/2401.01234},
}
```

`scripts/build_publications.py` (pure standard library, no dependencies)
converts that file into `data/publications.json`, which the
`/publications/` page reads and groups by year. Run it after editing the
`.bib` file:

```sh
python3 scripts/build_publications.py
```

`data/publications.json` is generated and gitignored — the deploy
workflow regenerates it on every build, so it never needs to be committed.

## Local development

```sh
python3 scripts/build_publications.py   # generate data/publications.json
hugo server -D                          # http://localhost:1313
```

## Math

LaTeX in Markdown renders via [KaTeX](https://katex.org), loaded from a
CDN and auto-rendered client-side. Supported delimiters: `$...$`,
`$$...$$`, `\(...\)`, `\[...\]`. Hugo's Goldmark `passthrough` extension
(configured in `hugo.toml`) protects raw math from Markdown parsing, so
things like `$a_i$` are not mistaken for emphasis.

## Deployment

`.github/workflows/hugo.yml` builds the site with Hugo and deploys it via
GitHub Pages' "Actions" build source on every push to `master`. In the
repo's **Settings → Pages**, set "Build and deployment source" to
**GitHub Actions** (one-time setup).
