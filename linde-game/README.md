# Operatie Linde – wandelspel

Eén bestand: `index.html`. Zet het online (bv. GitHub Pages) en open de link op alle gsm's.

- **Spelleider** kiest "Ik ben de spelleider", start het spel en deelt de spelcode (staat bovenaan op het scherm).
- **Spelers** kiezen "Ik ben een speler" en vullen de spelcode en hun eigen naam in (de jarige vult Linde in). De spelleider ziet wie zich aanmeldt.
  Namen vooraf invullen mag, maar hoeft niet. Wie later binnenkomt doet mee vanaf de volgende opdracht.
- Alles loopt via ntfy.sh (gratis, geen account). De spelcode is dus het enige "wachtwoord".
- Opdrachten, de zin voor de letterfinale en je GPX pas je bovenaan in `index.html` aan (`CONFIG`, `GROUP_TASKS`, `IND_TASKS`).

## De route (GPX)
De route van de verjaardagswandeling (Garmin cursus 522994433, `route/COURSE_522994433.gpx`, een lus van 4,1 km) zit al in de app (`CONFIG.route`).
Wil je een andere route, dan kiest de spelleider bij het instellen een ander GPX-bestand. De app vereenvoudigt de route tot ±100 punten en
stuurt ze mee naar alle spelers, die dus niets hoeven te laden. Uit Garmin Connect (website): open de cursus, tik op het tandwiel
en kies "Exporteren naar GPX". De 8 checkpoints worden gelijkmatig over de route verdeeld.

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

## Online zetten (GitHub Pages)
1. GitHub, de fork `GDG1404/streamlit` > **Settings** > **Pages**.
2. Onder *Build and deployment*: Source = **Deploy from a branch**.
3. Branch = `claude/linde-interactive-walk-game-26lyqv`, map = **/docs**, dan **Save**.
4. Na 1 tot 2 minuten staat bovenaan de link (verwacht: https://gdg1404.github.io/streamlit/).
5. Na elke wijziging in `index.html`: `python3 linde-game/build-docs.py`, committen en pushen (`docs/` is een kopie).

## Op de dag zelf (spelleider)
- Mee: gsm met data, **powerbank**, rugzak, kroontje voor Linde.
- Op de parking: open de link > "Ik ben de spelleider" > Start. (Eerder getest? Eerst ☰ > Alles resetten.)
- Tik op **📲 Uitnodigen** en deel de link in de WhatsApp-groep. Spelers vullen enkel hun naam in.
- Wacht tot iedereen in de lijst staat (🏆 toont het aantal), toon dan het verhaal en vertrek.
- Valt het bereik weg? Het spel gaat gewoon door op jouw gsm; de spelers sluiten vanzelf weer aan.
