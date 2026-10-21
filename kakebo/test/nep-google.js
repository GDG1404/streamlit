/*
 * Nagebootste Google Apps Script-omgeving voor tests en de demo.
 * Bewaart waarden, formules en getalnotaties per cel en gedraagt zich zoals
 * Google Sheets waar het voor Kakebo telt (rijen invoegen/verwijderen, grenzen,
 * datums uit opgemaakte cellen). Onbekende methodes bestaan bewust niet, zodat
 * een tikfout in het script hier meteen een fout geeft.
 */
(function (wortel) {
  'use strict';

  function isDatum(v) { return Object.prototype.toString.call(v) === '[object Date]'; }

  function kolomLetters(n) {
    var s = '';
    while (n > 0) { var m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); }
    return s;
  }
  function kolomNummer(letters) {
    var n = 0;
    for (var i = 0; i < letters.length; i++) n = n * 26 + (letters.charCodeAt(i) - 64);
    return n;
  }

  /** Controleert of een formule er syntactisch gezond uitziet. */
  function controleerFormule(f, waar) {
    if (typeof f !== 'string' || f.charAt(0) !== '=') throw new Error('Formule moet met = beginnen (' + waar + '): ' + f);
    var haakjes = 0, accolades = 0, inTekst = false;
    for (var i = 1; i < f.length; i++) {
      var c = f.charAt(i);
      if (c === '"') { inTekst = !inTekst; continue; }
      if (inTekst) continue;
      if (c === '(') haakjes++;
      if (c === ')') haakjes--;
      if (c === '{') accolades++;
      if (c === '}') accolades--;
      if (haakjes < 0 || accolades < 0) throw new Error('Haakjes kloppen niet (' + waar + '): ' + f);
      if (c === ';' && accolades === 0) throw new Error('Puntkomma buiten {} in formule (' + waar + '): ' + f);
    }
    if (inTekst || haakjes !== 0 || accolades !== 0) throw new Error('Formule niet afgesloten (' + waar + '): ' + f);
    var functies = f.replace(/"[^"]*"/g, '""').match(/[A-Z][A-Z0-9.]*(?=\()/g) || [];
    var bekend = ['SUM', 'SUMIFS', 'COUNTIFS', 'IF', 'IFERROR', 'AND', 'OR', 'MAX', 'MIN', 'DAY', 'EDATE', 'EOMONTH',
      'TODAY', 'WEEKDAY', 'INDEX', 'MATCH', 'FILTER', 'SORT', 'TEXT', 'ARRAYFORMULA', 'SPARKLINE', 'MOD'];
    functies.forEach(function (fn) {
      if (bekend.indexOf(fn) < 0) throw new Error('Onbekende functie ' + fn + ' (' + waar + '): ' + f);
    });
  }

  function maakNepGoogle(opties) {
    opties = opties || {};
    var tijdzone = opties.tijdzone || 'Europe/Brussels';
    var log = [];

    /* ---------- Tijd ---------- */
    function delen(datum, tz) {
      var f = new Intl.DateTimeFormat('en-US', {
        timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
      });
      var uit = {};
      f.formatToParts(datum).forEach(function (p) { uit[p.type] = p.value; });
      return uit;
    }
    function formatDate(datum, tz, patroon) {
      if (!isDatum(datum)) throw new Error('Utilities.formatDate verwacht een Date');
      if (typeof tz !== 'string' || !tz) throw new Error('Utilities.formatDate verwacht een tijdzone');
      var p = delen(datum, tz);
      return patroon.replace(/yyyy|MM|dd|HH|mm|ss/g, function (t) {
        return { yyyy: p.year, MM: p.month, dd: p.day, HH: p.hour, mm: p.minute, ss: p.second }[t];
      });
    }
    /** Middernacht in de tijdzone van de sheet voor een serieel datumgetal. */
    function datumUitSerieel(s, tz) {
      var utc = Date.UTC(1899, 11, 30) + Math.round(s * 86400000);
      var dagStart = Math.floor(s);
      var basis = Date.UTC(1899, 11, 30) + dagStart * 86400000;
      // Zoek het tijdstip waarop het in tz middernacht is op die kalenderdag.
      var p = delen(new Date(basis), tz);
      var lokaalAlsUtc = Date.UTC(Number(p.year), Number(p.month) - 1, Number(p.day), Number(p.hour), Number(p.minute), Number(p.second));
      var verschil = lokaalAlsUtc - basis;
      return new Date(utc - verschil);
    }
    function isDatumNotatie(fmt) { return !!fmt && /[dmyh]/i.test(fmt) && !/[#0]/.test(fmt.replace(/"[^"]*"/g, '')); }

    /* ---------- Bouwers met vaste methodes ---------- */
    function bouwer(naam, methodes, resultaat) {
      var obj = { _naam: naam, _stappen: [] };
      methodes.forEach(function (m) {
        obj[m] = function () { obj._stappen.push([m].concat(Array.prototype.slice.call(arguments))); return obj; };
      });
      obj.build = function () { return resultaat ? resultaat(obj) : { _type: naam, _stappen: obj._stappen }; };
      return obj;
    }

    /* ---------- Spreadsheet ---------- */
    var bladTeller = 0;
    var ss = {
      _bladen: [], _actief: null, _locale: opties.locale || 'en_US', _thema: null, _toasts: [],
      getId: function () { return 'nep-sheet-id'; },
      getUrl: function () { return 'https://docs.google.com/spreadsheets/d/nep-sheet-id/edit'; },
      getName: function () { return 'Kakebo'; },
      getSheets: function () { return ss._bladen.slice(); },
      getSheetByName: function (naam) {
        for (var i = 0; i < ss._bladen.length; i++) if (ss._bladen[i]._naam === naam) return ss._bladen[i];
        return null;
      },
      insertSheet: function (naam, index) {
        if (naam !== undefined && ss.getSheetByName(naam)) throw new Error('Er bestaat al een blad met de naam ' + naam);
        var b = maakBlad(naam || ('Blad' + (ss._bladen.length + 1)));
        if (typeof index === 'number') ss._bladen.splice(index, 0, b); else ss._bladen.push(b);
        ss._actief = b;
        return b;
      },
      deleteSheet: function (blad) {
        if (ss._bladen.length <= 1) throw new Error('Je kunt niet alle bladen verwijderen');
        ss._bladen = ss._bladen.filter(function (b) { return b !== blad; });
        if (ss._actief === blad) ss._actief = ss._bladen[0];
      },
      setActiveSheet: function (blad) { if (blad._verborgen) blad._verborgen = false; ss._actief = blad; return blad; },
      getActiveSheet: function () { return ss._actief; },
      moveActiveSheet: function (pos) {
        if (pos < 1 || pos > ss._bladen.length) throw new Error('Ongeldige positie ' + pos);
        var b = ss._actief;
        ss._bladen = ss._bladen.filter(function (x) { return x !== b; });
        ss._bladen.splice(pos - 1, 0, b);
      },
      getSpreadsheetTimeZone: function () { return tijdzone; },
      getSpreadsheetLocale: function () { return ss._locale; },
      setSpreadsheetLocale: function (l) { ss._locale = l; },
      getSpreadsheetTheme: function () { return ss._thema; },
      resetSpreadsheetTheme: function () {
        ss._thema = { _font: 'Arial', setFontFamily: function (f) { ss._thema._font = f; return ss._thema; }, getFontFamily: function () { return ss._thema._font; } };
        return ss._thema;
      },
      toast: function (bericht, titel) { ss._toasts.push([bericht, titel]); }
    };

    function maakBlad(naam) {
      bladTeller += 1;
      var blad = {
        _naam: naam, _id: bladTeller, _rijen: 1000, _kolommen: 26, _cellen: new Map(), _verborgen: false,
        _bandings: [], _filter: null, _beschermingen: [], _grafieken: [], _cf: [], _bevroren: [0, 0], _tab: null, _rasterUit: false,
        _breedtes: {}, _hoogtes: {}
      };
      function sleutel(r, k) { return r + ',' + k; }
      function cel(r, k, maak) {
        var s = sleutel(r, k);
        var c = blad._cellen.get(s);
        if (!c && maak) { c = { v: '', f: '', fmt: '' }; blad._cellen.set(s, c); }
        return c;
      }
      function verschuif(fn) {
        var nieuw = new Map();
        blad._cellen.forEach(function (c, s) {
          var d = s.split(',').map(Number);
          var doel = fn(d[0], d[1]);
          if (doel) nieuw.set(sleutel(doel[0], doel[1]), c);
        });
        blad._cellen = nieuw;
      }
      function check(n, wat) { if (typeof n !== 'number' || !isFinite(n) || n < 1 || Math.floor(n) !== n) throw new Error('Ongeldige ' + wat + ': ' + n); }

      blad.getName = function () { return blad._naam; };
      blad.setName = function (n) { blad._naam = n; return blad; };
      blad.getParent = function () { return ss; };
      blad.getSheetId = function () { return blad._id; };
      blad.getIndex = function () { return ss._bladen.indexOf(blad) + 1; };
      blad.activate = function () { ss._actief = blad; return blad; };
      blad.getMaxRows = function () { return blad._rijen; };
      blad.getMaxColumns = function () { return blad._kolommen; };
      blad.getLastRow = function () {
        var max = 0;
        blad._cellen.forEach(function (c, s) { if (c.v !== '' || c.f) { var r = Number(s.split(',')[0]); if (r > max) max = r; } });
        return max;
      };
      blad.getLastColumn = function () {
        var max = 0;
        blad._cellen.forEach(function (c, s) { if (c.v !== '' || c.f) { var k = Number(s.split(',')[1]); if (k > max) max = k; } });
        return max;
      };
      blad.insertRowsAfter = function (na, aantal) {
        check(na, 'rij'); check(aantal, 'aantal');
        if (na > blad._rijen) throw new Error('Rij buiten het blad');
        var bron = {};
        for (var k = 1; k <= blad._kolommen; k++) { var c = cel(na, k); if (c && c.fmt) bron[k] = c.fmt; }
        verschuif(function (r, k) { return [r > na ? r + aantal : r, k]; });
        blad._rijen += aantal;
        for (var r = na + 1; r <= na + aantal; r++) Object.keys(bron).forEach(function (k) { cel(r, Number(k), true).fmt = bron[k]; });
        return blad;
      };
      blad.insertRowBefore = function (voor) {
        check(voor, 'rij');
        if (voor > blad._rijen) throw new Error('Rij buiten het blad');
        verschuif(function (r, k) { return [r >= voor ? r + 1 : r, k]; });
        blad._rijen += 1;
        return blad;
      };
      blad.insertRowAfter = function (na) { return blad.insertRowsAfter(na, 1); };
      blad.deleteRow = function (r) { return blad.deleteRows(r, 1); };
      blad.deleteRows = function (r, aantal) {
        check(r, 'rij'); check(aantal, 'aantal');
        if (r + aantal - 1 > blad._rijen) throw new Error('Rijen buiten het blad');
        if (aantal >= blad._rijen - blad._bevroren[0]) throw new Error('Je kunt niet alle niet-bevroren rijen verwijderen');
        verschuif(function (rr, k) { if (rr >= r && rr < r + aantal) return null; return [rr >= r + aantal ? rr - aantal : rr, k]; });
        blad._rijen -= aantal;
        return blad;
      };
      blad.deleteColumns = function (k, aantal) {
        check(k, 'kolom'); check(aantal, 'aantal');
        if (k + aantal - 1 > blad._kolommen) throw new Error('Kolommen buiten het blad');
        verschuif(function (r, kk) { if (kk >= k && kk < k + aantal) return null; return [r, kk >= k + aantal ? kk - aantal : kk]; });
        blad._kolommen -= aantal;
        return blad;
      };
      blad.insertColumnsAfter = function (na, aantal) {
        check(na, 'kolom'); check(aantal, 'aantal');
        verschuif(function (r, k) { return [r, k > na ? k + aantal : k]; });
        blad._kolommen += aantal;
        return blad;
      };
      blad.setFrozenRows = function (n) { blad._bevroren[0] = n; return blad; };
      blad.setFrozenColumns = function (n) { blad._bevroren[1] = n; return blad; };
      blad.setColumnWidth = function (k, w) { check(k, 'kolom'); if (k > blad._kolommen) throw new Error('Kolom ' + k + ' bestaat niet'); blad._breedtes[k] = w; return blad; };
      blad.setColumnWidths = function (k, n, w) { for (var i = 0; i < n; i++) blad.setColumnWidth(k + i, w); return blad; };
      blad.setRowHeight = function (r, h) { check(r, 'rij'); if (r > blad._rijen) throw new Error('Rij ' + r + ' bestaat niet'); blad._hoogtes[r] = h; return blad; };
      blad.setRowHeights = function (r, n, h) { for (var i = 0; i < n; i++) blad.setRowHeight(r + i, h); return blad; };
      blad.setTabColor = function (c) { blad._tab = c; return blad; };
      blad.setHiddenGridlines = function (b) { blad._rasterUit = b; return blad; };
      blad.hideSheet = function () {
        var zichtbaar = ss._bladen.filter(function (b) { return !b._verborgen; });
        if (zichtbaar.length <= 1 && !blad._verborgen) throw new Error('Kan het enige zichtbare blad niet verbergen');
        blad._verborgen = true;
        return blad;
      };
      blad.showSheet = function () { blad._verborgen = false; return blad; };
      blad.isSheetHidden = function () { return blad._verborgen; };
      blad.getCharts = function () { return blad._grafieken.slice(); };
      blad.removeChart = function (g) { blad._grafieken = blad._grafieken.filter(function (x) { return x !== g; }); };
      blad.insertChart = function (g) { if (!g || g._type !== 'grafiek') throw new Error('Geen grafiek'); blad._grafieken.push(g); };
      blad.newChart = function () { return nieuweGrafiek(); };
      blad.getFilter = function () { return blad._filter; };
      blad.getBandings = function () { return blad._bandings.slice(); };
      blad.getProtections = function (type) {
        if (type !== 'RANGE' && type !== 'SHEET') throw new Error('Onbekend ProtectionType');
        return blad._beschermingen.filter(function (p) { return p._type === type; });
      };
      blad.setConditionalFormatRules = function (regels) {
        regels.forEach(function (r) { if (!r || r._type !== 'ConditionalFormatRule') throw new Error('Geen geldige opmaakregel'); });
        blad._cf = regels.slice();
      };
      blad.getConditionalFormatRules = function () { return blad._cf.slice(); };
      blad.clearConditionalFormatRules = function () { blad._cf = []; };
      blad.clear = function () { blad._cellen = new Map(); return blad; };
      blad.getDataRange = function () { return bereik(1, 1, Math.max(blad.getLastRow(), 1), Math.max(blad.getLastColumn(), 1)); };

      blad.getRange = function (a, b, c, d) {
        if (typeof a === 'string') {
          var m = a.match(/^([A-Z]+)(\d+)(?::([A-Z]+)(\d*))?$/);
          if (!m) throw new Error('Ongeldige A1-notatie: ' + a);
          var r1 = Number(m[2]), k1 = kolomNummer(m[1]);
          var k2 = m[3] ? kolomNummer(m[3]) : k1;
          var r2 = m[3] ? (m[4] ? Number(m[4]) : blad._rijen) : r1;
          return bereik(Math.min(r1, r2), Math.min(k1, k2), Math.abs(r2 - r1) + 1, Math.abs(k2 - k1) + 1);
        }
        return bereik(a, b, c === undefined ? 1 : c, d === undefined ? 1 : d);
      };

      function bereik(rij, kol, rijen, kolommen) {
        check(rij, 'rij'); check(kol, 'kolom'); check(rijen, 'aantal rijen'); check(kolommen, 'aantal kolommen');
        if (rij + rijen - 1 > blad._rijen || kol + kolommen - 1 > blad._kolommen) {
          throw new Error('Bereik buiten het blad "' + blad._naam + '": ' + kolomLetters(kol) + rij + ':' +
            kolomLetters(kol + kolommen - 1) + (rij + rijen - 1) + ' (blad is ' + blad._rijen + 'x' + blad._kolommen + ')');
        }
        var R = { _blad: blad };
        var zelf = function () { return R; };
        function elke(fn) { for (var r = 0; r < rijen; r++) for (var k = 0; k < kolommen; k++) fn(rij + r, kol + k, r, k); }
        function zetWaarde(r, k, v) {
          var c = cel(r, k, true);
          if (v === null || v === undefined || v === '') { c.v = ''; c.f = ''; return; }
          if (typeof v === 'string') {
            if (v.charAt(0) === '=') { controleerFormule(v, blad._naam + '!' + kolomLetters(k) + r); c.f = v; c.v = ''; return; }
            if (v.charAt(0) === "'") { c.v = v.slice(1); c.f = ''; return; }
            if (/^-?\d+([.,]\d+)?$/.test(v)) { c.v = Number(v.replace(',', '.')); c.f = ''; return; }
            c.v = v; c.f = '';
            return;
          }
          if (typeof v === 'number' || typeof v === 'boolean' || isDatum(v)) { c.v = v; c.f = ''; return; }
          throw new Error('Ongeldige celwaarde: ' + v);
        }
        function leesWaarde(r, k) {
          var c = cel(r, k);
          if (!c) return '';
          if (c.f) return c._uitkomst !== undefined ? c._uitkomst : '';
          if (typeof c.v === 'number' && isDatumNotatie(c.fmt)) return datumUitSerieel(c.v, tijdzone);
          return c.v;
        }
        function vorm(data, wat) {
          if (!Array.isArray(data) || data.length !== rijen) throw new Error(wat + ': aantal rijen (' + (data && data.length) + ') past niet bij het bereik (' + rijen + ')');
          data.forEach(function (rij2) {
            if (!Array.isArray(rij2) || rij2.length !== kolommen) throw new Error(wat + ': aantal kolommen past niet bij het bereik (' + kolommen + ')');
          });
        }
        R.getRow = function () { return rij; };
        R.getColumn = function () { return kol; };
        R.getNumRows = function () { return rijen; };
        R.getNumColumns = function () { return kolommen; };
        R.getLastRow = function () { return rij + rijen - 1; };
        R.getSheet = function () { return blad; };
        R.getA1Notation = function () { return kolomLetters(kol) + rij + (rijen > 1 || kolommen > 1 ? ':' + kolomLetters(kol + kolommen - 1) + (rij + rijen - 1) : ''); };
        R.getValues = function () { var uit = []; for (var r = 0; r < rijen; r++) { var rr = []; for (var k = 0; k < kolommen; k++) rr.push(leesWaarde(rij + r, kol + k)); uit.push(rr); } return uit; };
        R.getValue = function () { return leesWaarde(rij, kol); };
        R.getDisplayValue = function () { var v = leesWaarde(rij, kol); return v === '' ? '' : String(v); };
        R.setValues = function (data) { vorm(data, 'setValues'); elke(function (r, k, i, j) { zetWaarde(r, k, data[i][j]); }); return R; };
        R.setValue = function (v) { elke(function (r, k) { zetWaarde(r, k, v); }); return R; };
        R.getFormulas = function () { var uit = []; for (var r = 0; r < rijen; r++) { var rr = []; for (var k = 0; k < kolommen; k++) { var c = cel(rij + r, kol + k); rr.push(c && c.f ? c.f : ''); } uit.push(rr); } return uit; };
        R.getFormula = function () { var c = cel(rij, kol); return c && c.f ? c.f : ''; };
        R.setFormula = function (f) { controleerFormule(f, blad._naam + '!' + R.getA1Notation()); elke(function (r, k) { var c = cel(r, k, true); c.f = f; c.v = ''; }); return R; };
        R.setFormulas = function (data) {
          vorm(data, 'setFormulas');
          elke(function (r, k, i, j) { controleerFormule(data[i][j], blad._naam + '!' + kolomLetters(k) + r); var c = cel(r, k, true); c.f = data[i][j]; c.v = ''; });
          return R;
        };
        R.setNumberFormat = function (fmt) { if (typeof fmt !== 'string') throw new Error('Notatie moet tekst zijn'); elke(function (r, k) { cel(r, k, true).fmt = fmt; }); return R; };
        R.setNumberFormats = function (data) { vorm(data, 'setNumberFormats'); elke(function (r, k, i, j) { cel(r, k, true).fmt = data[i][j]; }); return R; };
        R.getNumberFormat = function () { var c = cel(rij, kol); return c && c.fmt ? c.fmt : 'General'; };
        R.clear = function () { elke(function (r, k) { blad._cellen.delete(sleutel(r, k)); }); return R; };
        R.clearContent = function () { elke(function (r, k) { var c = cel(r, k); if (c) { c.v = ''; c.f = ''; } }); return R; };
        R.clearDataValidations = zelf;
        R.clearNote = zelf;
        R.setNote = function (t) { if (typeof t !== 'string') throw new Error('Notitie moet tekst zijn'); return R; };
        R.merge = zelf;
        R.breakApart = zelf;
        ['setBackground', 'setFontColor', 'setFontWeight', 'setFontStyle', 'setHorizontalAlignment', 'setVerticalAlignment', 'setFontFamily'].forEach(function (m) {
          R[m] = function (x) { if (x !== null && typeof x !== 'string') throw new Error(m + ' verwacht tekst'); return R; };
        });
        R.setFontSize = function (n) { if (typeof n !== 'number') throw new Error('setFontSize verwacht een getal'); return R; };
        R.setWrap = function (b) { if (typeof b !== 'boolean') throw new Error('setWrap verwacht true/false'); return R; };
        R.setBorder = function () {
          if (arguments.length !== 6 && arguments.length !== 8) throw new Error('setBorder verwacht 6 of 8 argumenten');
          if (arguments.length === 8) {
            var stijlen = SpreadsheetApp.BorderStyle;
            var stijl = arguments[7];
            if (!Object.keys(stijlen).some(function (k) { return stijlen[k] === stijl; })) throw new Error('Onbekende BorderStyle');
          }
          return R;
        };
        R.setDataValidation = function (regel) { if (!regel || regel._type !== 'DataValidation') throw new Error('Geen geldige validatieregel'); return R; };
        R.setRichTextValue = function (t) {
          if (!t || t._type !== 'RichTextValue') throw new Error('Geen RichTextValue');
          var c = cel(rij, kol, true); c.v = t._tekst; c.f = '';
          return R;
        };
        R.applyRowBanding = function (thema, kop, voet) {
          var themas = SpreadsheetApp.BandingTheme;
          if (!Object.keys(themas).some(function (k) { return themas[k] === thema; })) throw new Error('Onbekend BandingTheme');
          if (typeof kop !== 'boolean' || typeof voet !== 'boolean') throw new Error('applyRowBanding verwacht true/false');
          blad._bandings.forEach(function (b) {
            if (!(b._r2 < rij || b._r1 > rij + rijen - 1 || b._k2 < kol || b._k1 > kol + kolommen - 1)) throw new Error('Bereik heeft al afwisselende kleuren');
          });
          var banding = { _r1: rij, _r2: rij + rijen - 1, _k1: kol, _k2: kol + kolommen - 1 };
          ['setHeaderRowColor', 'setFirstRowColor', 'setSecondRowColor', 'setFooterRowColor'].forEach(function (m) { banding[m] = function () { return banding; }; });
          banding.remove = function () { blad._bandings = blad._bandings.filter(function (x) { return x !== banding; }); };
          blad._bandings.push(banding);
          return banding;
        };
        R.createFilter = function () {
          if (blad._filter) throw new Error('Dit blad heeft al een filter');
          var f = { remove: function () { blad._filter = null; }, getRange: function () { return R; } };
          blad._filter = f;
          return f;
        };
        R.protect = function () {
          var p = { _type: 'RANGE', _omschrijving: '', _waarschuwing: false };
          p.setDescription = function (t) { p._omschrijving = t; return p; };
          p.getDescription = function () { return p._omschrijving; };
          p.setWarningOnly = function (b) { p._waarschuwing = b; return p; };
          p.canEdit = function () { return true; };
          p.remove = function () { blad._beschermingen = blad._beschermingen.filter(function (x) { return x !== p; }); };
          blad._beschermingen.push(p);
          return p;
        };
        return R;
      }
      return blad;
    }

    function nieuweGrafiek() {
      var b = { _bereiken: [], _opties: {}, _type: null };
      var basis = ['setChartType', 'setNumHeaders', 'setPosition', 'setOption'];
      basis.forEach(function (m) {
        b[m] = function (x, y) { if (m === 'setOption') b._opties[x] = y; return b; };
      });
      b.addRange = function (r) { if (!r || !r.getA1Notation) throw new Error('addRange verwacht een bereik'); b._bereiken.push(r); return b; };
      b.asColumnChart = function () {
        b._type = 'kolom';
        b.setStacked = function () { return b; };
        b.setColors = function (c) { if (!Array.isArray(c)) throw new Error('setColors verwacht een lijst'); return b; };
        b.setLegendPosition = function () { return b; };
        return b;
      };
      b.build = function () { return { _type: 'grafiek', _bereiken: b._bereiken, _opties: b._opties }; };
      return b;
    }

    /* ---------- Diensten ---------- */
    var ui = {
      _menus: [], _zijpanelen: [], _dialogen: [],
      createMenu: function (naam) {
        var menu = { naam: naam, items: [] };
        var m = {
          addItem: function (tekst, fn) { menu.items.push([tekst, fn]); return m; },
          addSeparator: function () { menu.items.push(['-']); return m; },
          addToUi: function () { ui._menus.push(menu); }
        };
        return m;
      },
      showSidebar: function (uit) { if (!uit || !uit._html) throw new Error('Geen HtmlOutput'); ui._zijpanelen.push(uit); },
      showModalDialog: function (uit, titel) { if (!uit || !uit._html || typeof titel !== 'string') throw new Error('Ongeldige dialoog'); ui._dialogen.push(uit); }
    };

    var SpreadsheetApp = {
      BorderStyle: { DOTTED: 1, DASHED: 2, SOLID: 3, SOLID_MEDIUM: 4, SOLID_THICK: 5, DOUBLE: 6 },
      BandingTheme: { LIGHT_GREY: 1, CYAN: 2, GREEN: 3 },
      ProtectionType: { RANGE: 'RANGE', SHEET: 'SHEET' },
      WrapStrategy: { WRAP: 1, OVERFLOW: 2, CLIP: 3 },
      getActiveSpreadsheet: function () { return opties.geenActieveSheet ? null : ss; },
      getActive: function () { return opties.geenActieveSheet ? null : ss; },
      openById: function (id) { if (id !== ss.getId()) throw new Error('Geen toegang'); return ss; },
      flush: function () {},
      getUi: function () { if (opties.geenUi) throw new Error('Cannot call SpreadsheetApp.getUi() from this context.'); return ui; },
      newDataValidation: function () {
        return bouwer('DataValidation', ['requireDate', 'requireValueInRange', 'requireValueInList', 'setAllowInvalid', 'setHelpText'],
          function (o) { return { _type: 'DataValidation', _stappen: o._stappen }; });
      },
      newConditionalFormatRule: function () {
        return bouwer('ConditionalFormatRule', ['whenNumberLessThan', 'whenTextEqualTo', 'whenTextStartsWith', 'setFontColor', 'setBackground', 'setBold', 'setRanges'],
          function (o) { return { _type: 'ConditionalFormatRule', _stappen: o._stappen }; });
      },
      newTextStyle: function () {
        return bouwer('TextStyle', ['setForegroundColor', 'setBold', 'setFontSize', 'setFontFamily', 'setItalic'],
          function (o) { return { _type: 'TextStyle', _stappen: o._stappen }; });
      },
      newRichTextValue: function () {
        var tekst = '';
        var b = {
          setText: function (t) { tekst = t; return b; },
          setTextStyle: function (start, eind, stijl) {
            if (!stijl || stijl._type !== 'TextStyle') throw new Error('setTextStyle verwacht een TextStyle');
            if (start < 0 || eind > tekst.length || start >= eind) throw new Error('setTextStyle: ongeldige posities ' + start + '-' + eind);
            return b;
          },
          build: function () { return { _type: 'RichTextValue', _tekst: tekst }; }
        };
        return b;
      }
    };

    function eigenschappen() {
      var opslag = {};
      return {
        getProperty: function (k) { return Object.prototype.hasOwnProperty.call(opslag, k) ? opslag[k] : null; },
        setProperty: function (k, v) { opslag[k] = String(v); return this; },
        deleteProperty: function (k) { delete opslag[k]; return this; },
        getProperties: function () { return Object.assign({}, opslag); }
      };
    }
    var scriptEigenschappen = eigenschappen();
    var gebruikersEigenschappen = {};
    var huidigeGebruiker = opties.gebruiker || 'geert';

    var nep = {
      _ss: ss, _ui: ui, _log: log,
      zetGebruiker: function (g) { huidigeGebruiker = g; },
      zetUrl: function (u) { opties.url = u; },
      SpreadsheetApp: SpreadsheetApp,
      PropertiesService: {
        getScriptProperties: function () { return scriptEigenschappen; },
        getUserProperties: function () {
          if (!gebruikersEigenschappen[huidigeGebruiker]) gebruikersEigenschappen[huidigeGebruiker] = eigenschappen();
          return gebruikersEigenschappen[huidigeGebruiker];
        }
      },
      LockService: {
        getScriptLock: function () {
          var vast = false;
          return {
            tryLock: function (ms) { if (typeof ms !== 'number') throw new Error('tryLock verwacht ms'); vast = true; return true; },
            waitLock: function () { vast = true; },
            releaseLock: function () { vast = false; },
            hasLock: function () { return vast; }
          };
        }
      },
      HtmlService: {
        createHtmlOutput: function (html) {
          if (typeof html !== 'string') throw new Error('createHtmlOutput verwacht tekst');
          var uit = { _html: html, _titel: '', _meta: [] };
          uit.setTitle = function (t) { uit._titel = t; return uit; };
          uit.addMetaTag = function (n, c) {
            var toegestaan = ['viewport', 'apple-mobile-web-app-capable', 'mobile-web-app-capable', 'google-site-verification'];
            if (toegestaan.indexOf(n) < 0) throw new Error('Meta-tag ' + n + ' is niet toegestaan');
            uit._meta.push([n, c]); return uit;
          };
          uit.setWidth = function () { return uit; };
          uit.setHeight = function () { return uit; };
          uit.getContent = function () { return uit._html; };
          return uit;
        }
      },
      ScriptApp: { getService: function () { return { getUrl: function () { return opties.url || null; } }; } },
      Session: {
        getScriptTimeZone: function () { return tijdzone; },
        getActiveUser: function () { return { getEmail: function () { return ''; } }; }
      },
      Utilities: {
        formatDate: formatDate,
        getUuid: function () { return 'uuid-' + Math.random().toString(16).slice(2); }
      },
      Charts: { ChartType: { COLUMN: 'COLUMN', PIE: 'PIE', BAR: 'BAR' }, Position: { BOTTOM: 'BOTTOM', RIGHT: 'RIGHT' } },
      Logger: { log: function () { log.push(Array.prototype.slice.call(arguments)); } }
    };
    ss.insertSheet('Blad1');
    return nep;
  }

  var uitvoer = { maakNepGoogle: maakNepGoogle, kolomLetters: kolomLetters, kolomNummer: kolomNummer, controleerFormule: controleerFormule };
  if (typeof module !== 'undefined' && module.exports) module.exports = uitvoer;
  else wortel.NepGoogle = uitvoer;
})(typeof window !== 'undefined' ? window : this);
