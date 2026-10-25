// Server-kant van het oefenpad. Draait in Google Apps Script, gekoppeld aan één spreadsheet.
//
// Tabbladen (worden vanzelf aangemaakt als ze ontbreken; setupSheets doet ze allemaal in één keer):
//   Leerkrachten: id, gebruikersnaam, salt, hash, moet_wijzigen
//   Klassen:      id, naam, leerkracht_id                 (leerkracht_id = eigenaar van de klas)
//   Gedeeld:      klas_id, leerkracht_id                  (collega's met wie de eigenaar de klas deelt)
//   Leerlingen:   id, klas_id, naam, salt, hash           (alleen voornaam + eventueel initiaal)
//   Pogingen:     tijd, leerling_id, module, stap, antwoord, juist (1 / 0,5 deels / 0), seconden (actief)
//   Bekeken:      leerling_id, module, stap, tijd
//
// Beheer (leerkrachten toevoegen, wachtwoorden herstellen) gebeurt door de beheerder in de editor.
// Een leerkracht ziet haar eigen klassen en de klassen die een collega met haar deelt.
//
// Snelheid: elk verzoek leest elk tabblad hoogstens één keer. Een juist antwoord geeft meteen de
// volgende stap mee, zodat de pagina per stap maar één keer op de server wacht.

const LOGIN_MAX = 5;            // mislukte pogingen per venster
const LOGIN_SEC = 900;          // 15 minuten
const SESSIE_SEC = 21600;       // 6 uur (maximum van CacheService)
const WEEKDOEL_MIN = 30;        // actieve oefenminuten per week, als weekdoel getoond aan de leerling
const GELDIGE_NAAM = /^[\p{L}][\p{L}' .\-]{0,19}$/u;

const TABBLADEN = {
  Leerkrachten: ['id', 'gebruikersnaam', 'salt', 'hash', 'moet_wijzigen'],
  Klassen: ['id', 'naam', 'leerkracht_id'],
  Gedeeld: ['klas_id', 'leerkracht_id'],
  Leerlingen: ['id', 'klas_id', 'naam', 'salt', 'hash'],
  Pogingen: ['tijd', 'leerling_id', 'module', 'stap', 'antwoord', 'juist', 'seconden'],
  Bekeken: ['leerling_id', 'module', 'stap', 'tijd'],
};

// ---------- Webpagina's ----------
function doGet(e) {
  const pagina = 'Oefenpad'; // één link voor leerlingen en leerkrachten
  return HtmlService.createHtmlOutputFromFile(pagina)
    .setTitle('Oefenpad')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ---------- Spreadsheet-hulpfuncties ----------
// Een ontbrekend tabblad wordt aangemaakt met de juiste kopregel (bv. Gedeeld na een update).
function sheet_(naam) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const s = ss.getSheetByName(naam);
  if (s) return s;
  if (!TABBLADEN[naam]) throw new Error('Tabblad ontbreekt: ' + naam + '.');
  return maakTabblad_(ss, naam);
}

function maakTabblad_(ss, naam) {
  let s = ss.getSheetByName(naam);
  if (!s) s = ss.insertSheet(naam);
  if (s.getLastRow() === 0) s.appendRow(TABBLADEN[naam]);
  return s;
}

function leesTabel_(naam) {
  const v = sheet_(naam).getDataRange().getValues();
  if (v.length < 2) return [];
  const h = v[0];
  return v.slice(1)
    .filter(function (r) { return r[0] !== ''; })
    .map(function (r) {
      const obj = {};
      h.forEach(function (k, i) { obj[k] = r[i]; });
      return obj;
    });
}

function voegToe_(naam, obj) {
  const h = TABBLADEN[naam];
  sheet_(naam).appendRow(h.map(function (k) { return obj[k] === undefined ? '' : obj[k]; }));
}

// Verwijdert rijen waarvoor pred(rij) waar is. Leest het tabblad één keer en schrijft de rijen die
// blijven in één keer terug: rij per rij verwijderen duurt minuten bij een klas met veel pogingen.
function verwijderWaar_(naam, pred) {
  const s = sheet_(naam);
  const v = s.getDataRange().getValues();
  if (v.length < 2) return;
  const h = v[0];
  const blijven = v.slice(1).filter(function (r) {
    const obj = {};
    h.forEach(function (k, j) { obj[k] = r[j]; });
    return !pred(obj);
  });
  if (blijven.length === v.length - 1) return;
  s.getRange(2, 1, v.length - 1, h.length).clearContent();
  if (blijven.length) s.getRange(2, 1, blijven.length, h.length).setValues(blijven);
}

// Past rijen aan waarvoor pred waar is.
function updateWaar_(naam, pred, patch) {
  const s = sheet_(naam);
  const v = s.getDataRange().getValues();
  const h = v[0];
  for (let i = 1; i < v.length; i++) {
    const obj = {};
    h.forEach(function (k, j) { obj[k] = v[i][j]; });
    if (pred(obj)) {
      Object.keys(patch).forEach(function (k) {
        s.getRange(i + 1, h.indexOf(k) + 1).setValue(patch[k]);
      });
    }
  }
}

// ---------- Hashing en codes ----------
// Het resultaat begint met "x", zodat Sheets het niet als getal omzet.
function hashCode_(salt, code) {
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, salt + ':' + code);
  return 'x' + bytes.map(function (b) { return ((b + 256) % 256).toString(16).padStart(2, '0'); }).join('');
}

// ---------- Sessies en inlogbeveiliging ----------
function maakSessie_(rol, id, wijzig) {
  const token = Utilities.getUuid();
  CacheService.getScriptCache().put(
    's|' + token,
    JSON.stringify({ rol: rol, id: String(id), wijzig: !!wijzig }),
    SESSIE_SEC
  );
  return token;
}

// Geeft de sessie terug. Met wijzig: true moet de leerkracht eerst haar wachtwoord wijzigen.
function eisSessie_(token, rol) {
  const p = eisSessieAlleen_(token, rol);
  if (p.wijzig) throw new Error('Wijzig eerst je wachtwoord.');
  return p;
}

function eisSessieAlleen_(token, rol) {
  const v = token ? CacheService.getScriptCache().get('s|' + token) : null;
  if (!v) throw new Error('Niet ingelogd.');
  const p = JSON.parse(v);
  if (p.rol !== rol) throw new Error('Niet ingelogd.');
  return p;
}

function teller_(sleutel) {
  return Number(CacheService.getScriptCache().get('fail|' + sleutel) || 0);
}

function mislukt_(sleutel) {
  CacheService.getScriptCache().put('fail|' + sleutel, String(teller_(sleutel) + 1), LOGIN_SEC);
}

function gelukt_(sleutel) {
  CacheService.getScriptCache().remove('fail|' + sleutel);
}

// ---------- Toegang tot klassen ----------
// Elke klas heeft één eigenaar. De eigenaar kan de klas delen met collega's. Een collega ziet de
// voortgang en de fouten, kan leerlingen toevoegen en codes resetten. Alleen de eigenaar kan
// leerlingen of de klas verwijderen en beslissen met wie de klas gedeeld is.
function rolInKlas_(s, klas, gedeeld) {
  if (!klas) return null;
  if (String(klas.leerkracht_id) === String(s.id)) return 'eigenaar';
  const collega = gedeeld.some(function (g) {
    return String(g.klas_id) === String(klas.id) && String(g.leerkracht_id) === String(s.id);
  });
  return collega ? 'collega' : null;
}

function eisKlas_(s, klasId, alleenEigenaar) {
  const klas = leesTabel_('Klassen').find(function (k) { return String(k.id) === String(klasId); });
  const rol = rolInKlas_(s, klas, leesTabel_('Gedeeld'));
  if (!rol) throw new Error('Klas niet gevonden.');
  if (alleenEigenaar && rol !== 'eigenaar') throw new Error('Alleen de eigenaar van de klas kan dit.');
  return klas;
}

function eisLeerling_(s, leerlingId, alleenEigenaar) {
  const l = leesTabel_('Leerlingen').find(function (x) { return String(x.id) === String(leerlingId); });
  if (!l) throw new Error('Leerling niet gevonden.');
  eisKlas_(s, l.klas_id, alleenEigenaar);
  return l;
}

function eigenKlasIds_(s) {
  return leesTabel_('Klassen')
    .filter(function (k) { return String(k.leerkracht_id) === String(s.id); })
    .map(function (k) { return String(k.id); });
}

// ---------- Leerling ----------
function klassen() {
  return leesTabel_('Klassen')
    .map(function (k) { return { id: String(k.id), naam: String(k.naam) }; })
    .sort(function (a, b) { return a.naam.localeCompare(b.naam); });
}

// Elke leerling heeft een eigen pincode. Bij de eerste aanmelding kiest de leerling die zelf:
// eerst de code, daarna dezelfde code nog eens bij herhaal. Zo kan niemand onder een andere naam oefenen
// zonder de pincode van die leerling.
// Geeft meteen de eerste stap mee, zodat de pagina niet nog een keer moet wachten.
function loginLeerling(klasId, naam, code, herhaal) {
  const n = String(naam || '').trim();
  const sleutel = 'l|' + klasId + '|' + n.toLowerCase();
  if (teller_(sleutel) >= LOGIN_MAX) {
    throw new Error('Te veel mislukte pogingen. Vraag je leerkracht om hulp.');
  }
  if (!/^\d{4}$/.test(String(code || ''))) throw new Error('Een pincode bestaat uit precies 4 cijfers.');

  const l = leesTabel_('Leerlingen').find(function (x) {
    return String(x.klas_id) === String(klasId) && String(x.naam).toLowerCase() === n.toLowerCase();
  });
  if (!l) {
    mislukt_(sleutel);
    throw new Error('Naam of code klopt niet.');
  }

  if (!l.hash) {
    // Nog geen code ingesteld: vraag de herhaling, en sla de code pas op als die klopt.
    if (herhaal === undefined || herhaal === null) return { kiesCode: true };
    if (String(herhaal) !== String(code)) throw new Error('De twee codes zijn niet hetzelfde. Probeer opnieuw.');
    const salt = Utilities.getUuid();
    updateWaar_('Leerlingen', function (x) { return String(x.id) === String(l.id); },
      { salt: salt, hash: hashCode_(salt, String(code)) });
  } else if (hashCode_(l.salt, String(code)) !== l.hash) {
    mislukt_(sleutel);
    throw new Error('Naam of code klopt niet.');
  }
  gelukt_(sleutel);
  const eigen = pogingenVan_(l.id);
  return {
    token: maakSessie_('leerling', l.id, false),
    naam: String(l.naam),
    staat: staat_(l.id, eigen, gedaanUit_(eigen), false),
  };
}

// Actieve minuten sinds maandag. Telt alleen de tijd met echte activiteit (zie Oefenpad.html).
function maandagMs_() {
  const nu = new Date();
  return new Date(nu.getFullYear(), nu.getMonth(), nu.getDate() - ((nu.getDay() + 6) % 7)).getTime();
}

function weekMin_(pogingen) {
  const ma = maandagMs_();
  const sec = pogingen.reduce(function (som, p) {
    return Number(p.tijd) >= ma ? som + (Number(p.seconden) || 0) : som;
  }, 0);
  return Math.round(sec / 60);
}

function pogingenVan_(leerlingId) {
  return leesTabel_('Pogingen').filter(function (p) { return String(p.leerling_id) === String(leerlingId); });
}

function gedaanUit_(pogingen) {
  const set = new Set();
  pogingen.forEach(function (p) {
    // juist = 1 (volledig goed), 0.5 (deels goed) of 0. Alleen 1 telt als gedaan.
    if (Number(p.juist) === 1) set.add(p.module + '/' + p.stap);
  });
  return set;
}

// "Bekeken" onthoudt dat de leerling een stap te zien kreeg; pas dan mag die stap beantwoord worden.
// De cache spaart het inlezen van het hele tabblad bij bijna elke controle.
function bekekenSleutel_(leerlingId, moduleId, stap) {
  return 'b|' + leerlingId + '|' + moduleId + '|' + stap;
}

function isBekeken_(leerlingId, moduleId, stap) {
  const cache = CacheService.getScriptCache();
  const sleutel = bekekenSleutel_(leerlingId, moduleId, stap);
  if (cache.get(sleutel)) return true;
  const gezien = leesTabel_('Bekeken').some(function (b) {
    return String(b.leerling_id) === String(leerlingId) && String(b.module) === moduleId && String(b.stap) === stap;
  });
  if (gezien) cache.put(sleutel, '1', SESSIE_SEC);
  return gezien;
}

// nieuw: de stap is net vrijgekomen en kan dus nog niet bekeken zijn, zodat we niet hoeven te zoeken.
function markeerBekeken_(leerlingId, moduleId, stap, nieuw) {
  if (!nieuw && isBekeken_(leerlingId, moduleId, stap)) return;
  voegToe_('Bekeken', { leerling_id: leerlingId, module: moduleId, stap: stap, tijd: new Date().getTime() });
  CacheService.getScriptCache().put(bekekenSleutel_(leerlingId, moduleId, stap), '1', SESSIE_SEC);
}

// De stap die nu aan de beurt is, met de voortgang van de leerling.
function staat_(leerlingId, eigen, gedaan, nieuw) {
  const totaal = totaal_();
  const voortgang = { gedaan: Math.min(gedaan.size, totaal), totaal: totaal };
  const week = { min: weekMin_(eigen), doel: WEEKDOEL_MIN };
  const huidig = bepaalHuidig_(gedaan);
  if (!huidig) return { klaar: true, voortgang: voortgang, week: week };

  markeerBekeken_(String(leerlingId), huidig.mod.id, huidig.sleutel, nieuw);

  // Uitleg: de theorie van de module bij het begin van de module, de uitleg van de oefening bij de eerste stap.
  const stapIndex = huidig.oef.stappen.indexOf(huidig.stap);
  const oefIndex = huidig.mod.oefeningen.indexOf(huidig.oef);
  const theorie = (oefIndex === 0 && stapIndex === 0) ? (huidig.mod.theorie || null) : null;
  const uitleg = stapIndex === 0 ? (huidig.oef.uitleg || null) : null;

  // Stippen voor de stappen van deze oefening: ok (klaar), cur (nu), leeg (nog niet).
  const oefStappen = huidig.oef.stappen.map(function (st) {
    const sl = huidig.mod.id + '/' + huidig.oef.id + '.' + st.id;
    if (gedaan.has(sl)) return 'ok';
    return sl === huidig.mod.id + '/' + huidig.sleutel ? 'cur' : '';
  });

  return {
    klaar: false,
    theorie: theorie,
    uitleg: uitleg,
    module: { id: huidig.mod.id, titel: huidig.mod.titel, nr: MODULES.indexOf(huidig.mod) + 1, aantal: MODULES.length },
    oefening: { titel: huidig.oef.titel, nr: oefIndex + 1, aantal: huidig.mod.oefeningen.length, stappen: oefStappen },
    week: week,
    stap: {
      sleutel: huidig.sleutel,
      type: huidig.stap.type,
      prompt: huidig.stap.prompt,
      opties: huidig.stap.opties || null,
      velden: huidig.stap.velden ? huidig.stap.velden.map(function (v) { return v.label; }) : null,
    },
    voortgang: voortgang,
  };
}

function voortgang(token) {
  const s = eisSessie_(token, 'leerling');
  const eigen = pogingenVan_(s.id);
  return staat_(s.id, eigen, gedaanUit_(eigen), false);
}

// actief = seconden met echte activiteit sinds de vorige poging op deze stap (door de pagina gemeten).
// Bij een juist antwoord zit de volgende stap er meteen bij.
function antwoord(token, moduleId, stapSleutel, ingevoerd, actief) {
  const s = eisSessie_(token, 'leerling');
  const eigen = pogingenVan_(s.id);
  const gedaan = gedaanUit_(eigen);
  const huidig = bepaalHuidig_(gedaan);
  if (!huidig || huidig.mod.id !== moduleId || huidig.sleutel !== stapSleutel) {
    throw new Error('Deze stap is niet aan de beurt. Ververs de pagina.');
  }
  if (!isBekeken_(s.id, moduleId, stapSleutel)) throw new Error('Ververs de pagina en probeer opnieuw.');

  const score = controleer_(huidig.stap, ingevoerd); // 1, 0.5 of 0
  const poging = {
    tijd: new Date().getTime(),
    leerling_id: s.id,
    module: moduleId,
    stap: stapSleutel,
    antwoord: JSON.stringify(ingevoerd === undefined ? null : ingevoerd).slice(0, 200),
    juist: score,
    seconden: Math.min(300, Math.max(0, Math.round(Number(actief) || 0))),
  };
  voegToe_('Pogingen', poging);
  if (score !== 1) return { juist: false, score: score, hint: huidig.stap.hint };

  eigen.push(poging);
  gedaan.add(moduleId + '/' + stapSleutel);
  return { juist: true, score: 1, volgende: staat_(s.id, eigen, gedaan, true) };
}

// ---------- Leerkracht: inloggen en eigen wachtwoord ----------
function loginLeerkracht(gebruikersnaam, wachtwoord) {
  const n = String(gebruikersnaam || '').trim().toLowerCase();
  const sleutel = 'lk|' + n;
  if (teller_(sleutel) >= LOGIN_MAX) throw new Error('Te veel mislukte pogingen. Vraag hulp aan de beheerder.');

  const lk = leesTabel_('Leerkrachten').find(function (x) {
    return String(x.gebruikersnaam).toLowerCase() === n;
  });
  const geldig = !!lk && hashCode_(lk.salt, String(wachtwoord || '')) === lk.hash;
  if (!geldig) {
    mislukt_(sleutel);
    throw new Error('Gebruikersnaam of wachtwoord klopt niet.');
  }
  gelukt_(sleutel);
  const moetWijzigen = lk.moet_wijzigen === true;
  return { token: maakSessie_('leerkracht', lk.id, moetWijzigen), moetWijzigen: moetWijzigen };
}

// Eigen wachtwoord wijzigen. Verplicht na een tijdelijk wachtwoord van de beheerder.
function wijzigEigenWachtwoord(token, huidig, nieuw) {
  const s = eisSessieAlleen_(token, 'leerkracht');
  const sleutel = 'wijzig|' + s.id;
  if (teller_(sleutel) >= LOGIN_MAX) throw new Error('Te veel mislukte pogingen. Vraag hulp aan de beheerder.');

  const lk = leesTabel_('Leerkrachten').find(function (x) { return String(x.id) === String(s.id); });
  if (!lk) throw new Error('Niet ingelogd.');
  if (hashCode_(lk.salt, String(huidig || '')) !== lk.hash) {
    mislukt_(sleutel);
    throw new Error('Het huidige wachtwoord klopt niet.');
  }
  if (String(nieuw || '').length < 8) throw new Error('Het nieuwe wachtwoord moet minstens 8 tekens hebben.');

  const salt = Utilities.getUuid();
  updateWaar_('Leerkrachten', function (x) { return String(x.id) === String(s.id); },
    { salt: salt, hash: hashCode_(salt, String(nieuw)), moet_wijzigen: false });
  gelukt_(sleutel);
  CacheService.getScriptCache().put('s|' + token,
    JSON.stringify({ rol: 'leerkracht', id: String(s.id), wijzig: false }), SESSIE_SEC);
  return { ok: true };
}

// ---------- Leerkracht: overzicht ----------
// Alles wat het dashboard toont, in één verzoek: de klassen waar de leerkracht bij kan en de voortgang
// van de gekozen klas (of de eerste klas). Elke wijziging geeft dit overzicht ook terug.
function lkOverzicht(token, klasId) {
  return overzicht_(eisSessie_(token, 'leerkracht'), klasId);
}

function overzicht_(s, klasId) {
  const klassenRijen = leesTabel_('Klassen');
  const gedeeld = leesTabel_('Gedeeld');
  const leerlingen = leesTabel_('Leerlingen');
  const naamVan = {};
  leesTabel_('Leerkrachten').forEach(function (lk) { naamVan[String(lk.id)] = String(lk.gebruikersnaam); });
  const aantal = {};
  leerlingen.forEach(function (l) { aantal[String(l.klas_id)] = (aantal[String(l.klas_id)] || 0) + 1; });

  const lijst = [];
  klassenRijen.forEach(function (k) {
    const rol = rolInKlas_(s, k, gedeeld);
    if (!rol) return;
    const id = String(k.id);
    lijst.push({
      id: id,
      naam: String(k.naam),
      aantal: aantal[id] || 0,
      eigenaar: rol === 'eigenaar',
      eigenaarNaam: naamVan[String(k.leerkracht_id)] || '?',
      gedeeldMet: gedeeld
        .filter(function (g) { return String(g.klas_id) === id; })
        .map(function (g) { return { id: String(g.leerkracht_id), naam: naamVan[String(g.leerkracht_id)] || '?' }; }),
    });
  });
  // Eerst de eigen klassen, dan de gedeelde, telkens alfabetisch.
  lijst.sort(function (a, b) { return (b.eigenaar - a.eigenaar) || a.naam.localeCompare(b.naam); });

  const gekozen = lijst.find(function (k) { return k.id === String(klasId); }) || lijst[0] || null;
  const stappen = alleStappen_();
  return {
    klassen: lijst,
    klasId: gekozen ? gekozen.id : '',
    doel: WEEKDOEL_MIN,
    stappen: stappen.map(function (st) { return st.label; }),
    rijen: gekozen ? voortgangRijen_(gekozen.id, leerlingen, stappen) : [],
  };
}

// Alle stappen van alle modules in volgorde, voor de heatmap van de leerkracht.
function alleStappen_() {
  const lijst = [];
  MODULES.forEach(function (mod) {
    mod.oefeningen.forEach(function (oef) {
      oef.stappen.forEach(function (stap) {
        lijst.push({ sleutel: mod.id + '/' + oef.id + '.' + stap.id, label: mod.titel + ' · ' + oef.titel + ' · ' + stap.prompt });
      });
    });
  });
  return lijst;
}

function voortgangRijen_(klasId, leerlingen, stappen) {
  const vanKlas = leerlingen
    .filter(function (l) { return String(l.klas_id) === String(klasId); })
    .sort(function (a, b) { return String(a.naam).localeCompare(String(b.naam)); });
  if (!vanKlas.length) return [];

  // Pogingen één keer doorlopen en per leerling verdelen.
  const perLeerling = {};
  vanKlas.forEach(function (l) { perLeerling[String(l.id)] = []; });
  leesTabel_('Pogingen').forEach(function (p) {
    const eigen = perLeerling[String(p.leerling_id)];
    if (eigen) eigen.push(p);
  });
  const totaal = totaal_();

  return vanKlas.map(function (l) {
    const id = String(l.id);
    const eigen = perLeerling[id];
    const gedaan = new Set();
    const flags = {}; // per stap: heeft deels juist / fout gehad
    let laatste = 0, seconden = 0;
    eigen.forEach(function (p) {
      const sleutel = p.module + '/' + p.stap;
      laatste = Math.max(laatste, Number(p.tijd));
      seconden += Number(p.seconden) || 0;
      const score = Number(p.juist);
      flags[sleutel] = flags[sleutel] || { half: false, no: false };
      if (score === 1) gedaan.add(sleutel);
      else if (score === 0.5) flags[sleutel].half = true;
      else flags[sleutel].no = true;
    });
    const huidig = bepaalHuidig_(gedaan);
    const huidigSleutel = huidig ? huidig.mod.id + '/' + huidig.sleutel : '';
    const heat = stappen.map(function (st) {
      if (gedaan.has(st.sleutel)) return 'ok';
      if (st.sleutel === huidigSleutel) return 'cur';
      if (flags[st.sleutel] && flags[st.sleutel].half) return 'half';
      if (flags[st.sleutel] && flags[st.sleutel].no) return 'no';
      return '';
    });
    return {
      id: id,
      naam: String(l.naam),
      heeftCode: !!l.hash,
      gedaan: Math.min(gedaan.size, totaal),
      totaal: totaal,
      minuten: Math.round(seconden / 60),
      weekMin: weekMin_(eigen),
      laatste: laatste ? new Date(laatste).toLocaleString('nl-BE') : '—',
      huidig: huidig ? huidig.oef.titel + ' – ' + huidig.stap.prompt : 'klaar',
      heat: heat,
    };
  });
}

// ---------- Leerkracht: klassen, leerlingen en delen ----------
function voegKlasToe(token, naam) {
  const s = eisSessie_(token, 'leerkracht');
  const n = String(naam || '').trim();
  if (!n || n.length > 40) throw new Error('Geef een klasnaam (max. 40 tekens).');
  const id = Utilities.getUuid();
  voegToe_('Klassen', { id: id, naam: n, leerkracht_id: s.id });
  return overzicht_(s, id);
}

function verwijderKlas(token, klasId) {
  const s = eisSessie_(token, 'leerkracht');
  eisKlas_(s, klasId, true);
  verwijderKlassen_([String(klasId)]);
  return overzicht_(s, '');
}

// Wist klassen met hun leerlingen, resultaten en delingen. Elk tabblad wordt één keer herschreven.
function verwijderKlassen_(klasIds) {
  if (!klasIds.length) return;
  const klasSet = new Set(klasIds.map(String));
  const leerlingSet = new Set(leesTabel_('Leerlingen')
    .filter(function (l) { return klasSet.has(String(l.klas_id)); })
    .map(function (l) { return String(l.id); }));
  verwijderWaar_('Pogingen', function (p) { return leerlingSet.has(String(p.leerling_id)); });
  verwijderWaar_('Bekeken', function (b) { return leerlingSet.has(String(b.leerling_id)); });
  verwijderWaar_('Leerlingen', function (l) { return klasSet.has(String(l.klas_id)); });
  verwijderWaar_('Gedeeld', function (g) { return klasSet.has(String(g.klas_id)); });
  verwijderWaar_('Klassen', function (k) { return klasSet.has(String(k.id)); });
}

function voegLeerlingToe(token, klasId, naam) {
  const s = eisSessie_(token, 'leerkracht');
  eisKlas_(s, klasId, false);
  const n = String(naam || '').trim();
  if (!GELDIGE_NAAM.test(n)) throw new Error('Gebruik een voornaam, eventueel met initiaal, bv. "Lotte V.".');
  const dubbel = leesTabel_('Leerlingen').some(function (l) {
    return String(l.klas_id) === String(klasId) && String(l.naam).toLowerCase() === n.toLowerCase();
  });
  if (dubbel) throw new Error('Deze leerling staat al in deze klas.');
  // Geen code: de leerling kiest er zelf een bij de eerste aanmelding.
  voegToe_('Leerlingen', { id: Utilities.getUuid(), klas_id: klasId, naam: n, salt: '', hash: '' });
  return { naam: n, overzicht: overzicht_(s, klasId) };
}

// Reset de pincode. De leerling kiest bij de volgende aanmelding opnieuw een code.
function nieuweCode(token, leerlingId) {
  const s = eisSessie_(token, 'leerkracht');
  const l = eisLeerling_(s, leerlingId, false);
  updateWaar_('Leerlingen', function (x) { return String(x.id) === String(leerlingId); }, { salt: '', hash: '' });
  return overzicht_(s, l.klas_id);
}

function verwijderLeerling(token, leerlingId) {
  const s = eisSessie_(token, 'leerkracht');
  const l = eisLeerling_(s, leerlingId, true);
  verwijderWaar_('Pogingen', function (p) { return String(p.leerling_id) === String(leerlingId); });
  verwijderWaar_('Bekeken', function (b) { return String(b.leerling_id) === String(leerlingId); });
  verwijderWaar_('Leerlingen', function (x) { return String(x.id) === String(leerlingId); });
  return overzicht_(s, l.klas_id);
}

// Deel een eigen klas met een collega (op gebruikersnaam).
function deelKlas(token, klasId, gebruikersnaam) {
  const s = eisSessie_(token, 'leerkracht');
  eisKlas_(s, klasId, true);
  const n = String(gebruikersnaam || '').trim().toLowerCase();
  const lk = leesTabel_('Leerkrachten').find(function (x) { return String(x.gebruikersnaam).toLowerCase() === n; });
  if (!lk) throw new Error('Er is geen leerkracht met deze gebruikersnaam.');
  if (String(lk.id) === String(s.id)) throw new Error('Dit is je eigen gebruikersnaam.');
  const al = leesTabel_('Gedeeld').some(function (g) {
    return String(g.klas_id) === String(klasId) && String(g.leerkracht_id) === String(lk.id);
  });
  if (!al) voegToe_('Gedeeld', { klas_id: String(klasId), leerkracht_id: String(lk.id) });
  return overzicht_(s, klasId);
}

function stopDelen(token, klasId, leerkrachtId) {
  const s = eisSessie_(token, 'leerkracht');
  eisKlas_(s, klasId, true);
  verwijderWaar_('Gedeeld', function (g) {
    return String(g.klas_id) === String(klasId) && String(g.leerkracht_id) === String(leerkrachtId);
  });
  return overzicht_(s, klasId);
}

function weergaveAntwoord_(raw) {
  try {
    const v = JSON.parse(raw);
    if (Array.isArray(v)) return v.join(' / ') || '—';
    return (v === null || v === '') ? '—' : String(v);
  } catch (e) {
    return raw || '—';
  }
}

function foutenKlas(token, klasId, moduleId) {
  const s = eisSessie_(token, 'leerkracht');
  eisKlas_(s, klasId, false);
  const mod = getModule_(moduleId) || MODULES[0];
  const leerlingIds = new Set(leesTabel_('Leerlingen')
    .filter(function (l) { return String(l.klas_id) === String(klasId); })
    .map(function (l) { return String(l.id); }));
  const pogingen = leesTabel_('Pogingen').filter(function (p) {
    return leerlingIds.has(String(p.leerling_id)) && String(p.module) === mod.id;
  });

  const stappen = [];
  mod.oefeningen.forEach(function (oef) {
    oef.stappen.forEach(function (stap) {
      const sleutel = oef.id + '.' + stap.id;
      const eigen = pogingen.filter(function (p) { return String(p.stap) === sleutel; });
      const fouten = eigen.filter(function (p) { return Number(p.juist) < 1; });
      const telling = {};
      fouten.forEach(function (f) {
        const tekst = weergaveAntwoord_(f.antwoord);
        telling[tekst] = (telling[tekst] || 0) + 1;
      });
      const veelvoorkomend = Object.keys(telling)
        .map(function (a) { return { antwoord: a, aantal: telling[a] }; })
        .sort(function (a, b) { return b.aantal - a.aantal; })
        .slice(0, 3);
      stappen.push({
        oefening: oef.titel,
        vraag: stap.prompt,
        pogingen: eigen.length,
        fout: fouten.length,
        veelvoorkomend: veelvoorkomend,
      });
    });
  });
  return { module: mod.id, stappen: stappen };
}

// Wist alleen de eigen klassen van deze leerkracht (ook als ze gedeeld zijn).
function wisAlles(token, bevestig) {
  const s = eisSessie_(token, 'leerkracht');
  if (bevestig !== 'WISSEN') throw new Error('Typ WISSEN ter bevestiging.');
  verwijderKlassen_(eigenKlasIds_(s));
  return overzicht_(s, '');
}

// ---------- Jaarwissel (alle leerlingen van alle leerkrachten) ----------
// Wist alle leerlinggegevens. Leerkrachtaccounts blijven bestaan.
function wisLeerlingdata_() {
  ['Pogingen', 'Bekeken', 'Leerlingen', 'Gedeeld', 'Klassen'].forEach(function (naam) {
    const s = sheet_(naam);
    const laatsteRij = s.getLastRow();
    if (laatsteRij > 1) s.deleteRows(2, laatsteRij - 1);
  });
}

// Wordt dagelijks uitgevoerd door de trigger, maar wist alleen op 1 september.
function jaarwissel() {
  const nu = new Date();
  if (nu.getMonth() !== 8 || nu.getDate() !== 1) return; // 8 = september (0-gebaseerd)
  wisLeerlingdata_();
}

// ---------- Beheer door de beheerder (via de editor) ----------

// Voeg een leerkracht toe met een tijdelijk wachtwoord. Bij de eerste login moet ze het wijzigen.
function voegLeerkrachtToe_(gebruikersnaam, tijdelijkWachtwoord) {
  const n = String(gebruikersnaam).trim();
  if (!n) throw new Error('Geef een gebruikersnaam.');
  if (String(tijdelijkWachtwoord).length < 8) throw new Error('Het tijdelijke wachtwoord moet minstens 8 tekens hebben.');
  const bestaat = leesTabel_('Leerkrachten').some(function (x) {
    return String(x.gebruikersnaam).toLowerCase() === n.toLowerCase();
  });
  if (bestaat) throw new Error('Deze gebruikersnaam bestaat al.');
  const salt = Utilities.getUuid();
  voegToe_('Leerkrachten', {
    id: Utilities.getUuid(),
    gebruikersnaam: n,
    salt: salt,
    hash: hashCode_(salt, String(tijdelijkWachtwoord)),
    moet_wijzigen: true,
  });
  Logger.log('Leerkracht toegevoegd: ' + n + ' (moet wachtwoord wijzigen bij eerste login)');
}

// Zet een tijdelijk wachtwoord voor een leerkracht die het vergeten is.
// Bij de volgende login moet ze een eigen wachtwoord kiezen.
function herstelWachtwoord_(gebruikersnaam, tijdelijkWachtwoord) {
  const n = String(gebruikersnaam).trim().toLowerCase();
  const bestaat = leesTabel_('Leerkrachten').some(function (x) {
    return String(x.gebruikersnaam).toLowerCase() === n;
  });
  if (!bestaat) throw new Error('Gebruikersnaam niet gevonden.');
  if (String(tijdelijkWachtwoord).length < 8) throw new Error('Het tijdelijke wachtwoord moet minstens 8 tekens hebben.');
  const salt = Utilities.getUuid();
  updateWaar_('Leerkrachten', function (x) { return String(x.gebruikersnaam).toLowerCase() === n; },
    { salt: salt, hash: hashCode_(salt, String(tijdelijkWachtwoord)), moet_wijzigen: true });
  Logger.log('Tijdelijk wachtwoord ingesteld voor ' + n);
}

// Voeg de leerkrachten toe en voer deze functie één keer uit.
// Daarna het wachtwoord uit de code halen. Bij de eerste aanmelding kiest elke leerkracht zelf een eigen wachtwoord.
function voorbeeldLeerkracht() {
  voegLeerkrachtToe_('geert.degrave', 'ww12345678');
  voegLeerkrachtToe_('linda.nieman', 'ww12345678');
}

// Maakt de tabbladen met de juiste kopregels aan, als ze nog niet bestaan.
function setupSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  Object.keys(TABBLADEN).forEach(function (naam) { maakTabblad_(ss, naam); });
}

// Zet de dagelijkse controle in voor de jaarwissel. Eenmalig uitvoeren.
function installeerJaarwissel() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'jaarwissel') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('jaarwissel').timeBased().everyDays(1).atHour(4).create();
}
