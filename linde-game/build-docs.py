#!/usr/bin/env python3
"""Kopieert het spel naar docs/ voor GitHub Pages (Settings > Pages > Branch > map /docs)."""
import pathlib, shutil

here = pathlib.Path(__file__).parent
out = here.parent / 'docs'
out.mkdir(exist_ok=True)
shutil.copy(here / 'index.html', out / 'index.html')
(out / '.nojekyll').write_text('')
for d in ('audio', 'img'):
    if (here / d).exists():
        shutil.copytree(here / d, out / d, dirs_exist_ok=True)
print('docs/ bijgewerkt')
