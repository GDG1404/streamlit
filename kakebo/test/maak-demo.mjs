// Maakt test/demo.html: de echte app met het echte script erachter, maar met een
// nagebootste Google Sheet in de browser en voorbeeldgegevens. Handig om de app te
// bekijken zonder Google-account. Gebruik: node kakebo/test/maak-demo.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const map = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(map, '..', 'src', 'app.html'), 'utf8');
const server = readFileSync(join(map, '..', 'src', 'Code.js'), 'utf8');
const nep = readFileSync(join(map, 'nep-google.js'), 'utf8');
const veilig = (js) => js.replace(/<\/script/gi, '<\\/script');

const brug = `
(function () {
  var nep = NepGoogle.maakNepGoogle({ tijdzone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Brussels', geenUi: true });
  ['SpreadsheetApp', 'PropertiesService', 'LockService', 'HtmlService', 'ScriptApp', 'Session', 'Utilities', 'Charts', 'Logger']
    .forEach(function (n) { window[n] = nep[n]; });
  window.KB_APP_HTML = '';
  window.__KB_NEP__ = nep;
})();
`;

const vulling = `
(function () {
  // Voorspelbaar 'toeval' zodat de demo er elke keer hetzelfde uitziet.
  var zaad = 7;
  function kans() { zaad = (zaad * 16807) % 2147483647; return (zaad - 1) / 2147483646; }
  function kies(lijst) { return lijst[Math.floor(kans() * lijst.length)]; }
  function iso(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  var nu = new Date();
  var huidig = iso(nu).slice(0, 7);
  var vorige = iso(new Date(nu.getFullYear(), nu.getMonth() - 1, 1)).slice(0, 7);

  installeren();
  var vast = [
    { naam: 'Huur of hypotheek', bedrag: 1050 }, { naam: 'Energie', bedrag: 165 },
    { naam: 'Water', bedrag: 35 }, { naam: 'Internet en telefoon', bedrag: 65 }, { naam: 'Verzekeringen', bedrag: 120 },
    { naam: 'Abonnementen', bedrag: 38 }, { naam: 'Vervoer', bedrag: 90 }
  ];
  kbBewaarMaand(vorige, { ink1: 2450, ink2: 1980, overig: 0, spaardoel: 600, vaste: 1563,
    goed: 'Veel zelf gekookt en de fiets genomen in plaats van de auto.',
    beter: 'Te veel kleine aankopen op weg naar huis.',
    voornemen: 'Elke woensdag een dag zonder uitgaven.' });
  kbBewaarMaand(huidig, { ink1: 2450, ink2: 1980, overig: 0, spaardoel: 600, vasteLijst: vast,
    goed: '', beter: '', voornemen: '' });

  var posten = {
    Overleven: [['Supermarkt', 35, 110], ['Supermarkt', 25, 80], ['Bakker', 3, 9], ['Apotheek', 6, 24], ['Tanken', 50, 75], ['Groenteboer', 8, 22], ['Treinticket', 9, 19]],
    Optioneel: [['Pizza', 18, 32], ['Koffie met collega’s', 4, 9], ['Kleding', 30, 70], ['Etentje', 40, 85], ['Bloemen', 12, 20]],
    Cultuur: [['Boek', 12, 26], ['Bioscoop', 22, 28], ['Museum', 15, 30], ['Concertticket', 35, 60]],
    Extra: [['Verjaardagscadeau', 20, 45], ['Fietsreparatie', 25, 60], ['Nieuwe oplader', 15, 25]]
  };
  var gewicht = ['Overleven', 'Overleven', 'Overleven', 'Overleven', 'Overleven', 'Optioneel', 'Optioneel', 'Optioneel', 'Cultuur', 'Extra'];
  var namen = ['Geert', 'Mart'];
  var start = new Date(nu.getFullYear(), nu.getMonth() - 1, 1);
  for (var d = new Date(start); d <= nu; d.setDate(d.getDate() + 1)) {
    var aantal = 1 + Math.floor(kans() * 2.4);
    for (var i = 0; i < aantal; i++) {
      var cat = kies(gewicht);
      var p = kies(posten[cat]);
      var bedrag = Math.round((p[1] + kans() * (p[2] - p[1])) * 100) / 100;
      kbVoegToe({ datum: iso(d), bedrag: bedrag, categorie: cat, omschrijving: p[0], wie: kies(namen) });
    }
  }
  kbKiesIk('Geert');

  // google.script.run zoals in Apps Script: asynchroon en via JSON (dus geen Date-objecten).
  function kloon(x) { return x === undefined ? undefined : JSON.parse(JSON.stringify(x)); }
  function maakRunner(ok, nok) {
    return new Proxy({}, {
      get: function (_, naam) {
        if (naam === 'withSuccessHandler') return function (f) { return maakRunner(f, nok); };
        if (naam === 'withFailureHandler') return function (f) { return maakRunner(ok, f); };
        return function () {
          var args = Array.prototype.slice.call(arguments).map(kloon);
          setTimeout(function () {
            try {
              if (typeof window[naam] !== 'function' || /_$/.test(naam)) throw new Error('Script function not found: ' + naam);
              var uit = kloon(window[naam].apply(null, args));
              if (ok) ok(uit);
            } catch (e) {
              if (nok) nok(e); else console.error(e);
            }
          }, 220);
        };
      }
    });
  }
  window.google = { script: { run: maakRunner(null, null) } };
  window.__KB_DEMO_START__ = kloon(kbStart());
})();
`;

let pagina = app
  .replace('/*__KB_START__*/null', 'window.__KB_DEMO_START__')
  .replace('__KB_MODUS__', 'web');
const scripts = `<script>\n${veilig(nep)}\n</script>\n<script>\n${veilig(brug)}\n</script>\n<script>\n${veilig(server)}\n</script>\n<script>\n${veilig(vulling)}\n</script>\n`;
const plek = pagina.lastIndexOf('<script>');
pagina = pagina.slice(0, plek) + scripts + pagina.slice(plek);
writeFileSync(join(map, 'demo.html'), pagina);
console.log('test/demo.html geschreven (' + Math.round(pagina.length / 1024) + ' kB)');
