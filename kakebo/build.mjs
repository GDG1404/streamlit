// Bundelt src/Code.js en src/app.html tot één bestand Kakebo.gs om in Apps Script te plakken.
// Gebruik: node kakebo/build.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const map = dirname(fileURLToPath(import.meta.url));
const code = readFileSync(join(map, 'src', 'Code.js'), 'utf8');
const html = readFileSync(join(map, 'src', 'app.html'), 'utf8');

// Inhoud van een template literal: \ ` en ${ moeten ontsnapt worden.
const ontsnapt = html.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$\{/g, '\\${');

const uit = code.trimEnd() + `

/* ============================================================
 *  DE APP (HTML) — automatisch gegenereerd uit src/app.html
 *  Niet met de hand aanpassen.
 * ============================================================ */

var KB_APP_HTML = \`${ontsnapt}\`;
`;

writeFileSync(join(map, 'Kakebo.gs'), uit);

// Controle: de ingebedde HTML moet exact gelijk zijn aan het bronbestand.
const KB_APP_HTML = new Function(uit.slice(uit.indexOf('var KB_APP_HTML')) + '\nreturn KB_APP_HTML;')();
if (KB_APP_HTML !== html) throw new Error('Ingebedde HTML wijkt af van src/app.html');
console.log(`Kakebo.gs geschreven: ${uit.split('\n').length} regels, ${(uit.length / 1024).toFixed(0)} kB`);
