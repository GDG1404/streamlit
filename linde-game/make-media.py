#!/usr/bin/env python3
"""Maakt het mediagedeelte (opname + beelden) voor de demopagina.

Gebruik: make-media.py <opname.webm> <map-met-beelden> <uitvoer.html>
De beelden (01.jpg ...) en captions.txt komen uit de autopilot-opname.
"""
import base64, pathlib, subprocess, sys, html

video_in, shots_dir, out = map(pathlib.Path, sys.argv[1:4])
tmp = out.with_suffix('.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(video_in), '-vf', 'scale=720:-2,fps=15',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '30', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', str(tmp)], check=True)
b64 = lambda path, mime: 'data:%s;base64,%s' % (mime, base64.b64encode(pathlib.Path(path).read_bytes()).decode())

caps = {}
for line in (shots_dir / 'captions.txt').read_text(encoding='utf-8').splitlines():
    n, _t, text = line.split('\t', 2)
    caps[n] = text

# gekozen beelden: (nummer, bijschrift)
picks = [
    ('04', 'De spelleider toont het verhaal op alle gsm\'s tegelijk.'),
    ('08', 'Linde meldt "klaar", de spelleider geeft punten.'),
    ('09', 'Het hartje voor Linde groeit met elke goede opdracht.'),
    ('12', 'Groepsopdracht met hoofdstuk uit het verhaal (Lion King).'),
    ('16', 'Opdracht met timer en pogingen: de klok loopt op beide gsm\'s.'),
    ('22', 'Het scorebord met de verdiende letters.'),
    ('23', 'Letterfinale: iedereen heeft letters gekregen.'),
    ('25', 'De oplossing en het slot van het verhaal.'),
]
figs = ''
for n, cap in picks:
    f = shots_dir / (n + '.jpg')
    if f.exists():
        figs += '<figure><img alt="%s" src="%s"><figcaption>%s</figcaption></figure>\n' % (html.escape(cap), b64(f, 'image/jpeg'), html.escape(cap))

poster = b64(shots_dir / '09.jpg', 'image/jpeg') if (shots_dir / '09.jpg').exists() else ''
media = ('<div class="box" id="opname"><h2>Opname van de hele demo</h2>'
         '<video controls playsinline preload="metadata" poster="%s" src="%s"></video>'
         '<p class="muted" style="margin-top:8px">Zo loopt het spel van begin tot einde. In het echte spel doet de spelleider deze stappen zelf.</p></div>\n'
         '<div class="box"><h2>Beelden uit de demo</h2><div class="grid">\n%s</div></div>\n') % (poster, b64(tmp, 'video/mp4'), figs)
out.write_text(media, encoding='utf-8')
print('media', len(media) // 1024, 'KB; mp4', tmp.stat().st_size // 1024, 'KB')
