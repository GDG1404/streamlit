# Operatie Linde – wandelspel

Eén bestand: `index.html`. Zet het online (bv. GitHub Pages) en open de link op alle gsm's.

- **Spelleider** kiest "Ik ben de spelleider", vult namen in en deelt de spelcode.
- **Spelers** kiezen "Ik ben een speler", vullen de code in en kiezen hun naam.
- Alles loopt via ntfy.sh (gratis, geen account). De spelcode is dus het enige "wachtwoord".
- Opdrachten, de zin voor de letterfinale en je GPX pas je bovenaan in `index.html` aan (`CONFIG`, `GROUP_TASKS`, `IND_TASKS`).

## Rugzak (bewust minimaal)
Je rugzak zelf (als "Simba") en een kroontje voor Linde. Meer is niet nodig; het menu ☰ toont de lijst.

## Beeldmateriaal
- **Munch, De Schreeuw** (publiek domein) laadt rechtstreeks van Wikimedia Commons.
- Voor de film- en musicalscènes opent de knop "🔎 Voorbeeldfoto zoeken" Google Afbeeldingen. Beelden uit films kopiëren we niet in de app (auteursrecht).
- Eigen foto's mag je altijd in `img/` zetten en bij de opdracht als `img:"img/bestand.jpg"` opgeven.

## Lachgeluid ("Stil kijken")
Zet een bestand `audio/lach.mp3` (of .ogg, pas dan het pad aan in `GROUP_TASKS`) neer. Gratis CC0-fragmenten:
- https://opengameart.org/content/group-giggling
- https://bigsoundbank.com/rires-d-enfants-s1660.html

Zonder bestand laat de app de stem van de gsm "hahaha/hihihi" zeggen, met als laatste noodoplossing een elektronische lach.

## Demo
`demo.html` toont de spelleider en een speler naast elkaar (de verbinding wordt in de pagina nagebootst, geen internet nodig)
met een autopilot die het hele spel doorloopt. Opnieuw bouwen na een wijziging in `index.html`:

    python3 linde-game/build-demo.py

`make-media.py` maakt van een autopilot-opname een video + beelden voor een gepubliceerde versie (vereist ffmpeg).
