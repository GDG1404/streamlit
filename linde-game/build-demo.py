#!/usr/bin/env python3
"""Bouwt de demo: demo-template.html + index.html (+ Leaflet inline) -> demo.html en demo-fragment.html.

demo-fragment.html is de pagina zonder <html>/<head>/<body>, voor publicatie als Artifact.
Optioneel: --media <html-bestand> voegt extra HTML toe (bv. een opname) op de plek van <!--MEDIA-->.
"""
import json, pathlib, sys

here = pathlib.Path(__file__).parent
game = (here / 'index.html').read_text(encoding='utf-8')
css = (here / 'vendor/leaflet/leaflet.css').read_text(encoding='utf-8')
js = (here / 'vendor/leaflet/leaflet.js').read_text(encoding='utf-8')

link = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">'
script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>'
assert link in game and script in game
game = game.replace(link, '<style>' + css + '</style>').replace(script, '<script>' + js + '</script>')

literal = json.dumps(game, ensure_ascii=False).replace('</', '<\\/').replace('<!--', '<\\!--')
tpl = (here / 'demo-template.html').read_text(encoding='utf-8')
media = ''
if '--media' in sys.argv:
    media = pathlib.Path(sys.argv[sys.argv.index('--media') + 1]).read_text(encoding='utf-8')
fragment = tpl.replace('/*GAME_JSON*/', literal).replace('<!--MEDIA-->', media)
(here / 'demo-fragment.html').write_text(fragment, encoding='utf-8')
full = ('<!doctype html>\n<html lang="nl">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '</head>\n<body>\n' + fragment + '\n</body>\n</html>\n')
(here / 'demo.html').write_text(full, encoding='utf-8')
print('demo.html', len(full) // 1024, 'KB; demo-fragment.html', len(fragment) // 1024, 'KB')
