// Draait Kakebo.gs tegen een nagebootste Google-omgeving.
// Gebruik: node --test kakebo/test/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const map = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const { maakNepGoogle } = require('./nep-google.js');
const code = readFileSync(join(map, '..', 'Kakebo.gs'), 'utf8');

// Klok die we zelf kunnen zetten.
const EchteDate = Date;
let nuMs = EchteDate.UTC(2026, 9, 21, 10, 0, 0); // 21 oktober 2026
class NepDate extends EchteDate {
  constructor(...a) { if (a.length === 0) super(nuMs); else super(...a); }
  static now() { return nuMs; }
}
globalThis.Date = NepDate;
const zetDatum = (j, m, d) => { nuMs = EchteDate.UTC(j, m - 1, d, 10, 0, 0); };

const nep = maakNepGoogle({ tijdzone: 'Europe/Brussels', geenUi: true });
for (const naam of ['SpreadsheetApp', 'PropertiesService', 'LockService', 'HtmlService', 'ScriptApp', 'Session', 'Utilities', 'Charts', 'Logger']) {
  globalThis[naam] = nep[naam];
}
(0, eval)(code);
const G = globalThis;
const ss = nep._ss;
const blad = (n) => ss.getSheetByName(n);

test('installeren bouwt alle tabbladen in de juiste volgorde', () => {
  G.installeren();
  assert.deepEqual(ss.getSheets().map((b) => b.getName()), ['Overzicht', 'Uitgaven', 'Maanden', 'Vaste lasten', 'Instellingen', 'Hulp']);
  assert.equal(blad('Hulp').isSheetHidden(), true);
  assert.equal(ss.getActiveSheet().getName(), 'Overzicht');
  assert.equal(ss.getSpreadsheetLocale(), 'nl_NL');
  assert.equal(blad('Instellingen').getRange('C5').getValue(), 'Geert');
  assert.equal(blad('Instellingen').getRange('C6').getValue(), 'Mart');
  assert.equal(blad('Vaste lasten').getRange('A2').getValue(), 'Huur of hypotheek');
  assert.equal(blad('Overzicht').getCharts().length, 1);
  assert.equal(blad('Overzicht').getMaxRows(), 46);
  assert.equal(blad('Overzicht').getMaxColumns(), 13);
  assert.match(ss._toasts.at(-1)[0], /Klaar/);
  // Huidige maand staat klaar, met vaste lasten die de lijst volgen.
  const m = blad('Maanden');
  assert.equal(m.getLastRow(), 2);
  assert.equal(G.naarIso_(m.getRange('A2').getValue(), 'Europe/Brussels'), '2026-10-01');
  assert.match(m.getRange('F2').getFormula(), /Vaste lasten/);
  assert.match(m.getRange('I2').getFormula(), /^=SUMIFS\(Uitgaven!/);
});

test('opnieuw installeren is veilig en bewaart gegevens', () => {
  blad('Instellingen').getRange('C6').setValue('Martje');
  G.installeren();
  G.installeren();
  assert.equal(blad('Instellingen').getRange('C6').getValue(), 'Martje');
  assert.equal(blad('Maanden').getLastRow(), 2, 'geen dubbele maandrij');
  assert.equal(blad('Vaste lasten').getRange('A9').getValue(), 'Overige vaste lasten');
  assert.equal(blad('Vaste lasten').getRange('A10').getValue(), '');
  blad('Instellingen').getRange('C6').setValue('Mart');
});

test('start van de app', () => {
  const s = G.kbStart();
  assert.deepEqual(s.namen, ['Geert', 'Mart']);
  assert.equal(s.ik, null);
  assert.equal(s.vandaag, '2026-10-21');
  assert.equal(s.maand.maand, '2026-10');
  assert.equal(s.maand.label, 'oktober 2026');
  assert.equal(s.maand.status, 'huidig');
  assert.equal(s.maand.plan.bestaat, true);
  assert.equal(s.maand.budget, 0);
  assert.equal(s.maand.perWeek.length, 5);
  // Wat de app krijgt moet zonder verlies door JSON kunnen (google.script.run kan geen Date doorgeven).
  assert.deepEqual(JSON.parse(JSON.stringify(s)), s);
  assert.equal(G.kbKiesIk('Mart'), 'Mart');
  assert.equal(G.kbStart().ik, 'Mart');
  nep.zetGebruiker('geert');
});

test('maandplan bewaren met vaste lasten', () => {
  const res = G.kbBewaarMaand('2026-10', {
    ink1: '2.400', ink2: 1850.5, overig: '', spaardoel: '500',
    vasteLijst: [{ naam: 'Huur', bedrag: 950 }, { naam: 'Energie', bedrag: '145,50' }, { naam: '', bedrag: 0 }, { naam: 'Internet', bedrag: 60, notitie: 'Proximus' }],
    goed: 'Veel zelf gekookt', beter: '', voornemen: '=geen formule'
  });
  assert.equal(res.totaalInkomen, 4250.5);
  assert.equal(res.plan.vaste, 1155.5);
  assert.equal(res.plan.vasteLive, true);
  assert.equal(res.budget, 4250.5 - 1155.5 - 500);
  assert.equal(res.vasteLijst.length, 3);
  assert.equal(res.plan.voornemen, '=geen formule');
  assert.equal(blad('Vaste lasten').getRange('A5').getValue(), '');
  assert.equal(blad('Vaste lasten').getRange('C4').getValue(), 'Proximus');
  assert.equal(blad('Maanden').getRange('O2').getFormula(), '', 'tekst mag geen formule worden');
});

test('uitgaven toevoegen en samenvatten', () => {
  const lijst = [
    ['2026-10-01', 32.4, 'Overleven', 'Delhaize', 'Geert'],
    ['2026-10-04', 12, 'Cultuur', 'Boek', 'Mart'],
    ['2026-10-05', 58.9, 'Optioneel', 'Restaurant', 'Mart'],
    ['2026-10-12', 7.5, 'Extra', '=SUM(1,2)', 'Geert'],
    ['2026-10-18', 21, 'Overleven', '12-10', 'Geert'],
    ['2026-10-21', 3.2, 'Overleven', 'Bakker', 'Mart'],
    ['2026-09-30', 100, 'Optioneel', 'Vorige maand', 'Geert']
  ];
  let res;
  for (const [datum, bedrag, categorie, omschrijving, wie] of lijst) {
    res = G.kbVoegToe({ datum, bedrag, categorie, omschrijving, wie });
  }
  assert.equal(res.maand, '2026-09');
  const okt = G.kbMaand('2026-10');
  assert.equal(okt.aantal, 6);
  assert.equal(okt.uitgegeven, 135);
  assert.deepEqual(okt.perCategorie.map((c) => [c.naam, c.bedrag, c.aantal]), [
    ['Overleven', 56.6, 3], ['Optioneel', 58.9, 1], ['Cultuur', 12, 1], ['Extra', 7.5, 1]
  ]);
  assert.deepEqual(okt.perWeek.map((w) => [w.vanDag, w.totDag, w.totaal]), [
    [1, 4, 44.4], [5, 11, 58.9], [12, 18, 28.5], [19, 25, 3.2], [26, 31, 0]
  ]);
  assert.deepEqual(okt.perPersoon.map((p) => [p.naam, p.bedrag]), [['Geert', 60.9], ['Mart', 74.1]]);
  assert.equal(okt.uitgaven[0].datum, '2026-10-21');
  assert.equal(okt.uitgaven.find((u) => u.bedrag === 7.5).omschrijving, '=SUM(1,2)');
  assert.equal(okt.uitgaven.find((u) => u.bedrag === 21).omschrijving, '12-10');
  assert.equal(okt.dagenOver, 11);
  assert.equal(okt.over, okt.budget - 135);
  assert.equal(okt.perDagNog, Math.round(okt.over / 11 * 100) / 100);
  // In de sheet: een echte datum, een bedrag en geen formules in de omschrijving.
  const u = blad('Uitgaven');
  assert.equal(u.getLastRow(), 8);
  assert.equal(u.getRange('D5').getFormula(), '');
  assert.ok(Object.prototype.toString.call(u.getRange('A2').getValue()) === '[object Date]');
  assert.equal(G.naarIso_(u.getRange('A2').getValue(), 'Europe/Brussels'), '2026-10-01');
  const sep = G.kbMaand('2026-09');
  assert.equal(sep.status, 'verleden');
  assert.equal(sep.plan.bestaat, false);
  assert.equal(sep.uitgegeven, 100);
});

test('uitgave wijzigen en verwijderen', () => {
  let okt = G.kbMaand('2026-10');
  const boek = okt.uitgaven.find((u) => u.omschrijving === 'Boek');
  okt = G.kbWijzig({ rij: boek.rij, sleutel: boek.sleutel }, { datum: '2026-10-04', bedrag: '14,99', categorie: 'Cultuur', omschrijving: 'Boek (pocket)', wie: 'Mart' });
  assert.equal(okt.uitgegeven, 137.99);
  // Verplaatsen naar een andere maand.
  const bakker = okt.uitgaven.find((u) => u.omschrijving === 'Bakker');
  const nov = G.kbWijzig(bakker, { datum: '2026-11-02', bedrag: 3.2, categorie: 'Overleven', omschrijving: 'Bakker', wie: 'Mart' });
  assert.equal(nov.maand, '2026-11');
  assert.equal(nov.status, 'toekomst');
  assert.equal(nov.uitgegeven, 3.2);
  okt = G.kbMaand('2026-10');
  assert.equal(okt.aantal, 5);
  // Verwijderen; een verouderde verwijzing geeft een nette fout.
  const resto = okt.uitgaven.find((u) => u.omschrijving === 'Restaurant');
  okt = G.kbVerwijder({ rij: resto.rij, sleutel: resto.sleutel });
  assert.equal(okt.aantal, 4);
  assert.throws(() => G.kbVerwijder({ rij: resto.rij, sleutel: resto.sleutel }), /niet meer gevonden/);
  // Zelfde uitgave twee keer: verwijderen haalt er precies één weg.
  G.kbVoegToe({ datum: '2026-10-20', bedrag: 2, categorie: 'Overleven', omschrijving: 'Koffie', wie: 'Geert' });
  okt = G.kbVoegToe({ datum: '2026-10-20', bedrag: 2, categorie: 'Overleven', omschrijving: 'Koffie', wie: 'Geert' });
  const koffie = okt.uitgaven.filter((u) => u.omschrijving === 'Koffie');
  assert.equal(koffie.length, 2);
  okt = G.kbVerwijder(koffie[0]);
  assert.equal(okt.uitgaven.filter((u) => u.omschrijving === 'Koffie').length, 1);
});

test('foute invoer geeft duidelijke meldingen', () => {
  const goed = { datum: '2026-10-21', bedrag: 5, categorie: 'Overleven', omschrijving: '', wie: 'Geert' };
  assert.throws(() => G.kbVoegToe({ ...goed, bedrag: '' }), /bedrag/);
  assert.throws(() => G.kbVoegToe({ ...goed, bedrag: 'abc' }), /bedrag/);
  assert.throws(() => G.kbVoegToe({ ...goed, categorie: 'Feest' }), /categorie/);
  assert.throws(() => G.kbVoegToe({ ...goed, wie: 'Piet' }), /wie/);
  assert.throws(() => G.kbVoegToe({ ...goed, datum: '2026-02-30' }), /datum/);
  assert.throws(() => G.kbMaand('2026-13'), /maand/);
  assert.throws(() => G.kbBewaarMaand('2026-10', { ink1: 'veel' }), /ongeldig bedrag/);
  assert.throws(() => G.kbKiesIk('Piet'), /Onbekende naam/);
});

test('nieuwe maand: plan wordt overgenomen en vaste lasten van oktober worden vastgezet', () => {
  zetDatum(2026, 11, 2);
  const s = G.kbStart();
  assert.equal(s.maand.maand, '2026-11');
  assert.equal(s.maand.plan.bestaat, true);
  assert.equal(s.maand.plan.ink1, 2400);
  assert.equal(s.maand.plan.spaardoel, 500);
  assert.equal(s.maand.plan.vasteLive, true);
  assert.equal(s.maand.uitgegeven, 3.2);
  const m = blad('Maanden');
  assert.equal(m.getLastRow(), 3);
  assert.equal(m.getRange('F2').getFormula(), '', 'oktober is vastgezet');
  assert.equal(m.getRange('F2').getValue(), 1155.5);
  assert.match(m.getRange('F3').getFormula(), /Vaste lasten/);
  // Lijst aanpassen raakt oktober niet meer.
  G.kbBewaarMaand('2026-11', { ink1: 2400, ink2: 1850.5, overig: 0, spaardoel: 600, vasteLijst: [{ naam: 'Huur', bedrag: 975 }] });
  assert.equal(G.kbMaand('2026-10').plan.vaste, 1155.5);
  assert.equal(G.kbMaand('2026-11').plan.vaste, 975);
  // Afgelopen maand met een vast bedrag aanpassen.
  const okt = G.kbBewaarMaand('2026-10', { ink1: 2400, ink2: 1850.5, spaardoel: 500, vaste: 1200 });
  assert.equal(okt.plan.vaste, 1200);
  assert.equal(okt.plan.vasteLive, false);
  // Een oudere maand invoegen komt netjes vóór oktober te staan.
  G.kbBewaarMaand('2026-08', { ink1: 2300, ink2: 1800, spaardoel: 400, vaste: 1100 });
  const maanden = m.getRange(2, 1, m.getLastRow() - 1, 1).getValues().map((r) => G.naarIso_(r[0], 'Europe/Brussels'));
  assert.deepEqual(maanden, ['2026-08-01', '2026-10-01', '2026-11-01']);
  assert.equal(m.getRange('E2').getFormula(), '=SUM(B2:D2)');
  assert.equal(m.getRange('E3').getFormula(), '=SUM(B3:D3)');
  // Toekomstige maand zonder rij: voorstel op basis van de laatste maand.
  const dec = G.kbMaand('2026-12');
  assert.equal(dec.plan.bestaat, false);
  assert.equal(dec.plan.spaardoel, 600);
  assert.equal(dec.status, 'toekomst');
});

test('weken van maandag tot zondag', () => {
  assert.deepEqual(G.weken_(2026, 3).map((w) => [w.vanDag, w.totDag]), [[1, 1], [2, 8], [9, 15], [16, 22], [23, 29], [30, 31]]);
  assert.deepEqual(G.weken_(2027, 2).map((w) => [w.vanDag, w.totDag]), [[1, 7], [8, 14], [15, 21], [22, 28]]);
});

test('bedragen lezen zoals een Nederlandstalige typt', () => {
  const p = G.parseBedrag_;
  assert.equal(p('12,50'), 12.5);
  assert.equal(p('1.250'), 1250);
  assert.equal(p('1.250,75'), 1250.75);
  assert.equal(p('1,250.75'), 1250.75);
  assert.equal(p('12.5'), 12.5);
  assert.equal(p('€ 3,20'), 3.2);
  assert.equal(p('-4'), -4);
  assert.equal(p('1.2.3'), null);
  assert.equal(p('abc'), null);
  assert.equal(p(''), null);
  assert.equal(p(7), 7);
});

test('zijpaneel, telefoonlink en web-app geven HTML', () => {
  const metUi = maakNepGoogle({ tijdzone: 'Europe/Brussels' });
  globalThis.SpreadsheetApp.getUi = metUi.SpreadsheetApp.getUi; // nu wel een menubalk
  G.toonApp();
  const zij = metUi._ui._zijpanelen[0];
  assert.match(zij._html, /<title>Kakebo<\/title>/);
  assert.doesNotMatch(zij._html, /__KB_START__|__KB_MODUS__/);
  assert.match(zij._html, /var MODUS = 'zijpaneel'/);
  G.toonTelefoonLink();
  assert.match(metUi._ui._dialogen[0]._html, /Nog geen web-app/);
  nep.zetUrl('https://script.google.com/macros/s/ABC/exec');
  const web = G.doGet();
  assert.match(web._html, /var MODUS = 'web'/);
  assert.equal(blad('Instellingen').getRange('C9').getValue(), 'https://script.google.com/macros/s/ABC/exec');
  G.toonTelefoonLink();
  assert.match(metUi._ui._dialogen[1]._html, /qrcode/);
  G.onOpen();
  assert.equal(metUi._ui._menus[0].naam, '家計簿 Kakebo');
  // De startgegevens in de pagina zijn geldige JSON zonder </script>-gevaar.
  const json = web._html.match(/var START = (.*);\n/)[1];
  assert.equal(JSON.parse(json).maand.maand, '2026-11');
});
