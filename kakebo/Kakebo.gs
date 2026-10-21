/**
 * ============================================================
 *  家計簿  KAKEBO — het huishoudboekje van Geert & Mart
 * ============================================================
 *
 *  Installeren (eenmalig, ± 10 minuten — zie ook LEESMIJ.md):
 *   1. Maak een nieuwe Google Sheet (sheets.new) en noem hem "Kakebo".
 *   2. Kies Extensies › Apps Script. Wis alles in Code.gs en plak dit hele bestand.
 *   3. Klik op 💾 Opslaan, kies bovenaan de functie "installeren" en klik ▶ Uitvoeren.
 *      Geef toestemming (Geavanceerd › Ga naar Kakebo › Toestaan).
 *   4. Ga terug naar de sheet en herlaad de pagina: het menu 家計簿 Kakebo verschijnt.
 *   5. Web-app voor de telefoon: Implementeren › Nieuwe implementatie › Web-app,
 *      Uitvoeren als: "Gebruiker die de web-app opent",
 *      Toegang: "Iedereen met een Google-account". Open de link en zet hem op je beginscherm.
 *   6. Deel de sheet met Mart (Delen › e-mailadres › Bewerker).
 *
 *  Je hoeft hieronder niets aan te passen. Namen wijzig je in het tabblad Instellingen.
 */

var KB = {
  VERSIE: '1.0.0',
  NAMEN: ['Geert', 'Mart'],
  BLAD: {
    OVERZICHT: 'Overzicht',
    UITGAVEN: 'Uitgaven',
    MAANDEN: 'Maanden',
    VAST: 'Vaste lasten',
    INST: 'Instellingen',
    HULP: 'Hulp'
  },
  CATEGORIEEN: [
    { naam: 'Overleven', uitleg: 'Boodschappen, vervoer, gezondheid, verzorging', kleur: '#339e7c', tint: '#e2f1eb' },
    { naam: 'Optioneel', uitleg: 'Uit eten, kleding, hobby’s, iets leuks voor jezelf', kleur: '#d86105', tint: '#fae6d8' },
    { naam: 'Cultuur', uitleg: 'Boeken, film, concerten, musea, cursussen', kleur: '#3f6fcf', tint: '#e4eaf8' },
    { naam: 'Extra', uitleg: 'Onverwacht: reparaties, cadeaus, boetes', kleur: '#b54696', tint: '#f4e1ee' }
  ],
  KLEUR: {
    papier: '#f6f1e8',
    kaart: '#fffdf9',
    kaart2: '#faf5ec',
    berekend: '#f1ebe1',
    inkt: '#26231f',
    inkt2: '#5f5950',
    inkt3: '#756e63',
    lijn: '#e6dfd2',
    spoor: '#ebe4d8',
    hanko: '#c8553d',
    waarschuwing: '#c98500',
    kritiek: '#c93a35',
    wit: '#ffffff'
  },
  LETTER: 'Nunito',
  FMT: {
    EURO: '"€ "#,##0.00;"-€ "#,##0.00',
    DATUM: 'd mmm yyyy',
    MAAND: 'mmmm yyyy',
    TIJD: 'd-m-yyyy h:mm',
    PCT: '0%',
    ISO: 'yyyy-mm-dd'
  },
  // Cellen op het tabblad Instellingen
  CEL: { NAAM1: 'C5', NAAM2: 'C6', LINK: 'C9' },
  MAANDNAMEN: ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december']
};

// Kolommen van het tabblad Uitgaven
var UITG = { DATUM: 1, WIE: 2, CAT: 3, OMS: 4, BEDRAG: 5, TOEGEVOEGD: 6, KOLOMMEN: 6 };

// Kolommen van het tabblad Maanden
var MND = {
  MAAND: 1, INK1: 2, INK2: 3, OVERIG: 4, TOTAAL: 5, VAST: 6, SPAAR: 7, BUDGET: 8,
  UITGEGEVEN: 9, OVER: 10, GESPAARD: 11, GEHAALD: 12, GOED: 13, BETER: 14, VOORNEMEN: 15, KOLOMMEN: 15
};

var VAST_FORMULE = "=SUM('Vaste lasten'!$B$2:$B)";

var TIPS = [
  'Wacht 24 uur voordat je iets koopt wat je niet echt nodig hebt.',
  'Schrijf elke uitgave meteen op, ook de kleine. Juist die tellen op.',
  'Ga met een boodschappenlijstje naar de winkel en houd je eraan.',
  'Kijk elke zondag samen even naar jullie weekoverzicht.',
  'Vraag jezelf af: heb ik dit nodig, of wil ik het alleen?',
  'Cultuur hoeft niet duur te zijn: denk aan de bibliotheek of gratis musea.',
  'Zet je spaargeld aan het begin van de maand opzij, niet aan het einde.',
  'Plan elke week een dag zonder uitgaven.',
  'Kook voor twee dagen tegelijk: dat bespaart tijd én geld.',
  'Zeg abonnementen op die je de afgelopen maand niet gebruikte.',
  'Vergelijk prijzen per kilo of per liter, niet per verpakking.',
  'Vier een gehaald spaardoel, met iets kleins en gratis.'
];

/* ============================================================
 *  INSTALLEREN
 * ============================================================ */

/**
 * Bouwt alle tabbladen, opmaak, formules en de grafiek op.
 * Veilig om opnieuw uit te voeren: ingevulde gegevens blijven bewaard.
 */
function installeren() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('Open dit script vanuit je Google Sheet (Extensies › Apps Script) en probeer opnieuw.');
  PropertiesService.getScriptProperties().setProperty('KB_SHEET_ID', ss.getId());
  var taal = /^nl/i.test(ss.getSpreadsheetLocale()) ? ss.getSpreadsheetLocale() : 'nl_NL';

  var overzicht = metEngelseFormules_(ss, function () {
    stelThemaIn_(ss);
    maakBladen_(ss);
    bouwInstellingen_(ss);
    bouwVasteLasten_(ss);
    bouwUitgaven_(ss);
    bouwMaanden_(ss);
    zorgVoorMaanden_(ss);
    bouwHulp_(ss);
    var blad = bouwOverzicht_(ss);
    ordenTabbladen_(ss);
    ruimLegeBladenOp_(ss);
    return blad;
  });
  if (ss.getSpreadsheetLocale() !== taal) ss.setSpreadsheetLocale(taal);
  ss.setActiveSheet(overzicht);
  SpreadsheetApp.flush();

  ss.toast('Klaar! Herlaad deze pagina om het menu 家計簿 Kakebo te zien.', '家計簿 Kakebo', 15);
  try {
    onOpen();
  } catch (e) {
    // Vanuit de scripteditor bestaat er geen menubalk; na herladen verschijnt het menu vanzelf.
  }
}

/* ============================================================
 *  MENU, ZIJPANEEL EN WEB-APP
 * ============================================================ */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('家計簿 Kakebo')
    .addItem('➕ Uitgave toevoegen', 'toonApp')
    .addItem('📱 App op je telefoon', 'toonTelefoonLink')
    .addSeparator()
    .addItem('🛠️ Installeren / opmaak herstellen', 'installeren')
    .addToUi();
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (ss && ss.getSheetByName(KB.BLAD.MAANDEN)) zorgVoorMaandenMetSlot_(ss);
  } catch (e) {
    // Niet erg: de app maakt de nieuwe maand ook aan.
  }
}

/** Opent de app in een zijpaneel van de sheet. */
function toonApp() {
  var uitvoer = appUitvoer_(kbStart(), 'zijpaneel');
  SpreadsheetApp.getUi().showSidebar(uitvoer);
}

/** Toont de link en QR-code van de web-app. */
function toonTelefoonLink() {
  var url = appUrl_(ss_());
  var uitvoer = HtmlService.createHtmlOutput(telefoonHtml_(url)).setWidth(420).setHeight(600);
  SpreadsheetApp.getUi().showModalDialog(uitvoer, 'App op je telefoon');
}

/** De web-app (na Implementeren › Web-app). */
function doGet() {
  var start;
  try {
    start = kbStart();
  } catch (err) {
    return HtmlService.createHtmlOutput(foutPagina_(err && err.message ? err.message : String(err)))
      .setTitle('Kakebo')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  }
  return appUitvoer_(start, 'web');
}

function appUitvoer_(start, modus) {
  var json = veiligJson_(start);
  var html = KB_APP_HTML
    .replace('/*__KB_START__*/null', function () { return json; })
    .replace('__KB_MODUS__', function () { return modus; });
  return HtmlService.createHtmlOutput(html)
    .setTitle('Kakebo')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover')
    .addMetaTag('mobile-web-app-capable', 'yes')
    .addMetaTag('apple-mobile-web-app-capable', 'yes');
}

/* ============================================================
 *  API VOOR DE APP  (aangeroepen via google.script.run)
 * ============================================================ */

/** Alles wat de app nodig heeft om te starten. */
function kbStart() {
  var ss = ss_();
  zorgVoorMaandenMetSlot_(ss);
  var vandaag = vandaag_(ss);
  var namen = namen_(ss);
  var ik = PropertiesService.getUserProperties().getProperty('kakebo_ik');
  if (namen.indexOf(ik) < 0) ik = null;
  var url = '';
  try {
    url = appUrl_(ss);
  } catch (e) {
    url = '';
  }
  return {
    versie: KB.VERSIE,
    namen: namen,
    ik: ik,
    vandaag: vandaag,
    appUrl: url,
    categorieen: KB.CATEGORIEEN.map(function (c) { return { naam: c.naam, uitleg: c.uitleg }; }),
    maand: maandOverzicht_(ss, vandaag.slice(0, 7), vandaag)
  };
}

/** Overzicht van één maand, bv. kbMaand('2026-10'). */
function kbMaand(maand) {
  var ss = ss_();
  return maandOverzicht_(ss, checkMaand_(maand));
}

/** Nieuwe uitgave bewaren. */
function kbVoegToe(uitgave) {
  var ss = ss_();
  var u = checkUitgave_(uitgave, namen_(ss));
  metSlot_(function () {
    var sh = blad_(ss, KB.BLAD.UITGAVEN);
    var rij = Math.max(sh.getLastRow(), 1) + 1;
    zorgRuimte_(sh, rij, stijlUitgavenRijen_);
    schrijfUitgave_(sh, rij, u, new Date());
  });
  return maandOverzicht_(ss, u.datum.slice(0, 7));
}

/** Bestaande uitgave wijzigen. ref = { rij, sleutel } uit de lijst van de app. */
function kbWijzig(ref, uitgave) {
  var ss = ss_();
  var u = checkUitgave_(uitgave, namen_(ss));
  metSlot_(function () {
    var sh = blad_(ss, KB.BLAD.UITGAVEN);
    var rij = zoekUitgaveRij_(ss, ref);
    var tijd = sh.getRange(rij, UITG.TOEGEVOEGD).getValue() || new Date();
    schrijfUitgave_(sh, rij, u, tijd);
  });
  return maandOverzicht_(ss, u.datum.slice(0, 7));
}

/** Uitgave verwijderen. */
function kbVerwijder(ref) {
  var ss = ss_();
  var maand = null;
  metSlot_(function () {
    var sh = blad_(ss, KB.BLAD.UITGAVEN);
    var rij = zoekUitgaveRij_(ss, ref);
    maand = naarIso_(sh.getRange(rij, UITG.DATUM).getValue(), tz_(ss));
    sh.deleteRow(rij);
  });
  return maandOverzicht_(ss, maand ? maand.slice(0, 7) : vandaag_(ss).slice(0, 7));
}

/**
 * Maandplan en reflectie bewaren.
 * plan = { ink1, ink2, overig, spaardoel, vaste?, vasteLijst?, goed, beter, voornemen }
 */
function kbBewaarMaand(maand, plan) {
  var ss = ss_();
  var sleutel = checkMaand_(maand);
  if (!plan || typeof plan !== 'object') throw new Error('Geen gegevens ontvangen.');
  var p = {
    ink1: checkBedrag_(plan.ink1, 'Inkomen'),
    ink2: checkBedrag_(plan.ink2, 'Inkomen'),
    overig: checkBedrag_(plan.overig, 'Overig inkomen'),
    spaardoel: checkBedrag_(plan.spaardoel, 'Spaardoel'),
    goed: tekstKort_(plan.goed, 1000),
    beter: tekstKort_(plan.beter, 1000),
    voornemen: tekstKort_(plan.voornemen, 1000)
  };
  var lijst = Array.isArray(plan.vasteLijst) ? checkVasteLijst_(plan.vasteLijst) : null;
  var vaste = (plan.vaste === undefined || plan.vaste === null || plan.vaste === '') ? null : checkBedrag_(plan.vaste, 'Vaste lasten');

  metSlot_(function () {
    var rij = zorgVoorMaand_(ss, sleutel);
    var sh = blad_(ss, KB.BLAD.MAANDEN);
    var live = /Vaste lasten/i.test(sh.getRange(rij, MND.VAST).getFormula());
    if (lijst && live) schrijfVasteLasten_(ss, lijst);
    if (vaste !== null && !live) sh.getRange(rij, MND.VAST).setValue(vaste);
    sh.getRange(rij, MND.INK1, 1, 3).setValues([[p.ink1, p.ink2, p.overig]]);
    sh.getRange(rij, MND.SPAAR).setValue(p.spaardoel);
    sh.getRange(rij, MND.GOED, 1, 3).setValues([[tekstVeilig_(p.goed), tekstVeilig_(p.beter), tekstVeilig_(p.voornemen)]]);
  });
  return maandOverzicht_(ss, sleutel);
}

/** Onthoudt wie deze Google-gebruiker is (Geert of Mart). */
function kbKiesIk(naam) {
  var namen = namen_(ss_());
  if (namen.indexOf(naam) < 0) throw new Error('Onbekende naam.');
  PropertiesService.getUserProperties().setProperty('kakebo_ik', naam);
  return naam;
}

/* ============================================================
 *  GEGEVENS LEZEN EN SCHRIJVEN
 * ============================================================ */

function ss_() {
  var ss = null;
  try {
    ss = SpreadsheetApp.getActiveSpreadsheet();
  } catch (e) {
    ss = null;
  }
  if (ss) return ss;
  var id = PropertiesService.getScriptProperties().getProperty('KB_SHEET_ID');
  if (!id) throw new Error('Kakebo is nog niet geïnstalleerd. Open de sheet en voer "installeren" uit.');
  try {
    return SpreadsheetApp.openById(id);
  } catch (e) {
    throw new Error('Je hebt geen toegang tot de Kakebo-sheet. Vraag om de sheet met jou te delen als bewerker.');
  }
}

function blad_(ss, naam) {
  var sh = ss.getSheetByName(naam);
  if (!sh) throw new Error('Het tabblad "' + naam + '" ontbreekt. Kies in de sheet: 家計簿 Kakebo › Installeren.');
  return sh;
}

function tz_(ss) {
  return ss.getSpreadsheetTimeZone() || Session.getScriptTimeZone() || 'Europe/Brussels';
}

function vandaag_(ss) {
  return Utilities.formatDate(new Date(), tz_(ss), 'yyyy-MM-dd');
}

function namen_(ss) {
  var namen = KB.NAMEN.slice();
  var sh = ss.getSheetByName(KB.BLAD.INST);
  if (sh) {
    var n1 = String(sh.getRange(KB.CEL.NAAM1).getValue() || '').trim();
    var n2 = String(sh.getRange(KB.CEL.NAAM2).getValue() || '').trim();
    if (n1) namen[0] = n1;
    if (n2 && n2 !== namen[0]) namen[1] = n2;
  }
  return namen;
}

function metSlot_(fn) {
  var slot = LockService.getScriptLock();
  if (!slot.tryLock(20000)) throw new Error('Het boekje is even bezet. Probeer het zo opnieuw.');
  try {
    return fn();
  } finally {
    SpreadsheetApp.flush();
    slot.releaseLock();
  }
}

function leesUitgaven_(ss) {
  var sh = blad_(ss, KB.BLAD.UITGAVEN);
  var tz = tz_(ss);
  var n = sh.getLastRow() - 1;
  if (n < 1) return [];
  var waarden = sh.getRange(2, 1, n, UITG.KOLOMMEN).getValues();
  var lijst = [];
  for (var i = 0; i < waarden.length; i++) {
    var r = waarden[i];
    var datum = naarIso_(r[UITG.DATUM - 1], tz);
    var bedrag = parseBedrag_(r[UITG.BEDRAG - 1]);
    if (!datum || bedrag === null) continue;
    var u = {
      rij: i + 2,
      datum: datum,
      wie: String(r[UITG.WIE - 1] || '').trim(),
      categorie: String(r[UITG.CAT - 1] || '').trim(),
      omschrijving: String(r[UITG.OMS - 1] || '').trim(),
      bedrag: rond_(bedrag)
    };
    u.sleutel = sleutel_(u);
    lijst.push(u);
  }
  return lijst;
}

function leesMaanden_(ss) {
  var sh = blad_(ss, KB.BLAD.MAANDEN);
  var tz = tz_(ss);
  var n = sh.getLastRow() - 1;
  if (n < 1) return [];
  var waarden = sh.getRange(2, 1, n, MND.KOLOMMEN).getValues();
  var formules = sh.getRange(2, MND.VAST, n, 1).getFormulas();
  var lijst = [];
  for (var i = 0; i < waarden.length; i++) {
    var r = waarden[i];
    var iso = naarIso_(r[MND.MAAND - 1], tz);
    if (!iso) continue;
    lijst.push({
      rij: i + 2,
      maand: iso.slice(0, 7),
      ink1: getal_(r[MND.INK1 - 1]),
      ink2: getal_(r[MND.INK2 - 1]),
      overig: getal_(r[MND.OVERIG - 1]),
      vaste: getal_(r[MND.VAST - 1]),
      vasteLive: /Vaste lasten/i.test(formules[i][0]),
      spaardoel: getal_(r[MND.SPAAR - 1]),
      goed: String(r[MND.GOED - 1] || ''),
      beter: String(r[MND.BETER - 1] || ''),
      voornemen: String(r[MND.VOORNEMEN - 1] || '')
    });
  }
  return lijst;
}

function leesVasteLasten_(ss) {
  var sh = blad_(ss, KB.BLAD.VAST);
  var n = sh.getLastRow() - 1;
  if (n < 1) return [];
  var waarden = sh.getRange(2, 1, n, 3).getValues();
  var lijst = [];
  for (var i = 0; i < waarden.length; i++) {
    var naam = String(waarden[i][0] || '').trim();
    var bedrag = parseBedrag_(waarden[i][1]);
    if (!naam && bedrag === null) continue;
    lijst.push({ naam: naam, bedrag: rond_(bedrag || 0), notitie: String(waarden[i][2] || '').trim() });
  }
  return lijst;
}

function schrijfVasteLasten_(ss, lijst) {
  var sh = blad_(ss, KB.BLAD.VAST);
  var oud = Math.max(sh.getLastRow() - 1, 0);
  if (oud > 0) sh.getRange(2, 1, oud, 3).clearContent();
  if (!lijst.length) return;
  zorgRuimte_(sh, lijst.length + 1, null);
  sh.getRange(2, 1, lijst.length, 3).setValues(lijst.map(function (v) {
    return [tekstVeilig_(v.naam), v.bedrag, tekstVeilig_(v.notitie)];
  }));
}

function schrijfUitgave_(sh, rij, u, tijd) {
  sh.getRange(rij, 1, 1, UITG.KOLOMMEN).setValues([[
    serieel_(u.datum),
    u.wie,
    u.categorie,
    tekstVeilig_(u.omschrijving),
    u.bedrag,
    tijd
  ]]);
  // De kolommen zijn bij het installeren opgemaakt; kopieer die opmaak voor de zekerheid
  // van de eerste rij (zonder notaties opnieuw te laten lezen in de taal van de sheet).
  if (rij > 2) sh.getRange(2, 1, 1, UITG.KOLOMMEN).copyFormatToRange(sh, 1, UITG.KOLOMMEN, rij, rij);
}

function zoekUitgaveRij_(ss, ref) {
  if (!ref || typeof ref.sleutel !== 'string') throw new Error('Onbekende uitgave.');
  var lijst = leesUitgaven_(ss);
  var gevonden = null;
  for (var i = 0; i < lijst.length; i++) {
    if (lijst[i].sleutel !== ref.sleutel) continue;
    if (lijst[i].rij === Number(ref.rij)) return lijst[i].rij;
    if (gevonden === null) gevonden = lijst[i].rij;
  }
  if (gevonden !== null) return gevonden;
  throw new Error('Deze uitgave is niet meer gevonden. Misschien is ze net gewijzigd of verwijderd. Vernieuw de app.');
}

/** Zelfde als zorgVoorMaanden_, maar nooit tegelijk met iemand anders (geen dubbele maanden). */
function zorgVoorMaandenMetSlot_(ss) {
  var slot = LockService.getScriptLock();
  if (!slot.tryLock(10000)) return;
  try {
    zorgVoorMaanden_(ss);
    SpreadsheetApp.flush();
  } finally {
    slot.releaseLock();
  }
}

/** Zorgt dat de lopende maand bestaat en zet de vaste lasten van afgelopen maanden vast. */
function zorgVoorMaanden_(ss) {
  var sh = ss.getSheetByName(KB.BLAD.MAANDEN);
  if (!sh || !ss.getSheetByName(KB.BLAD.VAST)) return;
  var huidig = vandaag_(ss).slice(0, 7);
  var lijst = leesMaanden_(ss);
  var totaal = null;
  lijst.forEach(function (m) {
    if (m.maand < huidig && m.vasteLive) {
      if (totaal === null) totaal = somVast_(leesVasteLasten_(ss));
      sh.getRange(m.rij, MND.VAST).setValue(totaal);
    }
  });
  var bestaat = lijst.some(function (m) { return m.maand === huidig; });
  if (!bestaat) zorgVoorMaand_(ss, huidig, lijst);
}

/** Geeft het rijnummer van een maand; maakt de rij aan (op de juiste plek) als die nog niet bestaat. */
function zorgVoorMaand_(ss, maand, lijst) {
  lijst = lijst || leesMaanden_(ss);
  for (var i = 0; i < lijst.length; i++) {
    if (lijst[i].maand === maand) return lijst[i].rij;
  }
  return metEngelseFormules_(ss, function () { return maakMaandRij_(ss, maand, lijst); });
}

function maakMaandRij_(ss, maand, lijst) {
  var sh = blad_(ss, KB.BLAD.MAANDEN);
  var huidig = vandaag_(ss).slice(0, 7);
  var vorige = null;
  var volgendeRij = null;
  lijst.forEach(function (m) {
    if (m.maand < maand && (!vorige || m.maand > vorige.maand)) vorige = m;
    if (m.maand > maand && (volgendeRij === null || m.rij < volgendeRij)) volgendeRij = m.rij;
  });

  var rij;
  if (volgendeRij !== null) {
    schuifMaandRijenOp_(sh, volgendeRij);
    rij = volgendeRij;
  } else {
    rij = Math.max(sh.getLastRow(), 1) + 1;
    zorgRuimte_(sh, rij, null);
  }

  sh.getRange(rij, 1, 1, MND.KOLOMMEN).clearContent();
  sh.getRange(rij, MND.MAAND, 1, 4).setValues([[
    serieel_(maand + '-01'),
    vorige ? vorige.ink1 : 0,
    vorige ? vorige.ink2 : 0,
    vorige ? vorige.overig : 0
  ]]);
  if (maand >= huidig) {
    sh.getRange(rij, MND.VAST).setFormula(VAST_FORMULE);
  } else {
    sh.getRange(rij, MND.VAST).setValue(somVast_(leesVasteLasten_(ss)));
  }
  sh.getRange(rij, MND.SPAAR).setValue(vorige ? vorige.spaardoel : 0);
  zetMaandFormules_(sh, rij);
  stijlMaandRijen_(sh, rij, 1);
  return rij;
}

/**
 * Schuift de maandrijen vanaf `vanaf` één rij naar beneden door ze te herschrijven.
 * Bewust geen rij invoegen: dan zou Google Sheets de verwijzingen naar Maanden!A2:A
 * in het dashboard mee laten opschuiven.
 */
function schuifMaandRijenOp_(sh, vanaf) {
  var laatste = sh.getLastRow();
  if (vanaf > laatste) return;
  var aantal = laatste - vanaf + 1;
  var bron = sh.getRange(vanaf, 1, aantal, MND.KOLOMMEN);
  var waarden = bron.getValues();
  var formules = bron.getFormulas();
  var data = waarden.map(function (r, i) {
    return r.map(function (v, k) { return formules[i][k] || v; });
  });
  zorgRuimte_(sh, laatste + 1, null);
  sh.getRange(vanaf + 1, 1, aantal, MND.KOLOMMEN).setValues(data);
  for (var r = vanaf + 1; r <= laatste + 1; r++) zetMaandFormules_(sh, r);
}

function zetMaandFormules_(sh, r) {
  sh.getRange(r, MND.TOTAAL).setFormula('=SUM(B' + r + ':D' + r + ')');
  var start = '$A' + r;
  sh.getRange(r, MND.BUDGET, 1, 5).setFormulas([[
    '=E' + r + '-F' + r + '-G' + r,
    '=SUMIFS(Uitgaven!$E$2:$E,Uitgaven!$A$2:$A,">="&' + start + ',Uitgaven!$A$2:$A,"<"&EDATE(' + start + ',1))',
    '=H' + r + '-I' + r,
    '=E' + r + '-F' + r + '-I' + r,
    '=IF(E' + r + '=0,"",IF(K' + r + '>=G' + r + ',IF(TODAY()>=EDATE(' + start + ',1),"✓ gehaald","✓ op koers"),IF(TODAY()>=EDATE(' + start + ',1),"✗ niet gehaald","⚠ let op")))'
  ]]);
}

/* ============================================================
 *  BEREKENINGEN (zonder sheet — ook getest buiten Google)
 * ============================================================ */

function maandOverzicht_(ss, maand, vandaag) {
  var gegevens = {
    uitgaven: leesUitgaven_(ss),
    maanden: leesMaanden_(ss),
    vast: leesVasteLasten_(ss),
    namen: namen_(ss)
  };
  return vatSamen_(gegevens, maand, vandaag || vandaag_(ss));
}

/**
 * Rekent alles uit wat de app voor één maand toont.
 * d = { uitgaven, maanden, vast, namen }, maand = 'jjjj-mm', vandaag = 'jjjj-mm-dd'
 */
function vatSamen_(d, maand, vandaag) {
  var huidig = vandaag.slice(0, 7);
  var j = Number(maand.slice(0, 4));
  var m = Number(maand.slice(5, 7));
  var vastTotaal = rond_(somVast_(d.vast));
  var plan = planVoor_(d.maanden, maand, vastTotaal, huidig);
  var dagen = dagenInMaand_(j, m);
  var status = maand < huidig ? 'verleden' : (maand > huidig ? 'toekomst' : 'huidig');
  var dagNr = status === 'huidig' ? Number(vandaag.slice(8, 10)) : (status === 'verleden' ? dagen : 0);
  var dagenOver = status === 'huidig' ? dagen - dagNr + 1 : (status === 'toekomst' ? dagen : 0);

  var items = d.uitgaven.filter(function (u) { return u.datum.slice(0, 7) === maand; });
  items.sort(function (a, b) {
    if (a.datum !== b.datum) return a.datum < b.datum ? 1 : -1;
    return b.rij - a.rij;
  });

  var perCategorie = KB.CATEGORIEEN.map(function (c) { return { naam: c.naam, bedrag: 0, aantal: 0 }; });
  var onbekend = { naam: 'Onbekend', bedrag: 0, aantal: 0 };
  var weken = weken_(j, m).map(function (w) {
    var per = {};
    KB.CATEGORIEEN.forEach(function (c) { per[c.naam] = 0; });
    w.perCategorie = per;
    w.totaal = 0;
    return w;
  });
  var personen = d.namen.map(function (n) { return { naam: n, bedrag: 0, aantal: 0 }; });
  var uitgegeven = 0;

  items.forEach(function (u) {
    uitgegeven += u.bedrag;
    var cat = null;
    for (var i = 0; i < perCategorie.length; i++) if (perCategorie[i].naam === u.categorie) cat = perCategorie[i];
    (cat || onbekend).bedrag += u.bedrag;
    (cat || onbekend).aantal += 1;
    var dag = Number(u.datum.slice(8, 10));
    weken.forEach(function (w) {
      if (dag >= w.vanDag && dag <= w.totDag) {
        w.totaal += u.bedrag;
        if (cat) w.perCategorie[cat.naam] += u.bedrag;
      }
    });
    var persoon = null;
    personen.forEach(function (p) { if (p.naam === u.wie) persoon = p; });
    if (!persoon) {
      persoon = { naam: u.wie || 'Onbekend', bedrag: 0, aantal: 0 };
      personen.push(persoon);
    }
    persoon.bedrag += u.bedrag;
    persoon.aantal += 1;
  });
  if (onbekend.aantal) perCategorie.push(onbekend);

  perCategorie.forEach(function (c) {
    c.bedrag = rond_(c.bedrag);
    c.aandeel = uitgegeven > 0 ? c.bedrag / uitgegeven : 0;
  });
  personen.forEach(function (p) {
    p.bedrag = rond_(p.bedrag);
    p.aandeel = uitgegeven > 0 ? p.bedrag / uitgegeven : 0;
  });
  weken.forEach(function (w) {
    w.totaal = rond_(w.totaal);
    Object.keys(w.perCategorie).forEach(function (k) { w.perCategorie[k] = rond_(w.perCategorie[k]); });
  });

  uitgegeven = rond_(uitgegeven);
  var totaalInkomen = rond_(plan.ink1 + plan.ink2 + plan.overig);
  var budget = rond_(totaalInkomen - plan.vaste - plan.spaardoel);
  var over = rond_(budget - uitgegeven);

  return {
    maand: maand,
    label: KB.MAANDNAMEN[m - 1] + ' ' + j,
    status: status,
    vandaag: vandaag,
    dagen: dagen,
    dagNr: dagNr,
    dagenOver: dagenOver,
    plan: plan,
    vasteLijst: d.vast,
    totaalInkomen: totaalInkomen,
    budget: budget,
    uitgegeven: uitgegeven,
    over: over,
    gespaard: rond_(totaalInkomen - plan.vaste - uitgegeven),
    perDagNog: status === 'huidig' && over > 0 ? rond_(over / dagenOver) : 0,
    gemiddeldPerDag: dagNr > 0 ? rond_(uitgegeven / dagNr) : 0,
    aantal: items.length,
    perCategorie: perCategorie,
    perWeek: weken,
    perPersoon: personen,
    uitgaven: items
  };
}

function planVoor_(maanden, maand, vastTotaal, huidig) {
  var rij = null;
  var vorige = null;
  maanden.forEach(function (m) {
    if (m.maand === maand) rij = m;
    else if (m.maand < maand && (!vorige || m.maand > vorige.maand)) vorige = m;
  });
  if (rij) {
    return {
      bestaat: true,
      ink1: rij.ink1, ink2: rij.ink2, overig: rij.overig,
      vaste: rij.vasteLive ? vastTotaal : rij.vaste,
      vasteLive: rij.vasteLive,
      spaardoel: rij.spaardoel,
      goed: rij.goed, beter: rij.beter, voornemen: rij.voornemen
    };
  }
  var bron = vorige || { ink1: 0, ink2: 0, overig: 0, spaardoel: 0 };
  return {
    bestaat: false,
    ink1: bron.ink1, ink2: bron.ink2, overig: bron.overig,
    vaste: vastTotaal,
    vasteLive: maand >= huidig,
    spaardoel: bron.spaardoel,
    goed: '', beter: '', voornemen: ''
  };
}

/** Weken van maandag t/m zondag binnen de maand (week 1 begint op de 1e). */
function weken_(j, m) {
  var dagen = dagenInMaand_(j, m);
  var eersteWeekdag = (new Date(Date.UTC(j, m - 1, 1)).getUTCDay() + 6) % 7; // 0 = maandag
  var lijst = [];
  var dag = 1;
  var nr = 1;
  while (dag <= dagen) {
    var weekdag = (eersteWeekdag + dag - 1) % 7;
    var eind = Math.min(dagen, dag + 6 - weekdag);
    lijst.push({ nr: nr, vanDag: dag, totDag: eind, van: isoUit_(j, m, dag), tot: isoUit_(j, m, eind) });
    dag = eind + 1;
    nr += 1;
  }
  return lijst;
}

function somVast_(lijst) {
  var som = 0;
  lijst.forEach(function (v) { som += v.bedrag || 0; });
  return rond_(som);
}

function sleutel_(u) {
  return [u.datum, u.wie, u.categorie, u.omschrijving, Number(u.bedrag).toFixed(2)].join('|');
}

/* ============================================================
 *  CONTROLES EN OMZETTINGEN
 * ============================================================ */

function checkUitgave_(u, namen) {
  if (!u || typeof u !== 'object') throw new Error('Geen uitgave ontvangen.');
  var datum = typeof u.datum === 'string' ? naarIso_(u.datum, 'UTC') : null;
  if (!datum || datum < '2000-01-01' || datum > '2100-12-31') throw new Error('Kies een geldige datum.');
  var bedrag = parseBedrag_(u.bedrag);
  if (bedrag === null || rond_(bedrag) === 0) throw new Error('Vul een bedrag in.');
  if (Math.abs(bedrag) > 1000000) throw new Error('Dat bedrag is wel erg groot. Klopt het?');
  var wie = String(u.wie || '');
  if (namen.indexOf(wie) < 0) throw new Error('Kies wie de uitgave deed.');
  var categorie = String(u.categorie || '');
  var bestaat = KB.CATEGORIEEN.some(function (c) { return c.naam === categorie; });
  if (!bestaat) throw new Error('Kies een categorie.');
  return {
    datum: datum,
    bedrag: rond_(bedrag),
    wie: wie,
    categorie: categorie,
    omschrijving: tekstKort_(u.omschrijving, 200).replace(/\s+/g, ' ')
  };
}

function checkMaand_(maand) {
  var s = String(maand || '');
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(s) || s < '2000-01' || s > '2100-12') throw new Error('Ongeldige maand.');
  return s;
}

function checkBedrag_(waarde, wat) {
  if (waarde === undefined || waarde === null || waarde === '') return 0;
  var n = parseBedrag_(waarde);
  if (n === null || Math.abs(n) > 100000000) throw new Error(wat + ': ongeldig bedrag.');
  return rond_(n);
}

function checkVasteLijst_(lijst) {
  if (lijst.length > 60) throw new Error('Dat zijn wel heel veel vaste lasten (max. 60).');
  return lijst.map(function (v) {
    return {
      naam: tekstKort_(v && v.naam, 80),
      bedrag: checkBedrag_(v && v.bedrag, 'Vaste last'),
      notitie: tekstKort_(v && v.notitie, 200)
    };
  }).filter(function (v) { return v.naam || v.bedrag; });
}

function tekstKort_(s, max) {
  return String(s === undefined || s === null ? '' : s).trim().slice(0, max);
}

/** Voorkomt dat tekst als formule of getal wordt gelezen (bv. "=..." of "12-10"). */
function tekstVeilig_(s) {
  s = String(s === undefined || s === null ? '' : s);
  if (/^[=+\-@]/.test(s) || (/^[\d\s.,\/:-]+$/.test(s) && /\d/.test(s))) return "'" + s;
  return s;
}

/** Leest bedragen als "12,50", "1.250", "€ 3,20" of 12.5. */
function parseBedrag_(waarde) {
  if (typeof waarde === 'number') return isFinite(waarde) ? waarde : null;
  var s = String(waarde === undefined || waarde === null ? '' : waarde).replace(/[€\s\u00a0']/g, '');
  if (!s) return null;
  var teken = 1;
  if (s.charAt(0) === '-' || s.charAt(0) === '−') {
    teken = -1;
    s = s.slice(1);
  }
  if (!/^[\d.,]+$/.test(s) || !/\d/.test(s)) return null;
  var komma = s.lastIndexOf(',');
  var punt = s.lastIndexOf('.');
  if (komma >= 0 && punt >= 0) {
    s = komma > punt ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
  } else if (komma >= 0) {
    if (s.split(',').length > 2) return null;
    s = s.replace(',', '.');
  } else if (punt >= 0) {
    var delen = s.split('.');
    if (delen.length > 2 || delen[1].length === 3) {
      for (var i = 1; i < delen.length; i++) if (delen[i].length !== 3) return null;
      s = delen.join('');
    }
  }
  var n = Number(s);
  return isFinite(n) ? teken * n : null;
}

function getal_(waarde) {
  var n = parseBedrag_(waarde);
  return n === null ? 0 : rond_(n);
}

function rond_(n) {
  return Math.round((Number(n) || 0) * 100) / 100;
}

function isDatum_(v) {
  return Object.prototype.toString.call(v) === '[object Date]' && !isNaN(v.getTime());
}

/** Zet een celwaarde om naar 'jjjj-mm-dd' (of null). */
function naarIso_(v, tz) {
  if (isDatum_(v)) return Utilities.formatDate(v, tz, 'yyyy-MM-dd');
  if (typeof v === 'number' && isFinite(v) && v > 20000 && v < 80000) {
    var d = new Date(Date.UTC(1899, 11, 30) + Math.floor(v) * 86400000);
    return isoUit_(d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate());
  }
  if (typeof v === 'string') {
    var s = v.trim();
    var m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (m) return isoUit_(Number(m[1]), Number(m[2]), Number(m[3]));
    m = s.match(/^(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{4})$/);
    if (m) return isoUit_(Number(m[3]), Number(m[2]), Number(m[1]));
  }
  return null;
}

function isoUit_(j, m, d) {
  if (!(j >= 1900 && j <= 2200 && m >= 1 && m <= 12 && d >= 1 && d <= dagenInMaand_(j, m))) return null;
  return j + '-' + (m < 10 ? '0' : '') + m + '-' + (d < 10 ? '0' : '') + d;
}

function dagenInMaand_(j, m) {
  return new Date(Date.UTC(j, m, 0)).getUTCDate();
}

/** 'jjjj-mm-dd' → serieel datumgetal van Google Sheets (tijdzone-onafhankelijk). */
function serieel_(iso) {
  var j = Number(iso.slice(0, 4));
  var m = Number(iso.slice(5, 7));
  var d = Number(iso.slice(8, 10));
  return Math.round((Date.UTC(j, m - 1, d) - Date.UTC(1899, 11, 30)) / 86400000);
}

function veiligJson_(obj) {
  return JSON.stringify(obj)
    .replace(/</g, '\\u003c')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

function appUrl_(ss) {
  var props = PropertiesService.getScriptProperties();
  var url = '';
  try {
    url = ScriptApp.getService().getUrl() || '';
  } catch (e) {
    url = '';
  }
  if (/\/exec$/.test(url)) {
    if (props.getProperty('KB_APP_URL') !== url) {
      props.setProperty('KB_APP_URL', url);
      var inst = ss.getSheetByName(KB.BLAD.INST);
      if (inst) {
        inst.getRange(KB.CEL.LINK).setValue(url).setFontColor(KB.KLEUR.inkt).setFontStyle('normal');
      }
    }
    return url;
  }
  return props.getProperty('KB_APP_URL') || '';
}

/* ============================================================
 *  TABBLADEN OPBOUWEN
 * ============================================================ */

/**
 * Voert fn uit terwijl de sheet even op Engels (VS) staat, en zet daarna de taal terug.
 * Google Sheets leest een formule uit een script in de taal van de sheet: in het Nederlands
 * met ; in plaats van ,. De formules hier zijn in de Engelse vorm geschreven. Eenmaal
 * opgeslagen werken ze in elke taal. Ook getalnotaties worden zo altijd op dezelfde manier gelezen.
 */
function metEngelseFormules_(ss, fn) {
  var taal = ss.getSpreadsheetLocale();
  if (taal === 'en_US') return fn();
  ss.setSpreadsheetLocale('en_US');
  try {
    var uit = fn();
    SpreadsheetApp.flush();
    return uit;
  } finally {
    ss.setSpreadsheetLocale(taal);
  }
}

function stelThemaIn_(ss) {
  try {
    var thema = ss.getSpreadsheetTheme() || ss.resetSpreadsheetTheme();
    thema.setFontFamily(KB.LETTER);
  } catch (e) {
    // Thema is niet essentieel.
  }
}

function maakBladen_(ss) {
  [KB.BLAD.OVERZICHT, KB.BLAD.UITGAVEN, KB.BLAD.MAANDEN, KB.BLAD.VAST, KB.BLAD.INST, KB.BLAD.HULP].forEach(function (naam) {
    if (!ss.getSheetByName(naam)) ss.insertSheet(naam);
  });
}

function ordenTabbladen_(ss) {
  var volgorde = [KB.BLAD.OVERZICHT, KB.BLAD.UITGAVEN, KB.BLAD.MAANDEN, KB.BLAD.VAST, KB.BLAD.INST, KB.BLAD.HULP];
  var hulp = ss.getSheetByName(KB.BLAD.HULP);
  if (hulp.isSheetHidden()) hulp.showSheet();
  volgorde.forEach(function (naam, i) {
    ss.setActiveSheet(ss.getSheetByName(naam));
    ss.moveActiveSheet(i + 1);
  });
  ss.setActiveSheet(ss.getSheetByName(KB.BLAD.OVERZICHT));
  ss.getSheetByName(KB.BLAD.HULP).hideSheet();
}

function ruimLegeBladenOp_(ss) {
  var eigen = {};
  Object.keys(KB.BLAD).forEach(function (k) { eigen[KB.BLAD[k]] = true; });
  ss.getSheets().forEach(function (sh) {
    if (eigen[sh.getName()]) return;
    if (sh.getLastRow() === 0 && sh.getLastColumn() === 0 && sh.getCharts().length === 0) ss.deleteSheet(sh);
  });
}

/** Zorgt voor precies zoveel rijen en kolommen (alleen voor bladen zonder invoer). */
function maatBlad_(sh, rijen, kolommen) {
  var mr = sh.getMaxRows();
  var mk = sh.getMaxColumns();
  if (mk > kolommen) sh.deleteColumns(kolommen + 1, mk - kolommen);
  else if (mk < kolommen) sh.insertColumnsAfter(mk, kolommen - mk);
  if (mr > rijen) sh.deleteRows(rijen + 1, mr - rijen);
  else if (mr < rijen) sh.insertRowsAfter(mr, rijen - mr);
}

/** Voor bladen met invoer: minstens zoveel rijen, en lege extra kolommen weg. */
function maatInvoerBlad_(sh, minRijen, kolommen) {
  var mr = sh.getMaxRows();
  if (mr < minRijen) sh.insertRowsAfter(mr, minRijen - mr);
  var mk = sh.getMaxColumns();
  if (mk < kolommen) sh.insertColumnsAfter(mk, kolommen - mk);
  else if (mk > kolommen && sh.getLastColumn() <= kolommen) sh.deleteColumns(kolommen + 1, mk - kolommen);
}

/** Zorgt dat rij `rij` bestaat, met ruimte erna; nieuwe rijen worden netjes opgemaakt. */
function zorgRuimte_(sh, rij, stijlFn) {
  var mr = sh.getMaxRows();
  if (rij + 20 <= mr) return;
  // Nooit vóór rij 3 invoegen: formules verwijzen naar bereiken die op rij 2 beginnen.
  var laatste = Math.min(Math.max(sh.getLastRow(), 2), mr);
  var extra = 500;
  sh.insertRowsAfter(laatste, extra);
  if (stijlFn) metEngelseFormules_(sh.getParent(), function () { stijlFn(sh, laatste + 1, extra); });
}

function stijl_(r, s) {
  if (s.bg !== undefined) r.setBackground(s.bg);
  if (s.kleur) r.setFontColor(s.kleur);
  if (s.grootte) r.setFontSize(s.grootte);
  if (s.vet !== undefined) r.setFontWeight(s.vet ? 'bold' : 'normal');
  if (s.cursief !== undefined) r.setFontStyle(s.cursief ? 'italic' : 'normal');
  if (s.uitlijn) r.setHorizontalAlignment(s.uitlijn);
  if (s.vuitlijn) r.setVerticalAlignment(s.vuitlijn);
  if (s.fmt) r.setNumberFormat(s.fmt);
  if (s.wrap !== undefined) r.setWrap(s.wrap);
  if (s.font) r.setFontFamily(s.font);
  return r;
}

function rand_(r, kleur, dik) {
  return r.setBorder(true, true, true, true, null, null, kleur || KB.KLEUR.lijn,
    dik ? SpreadsheetApp.BorderStyle.SOLID_MEDIUM : SpreadsheetApp.BorderStyle.SOLID);
}

function koprij_(r) {
  return stijl_(r, { bg: KB.KLEUR.inkt, kleur: KB.KLEUR.wit, vet: true, vuitlijn: 'middle', grootte: 10 });
}

function titelTekst_(tekst, grootte) {
  var stijlKanji = SpreadsheetApp.newTextStyle().setForegroundColor(KB.KLEUR.hanko).setBold(true).setFontSize(grootte).build();
  var stijlRest = SpreadsheetApp.newTextStyle().setForegroundColor(KB.KLEUR.inkt).setBold(true).setFontSize(grootte).build();
  return SpreadsheetApp.newRichTextValue()
    .setText(tekst)
    .setTextStyle(0, 3, stijlKanji)
    .setTextStyle(3, tekst.length, stijlRest)
    .build();
}

function verwijderBescherming_(sh) {
  sh.getProtections(SpreadsheetApp.ProtectionType.RANGE).forEach(function (p) {
    if (String(p.getDescription()).indexOf('Kakebo') === 0 && p.canEdit()) p.remove();
  });
}

function beschermWaarschuwing_(r, omschrijving) {
  var p = r.protect();
  p.setDescription('Kakebo: ' + omschrijving);
  p.setWarningOnly(true);
}

/* ---------- Instellingen ---------- */

function bouwInstellingen_(ss) {
  var sh = ss.getSheetByName(KB.BLAD.INST);
  var K = KB.KLEUR;
  var naam1 = KB.NAMEN[0];
  var naam2 = KB.NAMEN[1];
  var link = '';
  if (sh.getLastRow() >= 9) {
    var oud = sh.getRange('C5:C9').getValues();
    naam1 = String(oud[0][0] || '').trim() || naam1;
    naam2 = String(oud[1][0] || '').trim() || naam2;
    link = /^https:\/\//.test(String(oud[4][0])) ? String(oud[4][0]) : '';
  }
  link = link || PropertiesService.getScriptProperties().getProperty('KB_APP_URL') || '';

  verwijderBescherming_(sh);
  sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).breakApart();
  sh.clear();
  sh.clearConditionalFormatRules();
  maatBlad_(sh, 30, 6);
  sh.setHiddenGridlines(true);
  sh.setTabColor('#8f887d');
  stijl_(sh.getRange(1, 1, 30, 6), { bg: K.papier, font: KB.LETTER, kleur: K.inkt, grootte: 10, vuitlijn: 'middle' });
  [20, 210, 320, 20, 300, 20].forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
  sh.setRowHeights(1, 30, 24);
  sh.setRowHeight(1, 14);
  sh.setRowHeight(2, 46);

  sh.getRange('B2:E2').merge().setRichTextValue(titelTekst_('家計簿  Kakebo · instellingen en uitleg', 18));

  stijl_(sh.getRange('B4').setValue('Wie houden het boekje bij?'), { vet: true, grootte: 11 });
  sh.getRange('B5:B6').setValues([['Persoon 1'], ['Persoon 2']]);
  stijl_(sh.getRange('B5:B6'), { kleur: K.inkt2 });
  sh.getRange('C5:C6').setValues([[naam1], [naam2]]);
  rand_(stijl_(sh.getRange('C5:C6'), { bg: K.kaart, vet: true, grootte: 11 }), K.lijn);
  stijl_(sh.getRange('B7:E7').merge().setValue('Pas de namen gerust aan: ze verschijnen dan overal in het boekje en in de app.'), { kleur: K.inkt3, cursief: true });

  stijl_(sh.getRange('B9').setValue('Link naar de app'), { vet: true, grootte: 11 });
  var linkCel = sh.getRange(KB.CEL.LINK);
  if (link) {
    stijl_(linkCel.setValue(link), { kleur: K.inkt, wrap: false });
  } else {
    stijl_(linkCel.setValue('Nog niet gepubliceerd: zie de handleiding, stap 5.'), { kleur: K.inkt3, cursief: true });
  }
  stijl_(sh.getRange('B10:E10').merge().setValue(
    'De link wordt vanzelf ingevuld zodra de web-app één keer geopend is. Via 家計簿 Kakebo › App op je telefoon krijg je ook een QR-code.'),
    { kleur: K.inkt3, cursief: true, wrap: true });
  sh.setRowHeight(10, 36);

  stijl_(sh.getRange('B12').setValue('De vier categorieën'), { vet: true, grootte: 11 });
  KB.CATEGORIEEN.forEach(function (c, i) {
    var r = 13 + i;
    stijl_(sh.getRange(r, 2).setValue(c.naam), { bg: c.tint, vet: true });
    sh.getRange(r, 2).setBorder(null, true, null, null, null, null, c.kleur, SpreadsheetApp.BorderStyle.SOLID_THICK);
    stijl_(sh.getRange(r, 3, 1, 3).merge().setValue(c.uitleg), { bg: K.kaart, kleur: K.inkt2 });
    sh.setRowHeight(r, 28);
  });

  stijl_(sh.getRange('B18').setValue('Zo werkt Kakebo'), { vet: true, grootte: 11 });
  var stappen = [
    '1.  Begin van de maand: vul jullie inkomen, de vaste lasten en het spaardoel in (app › Maand). Wat overblijft is jullie budget.',
    '2.  Elke dag: schrijf elke uitgave op en kies een categorie: Overleven, Optioneel, Cultuur of Extra.',
    '3.  Elke week: kijk samen naar het weekoverzicht. Waar ging het geld naartoe?',
    '4.  Einde van de maand: beantwoord de vier vragen. Hoeveel hadden we? Hoeveel wilden we sparen? Hoeveel gaven we uit? Hoe kunnen we het beter doen?',
    'Tip: zet de app op het beginscherm van je telefoon (家計簿 Kakebo › App op je telefoon).'
  ];
  stappen.forEach(function (t, i) {
    var r = 19 + i;
    stijl_(sh.getRange(r, 2, 1, 4).merge().setValue(t), { bg: K.kaart, wrap: true, vuitlijn: 'middle', kleur: i === 4 ? K.inkt2 : K.inkt });
    sh.setRowHeight(r, 38);
  });
  rand_(sh.getRange(19, 2, stappen.length, 4), K.lijn);

  stijl_(sh.getRange('B26:E26').merge().setValue('Kakebo ' + KB.VERSIE + ' · gemaakt voor ' + naam1 + ' & ' + naam2),
    { kleur: K.inkt3, grootte: 9 });
  return sh;
}

/* ---------- Vaste lasten ---------- */

function bouwVasteLasten_(ss) {
  var sh = ss.getSheetByName(KB.BLAD.VAST);
  var K = KB.KLEUR;
  maatInvoerBlad_(sh, 100, 5);
  var heeftData = false;
  if (sh.getLastRow() >= 2) {
    heeftData = sh.getRange(2, 1, sh.getLastRow() - 1, 2).getValues().some(function (r) { return r[0] !== '' || r[1] !== ''; });
  }
  sh.getBandings().forEach(function (b) { b.remove(); });
  sh.getRange(1, 4, sh.getMaxRows(), 2).breakApart();
  sh.getRange(1, 4, sh.getMaxRows(), 2).clear();

  sh.getRange('A1:C1').setValues([['Vaste last', 'Bedrag per maand', 'Notitie']]);
  if (!heeftData) {
    var standaard = [
      'Huur of hypotheek', 'Energie', 'Water', 'Internet en telefoon',
      'Verzekeringen', 'Abonnementen', 'Vervoer', 'Overige vaste lasten'
    ];
    sh.getRange(2, 1, standaard.length, 3).setValues(standaard.map(function (n) { return [n, 0, '']; }));
  }

  var rijen = sh.getMaxRows();
  stijl_(sh.getRange(1, 1, rijen, 5), { font: KB.LETTER, kleur: K.inkt, grootte: 10, vuitlijn: 'middle' });
  koprij_(sh.getRange('A1:C1'));
  sh.getRange(2, 2, rijen - 1, 1).setNumberFormat(KB.FMT.EURO);
  sh.getRange(1, 1, rijen, 3).applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, true, false)
    .setHeaderRowColor(K.inkt).setFirstRowColor(K.kaart).setSecondRowColor(K.kaart2);
  sh.setFrozenRows(1);
  sh.setRowHeight(1, 30);
  [260, 150, 280, 24, 260].forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
  sh.setTabColor(KB.CATEGORIEEN[0].kleur);

  stijl_(sh.getRange('E1').setValue('Totaal per maand'), { bg: K.inkt, kleur: K.wit, vet: true });
  stijl_(sh.getRange('E2').setFormula('=SUM(B2:B)'), { bg: K.kaart, vet: true, grootte: 16, fmt: KB.FMT.EURO });
  sh.setRowHeight(2, 34);
  rand_(sh.getRange('E1:E2'), K.lijn);
  stijl_(sh.getRange('E4:E9').merge().setValue(
    'Zet hier alle vaste lasten per maand. Het totaal telt automatisch mee in de lopende maand ' +
    '(tabblad Maanden) en dus in jullie budget. Afgelopen maanden blijven bewaard zoals ze waren.\n\n' +
    'Iets dat één keer per jaar betaald wordt? Deel het bedrag door 12.'),
    { kleur: K.inkt2, wrap: true, vuitlijn: 'top', bg: K.kaart });
  rand_(sh.getRange('E4:E9'), K.lijn);
  return sh;
}

/* ---------- Uitgaven ---------- */

function bouwUitgaven_(ss) {
  var sh = ss.getSheetByName(KB.BLAD.UITGAVEN);
  var K = KB.KLEUR;
  maatInvoerBlad_(sh, 1000, UITG.KOLOMMEN);
  var rijen = sh.getMaxRows();

  var filter = sh.getFilter();
  if (filter) filter.remove();
  sh.getBandings().forEach(function (b) { b.remove(); });

  sh.getRange(1, 1, 1, UITG.KOLOMMEN).setValues([['Datum', 'Wie', 'Categorie', 'Omschrijving', 'Bedrag', 'Toegevoegd']]);
  stijl_(sh.getRange(1, 1, rijen, UITG.KOLOMMEN), { font: KB.LETTER, kleur: K.inkt, grootte: 10, vuitlijn: 'middle' });
  koprij_(sh.getRange(1, 1, 1, UITG.KOLOMMEN));
  sh.getRange('E1').setHorizontalAlignment('right');
  sh.getRange(1, 1).setNote('Datum van de uitgave.');
  sh.getRange(1, 2).setNote('Wie betaalde? Kies uit de namen op het tabblad Instellingen.');
  sh.getRange(1, 3).setNote(KB.CATEGORIEEN.map(function (c) { return c.naam + ': ' + c.uitleg; }).join('\n'));
  sh.getRange(1, 6).setNote('Wordt automatisch ingevuld door de app.');

  stijlUitgavenRijen_(sh, 2, rijen - 1);

  sh.getRange(1, 1, rijen, UITG.KOLOMMEN).applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, true, false)
    .setHeaderRowColor(K.inkt).setFirstRowColor(K.kaart).setSecondRowColor(K.kaart2);

  var regels = KB.CATEGORIEEN.map(function (c) {
    return SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo(c.naam)
      .setBackground(c.tint)
      .setRanges([sh.getRange(2, UITG.CAT, rijen - 1, 1)])
      .build();
  });
  sh.setConditionalFormatRules(regels);

  sh.getRange(1, 1, rijen, UITG.KOLOMMEN).createFilter();
  sh.setFrozenRows(1);
  sh.setRowHeight(1, 32);
  [118, 90, 120, 340, 110, 140].forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
  sh.setTabColor(K.inkt);
  return sh;
}

function stijlUitgavenRijen_(sh, start, aantal) {
  var K = KB.KLEUR;
  var namen = namenBereik_(sh);
  sh.getRange(start, UITG.DATUM, aantal, 1).setNumberFormat(KB.FMT.DATUM)
    .setDataValidation(SpreadsheetApp.newDataValidation().requireDate().setAllowInvalid(false)
      .setHelpText('Vul een datum in, bijvoorbeeld 21-10-2026.').build());
  sh.getRange(start, UITG.WIE, aantal, 1)
    .setDataValidation(SpreadsheetApp.newDataValidation().requireValueInRange(namen, true).setAllowInvalid(false)
      .setHelpText('Kies wie de uitgave deed.').build());
  sh.getRange(start, UITG.CAT, aantal, 1)
    .setDataValidation(SpreadsheetApp.newDataValidation()
      .requireValueInList(KB.CATEGORIEEN.map(function (c) { return c.naam; }), true).setAllowInvalid(false)
      .setHelpText('Overleven, Optioneel, Cultuur of Extra.').build());
  sh.getRange(start, UITG.BEDRAG, aantal, 1).setNumberFormat(KB.FMT.EURO);
  stijl_(sh.getRange(start, UITG.TOEGEVOEGD, aantal, 1), { fmt: KB.FMT.TIJD, kleur: K.inkt3, grootte: 9 });
}

function namenBereik_(sh) {
  return sh.getParent().getSheetByName(KB.BLAD.INST).getRange(KB.CEL.NAAM1 + ':' + KB.CEL.NAAM2);
}

/* ---------- Maanden ---------- */

function bouwMaanden_(ss) {
  var sh = ss.getSheetByName(KB.BLAD.MAANDEN);
  var K = KB.KLEUR;
  maatInvoerBlad_(sh, 200, MND.KOLOMMEN);
  var rijen = sh.getMaxRows();
  sh.getBandings().forEach(function (b) { b.remove(); });
  verwijderBescherming_(sh);

  sh.getRange(1, 1, 1, MND.KOLOMMEN).setValues([[
    'Maand', '', '', 'Overig inkomen', 'Totaal inkomen', 'Vaste lasten', 'Spaardoel', 'Budget',
    'Uitgegeven', 'Nog over', 'Gespaard', 'Spaardoel gehaald?', 'Wat ging goed?', 'Wat kan beter?', 'Voornemen volgende maand'
  ]]);
  sh.getRange(1, MND.INK1).setFormula('="Inkomen "&Instellingen!$' + KB.CEL.NAAM1.charAt(0) + '$' + KB.CEL.NAAM1.slice(1));
  sh.getRange(1, MND.INK2).setFormula('="Inkomen "&Instellingen!$' + KB.CEL.NAAM2.charAt(0) + '$' + KB.CEL.NAAM2.slice(1));

  stijl_(sh.getRange(1, 1, rijen, MND.KOLOMMEN), { font: KB.LETTER, kleur: K.inkt, grootte: 10, vuitlijn: 'middle' });
  koprij_(sh.getRange(1, 1, 1, MND.KOLOMMEN)).setWrap(true);
  sh.getRange(1, MND.INK1, 1, MND.GEHAALD - 1).setHorizontalAlignment('right');
  sh.getRange(1, MND.GEHAALD).setHorizontalAlignment('center');
  sh.getRange(1, MND.TOTAAL).setNote('Berekend: som van de inkomens.');
  sh.getRange(1, MND.VAST).setNote('Lopende en komende maanden volgen automatisch het totaal van het tabblad Vaste lasten. Afgelopen maanden worden vastgezet. Je mag hier ook zelf een bedrag typen.');
  sh.getRange(1, MND.BUDGET).setNote('Berekend: inkomen − vaste lasten − spaardoel. Dit mag je uitgeven.');
  sh.getRange(1, MND.UITGEGEVEN).setNote('Berekend uit het tabblad Uitgaven.');
  sh.getRange(1, MND.GESPAARD).setNote('Berekend: inkomen − vaste lasten − uitgegeven.');

  // Bestaande maanden: formules herstellen, gegevens laten staan.
  var tz = tz_(ss);
  var huidig = vandaag_(ss).slice(0, 7);
  var n = sh.getLastRow() - 1;
  if (n > 0) {
    var a = sh.getRange(2, 1, n, 1).getValues();
    var f = sh.getRange(2, MND.VAST, n, 1).getFormulas();
    var v = sh.getRange(2, MND.VAST, n, 1).getValues();
    for (var i = 0; i < n; i++) {
      var iso = naarIso_(a[i][0], tz);
      if (!iso) continue;
      var r = i + 2;
      zetMaandFormules_(sh, r);
      if (!f[i][0] && v[i][0] === '') {
        if (iso.slice(0, 7) >= huidig) sh.getRange(r, MND.VAST).setFormula(VAST_FORMULE);
        else sh.getRange(r, MND.VAST).setValue(0);
      }
    }
  }

  stijlMaandRijen_(sh, 2, rijen - 1);
  sh.getRange(1, 1, rijen, MND.KOLOMMEN).applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, true, false)
    .setHeaderRowColor(K.inkt).setFirstRowColor(K.kaart).setSecondRowColor(K.kaart2);

  [MND.TOTAAL, MND.BUDGET, MND.UITGEGEVEN, MND.OVER, MND.GESPAARD, MND.GEHAALD].forEach(function (k) {
    sh.getRange(2, k, rijen - 1, 1).setBackground(K.berekend);
  });
  beschermWaarschuwing_(sh.getRange(2, MND.TOTAAL, rijen - 1, 1), 'berekend');
  beschermWaarschuwing_(sh.getRange(2, MND.BUDGET, rijen - 1, 5), 'berekend');

  var j = sh.getRange(2, MND.OVER, rijen - 1, 1);
  var l = sh.getRange(2, MND.GEHAALD, rijen - 1, 1);
  sh.setConditionalFormatRules([
    SpreadsheetApp.newConditionalFormatRule().whenNumberLessThan(0).setFontColor(K.kritiek).setBold(true).setRanges([j]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextStartsWith('✗').setFontColor(K.kritiek).setRanges([l]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextStartsWith('⚠').setFontColor(K.waarschuwing).setRanges([l]).build()
  ]);

  sh.setFrozenRows(1);
  sh.setFrozenColumns(1);
  sh.setRowHeight(1, 40);
  sh.setColumnWidth(1, 130);
  for (var k = MND.INK1; k <= MND.GESPAARD; k++) sh.setColumnWidth(k, 112);
  sh.setColumnWidth(MND.GEHAALD, 130);
  sh.setColumnWidths(MND.GOED, 3, 260);
  sh.setTabColor(KB.CATEGORIEEN[2].kleur);
  return sh;
}

function stijlMaandRijen_(sh, start, aantal) {
  var K = KB.KLEUR;
  sh.getRange(start, MND.MAAND, aantal, 1).setNumberFormat(KB.FMT.MAAND).setFontWeight('bold')
    .setDataValidation(SpreadsheetApp.newDataValidation().requireDate().setAllowInvalid(false)
      .setHelpText('De eerste dag van de maand, bijvoorbeeld 1-11-2026.').build());
  sh.getRange(start, MND.INK1, aantal, MND.GESPAARD - 1).setNumberFormat(KB.FMT.EURO);
  sh.getRange(start, MND.GEHAALD, aantal, 1).setHorizontalAlignment('center');
  stijl_(sh.getRange(start, MND.GOED, aantal, 3), { wrap: true, vuitlijn: 'top', kleur: K.inkt });
}

/* ---------- Hulp (verborgen) ---------- */

function bouwHulp_(ss) {
  var sh = ss.getSheetByName(KB.BLAD.HULP);
  sh.clear();
  maatBlad_(sh, 220, 12);
  sh.getRange('A1:B1').setValues([['Maandkeuze', 'Datum']]);
  sh.getRange('A2').setValue('Deze maand');
  sh.getRange('A3').setFormula('=IFERROR(ARRAYFORMULA(TEXT(SORT(FILTER(Maanden!$A$2:$A,Maanden!$A$2:$A<>""),1,FALSE),"mmmm yyyy")),"")');
  sh.getRange('B3').setFormula('=IFERROR(SORT(FILTER(Maanden!$A$2:$A,Maanden!$A$2:$A<>""),1,FALSE),"")');
  sh.getRange('B3:B220').setNumberFormat(KB.FMT.ISO);

  sh.getRange('D1').setValue('Gekozen maand · volgende maand · maandag van week 1');
  var vandaagMaand = 'EOMONTH(TODAY(),-1)+1';
  sh.getRange('D2').setFormula('=IF(OR(Overzicht!$I$2="",Overzicht!$I$2="Deze maand"),' + vandaagMaand +
    ',IFERROR(EOMONTH(INDEX($B$3:$B,MATCH(Overzicht!$I$2,$A$3:$A,0)),-1)+1,' + vandaagMaand + '))');
  sh.getRange('D3').setFormula('=EDATE(D2,1)');
  sh.getRange('D4').setFormula('=D2-WEEKDAY(D2,3)');
  sh.getRange('D2:D4').setNumberFormat(KB.FMT.ISO);

  sh.getRange('F1').setValue('Kakebo-tips');
  sh.getRange(2, 6, TIPS.length, 1).setValues(TIPS.map(function (t) { return [t]; }));

  sh.getRange('H1:L1').setValues([['Week'].concat(KB.CATEGORIEEN.map(function (c) { return c.naam; }))]);
  sh.getRange('H2').setFormula('=IFERROR(FILTER({Overzicht!$B$30:$B$35,Overzicht!$E$30:$E$35,Overzicht!$F$30:$F$35,' +
    'Overzicht!$H$30:$H$35,Overzicht!$I$30:$I$35},Overzicht!$B$30:$B$35<>""),"")');
  return sh;
}

/* ---------- Overzicht (dashboard) ---------- */

function bouwOverzicht_(ss) {
  var sh = ss.getSheetByName(KB.BLAD.OVERZICHT);
  var hulp = ss.getSheetByName(KB.BLAD.HULP);
  var K = KB.KLEUR;
  var EURO = KB.FMT.EURO;
  var N1 = 'Instellingen!$' + KB.CEL.NAAM1.charAt(0) + '$' + KB.CEL.NAAM1.slice(1);
  var N2 = 'Instellingen!$' + KB.CEL.NAAM2.charAt(0) + '$' + KB.CEL.NAAM2.slice(1);
  var M0 = 'Hulp!$D$2';
  var M1 = 'Hulp!$D$3';
  var W0 = 'Hulp!$D$4';
  var somMaanden = function (k) {
    return '=SUMIFS(Maanden!$' + k + '$2:$' + k + ',Maanden!$A$2:$A,">="&' + M0 + ',Maanden!$A$2:$A,"<"&' + M1 + ')';
  };
  var somUitgaven = function (extra) {
    return 'SUMIFS(Uitgaven!$E$2:$E,Uitgaven!$A$2:$A,">="&' + M0 + ',Uitgaven!$A$2:$A,"<"&' + M1 + (extra || '') + ')';
  };

  // Leegmaken
  sh.getCharts().forEach(function (c) { sh.removeChart(c); });
  verwijderBescherming_(sh);
  var alles = sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns());
  alles.breakApart();
  alles.clear();
  alles.clearDataValidations();
  alles.clearNote();
  sh.clearConditionalFormatRules();
  maatBlad_(sh, 46, 13);
  sh.setHiddenGridlines(true);
  sh.setTabColor(K.hanko);

  stijl_(sh.getRange(1, 1, 46, 13), { bg: K.papier, font: KB.LETTER, kleur: K.inkt, grootte: 10, vuitlijn: 'middle' });
  [20, 122, 112, 16, 122, 112, 16, 122, 112, 16, 122, 112, 20].forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
  var hoogtes = {
    1: 14, 2: 46, 3: 22, 4: 12, 5: 28, 6: 40, 7: 22, 8: 22, 9: 22, 10: 10, 11: 16, 12: 22, 13: 26, 14: 18,
    15: 28, 16: 22, 17: 30, 18: 30, 19: 30, 20: 30, 21: 26, 22: 18, 23: 28, 24: 22, 25: 30, 26: 30, 27: 18,
    28: 28, 29: 24, 36: 26, 37: 18, 38: 28, 39: 46, 40: 46, 41: 46, 42: 22, 43: 12, 44: 24, 45: 22, 46: 14
  };
  for (var r = 1; r <= 46; r++) sh.setRowHeight(r, hoogtes[r] || 26);

  // Kop met maandkeuze
  sh.getRange('B2:G2').merge().setRichTextValue(titelTekst_('家計簿  Kakebo', 24));
  stijl_(sh.getRange('B3:G3').merge().setFormula('="Het huishoudboekje van "&' + N1 + '&" & "&' + N2), { kleur: K.inkt2 });
  stijl_(sh.getRange('H2').setValue('Maand'), { kleur: K.inkt3, uitlijn: 'right' });
  var keuze = sh.getRange('I2:L2').merge();
  keuze.setValue('Deze maand');
  stijl_(keuze, { bg: K.kaart, vet: true, grootte: 12, uitlijn: 'center' });
  rand_(keuze, K.inkt);
  keuze.setDataValidation(SpreadsheetApp.newDataValidation().requireValueInRange(hulp.getRange('A2:A200'), true)
    .setAllowInvalid(false).setHelpText('Kies een maand.').build());
  stijl_(sh.getRange('I3:L3').merge().setFormula('=' + M0), { kleur: K.inkt2, fmt: KB.FMT.MAAND, uitlijn: 'center' });

  // De vier kaarten
  var kaarten = [
    {
      kol: 2, kop: '① Hoeveel hebben we?', groot: somMaanden('E'),
      regels: [['=' + N1, somMaanden('B')], ['=' + N2, somMaanden('C')], ['Overig', somMaanden('D')]]
    },
    {
      kol: 5, kop: '② Hoeveel sparen we?', groot: somMaanden('G'),
      regels: [['Vaste lasten', somMaanden('F')], ['Budget', somMaanden('H')],
        ['Per week', '=IFERROR(F8/(DAY(EOMONTH(' + M0 + ',0))/7),0)']]
    },
    {
      kol: 8, kop: '③ Hoeveel geven we uit?', groot: '=' + somUitgaven(),
      regels: [['Nog te besteden', '=F8-H6'],
        ['Per dag nog', '=IF(AND(TODAY()>=' + M0 + ',TODAY()<' + M1 + '),MAX(0,I7)/(' + M1 + '-TODAY()),"—")'],
        ['Aantal uitgaven', '=COUNTIFS(Uitgaven!$A$2:$A,">="&' + M0 + ',Uitgaven!$A$2:$A,"<"&' + M1 + ')']]
    },
    {
      kol: 11, kop: 'Resultaat: gespaard', groot: '=B6-F7-H6',
      regels: [['Spaardoel', '=E6'], ['Verschil', '=K6-E6'],
        ['Status', '=IF(B6=0,"—",IF(K6>=E6,IF(TODAY()>=' + M1 + ',"✓ gehaald","✓ op koers"),IF(TODAY()>=' + M1 + ',"✗ niet gehaald","⚠ let op")))']]
    }
  ];
  kaarten.forEach(function (k) {
    var c = k.kol;
    stijl_(sh.getRange(5, c, 6, 2), { bg: K.kaart });
    rand_(sh.getRange(5, c, 6, 2), K.lijn);
    stijl_(sh.getRange(5, c, 1, 2).merge().setValue(k.kop), { kleur: K.inkt2, vet: true, grootte: 10 });
    stijl_(sh.getRange(6, c, 1, 2).merge().setFormula(k.groot), { vet: true, grootte: 18, fmt: EURO, uitlijn: 'left' });
    k.regels.forEach(function (regel, i) {
      var rij = 7 + i;
      var label = sh.getRange(rij, c);
      if (regel[0].charAt(0) === '=') label.setFormula(regel[0]); else label.setValue(regel[0]);
      stijl_(label, { kleur: K.inkt2 });
      stijl_(sh.getRange(rij, c + 1).setFormula(regel[1]), { uitlijn: 'right', fmt: EURO });
    });
  });
  sh.getRange('I9').setNumberFormat('0');

  // Voortgang van het budget
  stijl_(sh.getRange('B12:H12').merge().setFormula(
    '=IF(F8<=0,"Budget gebruikt · vul eerst inkomen en spaardoel in (tabblad Maanden of de app)",' +
    'IF(H6>F8,"⚠ Over budget",IF(H6/F8>=0.9,"⚠ Budget bijna op","Budget gebruikt")))'), { kleur: K.inkt2, vet: true });
  stijl_(sh.getRange('K12:L12').merge().setFormula('=IF(F8<=0,"",H6/F8)'), { fmt: KB.FMT.PCT, uitlijn: 'right', vet: true });
  sh.getRange('B13:L13').merge().setFormula(
    '=IF(F8<=0,SPARKLINE({0,1},{"charttype","bar";"max",1;"color1","' + K.inkt + '";"color2","' + K.spoor + '"}),' +
    'IF(H6>F8,SPARKLINE(1,{"charttype","bar";"max",1;"color1","' + K.kritiek + '"}),' +
    'SPARKLINE({H6,F8-H6},{"charttype","bar";"max",F8;"color1",IF(H6/F8>=0.9,"' + K.waarschuwing + '","' + K.inkt + '");"color2","' + K.spoor + '"})))');

  // Per categorie
  stijl_(sh.getRange(15, 2, 7, 5), { bg: K.kaart });
  rand_(sh.getRange(15, 2, 7, 5), K.lijn);
  stijl_(sh.getRange('B15:F15').merge().setValue('Per categorie'), { vet: true, grootte: 12 });
  sh.getRange('B16:F16').setValues([['Categorie', 'Uitgegeven', '', 'Aandeel', '']]);
  stijl_(sh.getRange('B16:F16'), { kleur: K.inkt3, grootte: 9 });
  sh.getRange('C16').setHorizontalAlignment('right');
  sh.getRange('E16').setHorizontalAlignment('right');
  KB.CATEGORIEEN.forEach(function (c, i) {
    var rij = 17 + i;
    stijl_(sh.getRange(rij, 2).setValue(c.naam), { vet: true });
    sh.getRange(rij, 2).setBorder(null, true, null, null, null, null, c.kleur, SpreadsheetApp.BorderStyle.SOLID_THICK);
    sh.getRange(rij, 2).setNote(c.uitleg);
    stijl_(sh.getRange(rij, 3).setFormula('=' + somUitgaven(',Uitgaven!$C$2:$C,$B' + rij)), { uitlijn: 'right', fmt: EURO });
    stijl_(sh.getRange(rij, 5).setFormula('=IF($C$21=0,"",C' + rij + '/$C$21)'), { uitlijn: 'right', fmt: KB.FMT.PCT, kleur: K.inkt2 });
    sh.getRange(rij, 6).setFormula('=SPARKLINE(C' + rij + ',{"charttype","bar";"max",MAX(1,MAX($C$17:$C$20));"color1","' + c.kleur + '"})');
  });
  stijl_(sh.getRange('B21').setValue('Totaal'), { vet: true });
  stijl_(sh.getRange('C21').setFormula('=SUM(C17:C20)'), { vet: true, uitlijn: 'right', fmt: EURO });
  sh.getRange('B21:F21').setBorder(true, null, null, null, null, null, K.lijn, SpreadsheetApp.BorderStyle.SOLID);

  // Wie gaf wat uit?
  stijl_(sh.getRange(23, 2, 4, 5), { bg: K.kaart });
  rand_(sh.getRange(23, 2, 4, 5), K.lijn);
  stijl_(sh.getRange('B23:F23').merge().setValue('Wie gaf wat uit?'), { vet: true, grootte: 12 });
  sh.getRange('B24:F24').setValues([['Wie', 'Uitgegeven', '', 'Aandeel', '']]);
  stijl_(sh.getRange('B24:F24'), { kleur: K.inkt3, grootte: 9 });
  sh.getRange('C24').setHorizontalAlignment('right');
  sh.getRange('E24').setHorizontalAlignment('right');
  [N1, N2].forEach(function (naamRef, i) {
    var rij = 25 + i;
    stijl_(sh.getRange(rij, 2).setFormula('=' + naamRef), { vet: true });
    stijl_(sh.getRange(rij, 3).setFormula('=' + somUitgaven(',Uitgaven!$B$2:$B,$B' + rij)), { uitlijn: 'right', fmt: EURO });
    stijl_(sh.getRange(rij, 5).setFormula('=IF(SUM($C$25:$C$26)=0,"",C' + rij + '/SUM($C$25:$C$26))'), { uitlijn: 'right', fmt: KB.FMT.PCT, kleur: K.inkt2 });
    sh.getRange(rij, 6).setFormula('=SPARKLINE(C' + rij + ',{"charttype","bar";"max",MAX(1,MAX($C$25:$C$26));"color1","' + K.inkt2 + '"})');
  });

  // Per week
  stijl_(sh.getRange(28, 2, 9, 11), { bg: K.kaart });
  rand_(sh.getRange(28, 2, 9, 11), K.lijn);
  stijl_(sh.getRange('B28:L28').merge().setValue('Per week (maandag t/m zondag)'), { vet: true, grootte: 12 });
  sh.getRange('B29:L29').setValues([['Week', 'Dagen', '', 'Overleven', 'Optioneel', '', 'Cultuur', 'Extra', '', 'Totaal', '']]);
  stijl_(sh.getRange('B29:L29'), { kleur: K.inkt3, grootte: 9 });
  var catKolommen = { Overleven: 5, Optioneel: 6, Cultuur: 8, Extra: 9 };
  KB.CATEGORIEEN.forEach(function (c) {
    var cel = sh.getRange(29, catKolommen[c.naam]);
    cel.setHorizontalAlignment('right');
    cel.setBorder(null, null, true, null, null, null, c.kleur, SpreadsheetApp.BorderStyle.SOLID_THICK);
  });
  sh.getRange('K29').setHorizontalAlignment('right');
  for (var w = 1; w <= 6; w++) {
    var rij = 29 + w;
    var van = 'MAX(' + M0 + ',' + W0 + '+' + (7 * (w - 1)) + ')';
    var totEx = 'MIN(' + M1 + ',' + W0 + '+' + (7 * w) + ')';
    sh.getRange(rij, 2).setFormula('=IF(' + W0 + '+' + (7 * (w - 1)) + '>=' + M1 + ',"","Week ' + w + '")');
    sh.getRange(rij, 3).setFormula('=IF($B' + rij + '="","",DAY(' + van + ')&"–"&DAY(' + totEx + '-1))');
    KB.CATEGORIEEN.forEach(function (c) {
      var k = catKolommen[c.naam];
      var kolomLetter = String.fromCharCode(64 + k);
      sh.getRange(rij, k).setFormula('=IF($B' + rij + '="","",SUMIFS(Uitgaven!$E$2:$E,Uitgaven!$C$2:$C,' + kolomLetter + '$29,' +
        'Uitgaven!$A$2:$A,">="&' + van + ',Uitgaven!$A$2:$A,"<"&' + totEx + '))');
    });
    sh.getRange(rij, 11).setFormula('=IF($B' + rij + '="","",SUM(E' + rij + ',F' + rij + ',H' + rij + ',I' + rij + '))');
    sh.getRange(rij, 12).setFormula('=IF($B' + rij + '="","",SPARKLINE(K' + rij + ',{"charttype","bar";"max",MAX(1,MAX($K$30:$K$35));"color1","' + K.inkt2 + '"}))');
  }
  stijl_(sh.getRange('B30:B35'), { vet: true });
  stijl_(sh.getRange('C30:C35'), { kleur: K.inkt2 });
  stijl_(sh.getRange('E30:K36'), { uitlijn: 'right', fmt: EURO });
  stijl_(sh.getRange('K30:K36'), { vet: true });
  stijl_(sh.getRange('B36').setValue('Totaal'), { vet: true });
  ['E', 'F', 'H', 'I', 'K'].forEach(function (k) {
    stijl_(sh.getRange(k + '36').setFormula('=SUM(' + k + '30:' + k + '35)'), { vet: true });
  });
  sh.getRange('B36:L36').setBorder(true, null, null, null, null, null, K.lijn, SpreadsheetApp.BorderStyle.SOLID);

  // Reflectie
  stijl_(sh.getRange(38, 2, 4, 11), { bg: K.kaart });
  rand_(sh.getRange(38, 2, 4, 11), K.lijn);
  stijl_(sh.getRange('B38:L38').merge().setValue('④ Hoe kunnen we het beter doen?'), { vet: true, grootte: 12 });
  [['Wat ging goed?', 'M'], ['Wat kan beter?', 'N'], ['Voornemen', 'O']].forEach(function (v, i) {
    var rij = 39 + i;
    stijl_(sh.getRange(rij, 2).setValue(v[0]), { kleur: K.inkt2, vuitlijn: 'top', vet: true });
    stijl_(sh.getRange(rij, 3, 1, 10).merge().setFormula('=IFERROR(INDEX(FILTER(Maanden!$' + v[1] + '$2:$' + v[1] +
      ',Maanden!$A$2:$A>=' + M0 + ',Maanden!$A$2:$A<' + M1 + ',Maanden!$' + v[1] + '$2:$' + v[1] + '<>""),1),"—")'),
      { wrap: true, vuitlijn: 'top' });
  });
  stijl_(sh.getRange('B42:L42').merge().setValue('Invullen kan in de app (scherm Maand) of op het tabblad Maanden.'),
    { kleur: K.inkt3, cursief: true, grootte: 9 });

  // Tip en uitleg
  stijl_(sh.getRange('B44:L44').merge().setFormula('="💡 Kakebo-tip: "&INDEX(Hulp!$F$2:$F$' + (TIPS.length + 1) + ',MOD(DAY(TODAY())-1,' + TIPS.length + ')+1)'),
    { kleur: K.inkt2, cursief: true });
  stijl_(sh.getRange('B45:L45').merge().setValue('Uitgave toevoegen? Menu 家計簿 Kakebo › Uitgave toevoegen, of gebruik de app op je telefoon.'),
    { kleur: K.inkt3, grootte: 9 });

  // Opvallende waarden
  sh.setConditionalFormatRules([
    SpreadsheetApp.newConditionalFormatRule().whenNumberLessThan(0).setFontColor(K.kritiek)
      .setRanges([sh.getRange('I7'), sh.getRange('L8'), sh.getRange('K6')]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextStartsWith('✗').setFontColor(K.kritiek).setRanges([sh.getRange('L9')]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextStartsWith('⚠').setFontColor(K.waarschuwing)
      .setRanges([sh.getRange('L9'), sh.getRange('B12')]).build()
  ]);

  // Grafiek: uitgaven per week per categorie
  var grafiek = sh.newChart()
    .asColumnChart()
    .setStacked()
    .setColors(KB.CATEGORIEEN.map(function (c) { return c.kleur; }))
    .addRange(hulp.getRange('H1:L7'))
    .setNumHeaders(1)
    .setPosition(15, 8, 0, 0)
    .setOption('title', 'Uitgaven per week')
    .setOption('titleTextStyle', { color: K.inkt, fontSize: 13, bold: true })
    .setOption('fontName', KB.LETTER)
    .setOption('legend', { position: 'bottom', textStyle: { color: K.inkt2, fontSize: 10 } })
    .setOption('backgroundColor', K.kaart)
    .setOption('bar', { groupWidth: '45%' })
    .setOption('vAxis', { minValue: 0, gridlines: { color: K.lijn }, textStyle: { color: K.inkt3, fontSize: 9 } })
    .setOption('hAxis', { textStyle: { color: K.inkt2, fontSize: 10 } })
    .setOption('width', 484)
    .setOption('height', 320)
    .build();
  sh.insertChart(grafiek);

  beschermWaarschuwing_(sh.getRange('B5:L46'), 'dashboard');
  return sh;
}

/* ============================================================
 *  KLEINE HTML-PAGINA'S
 * ============================================================ */

function telefoonHtml_(url) {
  var e = function (s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); };
  var stijl = '<style>' +
    'body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#26231f;background:#fffdf9;margin:0;padding:8px 4px;line-height:1.5}' +
    'h2{font-size:18px;margin:0 0 4px}p{margin:6px 0;color:#5f5950;font-size:14px}' +
    '#qr{display:flex;justify-content:center;margin:14px 0}#qr img,#qr svg{width:220px;height:220px;border:8px solid #fff;border-radius:12px;box-shadow:0 0 0 1px #e6dfd2}' +
    '.link{font-size:12px;word-break:break-all;background:#f6f1e8;border-radius:10px;padding:10px;color:#26231f}' +
    'button{font:inherit;font-weight:700;background:#26231f;color:#fffdf9;border:0;border-radius:12px;padding:10px 16px;margin-top:10px;cursor:pointer}' +
    'ol{padding-left:20px;color:#5f5950;font-size:14px}li{margin:6px 0}' +
    '</style>';
  if (!url) {
    return stijl +
      '<h2>Nog geen web-app</h2>' +
      '<p>Publiceer eerst de web-app (eenmalig):</p><ol>' +
      '<li>Kies <b>Extensies › Apps Script</b>.</li>' +
      '<li>Klik rechtsboven op <b>Implementeren › Nieuwe implementatie</b>.</li>' +
      '<li>Kies bij het tandwiel <b>Web-app</b>.</li>' +
      '<li>Uitvoeren als: <b>Gebruiker die de web-app opent</b>.</li>' +
      '<li>Wie heeft toegang: <b>Iedereen met een Google-account</b>.</li>' +
      '<li>Klik <b>Implementeren</b>, open de link één keer en kies dan opnieuw dit menu.</li></ol>';
  }
  return stijl +
    '<h2>Scan met je telefoon</h2>' +
    '<p>Open de camera en richt hem op de code. Kies daarna in de browser <b>Zet op beginscherm</b>.</p>' +
    '<div id="qr"></div>' +
    '<div class="link" id="link">' + e(url) + '</div>' +
    '<button id="kopieer">Link kopiëren</button>' +
    '<p style="font-size:12px">Deel de link ook met de anderen. Iedereen die de sheet mag bewerken, kan de app gebruiken.</p>' +
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script>' +
    '<script>' +
    'var url=' + veiligJson_(url) + ';' +
    'try{var q=qrcode(0,"M");q.addData(url);q.make();document.getElementById("qr").innerHTML=q.createSvgTag(6,2);}catch(e){}' +
    'document.getElementById("kopieer").onclick=function(){var b=this;' +
    'if(navigator.clipboard){navigator.clipboard.writeText(url).then(function(){b.textContent="Gekopieerd ✓";},function(){kies();});}else{kies();}' +
    'function kies(){var r=document.createRange();r.selectNodeContents(document.getElementById("link"));var s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent="Kopieer met Ctrl+C";}};' +
    '</script>';
}

function foutPagina_(bericht) {
  var e = String(bericht).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  return '<div style="font-family:system-ui,-apple-system,sans-serif;max-width:420px;margin:48px auto;padding:24px;' +
    'background:#fffdf9;border-radius:18px;color:#26231f;box-shadow:0 0 0 1px #e6dfd2">' +
    '<div style="width:44px;height:44px;border-radius:10px;background:#c8553d;color:#fff;display:flex;align-items:center;' +
    'justify-content:center;font-weight:800;font-size:20px">家</div>' +
    '<h2 style="margin:16px 0 8px">Er ging iets mis</h2>' +
    '<p style="color:#5f5950;line-height:1.5">' + e + '</p>' +
    '<p style="color:#5f5950;line-height:1.5">Werkt het niet? Controleer of de sheet met je gedeeld is als <b>bewerker</b> ' +
    'en of je met het juiste Google-account bent ingelogd.</p></div>';
}

/* ============================================================
 *  DE APP (HTML) — automatisch gegenereerd uit src/app.html
 *  Niet met de hand aanpassen.
 * ============================================================ */

var KB_APP_HTML = `<!DOCTYPE html>
<html lang="nl">
<head>
<base target="_top">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Kakebo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@800&text=%E5%AE%B6%E8%A8%88%E7%B0%BF&display=swap">
<style>
:root {
  color-scheme: light;
  --papier: #f6f1e8;
  --kaart: #fffdf9;
  --kaart-2: #f8f2e8;
  --inkt: #26231f;
  --inkt-2: #5f5950;
  --inkt-3: #6c655a;
  --lijn: #e6dfd2;
  --lijn-2: #d3c9b8;
  --spoor: #ebe4d8;
  --hanko: #c8553d;
  --hanko-zacht: #f7e4dd;
  --knop: #26231f;
  --knop-tekst: #fffdf9;
  --waarschuwing: #8f6000;
  --waarschuwing-vlak: #e0a020;
  --kritiek: #c93a35;
  --kritiek-zacht: #fbe7e4;
  --c-overleven: #339e7c;
  --c-optioneel: #d86105;
  --c-cultuur: #3f6fcf;
  --c-extra: #b54696;
  --schaduw: 0 1px 1px rgba(70, 50, 30, .04), 0 10px 26px -14px rgba(70, 50, 30, .22);
  --korrel: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='k'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .42 0 0 0 0 .34 0 0 0 0 .25 0 0 0 .07 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23k)'/%3E%3C/svg%3E");
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --papier: #171614;
    --kaart: #24221e;
    --kaart-2: #2b2824;
    --inkt: #f1ebe0;
    --inkt-2: #c9c1b4;
    --inkt-3: #a69e91;
    --lijn: #38342e;
    --lijn-2: #4b453d;
    --spoor: #3a362f;
    --hanko: #d9654c;
    --hanko-zacht: #3d2822;
    --knop: #f1ebe0;
    --knop-tekst: #1b1a17;
    --waarschuwing: #e8b04a;
    --waarschuwing-vlak: #e0a020;
    --kritiek: #ef6b62;
    --kritiek-zacht: #3e2522;
    --c-overleven: #37a17f;
    --c-optioneel: #db640e;
    --c-cultuur: #477ee8;
    --c-extra: #b84999;
    --schaduw: 0 1px 1px rgba(0, 0, 0, .2), 0 12px 28px -16px rgba(0, 0, 0, .6);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --papier: #171614;
  --kaart: #24221e;
  --kaart-2: #2b2824;
  --inkt: #f1ebe0;
  --inkt-2: #c9c1b4;
  --inkt-3: #a69e91;
  --lijn: #38342e;
  --lijn-2: #4b453d;
  --spoor: #3a362f;
  --hanko: #d9654c;
  --hanko-zacht: #3d2822;
  --knop: #f1ebe0;
  --knop-tekst: #1b1a17;
  --waarschuwing: #e8b04a;
  --waarschuwing-vlak: #e0a020;
  --kritiek: #ef6b62;
  --kritiek-zacht: #3e2522;
  --c-overleven: #37a17f;
  --c-optioneel: #db640e;
  --c-cultuur: #477ee8;
  --c-extra: #b84999;
  --schaduw: 0 1px 1px rgba(0, 0, 0, .2), 0 12px 28px -16px rgba(0, 0, 0, .6);
}

* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  min-height: 100vh;
  background-color: var(--papier);
  background-image: var(--korrel);
  color: var(--inkt);
  font: 15px/1.45 "Zen Maru Gothic", "Nunito", system-ui, -apple-system, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
  -webkit-tap-highlight-color: transparent;
}
body.vast { overflow: hidden; }
button, input, textarea { font: inherit; color: inherit; }
button { cursor: pointer; }
[hidden] { display: none !important; }
:focus-visible { outline: 2.5px solid var(--hanko); outline-offset: 2px; }
.i { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; flex: none; }
.verborgen { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* ---------- Kop ---------- */
.app {
  max-width: 520px; margin: 0 auto;
  padding-block: calc(14px + env(safe-area-inset-top, 0px)) calc(108px + env(safe-area-inset-bottom, 0px));
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
}
.kop { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.hanko {
  width: 46px; height: 46px; flex: none; border-radius: 11px; display: grid; place-items: center;
  background: var(--hanko); color: #fff; transform: rotate(-4deg);
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, .28), 0 6px 14px -6px rgba(200, 85, 61, .7);
}
.hanko span { white-space: nowrap; writing-mode: vertical-rl; font-family: "Shippori Mincho", "Noto Serif JP", "Hiragino Mincho ProN", serif; font-weight: 800; font-size: 12.5px; letter-spacing: 1px; line-height: 1; }
.kop-tekst { flex: 1; min-width: 0; }
.kop h1 { margin: 0; font-size: 22px; line-height: 1.15; letter-spacing: .2px; }
.kop p { margin: 0; color: var(--inkt-2); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rond {
  width: 40px; height: 40px; flex: none; border-radius: 50%; display: grid; place-items: center;
  border: 1px solid var(--lijn); background: var(--kaart); color: var(--inkt-2); padding: 0;
}
.rond .i { width: 20px; height: 20px; }
.rond.klein { width: 34px; height: 34px; }
.rond.draait .i { animation: draai .8s linear infinite; }
.ik-knop {
  display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 14px 0 10px; border-radius: 999px;
  border: 1px solid var(--lijn); background: var(--kaart); font-weight: 700; font-size: 14px; max-width: 140px;
}
.ik-knop span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ik-knop .i { width: 20px; height: 20px; color: var(--inkt-2); }

/* ---------- Algemeen ---------- */
.kaart { background: var(--kaart); border: 1px solid var(--lijn); border-radius: 20px; padding: 16px; margin-bottom: 14px; box-shadow: var(--schaduw); }
.kaart-kop { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.kaart-kop h3 { margin: 0; font-size: 16px; }
.kaart-sub { color: var(--inkt-2); font-size: 13px; font-weight: 700; }
.scherm-kop { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 12px; margin: 2px 2px 12px; }
.scherm-kop h2 { margin: 0; font-size: 20px; }
.chip-info { font-size: 12.5px; font-weight: 700; color: var(--inkt-2); background: var(--kaart); border: 1px solid var(--lijn); padding: 5px 10px; border-radius: 999px; white-space: nowrap; }
.chip-info[data-niveau="over"] { color: var(--kritiek); }
.label { display: block; font-size: 12.5px; color: var(--inkt-2); font-weight: 700; letter-spacing: .3px; }
.hint { color: var(--inkt-2); font-size: 12.5px; margin: 6px 0 0; }
.inhoud { transition: opacity .2s; }
.inhoud.laden { opacity: .5; pointer-events: none; }
.link-knop {
  border: 0; background: transparent; color: var(--inkt); font-weight: 700; font-size: 13.5px; padding: 8px 2px;
  display: inline-flex; align-items: center; gap: 6px;
}
.link-knop .i { width: 18px; height: 18px; }

/* ---------- Knoppen ---------- */
.knop {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 0; border-radius: 14px;
  padding: 14px 18px; font-weight: 700; font-size: 16px; transition: transform .12s, opacity .2s;
}
.knop:active { transform: scale(.98); }
.knop .i { width: 20px; height: 20px; }
.knop-primair { background: var(--knop); color: var(--knop-tekst); width: 100%; }
.knop-zacht { background: var(--kaart-2); color: var(--inkt); border: 1.5px solid var(--lijn); }
.knop-gevaar { background: var(--kritiek-zacht); color: var(--kritiek); }
.knop.bezig { pointer-events: none; opacity: .75; }
.knop.bezig::after { content: ""; width: 16px; height: 16px; border-radius: 50%; border: 2px solid currentColor; border-right-color: transparent; animation: draai .7s linear infinite; }
@keyframes draai { to { transform: rotate(360deg); } }
.knoppen {
  position: sticky; bottom: calc(70px + env(safe-area-inset-bottom)); z-index: 5; display: grid; gap: 6px;
  margin: 0 -4px; padding: 14px 4px 6px; background: linear-gradient(to bottom, transparent, var(--papier) 34%);
}

/* ---------- Invoer ---------- */
.invoer {
  width: 100%; border: 1.5px solid var(--lijn); background: var(--kaart-2); border-radius: 12px;
  padding: 11px 12px; font-size: 16px; outline: none; transition: border-color .15s, background-color .15s;
}
.invoer:focus { border-color: var(--inkt); background: var(--kaart); }
.invoer::placeholder, .geld-input input::placeholder { color: var(--inkt-3); opacity: .75; }
#omschrijving::-webkit-calendar-picker-indicator { display: none !important; }
.bedrag-kaart { padding: 14px 18px 18px; }
.bedrag-veld { display: flex; align-items: baseline; gap: 8px; border-bottom: 2px solid var(--lijn); padding-bottom: 4px; margin-top: 2px; transition: border-color .2s; }
.bedrag-veld:focus-within { border-color: var(--inkt); }
.bedrag-veld.fout { border-color: var(--kritiek); }
.bedrag-veld .euro { font-size: 28px; color: var(--inkt-2); font-weight: 500; }
.bedrag-veld input { flex: 1; min-width: 0; border: 0; outline: none; background: transparent; font-size: 44px; font-weight: 700; letter-spacing: -.5px; padding: 0; }
.bedrag-veld input::placeholder { color: var(--lijn-2); }
.cat-kies { border: 0; padding: 0; margin: 0 0 14px; min-width: 0; }
.cat-kies legend { padding: 0; margin: 0 0 8px 4px; }
.cat-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.cat-grid.schud { animation: schud .35s; }
@keyframes schud { 25% { transform: translateX(-6px); } 50% { transform: translateX(6px); } 75% { transform: translateX(-3px); } }
.cat {
  position: relative; text-align: left; display: grid; grid-template-columns: auto 1fr; column-gap: 10px; align-items: center;
  padding: 12px; min-height: 74px; border-radius: 16px; border: 1.5px solid var(--lijn); background: var(--kaart);
  transition: transform .12s, border-color .15s, background-color .15s;
}
.cat:active { transform: scale(.97); }
.cat-icoon {
  grid-row: span 2; width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center;
  background: color-mix(in srgb, var(--c) 14%, var(--kaart)); color: var(--c); transition: background-color .15s, color .15s;
}
.cat-naam { font-weight: 700; font-size: 15px; line-height: 1.2; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.cat-uitleg { font-size: 12px; color: var(--inkt-2); line-height: 1.25; }
.cat-vink { position: absolute; top: 8px; right: 8px; width: 18px; height: 18px; color: var(--c); opacity: 0; transform: scale(.6); transition: .15s; }
.cat[aria-checked="true"] { border-color: var(--c); background: color-mix(in srgb, var(--c) 8%, var(--kaart)); box-shadow: inset 0 0 0 1px var(--c); }
.cat[aria-checked="true"] .cat-icoon { background: var(--c); color: #fff; }
.cat[aria-checked="true"] .cat-vink { opacity: 1; transform: none; }
.velden { display: grid; gap: 14px; }
.veld { display: grid; gap: 6px; min-width: 0; }
.datum-rij { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.chips { display: flex; gap: 6px; }
.chip { border: 1.5px solid var(--lijn); background: var(--kaart); border-radius: 999px; padding: 8px 12px; font-size: 14px; font-weight: 500; }
.chip[aria-pressed="true"] { background: var(--inkt); color: var(--kaart); border-color: var(--inkt); }
.datum-rij input { flex: 1; min-width: 140px; width: auto; }
.segment { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 3px; padding: 3px; border-radius: 12px; border: 1.5px solid var(--lijn); background: var(--kaart-2); }
.segment button { border: 0; background: transparent; border-radius: 9px; padding: 9px 8px; font-weight: 700; color: var(--inkt-2); }
.segment button[aria-checked="true"] { background: var(--kaart); color: var(--inkt); box-shadow: 0 1px 3px rgba(0, 0, 0, .14); }
.voet-hint { text-align: center; color: var(--inkt-2); font-size: 13px; margin: 12px 0 0; }

/* ---------- Maandnavigatie ---------- */
.maand-nav { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 0 0 14px; }
.maand-titel { text-align: center; min-width: 0; }
.maand-titel h2 { margin: 0; font-size: 20px; line-height: 1.2; }
.maand-titel h2::first-letter { text-transform: uppercase; }
.maand-status { font-size: 12.5px; color: var(--inkt-2); }

/* ---------- Overzicht ---------- */
.held { padding: 18px; }
.held-label { font-size: 13px; color: var(--inkt-2); font-weight: 700; letter-spacing: .3px; }
.held-getal { font-size: clamp(40px, 13vw, 54px); font-weight: 700; letter-spacing: -1px; line-height: 1.05; margin: 2px 0 14px; }
.held-getal .centen { font-size: .48em; letter-spacing: 0; color: var(--inkt-2); }
.meter { height: 10px; border-radius: 999px; background: var(--spoor); overflow: hidden; }
.meter span { display: block; height: 100%; border-radius: 999px; background: var(--inkt); transition: width .6s cubic-bezier(.2, .8, .2, 1); }
.meter[data-niveau="let-op"] span { background: var(--waarschuwing-vlak); }
.meter[data-niveau="over"] span { background: var(--kritiek); }
.held-regel { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; font-size: 13px; color: var(--inkt-2); margin-top: 8px; }
.held-regel strong, .pill strong { color: var(--inkt); }
.status { display: flex; align-items: center; gap: 6px; font-size: 13.5px; font-weight: 700; margin: 12px 0 0; }
.status .i { width: 18px; height: 18px; }
.status[data-niveau="let-op"] { color: var(--waarschuwing); }
.status[data-niveau="over"] { color: var(--kritiek); }
.status[data-niveau="ok"] { color: var(--inkt-2); }
.pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.pill { font-size: 12.5px; background: var(--kaart-2); border: 1px solid var(--lijn); border-radius: 999px; padding: 4px 10px; color: var(--inkt-2); }
.leeg-held p { color: var(--inkt-2); margin: 6px 0 14px; }
.tegels { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
.tegel {
  text-align: left; display: grid; gap: 1px; align-content: start; padding: 12px 14px; border-radius: 16px;
  border: 1px solid var(--lijn); background: var(--kaart); box-shadow: var(--schaduw);
}
.tegel-label { font-size: 12.5px; color: var(--inkt-2); font-weight: 700; }
.tegel-waarde { font-size: 19px; font-weight: 700; }
.tegel-sub { font-size: 12px; color: var(--inkt-2); display: inline-flex; align-items: center; gap: 4px; }
.tegel-sub .i { width: 15px; height: 15px; }
.tegel-sub[data-niveau="over"] { color: var(--kritiek); font-weight: 700; }
.cat-lijst { list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; }
.cat-rij { display: grid; grid-template-columns: auto 1fr; gap: 12px; align-items: center; }
.cat-body { min-width: 0; }
.ico-rond {
  width: 38px; height: 38px; flex: none; border-radius: 12px; display: grid; place-items: center;
  background: color-mix(in srgb, var(--c) 14%, var(--kaart)); color: var(--c);
}
.ico-rond .i { width: 20px; height: 20px; }
.ico-rond.klein { width: 34px; height: 34px; border-radius: 10px; }
.ico-rond.klein .i { width: 18px; height: 18px; }
.ico-rond.groot { width: 52px; height: 52px; border-radius: 16px; }
.ico-rond.groot .i { width: 26px; height: 26px; }
.cat-top { display: flex; justify-content: space-between; gap: 8px; font-size: 14.5px; }
.cat-top .naam { font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cat-top .bedrag { font-weight: 700; white-space: nowrap; }
.balk { height: 8px; margin: 6px 0 4px; border-radius: 0 4px 4px 0; background: var(--spoor); overflow: hidden; }
.balk span { display: block; height: 100%; border-radius: 0 4px 4px 0; background: var(--c); transition: width .5s; }
.balk.neutraal span { background: var(--inkt-2); }
.cat-onder { font-size: 12px; color: var(--inkt-2); }
.avatar {
  width: 38px; height: 38px; flex: none; border-radius: 50%; display: grid; place-items: center;
  background: var(--spoor); color: var(--inkt); font-weight: 700;
}

/* Weekgrafiek */
.legenda { display: flex; flex-wrap: wrap; gap: 4px 14px; margin: -4px 0 10px; font-size: 12.5px; color: var(--inkt-2); }
.legenda span { display: inline-flex; align-items: center; gap: 6px; }
.legenda i { width: 10px; height: 10px; border-radius: 3px; background: var(--c); }
.wk-plot { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); align-items: end; height: 168px; border-bottom: 1px solid var(--lijn-2); }
.wk-kol {
  height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 4px;
  border: 0; background: transparent; border-radius: 10px 10px 0 0; padding: 0; color: inherit; transition: background-color .15s;
}
.wk-kol[aria-pressed="true"] { background: color-mix(in srgb, var(--inkt) 7%, transparent); }
.wk-waarde { font-size: 11.5px; font-weight: 700; color: var(--inkt-2); white-space: nowrap; }
.wk-stapel { width: 22px; display: flex; flex-direction: column-reverse; gap: 2px; }
.seg { display: block; width: 100%; background: var(--c); }
.wk-stapel .seg:last-child { border-radius: 4px 4px 0 0; }
.wk-as { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); text-align: center; font-size: 11.5px; color: var(--inkt-2); margin-top: 6px; }
.wk-as .nu { color: var(--inkt); font-weight: 700; }
.wk-detail { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--lijn); font-size: 13.5px; }
.wk-detail-kop { display: flex; justify-content: space-between; gap: 8px; font-weight: 700; margin-bottom: 4px; }
.wk-detail-rij { display: flex; justify-content: space-between; color: var(--inkt-2); padding: 2px 0; }
.wk-detail-rij > span:first-child { display: inline-flex; align-items: center; gap: 8px; }
.lijnsleutel { width: 14px; height: 3px; border-radius: 2px; background: var(--c); }
.tabel-wrap { overflow-x: auto; margin: 0 -4px; }
.wk-tabel { width: 100%; border-collapse: collapse; font-size: 12.5px; font-variant-numeric: tabular-nums; }
.wk-tabel th, .wk-tabel td { padding: 7px 4px; text-align: right; border-bottom: 1px solid var(--lijn); white-space: nowrap; }
.wk-tabel th:first-child, .wk-tabel td:first-child { text-align: left; }
.wk-tabel thead th { color: var(--inkt-2); font-size: 11.5px; }
.wk-tabel tfoot td { font-weight: 700; border-bottom: 0; }

/* Lijst met uitgaven */
.dag-groep + .dag-groep { margin-top: 8px; }
.dag-kop { display: flex; justify-content: space-between; font-size: 12.5px; color: var(--inkt-2); font-weight: 700; padding: 6px 2px; border-bottom: 1px solid var(--lijn); margin-bottom: 2px; }
.post {
  width: 100%; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 12px; align-items: center;
  padding: 8px 4px; border: 0; background: transparent; text-align: left; border-radius: 12px; color: inherit;
}
.post:active, .post:hover { background: var(--kaart-2); }
.post-tekst { min-width: 0; }
.post-titel { display: block; font-weight: 700; font-size: 14.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.post-sub { display: block; font-size: 12.5px; color: var(--inkt-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.post-bedrag { font-weight: 700; white-space: nowrap; font-variant-numeric: tabular-nums; }
.leeg { text-align: center; padding: 8px 8px 4px; color: var(--inkt-2); }
.leeg p { margin: 0 0 12px; }
.meer { display: flex; justify-content: center; margin-top: 6px; }

/* ---------- Maand ---------- */
.melding { display: flex; gap: 10px; align-items: flex-start; background: var(--hanko-zacht); border-radius: 14px; padding: 12px 14px; font-size: 13.5px; margin-bottom: 14px; }
.melding .i { width: 20px; height: 20px; color: var(--hanko); margin-top: 1px; }
.vraag-kop { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.vraag-nr { width: 28px; height: 28px; flex: none; border-radius: 50%; display: grid; place-items: center; background: var(--inkt); color: var(--kaart); font-weight: 700; font-size: 14px; }
.vraag-kop h3 { margin: 0; font-size: 16px; }
.geld-veld { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 5px 0; }
.geld-veld > span:first-child { font-size: 14.5px; min-width: 0; }
.geld-input {
  display: flex; align-items: center; gap: 6px; flex: none; width: 150px; padding: 0 10px; border-radius: 12px;
  border: 1.5px solid var(--lijn); background: var(--kaart-2); transition: border-color .15s, background-color .15s;
}
.geld-input:focus-within { border-color: var(--inkt); background: var(--kaart); }
.geld-input.fout { border-color: var(--kritiek); }
.geld-input > span { color: var(--inkt-2); }
.geld-input input { width: 100%; min-width: 0; border: 0; outline: none; background: transparent; padding: 10px 0; font-size: 16px; font-weight: 700; text-align: right; }
.som-regel { display: flex; justify-content: space-between; margin-top: 8px; padding-top: 10px; border-top: 1px solid var(--lijn); font-size: 14.5px; }
.sub-kop { display: flex; justify-content: space-between; gap: 8px; font-size: 14.5px; margin: 2px 0 6px; }
.sub-kop span { font-weight: 700; }
.vast-lijst { display: grid; gap: 8px; margin: 4px 0 2px; }
.vast-rij { display: grid; grid-template-columns: minmax(0, 1fr) 104px 32px; gap: 6px; align-items: center; }
.vast-rij .invoer { padding: 9px 10px; font-size: 15px; }
.vast-rij .geld-input { width: auto; }
.vast-rij .geld-input input { font-size: 15px; padding: 9px 0; }
.scheiding { height: 1px; background: var(--lijn); margin: 12px 0 8px; }
.resultaat { display: grid; gap: 2px; margin-top: 12px; padding: 14px; border-radius: 14px; background: var(--kaart-2); border: 1px solid var(--lijn); }
.resultaat > span { font-size: 13px; color: var(--inkt-2); }
.resultaat strong { font-size: 26px; line-height: 1.2; }
.resultaat strong.negatief { color: var(--kritiek); }
.feiten { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.feit { display: grid; gap: 2px; padding: 10px; border-radius: 12px; background: var(--kaart-2); }
.feit span { font-size: 12px; color: var(--inkt-2); }
.feit strong { font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tekst-veld { display: grid; gap: 6px; margin-bottom: 12px; }
.tekst-veld:last-child { margin-bottom: 0; }
textarea.invoer { resize: vertical; min-height: 74px; line-height: 1.4; }
.opslaan-balk {
  position: fixed; left: 50%; bottom: calc(80px + env(safe-area-inset-bottom)); z-index: 45; transform: translateX(-50%);
  width: calc(100% - 32px); max-width: 488px; display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 8px 8px 8px 16px; border-radius: 16px; background: var(--inkt); color: var(--kaart); box-shadow: 0 12px 30px rgba(0, 0, 0, .28);
  font-size: 14px; font-weight: 700; animation: omhoog .25s;
}
.opslaan-balk .knop { width: auto; padding: 10px 16px; font-size: 15px; background: var(--kaart); color: var(--inkt); }

/* ---------- Tabbalk ---------- */
.tabbalk {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 40; display: flex; justify-content: center;
  padding: 6px max(8px, env(safe-area-inset-right, 0px)) calc(6px + env(safe-area-inset-bottom, 0px)) max(8px, env(safe-area-inset-left, 0px));
  background: color-mix(in srgb, var(--kaart) 90%, transparent); border-top: 1px solid var(--lijn);
  -webkit-backdrop-filter: saturate(1.4) blur(14px); backdrop-filter: saturate(1.4) blur(14px);
}
.tabbalk-binnen { display: grid; grid-template-columns: repeat(3, 1fr); width: 100%; max-width: 520px; }
.tab { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 4px 0; border: 0; background: transparent; color: var(--inkt-2); font-size: 11.5px; font-weight: 700; }
.tab-ico { width: 58px; height: 30px; border-radius: 999px; display: grid; place-items: center; transition: background-color .2s, color .2s; }
.tab[aria-selected="true"] { color: var(--inkt); }
.tab[aria-selected="true"] .tab-ico { background: var(--hanko-zacht); color: var(--hanko); }

/* ---------- Lagen (onderpaneel) ---------- */
.laag { position: fixed; inset: 0; z-index: 50; display: flex; align-items: flex-end; justify-content: center; }
.laag-achter { position: absolute; inset: 0; background: rgba(20, 16, 12, .4); -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px); animation: vervaag .2s; }
.paneel {
  position: relative; width: 100%; max-width: 520px; max-height: 92vh; overflow: auto; background: var(--kaart);
  border-radius: 24px 24px 0 0; padding: 10px 18px calc(18px + env(safe-area-inset-bottom)); box-shadow: 0 -10px 40px rgba(0, 0, 0, .2);
  animation: omhoog .25s cubic-bezier(.2, .8, .2, 1);
}
.greep { width: 40px; height: 4px; border-radius: 2px; background: var(--lijn-2); margin: 0 auto 14px; }
@keyframes omhoog { from { transform: translateY(40px); opacity: .3; } }
@keyframes vervaag { from { opacity: 0; } }
.opslaan-balk { animation-name: omhoog-midden; }
@keyframes omhoog-midden { from { transform: translate(-50%, 30px); opacity: 0; } }
.detail-kop { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.detail-bedrag { font-size: 28px; font-weight: 700; line-height: 1.1; }
.detail-titel { color: var(--inkt-2); font-size: 15px; }
.detail-lijst { margin: 0 0 16px; display: grid; border-top: 1px solid var(--lijn); }
.detail-lijst div { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--lijn); }
.detail-lijst dt { color: var(--inkt-2); }
.detail-lijst dd { margin: 0; font-weight: 700; text-align: right; }
.paneel-knoppen { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.welkom { text-align: center; padding-top: 22px; }
.welkom .hanko { width: 64px; height: 64px; border-radius: 16px; margin: 0 auto 14px; }
.welkom .hanko span { font-size: 17px; }
.welkom h2 { margin: 0 0 4px; font-size: 22px; }
.welkom p { margin: 0; color: var(--inkt-2); }
.welkom-knoppen { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 18px; }
.welkom-knop { display: grid; justify-items: center; gap: 8px; padding: 18px 10px; border-radius: 18px; border: 1.5px solid var(--lijn); background: var(--kaart-2); font-weight: 700; font-size: 17px; }
.welkom-knop .avatar { width: 52px; height: 52px; font-size: 20px; background: var(--inkt); color: var(--kaart); }

/* ---------- Melding onderaan ---------- */
.toast {
  position: fixed; left: 50%; bottom: calc(88px + env(safe-area-inset-bottom)); z-index: 60; transform: translate(-50%, 16px);
  display: flex; align-items: center; gap: 8px; max-width: calc(100% - 32px); width: max-content;
  padding: 11px 16px; border-radius: 14px; background: var(--inkt); color: var(--kaart); font-size: 14px; font-weight: 500;
  box-shadow: 0 10px 30px rgba(0, 0, 0, .25); opacity: 0; pointer-events: none; transition: opacity .25s, transform .25s;
}
.toast.zichtbaar { opacity: 1; transform: translate(-50%, 0); }
.toast[data-soort="fout"] { background: var(--kritiek); color: #fff; }
.toast .i { width: 18px; height: 18px; }

/* ---------- Zijpaneel in Google Sheets ---------- */
[data-modus="zijpaneel"] .app { padding-block: 10px 104px; padding-left: 12px; padding-right: 12px; }
[data-modus="zijpaneel"] .kop { margin-bottom: 14px; }
[data-modus="zijpaneel"] .hanko { width: 40px; height: 40px; }
[data-modus="zijpaneel"] .hanko span { font-size: 10.5px; letter-spacing: .5px; }
[data-modus="zijpaneel"] .kop p { display: none; }
[data-modus="zijpaneel"] .kop h1 { font-size: 19px; }
[data-modus="zijpaneel"] .ik-knop { padding: 0 10px 0 8px; }
[data-modus="zijpaneel"] .bedrag-veld input { font-size: 36px; }
[data-modus="zijpaneel"] .geld-input { width: 128px; }
@media (max-width: 340px) {
  .cat-uitleg { display: none; }
  .cat { min-height: 0; grid-template-columns: 1fr; row-gap: 8px; padding: 10px 12px; }
  .cat-icoon { grid-row: auto; width: 34px; height: 34px; border-radius: 10px; }
  .feiten { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <symbol id="i-overleven" viewBox="0 0 24 24"><path d="M3.5 11.5h17a8.5 8.5 0 0 1-17 0z"/><path d="M10 3.5c-1 1.2 1 2.3 0 3.6M14 3.5c-1 1.2 1 2.3 0 3.6"/></symbol>
  <symbol id="i-optioneel" viewBox="0 0 24 24"><path d="M5.5 8.5h13l-1 11.5h-11z"/><path d="M9 8.5V7a3 3 0 0 1 6 0v1.5"/></symbol>
  <symbol id="i-cultuur" viewBox="0 0 24 24"><path d="M12 6.5C10 4.9 7 4.5 3.5 5v13c3.5-.5 6.5-.1 8.5 1.5 2-1.6 5-2 8.5-1.5V5C17 4.5 14 4.9 12 6.5z"/><path d="M12 6.5v13"/></symbol>
  <symbol id="i-extra" viewBox="0 0 24 24"><path d="M13 3 5.5 13.5H12l-1 7.5 7.5-10.5H12z"/></symbol>
  <symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
  <symbol id="i-grafiek" viewBox="0 0 24 24"><path d="M5.5 19.5v-7M12 19.5V5M18.5 19.5v-10"/><path d="M3 20.5h18"/></symbol>
  <symbol id="i-boek" viewBox="0 0 24 24"><rect x="4.5" y="3.5" width="15" height="17" rx="2.5"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/></symbol>
  <symbol id="i-links" viewBox="0 0 24 24"><path d="m14.5 6-6 6 6 6"/></symbol>
  <symbol id="i-rechts" viewBox="0 0 24 24"><path d="m9.5 6 6 6-6 6"/></symbol>
  <symbol id="i-vink" viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></symbol>
  <symbol id="i-sluit" viewBox="0 0 24 24"><path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/></symbol>
  <symbol id="i-prullenbak" viewBox="0 0 24 24"><path d="M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13M10 11v5.5M14 11v5.5"/></symbol>
  <symbol id="i-potlood" viewBox="0 0 24 24"><path d="M4.5 19.5h4l10-10-4-4-10 10z"/><path d="m13 7 4 4"/></symbol>
  <symbol id="i-persoon" viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20c1.2-3.6 4.2-5.5 7.5-5.5s6.3 1.9 7.5 5.5"/></symbol>
  <symbol id="i-tabel" viewBox="0 0 24 24"><rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M3.5 10h17M3.5 15h17M10 10v9.5"/></symbol>
  <symbol id="i-waarschuwing" viewBox="0 0 24 24"><path d="M12 4.5 21 19.5H3z"/><path d="M12 10v4.5M12 17.2v.1"/></symbol>
  <symbol id="i-vernieuw" viewBox="0 0 24 24"><path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5V9H15"/></symbol>
  <symbol id="i-info" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.1"/></symbol>
  <symbol id="i-vraag" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M9.8 9.6a2.3 2.3 0 1 1 3.2 2.1c-.6.3-1 .8-1 1.5v.4M12 16.6v.1"/></symbol>
</svg>

<div class="app" id="app">
  <header class="kop">
    <div class="hanko" aria-hidden="true"><span>家計簿</span></div>
    <div class="kop-tekst">
      <h1>Kakebo</h1>
      <p id="kopSub">Huishoudboekje</p>
    </div>
    <button type="button" class="rond" id="vernieuw" aria-label="Gegevens vernieuwen"><svg class="i" aria-hidden="true"><use href="#i-vernieuw"/></svg></button>
    <button type="button" class="ik-knop" id="ikKnop" aria-label="Wie ben jij? Tik om te wisselen"><svg class="i" aria-hidden="true"><use href="#i-persoon"/></svg><span id="ikNaam">Wie ben jij?</span></button>
  </header>

  <main>
    <!-- NIEUW -->
    <section class="scherm" id="scherm-nieuw" role="tabpanel" aria-labelledby="tab-nieuw">
      <div class="scherm-kop">
        <h2 id="nieuwTitel">Nieuwe uitgave</h2>
        <span class="chip-info" id="nieuwBudget" hidden></span>
        <button type="button" class="link-knop" id="annuleerBewerk" hidden><svg class="i" aria-hidden="true"><use href="#i-sluit"/></svg>Annuleren</button>
      </div>
      <div class="kaart bedrag-kaart">
        <label class="label" for="bedrag">Bedrag</label>
        <div class="bedrag-veld" id="bedragVeld">
          <span class="euro" aria-hidden="true">€</span>
          <input id="bedrag" type="text" inputmode="decimal" autocomplete="off" placeholder="0,00" enterkeyhint="next">
        </div>
      </div>
      <fieldset class="cat-kies">
        <legend class="label">Categorie</legend>
        <div class="cat-grid" id="catGrid" role="radiogroup" aria-label="Categorie"></div>
      </fieldset>
      <div class="kaart velden">
        <label class="veld">
          <span class="label">Omschrijving</span>
          <input class="invoer" id="omschrijving" list="suggesties" maxlength="120" placeholder="Bijv. boodschappen" autocomplete="off" enterkeyhint="done">
        </label>
        <datalist id="suggesties"></datalist>
        <div class="veld">
          <span class="label" id="datumLabel">Datum</span>
          <div class="datum-rij">
            <div class="chips">
              <button type="button" class="chip" data-dagen="0">Vandaag</button>
              <button type="button" class="chip" data-dagen="-1">Gisteren</button>
            </div>
            <input class="invoer" type="date" id="datum" aria-labelledby="datumLabel">
          </div>
        </div>
        <div class="veld">
          <span class="label" id="wieLabel">Betaald door</span>
          <div class="segment" id="wieSegment" role="radiogroup" aria-labelledby="wieLabel"></div>
        </div>
      </div>
      <div class="knoppen">
        <button type="button" class="knop knop-primair" id="bewaar"><svg class="i" aria-hidden="true"><use href="#i-vink"/></svg><span>Bewaren</span></button>
      </div>
    </section>

    <!-- OVERZICHT -->
    <section class="scherm" id="scherm-overzicht" role="tabpanel" aria-labelledby="tab-overzicht" hidden>
      <div class="maand-nav" id="ovNav">
        <button type="button" class="rond" data-stap="-1" aria-label="Vorige maand"><svg class="i" aria-hidden="true"><use href="#i-links"/></svg></button>
        <div class="maand-titel"><h2></h2><span class="maand-status"></span></div>
        <button type="button" class="rond" data-stap="1" aria-label="Volgende maand"><svg class="i" aria-hidden="true"><use href="#i-rechts"/></svg></button>
      </div>
      <div class="inhoud" id="ovInhoud"></div>
    </section>

    <!-- MAAND -->
    <section class="scherm" id="scherm-maand" role="tabpanel" aria-labelledby="tab-maand" hidden>
      <div class="maand-nav" id="mdNav">
        <button type="button" class="rond" data-stap="-1" aria-label="Vorige maand"><svg class="i" aria-hidden="true"><use href="#i-links"/></svg></button>
        <div class="maand-titel"><h2></h2><span class="maand-status"></span></div>
        <button type="button" class="rond" data-stap="1" aria-label="Volgende maand"><svg class="i" aria-hidden="true"><use href="#i-rechts"/></svg></button>
      </div>
      <div class="inhoud" id="mdInhoud"></div>
    </section>
  </main>
</div>

<div class="opslaan-balk" id="opslaanBalk" hidden>
  <span>Niet opgeslagen</span>
  <button type="button" class="knop" id="bewaarMaandSnel">Opslaan</button>
</div>

<nav class="tabbalk" aria-label="Schermen">
  <div class="tabbalk-binnen" role="tablist">
    <button type="button" class="tab" role="tab" id="tab-nieuw" data-scherm="nieuw" aria-controls="scherm-nieuw"><span class="tab-ico"><svg class="i" aria-hidden="true"><use href="#i-plus"/></svg></span>Nieuw</button>
    <button type="button" class="tab" role="tab" id="tab-overzicht" data-scherm="overzicht" aria-controls="scherm-overzicht"><span class="tab-ico"><svg class="i" aria-hidden="true"><use href="#i-grafiek"/></svg></span>Overzicht</button>
    <button type="button" class="tab" role="tab" id="tab-maand" data-scherm="maand" aria-controls="scherm-maand"><span class="tab-ico"><svg class="i" aria-hidden="true"><use href="#i-boek"/></svg></span>Maand</button>
  </div>
</nav>

<div class="laag" id="laagDetail" hidden>
  <div class="laag-achter" data-sluit></div>
  <div class="paneel" role="dialog" aria-modal="true" aria-labelledby="detailTitel">
    <div class="greep"></div>
    <div id="detailInhoud"></div>
    <div class="paneel-knoppen">
      <button type="button" class="knop knop-zacht" id="detailBewerk"><svg class="i" aria-hidden="true"><use href="#i-potlood"/></svg>Bewerken</button>
      <button type="button" class="knop knop-gevaar" id="detailVerwijder"><svg class="i" aria-hidden="true"><use href="#i-prullenbak"/></svg><span>Verwijderen</span></button>
    </div>
  </div>
</div>

<div class="laag" id="laagWelkom" hidden>
  <div class="laag-achter" data-sluit-welkom></div>
  <div class="paneel welkom" role="dialog" aria-modal="true" aria-labelledby="welkomTitel">
    <div class="hanko" aria-hidden="true"><span>家計簿</span></div>
    <h2 id="welkomTitel">Welkom bij Kakebo</h2>
    <p>Kies je naam. Dan weet het boekje wie een uitgave doet.</p>
    <div class="welkom-knoppen" id="welkomKnoppen"></div>
  </div>
</div>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<script>
(function () {
  'use strict';

  var START = /*__KB_START__*/null;
  var MODUS = '__KB_MODUS__';

  var CATS = [
    { naam: 'Overleven', kort: 'Eten, vervoer, zorg', icoon: 'i-overleven', kleur: '--c-overleven' },
    { naam: 'Optioneel', kort: 'Uit eten, kleding, hobby', icoon: 'i-optioneel', kleur: '--c-optioneel' },
    { naam: 'Cultuur', kort: 'Boeken, film, uitjes', icoon: 'i-cultuur', kleur: '--c-cultuur' },
    { naam: 'Extra', kort: 'Onverwacht, cadeaus', icoon: 'i-extra', kleur: '--c-extra' }
  ];
  var MAANDEN = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'];

  var euro = new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' });
  var euro0 = new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR', minimumFractionDigits: 0, maximumFractionDigits: 0 });
  var procent = new Intl.NumberFormat('nl-NL', { style: 'percent', maximumFractionDigits: 0 });
  var dagFormaat = new Intl.DateTimeFormat('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' });

  var S = {
    namen: [], ik: null, vandaag: '', huidig: '', maand: '', cache: {},
    scherm: 'nieuw', invoer: { cat: null, datum: '', wie: '' }, bewerk: null, detail: null,
    weekKeuze: null, weekTabel: false, alles: false,
    form: null, vuil: false, toch: false, bezig: false, laag: null, geladenOp: Date.now(), toastTimer: null
  };

  /* ---------- Hulpjes ---------- */
  function $(sel, el) { return (el || document).querySelector(sel); }
  function $$(sel, el) { return Array.prototype.slice.call((el || document).querySelectorAll(sel)); }
  function esc(s) {
    return String(s === undefined || s === null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }
  function rond(n) { return Math.round((Number(n) || 0) * 100) / 100; }
  function fmt(n) { return euro.format(rond(n)); }
  function fmt0(n) { return euro0.format(Math.round(Number(n) || 0)); }
  function fmtKort(n) {
    if (Math.abs(n) < 1000) return fmt0(n);
    return '€ ' + (n / 1000).toLocaleString('nl-NL', { maximumFractionDigits: 1 }) + 'k';
  }
  function icoon(id, klasse) { return '<svg class="' + (klasse || 'i') + '" aria-hidden="true"><use href="#' + id + '"/></svg>'; }
  function catInfo(naam) {
    for (var i = 0; i < CATS.length; i++) if (CATS[i].naam === naam) return CATS[i];
    return { naam: naam, kort: '', icoon: 'i-vraag', kleur: '--inkt-3' };
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function isoVan(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function vandaagLokaal() { return isoVan(new Date()); }
  function plusDagen(iso, n) { var p = iso.split('-').map(Number); return isoVan(new Date(p[0], p[1] - 1, p[2] + n)); }
  function maandPlus(sleutel, n) {
    var p = sleutel.split('-').map(Number);
    var d = new Date(p[0], p[1] - 1 + n, 1);
    return d.getFullYear() + '-' + pad(d.getMonth() + 1);
  }
  function maandLabel(sleutel) { return MAANDEN[Number(sleutel.slice(5, 7)) - 1] + ' ' + sleutel.slice(0, 4); }
  function datumLang(iso) {
    var p = iso.split('-').map(Number);
    return dagFormaat.format(new Date(p[0], p[1] - 1, p[2]));
  }
  function datumKop(iso) {
    var v = vandaagLokaal();
    if (iso === v) return 'Vandaag';
    if (iso === plusDagen(v, -1)) return 'Gisteren';
    return cap(datumLang(iso));
  }
  function groot(n) {
    return euro.formatToParts(rond(n)).map(function (d) {
      return d.type === 'decimal' || d.type === 'fraction' ? '<span class="centen">' + esc(d.value) + '</span>' : esc(d.value);
    }).join('');
  }
  function meervoud(n, een, meer) { return n + ' ' + (n === 1 ? een : meer); }

  /** Leest "12,50", "1.250", "€ 3,20" of "12.5". */
  function parseBedrag(waarde) {
    if (typeof waarde === 'number') return isFinite(waarde) ? waarde : null;
    var s = String(waarde === undefined || waarde === null ? '' : waarde).replace(/[€\\s\\u00a0']/g, '');
    if (!s) return null;
    var teken = 1;
    if (s.charAt(0) === '-' || s.charAt(0) === '−') { teken = -1; s = s.slice(1); }
    if (!/^[\\d.,]+$/.test(s) || !/\\d/.test(s)) return null;
    var komma = s.lastIndexOf(','), punt = s.lastIndexOf('.');
    if (komma >= 0 && punt >= 0) {
      s = komma > punt ? s.replace(/\\./g, '').replace(',', '.') : s.replace(/,/g, '');
    } else if (komma >= 0) {
      if (s.split(',').length > 2) return null;
      s = s.replace(',', '.');
    } else if (punt >= 0) {
      var delen = s.split('.');
      if (delen.length > 2 || delen[1].length === 3) {
        for (var i = 1; i < delen.length; i++) if (delen[i].length !== 3) return null;
        s = delen.join('');
      }
    }
    var n = Number(s);
    return isFinite(n) ? teken * n : null;
  }
  function getalInvoer(n) {
    n = rond(n);
    if (!n) return '';
    return n.toLocaleString('nl-NL', { minimumFractionDigits: n % 1 ? 2 : 0, maximumFractionDigits: 2, useGrouping: false });
  }

  function leesIk() { try { return localStorage.getItem('kakebo_ik'); } catch (e) { return null; } }
  function bewaarIk(n) { try { localStorage.setItem('kakebo_ik', n); } catch (e) { /* niet erg */ } }

  function api(naam) {
    var args = Array.prototype.slice.call(arguments, 1);
    return new Promise(function (ok, nok) {
      var run = window.google && google.script && google.script.run;
      if (!run) { nok(new Error('Geen verbinding met Google. Open de app via de link.')); return; }
      run.withSuccessHandler(ok).withFailureHandler(function (e) {
        nok(e instanceof Error ? e : new Error((e && e.message) || String(e)));
      })[naam].apply(null, args);
    });
  }

  function toast(tekst, soort) {
    var t = $('#toast');
    t.innerHTML = icoon(soort === 'fout' ? 'i-waarschuwing' : 'i-vink') + '<span>' + esc(tekst) + '</span>';
    t.dataset.soort = soort || 'ok';
    t.classList.add('zichtbaar');
    clearTimeout(S.toastTimer);
    S.toastTimer = setTimeout(function () { t.classList.remove('zichtbaar'); }, soort === 'fout' ? 4200 : 2600);
  }
  function zetBezig(knop, aan) { if (knop) knop.classList.toggle('bezig', !!aan); S.bezig = !!aan; }
  function tril() { if (navigator.vibrate) { try { navigator.vibrate(12); } catch (e) { /* niet erg */ } } }

  /* ---------- Start ---------- */
  function init() {
    document.documentElement.dataset.modus = MODUS;
    if (!START || !START.maand) {
      $('#app').innerHTML = '<div class="kaart" style="margin-top:40px"><h2 style="margin-top:0">Er ging iets mis</h2><p>De gegevens konden niet geladen worden. Herlaad de pagina.</p></div>';
      return;
    }
    S.namen = START.namen;
    S.vandaag = START.vandaag;
    S.huidig = START.vandaag.slice(0, 7);
    S.maand = START.maand.maand;
    S.cache[S.maand] = START.maand;
    S.ik = leesIk() || START.ik;
    if (S.namen.indexOf(S.ik) < 0) S.ik = null;
    S.invoer.wie = S.ik || S.namen[0];
    S.invoer.datum = vandaagLokaal();

    $('#catGrid').innerHTML = CATS.map(function (c) {
      return '<button type="button" class="cat" role="radio" aria-checked="false" data-cat="' + c.naam + '" style="--c: var(' + c.kleur + ')">' +
        '<span class="cat-icoon">' + icoon(c.icoon) + '</span>' +
        '<span class="cat-naam">' + c.naam + '</span>' +
        '<span class="cat-uitleg">' + c.kort + '</span>' + icoon('i-vink', 'i cat-vink') + '</button>';
    }).join('');
    $('#wieSegment').innerHTML = S.namen.map(function (n) {
      return '<button type="button" role="radio" aria-checked="false" data-wie="' + esc(n) + '">' + esc(n) + '</button>';
    }).join('');

    document.addEventListener('click', opKlik);
    document.addEventListener('input', opInvoer);
    document.addEventListener('focusout', opVerlaat);
    document.addEventListener('keydown', opToets);
    $('#datum').addEventListener('change', function (e) { S.invoer.datum = e.target.value || vandaagLokaal(); renderNieuw(); });
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden && Date.now() - S.geladenOp > 60000) vernieuw(true);
    });

    renderAlles();
    if (!S.ik) toonWelkom();
  }

  /* ---------- Gebeurtenissen ---------- */
  function opKlik(e) {
    var el = e.target.closest('button, [data-sluit], [data-sluit-welkom]');
    if (!el) return;
    if (el.hasAttribute('data-sluit')) { sluitLaag(); return; }
    if (el.hasAttribute('data-sluit-welkom')) { if (S.ik) sluitLaag(); return; }
    var d = el.dataset;
    if (d.scherm) return gaNaarScherm(d.scherm);
    if (d.naar) return gaNaarScherm(d.naar);
    if (d.stap) return wisselMaand(Number(d.stap));
    if (d.cat) { S.invoer.cat = d.cat; renderNieuw(); return; }
    if (d.wie) { S.invoer.wie = d.wie; renderNieuw(); return; }
    if (d.dagen !== undefined) { S.invoer.datum = plusDagen(vandaagLokaal(), Number(d.dagen)); renderNieuw(); return; }
    if (d.week) { S.weekKeuze = Number(d.week); renderOverzicht(); return; }
    if (d.i !== undefined && el.classList.contains('post')) return openDetail(Number(d.i));
    if (d.naam) return kiesIk(d.naam);
    if (el.classList.contains('vast-weg')) return verwijderVast(Number(el.closest('.vast-rij').dataset.i));
    switch (el.id) {
      case 'bewaar': return bewaarUitgave();
      case 'annuleerBewerk': return stopBewerk();
      case 'detailBewerk': return startBewerk();
      case 'detailVerwijder': return verwijder();
      case 'weekWissel': S.weekTabel = !S.weekTabel; return renderOverzicht();
      case 'toonAlles': S.alles = true; return renderOverzicht();
      case 'vastErbij': return voegVastToe();
      case 'mdBewaar': case 'bewaarMaandSnel': return bewaarMaand();
      case 'ikKnop': return toonWelkom();
      case 'vernieuw': return vernieuw(false);
    }
  }

  function opInvoer(e) {
    var el = e.target;
    if (el.id === 'bedrag') {
      var schoon = el.value.replace(/[^\\d.,\\-]/g, '');
      if (schoon !== el.value) el.value = schoon;
      $('#bedragVeld').classList.remove('fout');
      return;
    }
    if (!S.form) return;
    var veld = el.dataset.veld;
    if (veld === 'goed' || veld === 'beter' || veld === 'voornemen') {
      S.form[veld] = el.value;
      maakVuil();
      return;
    }
    var rij = el.closest('.vast-rij');
    if (veld || rij) {
      if (el.classList.contains('vast-naam')) {
        S.form.lijst[Number(rij.dataset.i)].naam = el.value;
      } else {
        var n = parseBedrag(el.value);
        el.closest('.geld-input').classList.toggle('fout', el.value.trim() !== '' && n === null);
        if (rij) S.form.lijst[Number(rij.dataset.i)].bedrag = n === null ? 0 : rond(n);
        else S.form[veld] = n === null ? 0 : rond(n);
        herbereken();
      }
      maakVuil();
    }
  }

  function opVerlaat(e) {
    var el = e.target;
    if (!el.closest || !el.closest('.geld-input')) return;
    var n = parseBedrag(el.value);
    if (n !== null) el.value = getalInvoer(n);
  }

  function opToets(e) {
    if (e.key === 'Escape' && S.laag) { if (S.laag.id !== 'laagWelkom' || S.ik) sluitLaag(); return; }
    if (e.key === 'Enter' && e.target.id === 'bedrag') { e.preventDefault(); $('#omschrijving').focus(); return; }
    if (e.key === 'Enter' && e.target.id === 'omschrijving') { e.preventDefault(); e.target.blur(); bewaarUitgave(); }
  }

  /* ---------- Navigatie ---------- */
  function gaNaarScherm(naam) {
    S.scherm = naam;
    renderTabs();
    window.scrollTo(0, 0);
    if (naam !== 'nieuw' && !S.cache[S.maand]) laadMaand(S.maand);
  }

  function wisselMaand(stap) {
    if (S.vuil && !S.toch) {
      S.toch = true;
      toast('Nog niet opgeslagen. Tik nog eens om toch te wisselen.', 'fout');
      setTimeout(function () { S.toch = false; }, 4000);
      return;
    }
    S.toch = false;
    S.vuil = false;
    S.form = null;
    S.maand = maandPlus(S.maand, stap);
    S.weekKeuze = null;
    S.alles = false;
    renderOverzicht();
    renderMaand();
    renderTabs();
    if (!S.cache[S.maand]) laadMaand(S.maand);
  }

  function laadMaand(sleutel) {
    $$('.inhoud').forEach(function (v) { v.classList.add('laden'); });
    return api('kbMaand', sleutel).then(zetMaandData).catch(function (e) {
      toast(e.message, 'fout');
    }).then(function () {
      $$('.inhoud').forEach(function (v) { v.classList.remove('laden'); });
    });
  }

  function vernieuw(stil) {
    var knop = $('#vernieuw');
    knop.classList.add('draait');
    var sleutels = [S.maand];
    if (S.huidig !== S.maand) sleutels.push(S.huidig);
    return Promise.all(sleutels.map(function (k) { return api('kbMaand', k); })).then(function (lijst) {
      lijst.forEach(zetMaandData);
      if (!stil) toast('Bijgewerkt');
    }).catch(function (e) {
      if (!stil) toast(e.message, 'fout');
    }).then(function () { knop.classList.remove('draait'); });
  }

  function zetMaandData(d) {
    if (!d || !d.maand) return;
    S.cache[d.maand] = d;
    S.geladenOp = Date.now();
    if (d.maand === S.maand) {
      renderOverzicht();
      if (!S.vuil) { S.form = null; renderMaand(); }
    }
    if (d.maand === S.huidig) renderBudgetChip();
    renderSuggesties();
  }

  /* ---------- Weergave ---------- */
  function renderAlles() {
    renderKop();
    renderTabs();
    renderNieuw();
    renderOverzicht();
    renderMaand();
  }

  function renderKop() {
    $('#kopSub').textContent = S.namen.join(' & ');
    $('#ikNaam').textContent = S.ik || 'Wie ben jij?';
  }

  function renderTabs() {
    $$('.tab').forEach(function (b) { b.setAttribute('aria-selected', String(b.dataset.scherm === S.scherm)); });
    ['nieuw', 'overzicht', 'maand'].forEach(function (n) { $('#scherm-' + n).hidden = n !== S.scherm; });
    $('#opslaanBalk').hidden = !(S.scherm === 'maand' && S.vuil);
  }

  function renderNav(sel) {
    var nav = $(sel);
    var status = S.maand === S.huidig ? 'Lopende maand' : (S.maand < S.huidig ? 'Afgelopen maand' : 'Komende maand');
    $('h2', nav).textContent = maandLabel(S.maand);
    $('.maand-status', nav).textContent = status;
  }

  function renderNieuw() {
    var bewerk = !!S.bewerk;
    $('#nieuwTitel').textContent = bewerk ? 'Uitgave bewerken' : 'Nieuwe uitgave';
    $('#bewaar span').textContent = bewerk ? 'Wijziging bewaren' : 'Bewaren';
    $('#annuleerBewerk').hidden = !bewerk;
    $$('.cat').forEach(function (b) { b.setAttribute('aria-checked', String(b.dataset.cat === S.invoer.cat)); });
    $$('#wieSegment button').forEach(function (b) { b.setAttribute('aria-checked', String(b.dataset.wie === S.invoer.wie)); });
    $('#datum').value = S.invoer.datum;
    var v = vandaagLokaal();
    $$('[data-dagen]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(plusDagen(v, Number(b.dataset.dagen)) === S.invoer.datum));
    });
    renderBudgetChip();
    renderSuggesties();
  }

  function renderBudgetChip() {
    var d = S.cache[S.huidig];
    var el = $('#nieuwBudget');
    if (!d || d.budget <= 0 || S.bewerk) { el.hidden = true; return; }
    el.hidden = false;
    if (d.over >= 0) {
      el.textContent = 'nog ' + fmt0(d.over) + ' in ' + MAANDEN[Number(S.huidig.slice(5, 7)) - 1];
      el.dataset.niveau = '';
    } else {
      el.textContent = fmt0(-d.over) + ' over budget';
      el.dataset.niveau = 'over';
    }
  }

  function renderSuggesties() {
    var gezien = {};
    var opties = [];
    Object.keys(S.cache).forEach(function (k) {
      S.cache[k].uitgaven.forEach(function (u) {
        var o = u.omschrijving;
        if (o && !gezien[o.toLowerCase()] && opties.length < 80) { gezien[o.toLowerCase()] = true; opties.push(o); }
      });
    });
    $('#suggesties').innerHTML = opties.map(function (o) { return '<option value="' + esc(o) + '">'; }).join('');
  }

  /* ----- Overzicht ----- */
  function renderOverzicht() {
    renderNav('#ovNav');
    var d = S.cache[S.maand];
    var box = $('#ovInhoud');
    if (!d) { box.classList.add('laden'); return; }
    box.classList.remove('laden');
    box.innerHTML = heldHTML(d) + tegelsHTML(d) + categorieHTML(d) + weekHTML(d) + personenHTML(d) + lijstHTML(d);
  }

  function niveauVan(d) {
    var ratio = d.budget > 0 ? d.uitgegeven / d.budget : (d.uitgegeven > 0 ? 2 : 0);
    return { ratio: ratio, niveau: ratio > 1 ? 'over' : (ratio >= 0.9 ? 'let-op' : 'ok') };
  }

  function heldHTML(d) {
    if (d.budget <= 0) {
      return '<section class="kaart held leeg-held">' +
        '<div class="held-label">' + (d.status === 'verleden' ? 'Geen budget voor deze maand' : 'Nog geen budget') + '</div>' +
        (d.uitgegeven > 0 ? '<div class="held-getal">' + groot(d.uitgegeven) + '</div><p>uitgegeven deze maand.</p>' : '') +
        '<p>Vul jullie inkomen, vaste lasten en spaardoel in. Wat overblijft is jullie budget om uit te geven.</p>' +
        '<button type="button" class="knop knop-primair" data-naar="maand">' + icoon('i-boek') + 'Plan ' + esc(maandLabel(d.maand)) + '</button></section>';
    }
    var n = niveauVan(d);
    var label, getal;
    if (d.status === 'toekomst') { label = 'Budget voor deze maand'; getal = d.budget; }
    else if (d.over >= 0) { label = d.status === 'huidig' ? 'Nog te besteden' : 'Overgebleven'; getal = d.over; }
    else { label = d.status === 'huidig' ? 'Over budget' : 'Te veel uitgegeven'; getal = -d.over; }
    var pills = [];
    if (d.status === 'huidig') {
      if (d.over > 0) pills.push('± <strong>' + fmt0(d.perDagNog) + '</strong> per dag');
      pills.push('nog <strong>' + meervoud(d.dagenOver, 'dag', 'dagen') + '</strong>');
    } else if (d.status === 'verleden') {
      pills.push('gespaard <strong>' + fmt0(d.gespaard) + '</strong>');
    }
    if (d.status !== 'toekomst' && d.uitgegeven > 0 && d.dagNr > 0) pills.push('gemiddeld <strong>' + fmt0(d.gemiddeldPerDag) + '</strong> per dag');
    var statusTekst = n.niveau === 'over' ? 'Over budget' : (n.niveau === 'let-op' ? 'Budget bijna op' : '');
    var breedte = Math.max(0, Math.min(100, n.ratio * 100));
    return '<section class="kaart held" aria-label="Budget">' +
      '<div class="held-label">' + label + '</div>' +
      '<div class="held-getal">' + groot(getal) + '</div>' +
      '<div class="meter" data-niveau="' + n.niveau + '" role="progressbar" aria-label="Deel van het budget uitgegeven" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + Math.round(breedte) + '"><span style="width:' + breedte.toFixed(1) + '%"></span></div>' +
      '<div class="held-regel"><span><strong>' + fmt0(d.uitgegeven) + '</strong> uitgegeven</span>' +
      '<span>' + (d.budget > 0 ? procent.format(n.ratio) + ' van <strong>' + fmt0(d.budget) + '</strong>' : 'geen budget') + '</span></div>' +
      (statusTekst ? '<p class="status" data-niveau="' + n.niveau + '">' + icoon('i-waarschuwing') + statusTekst + '</p>' : '') +
      (pills.length ? '<div class="pills">' + pills.map(function (p) { return '<span class="pill">' + p + '</span>'; }).join('') + '</div>' : '') +
      '</section>';
  }

  function tegelsHTML(d) {
    var p = d.plan;
    var doelSub = '';
    if (p.spaardoel > 0 && d.budget > 0 && d.status !== 'toekomst') {
      var ok = d.over >= 0;
      var tekst = d.status === 'verleden' ? (ok ? 'gehaald' : 'niet gehaald') : (ok ? 'op koers' : 'in gevaar');
      doelSub = '<span class="tegel-sub" data-niveau="' + (ok ? 'ok' : 'over') + '">' + icoon(ok ? 'i-vink' : 'i-waarschuwing') + tekst + '</span>';
    }
    var weekSub = d.budget > 0 ? '<span class="tegel-sub">± ' + fmt0(d.budget / (d.dagen / 7)) + ' per week</span>' : '';
    function tegel(label, waarde, sub) {
      return '<button type="button" class="tegel" data-naar="maand"><span class="tegel-label">' + label + '</span>' +
        '<span class="tegel-waarde">' + waarde + '</span>' + (sub || '') + '</button>';
    }
    return '<div class="tegels">' +
      tegel('Inkomen', fmt0(d.totaalInkomen)) +
      tegel('Vaste lasten', fmt0(p.vaste)) +
      tegel('Spaardoel', fmt0(p.spaardoel), doelSub) +
      tegel('Budget', fmt0(d.budget), weekSub) +
      '</div>';
  }

  function categorieHTML(d) {
    var rijen = d.perCategorie.map(function (c) {
      var info = catInfo(c.naam);
      return '<li class="cat-rij" style="--c: var(' + info.kleur + ')">' +
        '<span class="ico-rond">' + icoon(info.icoon) + '</span>' +
        '<div class="cat-body"><div class="cat-top"><span class="naam">' + esc(c.naam) + '</span><span class="bedrag">' + fmt(c.bedrag) + '</span></div>' +
        '<div class="balk" aria-hidden="true"><span style="width:' + (c.aandeel * 100).toFixed(1) + '%"></span></div>' +
        '<div class="cat-onder">' + procent.format(c.aandeel) + ' · ' + meervoud(c.aantal, 'uitgave', 'uitgaven') + '</div></div></li>';
    }).join('');
    return '<section class="kaart"><div class="kaart-kop"><h3>Per categorie</h3><span class="kaart-sub">' + fmt(d.uitgegeven) + '</span></div>' +
      '<ul class="cat-lijst">' + rijen + '</ul></section>';
  }

  function dagenTekst(w) {
    var m = MAANDEN[Number(w.van.slice(5, 7)) - 1];
    return (w.vanDag === w.totDag ? w.vanDag : w.vanDag + '–' + w.totDag) + ' ' + m;
  }

  function weekHTML(d) {
    var weken = d.perWeek;
    var huidigeWeek = null;
    if (d.status === 'huidig') {
      weken.forEach(function (w) { if (d.vandaag >= w.van && d.vandaag <= w.tot) huidigeWeek = w.nr; });
    }
    var keuze = S.weekKeuze || huidigeWeek;
    var knop = '<button type="button" class="link-knop" id="weekWissel" aria-pressed="' + S.weekTabel + '">' +
      icoon(S.weekTabel ? 'i-grafiek' : 'i-tabel') + (S.weekTabel ? 'Grafiek' : 'Tabel') + '</button>';
    var kop = '<div class="kaart-kop"><h3>Per week</h3>' + knop + '</div>';

    if (S.weekTabel) {
      var kopRij = '<tr><th>Week</th>' + CATS.map(function (c) { return '<th>' + c.naam + '</th>'; }).join('') + '<th>Totaal</th></tr>';
      var rijen = weken.map(function (w) {
        return '<tr><td>' + esc(dagenTekst(w)) + '</td>' + CATS.map(function (c) {
          return '<td>' + fmt0(w.perCategorie[c.naam] || 0) + '</td>';
        }).join('') + '<td><strong>' + fmt0(w.totaal) + '</strong></td></tr>';
      }).join('');
      var voet = '<tr><td>Totaal</td>' + CATS.map(function (c) {
        var som = 0;
        weken.forEach(function (w) { som += w.perCategorie[c.naam] || 0; });
        return '<td>' + fmt0(som) + '</td>';
      }).join('') + '<td>' + fmt0(d.uitgegeven) + '</td></tr>';
      return '<section class="kaart">' + kop + '<div class="tabel-wrap"><table class="wk-tabel"><thead>' + kopRij +
        '</thead><tbody>' + rijen + '</tbody><tfoot>' + voet + '</tfoot></table></div></section>';
    }

    var max = 1;
    weken.forEach(function (w) { if (w.totaal > max) max = w.totaal; });
    var plotHoogte = 124;
    var kolommen = weken.map(function (w) {
      var segmenten = CATS.map(function (c) { return { c: c, v: w.perCategorie[c.naam] || 0 }; })
        .filter(function (s) { return s.v > 0; })
        .map(function (s) {
          return '<span class="seg" style="height:' + Math.max(2, s.v / max * plotHoogte).toFixed(1) + 'px;--c: var(' + s.c.kleur + ')"></span>';
        }).join('');
      return '<button type="button" class="wk-kol" data-week="' + w.nr + '" aria-pressed="' + (keuze === w.nr) + '" ' +
        'aria-label="Week ' + w.nr + ', ' + esc(dagenTekst(w)) + ': ' + esc(fmt(w.totaal)) + '">' +
        '<span class="wk-waarde">' + (w.totaal > 0 ? fmtKort(w.totaal) : '') + '</span>' +
        '<span class="wk-stapel">' + segmenten + '</span></button>';
    }).join('');
    var as = weken.map(function (w) {
      return '<span' + (w.nr === huidigeWeek ? ' class="nu"' : '') + '>' + (w.vanDag === w.totDag ? w.vanDag : w.vanDag + '–' + w.totDag) + '</span>';
    }).join('');
    var gekozen = null;
    weken.forEach(function (w) { if (w.nr === keuze) gekozen = w; });
    var detail = gekozen
      ? '<div class="wk-detail-kop"><span>Week ' + gekozen.nr + ' · ' + esc(dagenTekst(gekozen)) + '</span><span>' + fmt(gekozen.totaal) + '</span></div>' +
        CATS.map(function (c) {
          return '<div class="wk-detail-rij"><span><i class="lijnsleutel" style="--c: var(' + c.kleur + ')"></i>' + c.naam + '</span><span>' + fmt(gekozen.perCategorie[c.naam] || 0) + '</span></div>';
        }).join('')
      : '<p class="hint" style="margin:0">Tik op een week voor de details.</p>';
    var legenda = CATS.map(function (c) { return '<span><i style="--c: var(' + c.kleur + ')"></i>' + c.naam + '</span>'; }).join('');
    return '<section class="kaart">' + kop + '<div class="legenda">' + legenda + '</div>' +
      '<div class="wk-plot">' + kolommen + '</div><div class="wk-as" aria-hidden="true">' + as + '</div>' +
      '<div class="wk-detail" aria-live="polite">' + detail + '</div></section>';
  }

  function personenHTML(d) {
    var lijst = d.perPersoon.filter(function (p) { return p.bedrag !== 0 || S.namen.indexOf(p.naam) >= 0; });
    var rijen = lijst.map(function (p) {
      return '<li class="cat-rij"><span class="avatar" aria-hidden="true">' + esc(p.naam.charAt(0).toUpperCase()) + '</span>' +
        '<div class="cat-body"><div class="cat-top"><span class="naam">' + esc(p.naam) + '</span><span class="bedrag">' + fmt(p.bedrag) + '</span></div>' +
        '<div class="balk neutraal" aria-hidden="true"><span style="width:' + (p.aandeel * 100).toFixed(1) + '%"></span></div>' +
        '<div class="cat-onder">' + procent.format(p.aandeel) + ' · ' + meervoud(p.aantal, 'uitgave', 'uitgaven') + '</div></div></li>';
    }).join('');
    return '<section class="kaart"><div class="kaart-kop"><h3>Wie gaf wat uit?</h3></div><ul class="cat-lijst">' + rijen + '</ul></section>';
  }

  function lijstHTML(d) {
    var kop = '<div class="kaart-kop"><h3>Uitgaven</h3>' + (d.aantal ? '<span class="kaart-sub">' + meervoud(d.aantal, 'uitgave', 'uitgaven') + '</span>' : '') + '</div>';
    if (!d.uitgaven.length) {
      return '<section class="kaart">' + kop + '<div class="leeg"><p>Nog geen uitgaven in ' + esc(maandLabel(d.maand)) + '.</p>' +
        (d.status !== 'toekomst' ? '<button type="button" class="knop knop-zacht" data-naar="nieuw">' + icoon('i-plus') + 'Uitgave toevoegen</button>' : '') +
        '</div></section>';
    }
    var dagSom = {};
    d.uitgaven.forEach(function (u) { dagSom[u.datum] = (dagSom[u.datum] || 0) + u.bedrag; });
    var max = S.alles ? d.uitgaven.length : 25;
    var html = '';
    var vorige = null;
    d.uitgaven.slice(0, max).forEach(function (u, i) {
      if (u.datum !== vorige) {
        if (vorige !== null) html += '</div>';
        html += '<div class="dag-groep"><div class="dag-kop"><span>' + esc(datumKop(u.datum)) + '</span><span>' + fmt(dagSom[u.datum]) + '</span></div>';
        vorige = u.datum;
      }
      var info = catInfo(u.categorie);
      html += '<button type="button" class="post" data-i="' + i + '">' +
        '<span class="ico-rond klein" style="--c: var(' + info.kleur + ')">' + icoon(info.icoon) + '</span>' +
        '<span class="post-tekst"><span class="post-titel">' + esc(u.omschrijving || u.categorie) + '</span>' +
        '<span class="post-sub">' + esc(u.wie) + ' · ' + esc(u.categorie) + '</span></span>' +
        '<span class="post-bedrag">' + fmt(u.bedrag) + '</span></button>';
    });
    html += '</div>';
    if (d.uitgaven.length > max) {
      html += '<div class="meer"><button type="button" class="link-knop" id="toonAlles">Toon alle ' + d.uitgaven.length + ' uitgaven</button></div>';
    }
    return '<section class="kaart">' + kop + html + '</section>';
  }

  /* ----- Maand ----- */
  function formVan(d) {
    var p = d.plan;
    return {
      maand: d.maand, live: p.vasteLive,
      ink1: p.ink1, ink2: p.ink2, overig: p.overig, spaardoel: p.spaardoel, vaste: p.vaste,
      lijst: (d.vasteLijst || []).map(function (v) { return { naam: v.naam, bedrag: v.bedrag, notitie: v.notitie || '' }; }),
      goed: p.goed || '', beter: p.beter || '', voornemen: p.voornemen || ''
    };
  }

  function geldVeld(veld, label, waarde) {
    return '<label class="geld-veld"><span>' + esc(label) + '</span><span class="geld-input"><span aria-hidden="true">€</span>' +
      '<input data-veld="' + veld + '" inputmode="decimal" autocomplete="off" placeholder="0" value="' + esc(getalInvoer(waarde)) + '"></span></label>';
  }

  function tekstVeld(veld, label, waarde, voorbeeld) {
    return '<label class="tekst-veld"><span class="label">' + esc(label) + '</span>' +
      '<textarea class="invoer" data-veld="' + veld + '" rows="3" maxlength="1000" placeholder="' + esc(voorbeeld) + '">' + esc(waarde) + '</textarea></label>';
  }

  function vastRij(v, i) {
    return '<div class="vast-rij" data-i="' + i + '">' +
      '<input class="invoer vast-naam" value="' + esc(v.naam) + '" placeholder="Omschrijving" aria-label="Omschrijving vaste last" maxlength="80">' +
      '<span class="geld-input"><span aria-hidden="true">€</span><input class="vast-bedrag" inputmode="decimal" autocomplete="off" placeholder="0" ' +
      'aria-label="Bedrag per maand" value="' + esc(getalInvoer(v.bedrag)) + '"></span>' +
      '<button type="button" class="rond klein vast-weg" aria-label="Verwijder ' + esc(v.naam || 'vaste last') + '">' + icoon('i-sluit') + '</button></div>';
  }

  function renderMaand() {
    renderNav('#mdNav');
    var d = S.cache[S.maand];
    var box = $('#mdInhoud');
    if (!d) { box.classList.add('laden'); return; }
    box.classList.remove('laden');
    if (!S.form || S.form.maand !== d.maand) S.form = formVan(d);
    var f = S.form;
    var melding = '';
    if (!d.plan.bestaat) {
      melding = '<div class="melding">' + icoon('i-info') + '<span>Deze maand is nog niet gepland. ' +
        'De bedragen hieronder komen van de vorige maand: pas ze aan en sla op.</span></div>';
    }
    var vast = f.live
      ? '<div class="vast-lijst" id="vastLijst">' + f.lijst.map(vastRij).join('') + '</div>' +
        '<button type="button" class="link-knop" id="vastErbij">' + icoon('i-plus') + 'Vaste last toevoegen</button>' +
        '<p class="hint">Deze lijst geldt voor deze en de volgende maanden.</p>'
      : geldVeld('vaste', 'Vaste lasten deze maand', f.vaste) +
        '<p class="hint">' + (d.status === 'verleden'
          ? 'Afgelopen maand: het bedrag staat vast zoals het toen was.'
          : 'Dit bedrag geldt alleen voor deze maand.') + '</p>';
    box.innerHTML = melding +
      '<section class="kaart"><div class="vraag-kop"><span class="vraag-nr">1</span><h3>Hoeveel geld hebben we?</h3></div>' +
      geldVeld('ink1', 'Inkomen ' + S.namen[0], f.ink1) +
      geldVeld('ink2', 'Inkomen ' + S.namen[1], f.ink2) +
      geldVeld('overig', 'Overig inkomen', f.overig) +
      '<div class="som-regel"><span>Totaal</span><strong id="mdTotaal"></strong></div></section>' +

      '<section class="kaart"><div class="vraag-kop"><span class="vraag-nr">2</span><h3>Hoeveel willen we sparen?</h3></div>' +
      '<div class="sub-kop"><span>Vaste lasten</span><strong id="mdVast"></strong></div>' + vast +
      '<div class="scheiding"></div>' + geldVeld('spaardoel', 'Spaardoel', f.spaardoel) +
      '<div class="resultaat"><span>Budget om uit te geven</span><strong id="mdBudget"></strong><span id="mdPerWeek"></span></div></section>' +

      '<section class="kaart"><div class="vraag-kop"><span class="vraag-nr">3</span><h3>Hoeveel geven we uit?</h3></div>' +
      '<div class="feiten" id="mdFeiten"></div></section>' +

      '<section class="kaart"><div class="vraag-kop"><span class="vraag-nr">4</span><h3>Hoe kunnen we het beter doen?</h3></div>' +
      tekstVeld('goed', 'Wat ging goed?', f.goed, 'Bijv. weinig uit eten geweest') +
      tekstVeld('beter', 'Wat kan beter?', f.beter, 'Bijv. minder kleine aankopen') +
      tekstVeld('voornemen', 'Voornemen voor volgende maand', f.voornemen, 'Bijv. elke week een dag zonder uitgaven') +
      '</section>' +
      '<button type="button" class="knop knop-primair" id="mdBewaar">' + icoon('i-vink') + 'Maand opslaan</button>';
    herbereken();
  }

  function herbereken() {
    var f = S.form;
    var d = S.cache[S.maand];
    if (!f || !d || !$('#mdTotaal')) return;
    var vaste = f.live ? f.lijst.reduce(function (s, v) { return s + (v.bedrag || 0); }, 0) : f.vaste;
    var inkomen = f.ink1 + f.ink2 + f.overig;
    var budget = rond(inkomen - vaste - f.spaardoel);
    $('#mdTotaal').textContent = fmt(inkomen);
    $('#mdVast').textContent = fmt(vaste);
    var b = $('#mdBudget');
    b.textContent = fmt(budget);
    b.classList.toggle('negatief', budget < 0);
    $('#mdPerWeek').textContent = budget > 0
      ? '± ' + fmt0(budget / (d.dagen / 7)) + ' per week · ± ' + fmt0(budget / d.dagen) + ' per dag'
      : (budget < 0 ? 'Let op: er gaat meer uit dan er binnenkomt.' : '');
    var over = rond(budget - d.uitgegeven);
    function feit(label, waarde) { return '<div class="feit"><span>' + label + '</span><strong>' + waarde + '</strong></div>'; }
    $('#mdFeiten').innerHTML =
      feit('Uitgegeven', fmt0(d.uitgegeven)) +
      feit('Van het budget', budget > 0 ? procent.format(d.uitgegeven / budget) : '—') +
      feit(over >= 0 ? (d.status === 'verleden' ? 'Overgebleven' : 'Nog over') : 'Te veel', fmt0(Math.abs(over)));
  }

  function maakVuil() {
    if (!S.vuil) { S.vuil = true; renderTabs(); }
  }

  function voegVastToe() {
    S.form.lijst.push({ naam: '', bedrag: 0, notitie: '' });
    $('#vastLijst').insertAdjacentHTML('beforeend', vastRij(S.form.lijst[S.form.lijst.length - 1], S.form.lijst.length - 1));
    var rijen = $$('#vastLijst .vast-rij');
    $('.vast-naam', rijen[rijen.length - 1]).focus();
    maakVuil();
  }

  function verwijderVast(i) {
    S.form.lijst.splice(i, 1);
    $('#vastLijst').innerHTML = S.form.lijst.map(vastRij).join('');
    herbereken();
    maakVuil();
  }

  function bewaarMaand() {
    var f = S.form;
    if (!f || S.bezig) return;
    if ($('#mdInhoud .geld-input.fout')) { toast('Controleer de rood omrande bedragen.', 'fout'); return; }
    var plan = {
      ink1: f.ink1, ink2: f.ink2, overig: f.overig, spaardoel: f.spaardoel,
      goed: f.goed, beter: f.beter, voornemen: f.voornemen
    };
    if (f.live) {
      plan.vasteLijst = f.lijst
        .filter(function (v) { return v.naam.trim() || v.bedrag; })
        .map(function (v) { return { naam: v.naam.trim(), bedrag: v.bedrag, notitie: v.notitie || '' }; });
    } else {
      plan.vaste = f.vaste;
    }
    var knoppen = [$('#mdBewaar'), $('#bewaarMaandSnel')];
    knoppen.forEach(function (k) { zetBezig(k, true); });
    api('kbBewaarMaand', f.maand, plan).then(function (res) {
      S.vuil = false;
      S.form = null;
      var bewaard = {};
      bewaard[res.maand] = res;
      S.cache = bewaard;
      zetMaandData(res);
      renderTabs();
      if (res.maand !== S.huidig) laadStil(S.huidig);
      toast('Maand opgeslagen');
      tril();
    }).catch(function (e) {
      toast(e.message, 'fout');
    }).then(function () {
      knoppen.forEach(function (k) { zetBezig(k, false); });
    });
  }

  function laadStil(sleutel) {
    api('kbMaand', sleutel).then(zetMaandData).catch(function () { /* later opnieuw */ });
  }

  /* ---------- Uitgaven ---------- */
  function bewaarUitgave() {
    if (S.bezig) return;
    var bedrag = parseBedrag($('#bedrag').value);
    if (bedrag === null || rond(bedrag) === 0) {
      $('#bedragVeld').classList.add('fout');
      toast('Vul een bedrag in.', 'fout');
      $('#bedrag').focus();
      return;
    }
    if (!S.invoer.cat) {
      var grid = $('#catGrid');
      grid.classList.remove('schud');
      void grid.offsetWidth;
      grid.classList.add('schud');
      toast('Kies een categorie.', 'fout');
      return;
    }
    var u = {
      datum: S.invoer.datum || vandaagLokaal(),
      bedrag: rond(bedrag),
      categorie: S.invoer.cat,
      omschrijving: $('#omschrijving').value.trim(),
      wie: S.invoer.wie
    };
    var knop = $('#bewaar');
    zetBezig(knop, true);
    var bewerk = S.bewerk;
    var verzoek = bewerk ? api('kbWijzig', bewerk.ref, u) : api('kbVoegToe', u);
    verzoek.then(function (res) {
      if (bewerk) {
        if (bewerk.maand !== res.maand) delete S.cache[bewerk.maand];
        S.bewerk = null;
        S.maand = res.maand;
        leegInvoer();
        zetMaandData(res);
        gaNaarScherm('overzicht');
        toast('Wijziging bewaard');
      } else {
        leegInvoer();
        zetMaandData(res);
        toast(fmt(u.bedrag) + ' bewaard bij ' + u.categorie);
      }
      tril();
    }).catch(function (e) {
      toast(e.message, 'fout');
    }).then(function () {
      zetBezig(knop, false);
    });
  }

  function leegInvoer() {
    $('#bedrag').value = '';
    $('#omschrijving').value = '';
    $('#bedragVeld').classList.remove('fout');
    S.invoer.cat = null;
    renderNieuw();
  }

  function openDetail(i) {
    var d = S.cache[S.maand];
    var u = d && d.uitgaven[i];
    if (!u) return;
    S.detail = u;
    var info = catInfo(u.categorie);
    $('#detailInhoud').innerHTML =
      '<div class="detail-kop" style="--c: var(' + info.kleur + ')"><span class="ico-rond groot">' + icoon(info.icoon) + '</span>' +
      '<div><div class="detail-bedrag">' + fmt(u.bedrag) + '</div><div class="detail-titel" id="detailTitel">' + esc(u.omschrijving || u.categorie) + '</div></div></div>' +
      '<dl class="detail-lijst">' +
      '<div><dt>Categorie</dt><dd>' + esc(u.categorie) + '</dd></div>' +
      '<div><dt>Datum</dt><dd>' + esc(cap(datumLang(u.datum))) + '</dd></div>' +
      '<div><dt>Betaald door</dt><dd>' + esc(u.wie) + '</dd></div></dl>';
    zetVerwijderKnop(false);
    toonLaag('#laagDetail');
  }

  function zetVerwijderKnop(zeker) {
    var knop = $('#detailVerwijder');
    knop.dataset.zeker = zeker ? '1' : '';
    $('span', knop).textContent = zeker ? 'Zeker weten?' : 'Verwijderen';
  }

  function startBewerk() {
    var u = S.detail;
    if (!u) return;
    sluitLaag();
    S.bewerk = { ref: { rij: u.rij, sleutel: u.sleutel }, maand: S.maand };
    S.invoer.cat = catInfo(u.categorie).icoon === 'i-vraag' ? null : u.categorie;
    S.invoer.datum = u.datum;
    if (S.namen.indexOf(u.wie) >= 0) S.invoer.wie = u.wie;
    $('#bedrag').value = getalInvoer(u.bedrag);
    $('#omschrijving').value = u.omschrijving;
    gaNaarScherm('nieuw');
    renderNieuw();
  }

  function stopBewerk() {
    S.bewerk = null;
    S.invoer.wie = S.ik || S.namen[0];
    S.invoer.datum = vandaagLokaal();
    leegInvoer();
    gaNaarScherm('overzicht');
  }

  function verwijder() {
    var knop = $('#detailVerwijder');
    if (!knop.dataset.zeker) {
      zetVerwijderKnop(true);
      clearTimeout(S.zekerTimer);
      S.zekerTimer = setTimeout(function () { zetVerwijderKnop(false); }, 4000);
      return;
    }
    var u = S.detail;
    zetBezig(knop, true);
    api('kbVerwijder', { rij: u.rij, sleutel: u.sleutel }).then(function (res) {
      sluitLaag();
      zetMaandData(res);
      toast('Uitgave verwijderd');
    }).catch(function (e) {
      toast(e.message, 'fout');
    }).then(function () {
      zetBezig(knop, false);
      zetVerwijderKnop(false);
    });
  }

  /* ---------- Wie ben jij ---------- */
  function toonWelkom() {
    $('#welkomTitel').textContent = S.ik ? 'Wie ben jij?' : 'Welkom bij Kakebo';
    $('#welkomKnoppen').innerHTML = S.namen.map(function (n) {
      return '<button type="button" class="welkom-knop" data-naam="' + esc(n) + '"><span class="avatar" aria-hidden="true">' +
        esc(n.charAt(0).toUpperCase()) + '</span>' + esc(n) + '</button>';
    }).join('');
    toonLaag('#laagWelkom');
  }

  function kiesIk(naam) {
    S.ik = naam;
    S.invoer.wie = naam;
    bewaarIk(naam);
    api('kbKiesIk', naam).catch(function () { /* lokaal onthouden is genoeg */ });
    sluitLaag();
    renderKop();
    renderNieuw();
    toast('Hoi ' + naam + '!');
  }

  /* ---------- Lagen ---------- */
  function toonLaag(sel) {
    var laag = $(sel);
    laag.hidden = false;
    S.laag = laag;
    document.body.classList.add('vast');
    var eerste = $('.paneel button', laag);
    if (eerste) eerste.focus({ preventScroll: true });
  }

  function sluitLaag() {
    if (S.laag) S.laag.hidden = true;
    S.laag = null;
    document.body.classList.remove('vast');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
</script>
</body>
</html>
`;
