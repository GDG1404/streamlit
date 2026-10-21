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

  stelSpreadsheetIn_(ss);
  maakBladen_(ss);
  bouwInstellingen_(ss);
  bouwVasteLasten_(ss);
  bouwUitgaven_(ss);
  bouwMaanden_(ss);
  zorgVoorMaanden_(ss);
  bouwHulp_(ss);
  var overzicht = bouwOverzicht_(ss);
  ordenTabbladen_(ss);
  ruimLegeBladenOp_(ss);
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
  sh.getRange(rij, UITG.DATUM).setNumberFormat(KB.FMT.DATUM);
  sh.getRange(rij, UITG.BEDRAG).setNumberFormat(KB.FMT.EURO);
  sh.getRange(rij, UITG.TOEGEVOEGD).setNumberFormat(KB.FMT.TIJD);
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

function stelSpreadsheetIn_(ss) {
  try {
    if (!/^nl/i.test(ss.getSpreadsheetLocale())) ss.setSpreadsheetLocale('nl_NL');
  } catch (e) {
    // Taalinstelling is niet essentieel.
  }
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
  if (stijlFn) stijlFn(sh, laatste + 1, extra);
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
    stijl_(sh.getRange(6, c, 1, 2).merge().setFormula(k.groot), { vet: true, grootte: 18, fmt: EURO });
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
