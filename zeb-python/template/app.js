(function () {
  "use strict";

  // =====================================================================
  // Gegevens
  // =====================================================================
  const NIV = DATA.niveaus;
  const LATER = DATA.later;
  const SPIEK = DATA.spiekbrief;
  const TEST = DATA.instaptest;
  const SPIEK_ID = Object.fromEntries(SPIEK.map((v) => [v.id, v]));
  const ALLE_OEF = [];
  NIV.forEach((n) =>
    n.oefeningen.forEach((o, i) => {
      o.niv = n.nr;
      o.idx = i;
      ALLE_OEF.push(o);
    })
  );
  const OEF_ID = Object.fromEntries(ALLE_OEF.map((o) => [o.id, o]));
  const SOORT = {
    voorspel: "Wat print dit?",
    keuze: "Meerkeuze",
    lees: "Wat doet dit programma?",
    fout: "Zoek de fout",
    aanvullen: "Vul aan",
    schrijf: "Schrijf op papier",
  };
  const DAGDOEL = 10;
  const $app = document.getElementById("app");

  // =====================================================================
  // Kleine hulpjes
  // =====================================================================
  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function inline(s) {
    // `code` eerst apart houden, dan **vet** en *schuin* in de rest.
    return String(s)
      .split(/(`[^`]+`)/g)
      .map((deel) => {
        if (deel.startsWith("`") && deel.endsWith("`") && deel.length > 1) {
          return "<code>" + esc(deel.slice(1, -1)) + "</code>";
        }
        return esc(deel)
          .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
          .replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s.,:;!?)]|$)/g, "$1<em>$2</em>");
      })
      .join("");
  }
  function md(tekst) {
    if (!tekst) return "";
    const blokken = String(tekst).split(/\n\s*\n/);
    return blokken
      .map((blok) => {
        const regels = blok.split("\n");
        let html = "";
        let lijst = null; // {tag, items}
        let para = [];
        const sluitPara = () => {
          if (para.length) html += "<p>" + inline(para.join(" ")) + "</p>";
          para = [];
        };
        const sluitLijst = () => {
          if (lijst) html += `<${lijst.tag}>` + lijst.items.map((i) => "<li>" + inline(i) + "</li>").join("") + `</${lijst.tag}>`;
          lijst = null;
        };
        for (const r of regels) {
          const ul = r.match(/^\s*-\s+(.*)$/);
          const ol = r.match(/^\s*\d+\.\s+(.*)$/);
          if (ul || ol) {
            sluitPara();
            const tag = ul ? "ul" : "ol";
            if (!lijst || lijst.tag !== tag) {
              sluitLijst();
              lijst = { tag, items: [] };
            }
            lijst.items.push((ul || ol)[1]);
          } else if (lijst && /^\s+\S/.test(r)) {
            lijst.items[lijst.items.length - 1] += " " + r.trim();
          } else {
            sluitLijst();
            if (r.trim()) para.push(r.trim());
          }
        }
        sluitPara();
        sluitLijst();
        return html;
      })
      .join("");
  }
  function maak(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }
  function vandaag(d) {
    const x = d || new Date();
    return x.getFullYear() + "-" + String(x.getMonth() + 1).padStart(2, "0") + "-" + String(x.getDate()).padStart(2, "0");
  }
  function norm(s) {
    const r = String(s).replace(/\r/g, "").split("\n").map((l) => l.replace(/\s+$/, ""));
    while (r.length && r[r.length - 1] === "") r.pop();
    return r.join("\n");
  }
  let toastTimer = null;
  function toast(msg) {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (t.hidden = true), 2600);
  }

  // =====================================================================
  // Syntaxkleuring
  // =====================================================================
  const KW = new Set("False None True and as assert break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield".split(" "));
  const BI = new Set("print input len range int float str list dict set tuple sum min max abs round sorted type enumerate zip bool pow sqrt reversed any all open floor ceil".split(" "));
  const TOK = /(#.*$)|("(?:\\.|[^"\\])*"?|'(?:\\.|[^'\\])*'?)|(\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)|(\s+)|([^])/g;
  function hl(regel) {
    let uit = "";
    regel.replace(TOK, (m, com, str, num, naam, ws) => {
      if (com) uit += `<span class="tk-com">${esc(com)}</span>`;
      else if (str) uit += `<span class="tk-str">${esc(str)}</span>`;
      else if (num) uit += `<span class="tk-num">${esc(num)}</span>`;
      else if (naam) {
        if (KW.has(naam)) uit += `<span class="tk-kw">${naam}</span>`;
        else if (BI.has(naam)) uit += `<span class="tk-bi">${naam}</span>`;
        else uit += esc(naam);
      } else uit += esc(m);
      return m;
    });
    return uit;
  }
  function codeHTML(code, opt) {
    opt = opt || {};
    const regels = code.split("\n");
    let vakNr = 0;
    const rijen = regels.map((r, i) => {
      const nr = i + 1;
      const cls = ["r"];
      if (opt.nu === nr) cls.push("nu");
      if (opt.vorige === nr && opt.nu !== nr) cls.push("vorige");
      if (opt.fout === nr) cls.push("fout-regel");
      if (opt.goed && opt.goed.includes(nr)) cls.push("goed-regel");
      let inhoud;
      if (opt.vakjes && r.includes("___")) {
        inhoud = r
          .split("___")
          .map((stuk, j) => (j === 0 ? "" : `<input class="vakje" data-v="${vakNr++}" aria-label="vakje ${vakNr}" autocomplete="off" autocapitalize="off" spellcheck="false">`) + hl(stuk))
          .join("");
      } else {
        inhoud = hl(r) || " ";
      }
      const rol = opt.klik ? ` role="button" tabindex="0" aria-label="regel ${nr}"` : "";
      return `<div class="${cls.join(" ")}" data-l="${nr}"${rol}><span class="ln">${nr}</span><span class="s">${inhoud}</span></div>`;
    });
    return `<div class="code${opt.klik ? " klikbaar" : ""}">${rijen.join("")}</div>`;
  }
  function uitvoerHTML(uit, leegTekst) {
    if (!uit) return `<div class="uitvoer leeg">${esc(leegTekst || "(geen uitvoer)")}</div>`;
    return `<div class="uitvoer">${esc(uit.replace(/\n$/, ""))}</div>`;
  }

  // =====================================================================
  // Voortgang (lokaal + optioneel gedeeld via de db-capability)
  // =====================================================================
  const SLEUTEL = "pop-voortgang-v1";
  const RANG = { fout: 1, hulp: 2, goed: 3 };
  function leeg() {
    return { ex: {}, days: {}, test: null, last: null };
  }
  function laad() {
    try {
      const s = JSON.parse(localStorage.getItem(SLEUTEL) || "null");
      if (s && typeof s === "object") return Object.assign(leeg(), s);
    } catch (e) {}
    return leeg();
  }
  let S = laad();
  function bewaar() {
    try {
      localStorage.setItem(SLEUTEL, JSON.stringify(S));
    } catch (e) {}
    planSync();
  }
  function markeer(id, status) {
    const nu = Date.now();
    const r = S.ex[id];
    if (!r) S.ex[id] = { b: status, e: status, n: 1, t: nu };
    else {
      r.n = (r.n || 0) + 1;
      r.t = nu;
      if ((RANG[status] || 0) > (RANG[r.b] || 0)) r.b = status;
    }
    const d = vandaag();
    S.days[d] = (S.days[d] || 0) + 1;
    S.last = id;
    bewaar();
  }
  function best(id) {
    return S.ex[id] ? S.ex[id].b : null;
  }
  function gelukt(id) {
    const b = best(id);
    return b === "goed" || b === "hulp";
  }
  function niveauStat(n) {
    const oefs = n.oefeningen;
    const ok = oefs.filter((o) => gelukt(o.id)).length;
    const meteen = oefs.filter((o) => S.ex[o.id] && S.ex[o.id].e === "goed").length;
    const gedaan = oefs.filter((o) => S.ex[o.id]).length;
    return { ok, meteen, gedaan, totaal: oefs.length, klaar: ok / oefs.length >= 0.8 };
  }
  function dagenOpRij() {
    let n = 0;
    const d = new Date();
    if (!S.days[vandaag(d)]) d.setDate(d.getDate() - 1);
    while (S.days[vandaag(d)]) {
      n++;
      d.setDate(d.getDate() - 1);
    }
    return n;
  }
  function aanbevolenNiveau() {
    const start = S.test && typeof S.test.start === "number" ? S.test.start : 0;
    for (const n of NIV) {
      if (n.nr < start) continue;
      if (!niveauStat(n).klaar) return n;
    }
    for (const n of NIV) if (!niveauStat(n).klaar) return n;
    return NIV[NIV.length - 1];
  }
  function volgendeOef(n) {
    return n.oefeningen.find((o) => !gelukt(o.id)) || null;
  }

  // ---- gedeelde voortgang (alleen als de pagina in claude.ai draait) ----
  const SYNC = { ref: null, db: null, user: null, id: null, owner: false, bezig: false, opnieuw: false, timer: null };
  function voegSamen(ander) {
    if (!ander || typeof ander !== "object") return;
    const ex = ander.ex || {};
    for (const id of Object.keys(ex)) {
      const a = ex[id];
      const m = S.ex[id];
      if (!m) S.ex[id] = Object.assign({}, a);
      else {
        if ((RANG[a.b] || 0) > (RANG[m.b] || 0)) m.b = a.b;
        m.n = Math.max(m.n || 0, a.n || 0);
        if ((a.t || 0) < (m.t || 0) && a.e) m.e = a.e;
        m.t = Math.max(m.t || 0, a.t || 0);
      }
    }
    const days = ander.days || {};
    for (const d of Object.keys(days)) S.days[d] = Math.max(S.days[d] || 0, days[d] || 0);
    if (ander.test && (!S.test || (ander.test.t || 0) > (S.test.t || 0))) S.test = ander.test;
  }
  async function startSync() {
    if (!window.claude || typeof window.claude.use !== "function") return;
    try {
      const [db, user] = await Promise.all([window.claude.use("db"), window.claude.use("user")]);
      if (!db || !user) return;
      const id = await user.id();
      if (!id) return;
      SYNC.db = db;
      SYNC.user = user;
      SYNC.id = id;
      SYNC.ref = db.doc("voortgang/" + id);
      SYNC.owner = await user.isOwner();
      const snap = await SYNC.ref.get();
      if (snap.exists) {
        voegSamen(snap.data());
        try {
          localStorage.setItem(SLEUTEL, JSON.stringify(S));
        } catch (e) {}
      }
      route();
    } catch (e) {
      SYNC.ref = null;
    }
  }
  function planSync() {
    if (!SYNC.ref) return;
    clearTimeout(SYNC.timer);
    SYNC.timer = setTimeout(stuurSync, 2500);
  }
  async function stuurSync() {
    if (!SYNC.ref) return;
    if (SYNC.bezig) {
      SYNC.opnieuw = true;
      return;
    }
    SYNC.bezig = true;
    try {
      await SYNC.ref.set({ ex: S.ex, days: S.days, test: S.test, bijgewerkt: Date.now() });
    } catch (e) {
      const code = e && e.code;
      if (code === "not_granted" || code === "permission_denied" || code === "not_writer") SYNC.ref = null;
    }
    SYNC.bezig = false;
    if (SYNC.opnieuw) {
      SYNC.opnieuw = false;
      stuurSync();
    }
  }

  // =====================================================================
  // Python in de browser (Brython in een Web Worker)
  // =====================================================================
  const PY = {
    staat: "uit", // uit | laden | klaar | kapot
    worker: null,
    klaarBelofte: null,
    volgnr: 0,
    wacht: {},
    luisteraars: new Set(),
    basis: window.POP_BRYTHON_BASE || "https://cdn.jsdelivr.net/npm/brython@3.14.3/",
  };
  const WORKER_SRC = `
self.onmessage = function (e) {
  var m = e.data;
  if (m.type === "init") {
    try {
      importScripts(m.basis + "brython.min.js", m.basis + "brython_stdlib.js");
      brython({ debug: 1 });
      __BRYTHON__.runPythonSource(m.src, "zebrunner");
      postMessage({ type: "ready" });
    } catch (err) {
      postMessage({ type: "fail", msg: String(err) });
    }
    return;
  }
  if (m.type === "call") {
    try {
      var res = m.fn === "run"
        ? self.zebRun(m.src, JSON.stringify(m.inputs || []))
        : self.zebTest(m.src, JSON.stringify(m.tests || []), JSON.stringify(m.ptests || []));
      postMessage({ type: "res", id: m.id, res: JSON.parse(res) });
    } catch (err) {
      postMessage({ type: "res", id: m.id, err: String(err) });
    }
  }
};`;
  function zetPyStaat(s) {
    PY.staat = s;
    PY.luisteraars.forEach((f) => {
      try {
        f(s);
      } catch (e) {}
    });
  }
  function startPython() {
    if (PY.staat === "klaar" || PY.staat === "laden") return PY.klaarBelofte;
    if (PY.staat === "kapot") return Promise.resolve(false);
    zetPyStaat("laden");
    PY.klaarBelofte = new Promise((resolve) => {
      let w;
      try {
        const url = URL.createObjectURL(new Blob([WORKER_SRC], { type: "text/javascript" }));
        w = new Worker(url);
      } catch (e) {
        zetPyStaat("kapot");
        resolve(false);
        return;
      }
      PY.worker = w;
      const opgeef = setTimeout(() => {
        w.terminate();
        PY.worker = null;
        zetPyStaat("kapot");
        resolve(false);
      }, 45000);
      w.onmessage = (e) => {
        const m = e.data;
        if (m.type === "ready") {
          clearTimeout(opgeef);
          zetPyStaat("klaar");
          resolve(true);
        } else if (m.type === "fail") {
          clearTimeout(opgeef);
          w.terminate();
          PY.worker = null;
          zetPyStaat("kapot");
          resolve(false);
        } else if (m.type === "res") {
          const p = PY.wacht[m.id];
          if (p) {
            delete PY.wacht[m.id];
            clearTimeout(p.timer);
            p.resolve(m.err ? { jsfout: m.err } : m.res);
          }
        }
      };
      w.onerror = (ev) => {
        if (PY.staat === "laden") {
          clearTimeout(opgeef);
          zetPyStaat("kapot");
          resolve(false);
        }
        if (ev && ev.preventDefault) ev.preventDefault();
      };
      w.postMessage({ type: "init", basis: PY.basis, src: RUNNER_PY });
    });
    return PY.klaarBelofte;
  }
  async function roepPython(bericht, ms) {
    const ok = await startPython();
    if (!ok) return { onbeschikbaar: true };
    const id = ++PY.volgnr;
    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        delete PY.wacht[id];
        // Waarschijnlijk een oneindige lus: worker afbreken en opnieuw starten.
        if (PY.worker) PY.worker.terminate();
        PY.worker = null;
        zetPyStaat("uit");
        PY.klaarBelofte = null;
        resolve({ tijd: true });
      }, ms || 5000);
      PY.wacht[id] = { resolve, timer };
      PY.worker.postMessage(Object.assign({ type: "call", id }, bericht));
    });
  }
  function pyStatusTekst(s) {
    return {
      uit: "Python start zodra je iets uitvoert.",
      laden: "Python wordt geladen… (de eerste keer duurt dat even)",
      klaar: "Python is klaar.",
      kapot: "Python kan op dit toestel niet starten. Controleer zelf met de modeloplossing en de stap-voor-stap-weergave.",
    }[s];
  }

  const FOUTUITLEG = {
    SyntaxError: ["Schrijffout (SyntaxError)", "Python begrijpt deze regel niet. Kijk naar een vergeten dubbele punt `:`, haakjes of aanhalingstekens die niet gesloten zijn, of `=` waar `==` moet staan."],
    IndentationError: ["Inspringfout (IndentationError)", "Het inspringen klopt niet. Na een regel met `:` moet je inspringen, en alles in hetzelfde blok staat even ver."],
    TabError: ["Inspringfout (TabError)", "Je mengt tabs en spaties. Gebruik overal 4 spaties."],
    NameError: ["Onbekende naam (NameError)", "Je gebruikt een naam die (nog) niet bestaat. Een tikfout of een hoofdletter? Of gebruik je de variabele voor ze een waarde kreeg?"],
    UnboundLocalError: ["Variabele zonder waarde (UnboundLocalError)", "In je functie gebruik je een variabele voor ze een waarde kreeg. Geef ze eerst een beginwaarde."],
    TypeError: ["Verkeerd type (TypeError)", "Je combineert waarden die niet samengaan, zoals tekst + getal (gebruik `int(...)` of `str(...)`). Of je roept een functie aan met het verkeerde aantal argumenten."],
    ValueError: ["Verkeerde waarde (ValueError)", "De waarde past niet, bijvoorbeeld `int(\"abc\")`: dat is geen getal."],
    IndexError: ["Index bestaat niet (IndexError)", "Je vraagt een positie die niet in de lijst of tekst zit. De laatste index is `len(...) - 1`."],
    KeyError: ["Sleutel bestaat niet (KeyError)", "Die sleutel zit niet in het woordenboek."],
    ZeroDivisionError: ["Delen door nul (ZeroDivisionError)", "Je deelt door 0. Controleer de waarde van de deler."],
    AttributeError: ["Onbekende methode (AttributeError)", "Deze waarde heeft die methode niet. Een tikfout? Bij een lijst is het bijvoorbeeld `append`, niet `add`."],
    EOFError: ["Geen invoer meer (EOFError)", "Je programma vraagt vaker `input()` dan er invoer is. Zet in het invoervak meer regels."],
    RecursionError: ["Te diep (RecursionError)", "Je functie roept zichzelf te vaak aan."],
  };
  function foutHTML(fout, src) {
    if (!fout) return "";
    const [type, msg, regel] = fout;
    const u = FOUTUITLEG[type] || ["Fout (" + type + ")", "Er liep iets mis tijdens het uitvoeren."];
    let regelTekst = "";
    if (regel && src) {
      const r = src.split("\n")[regel - 1];
      if (r !== undefined) regelTekst = `<div class="orig">Regel ${regel}: <code>${esc(r.trim())}</code></div>`;
    }
    return `<div class="foutuitleg" role="alert"><div class="titel">${esc(u[0])}${regel ? " op regel " + regel : ""}</div><div class="tekst">${md(u[1])}</div>${regelTekst}<div class="orig">Python zegt: ${esc(type)}: ${esc(msg)}</div></div>`;
  }

  // =====================================================================
  // Stap-voor-stap-weergave
  // =====================================================================
  function frameLabel(f) {
    return f.f ? `In functie ${f.f}()` : "Hoofdprogramma";
  }
  function regelVanRij(stappen, i) {
    // Welke regel werd uitgevoerd tussen stap i-1 en stap i?
    const v = stappen[i - 1];
    if (v.ret && v.fr.length >= 2) return v.fr[v.fr.length - 2].l || v.l;
    return v.l;
  }
  function maakStapper(houder, code, stappen, uitvoer, opt) {
    opt = opt || {};
    if (!stappen || !stappen.length) {
      houder.innerHTML = "";
      return;
    }
    let i = 0;
    let modus = "stap";
    const n = stappen.length;
    const invoerNoot = opt.inputs && opt.inputs.length ? `<div class="papiertip">De gebruiker typt: <b>${opt.inputs.map(esc).join(", ")}</b></div>` : "";
    houder.innerHTML = `
      <div class="stapper">
        <div class="rij tussen">
          <div class="wissel" role="group" aria-label="Weergave">
            <button type="button" data-m="stap" aria-pressed="true">Stap voor stap</button>
            <button type="button" data-m="tabel" aria-pressed="false">Tabel (zoals op papier)</button>
          </div>
        </div>
        ${invoerNoot}
        <div class="st-stap"></div>
        <div class="st-tabel" hidden></div>
      </div>`;
    const $stap = houder.querySelector(".st-stap");
    const $tabel = houder.querySelector(".st-tabel");
    houder.querySelectorAll(".wissel button").forEach((b) =>
      b.addEventListener("click", () => {
        modus = b.dataset.m;
        houder.querySelectorAll(".wissel button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        $stap.hidden = modus !== "stap";
        $tabel.hidden = modus !== "tabel";
        if (modus === "tabel") tekenTabel();
      })
    );

    function varsHTML(st, vorig) {
      const vorigeMap = {};
      if (vorig) vorig.fr.forEach((f) => f.v.forEach(([k, v]) => (vorigeMap[f.f + ":" + k] = v)));
      return st.fr
        .map((f) => {
          const rijen = f.v
            .map(([k, v]) => {
              const nieuw = vorig && vorigeMap[f.f + ":" + k] !== v;
              return `<tr><td>${esc(k)}</td><td class="${nieuw ? "nieuw" : ""}">${esc(v)}</td></tr>`;
            })
            .join("");
          return `<div class="frame"><div class="frame-kop">${esc(frameLabel(f))}</div>${rijen ? "<table>" + rijen + "</table>" : '<div class="leeg">nog geen variabelen</div>'}</div>`;
        })
        .join("");
    }
    function uitlegVoor(st, idx) {
      if (idx === 0) return "<b>Start.</b> Er is nog niets gebeurd. De gemarkeerde regel is de eerste die Python uitvoert.";
      if (st.end) {
        if (opt.fout) return `<b>Gestopt met een fout:</b> ${esc(opt.fout[0])}: ${esc(opt.fout[1])}`;
        return "<b>Klaar.</b> Het programma is helemaal uitgevoerd.";
      }
      if (st.ret) return `<b>${esc(st.ret[0])}() geeft ${esc(st.ret[1])} terug</b> (regel ${st.l}) en is daarmee gedaan.`;
      const vorig = stappen[idx - 1];
      const deel = vorig && !vorig.end ? `Regel ${regelVanRij(stappen, idx)} is uitgevoerd. ` : "";
      return `${deel}Nu is <b>regel ${st.l}</b> aan de beurt.`;
    }
    function tekenStap() {
      const st = stappen[i];
      const vorig = i > 0 ? stappen[i - 1] : null;
      const vorigeRegel = i > 0 ? regelVanRij(stappen, i) : null;
      const uit = (uitvoer || "").slice(0, st.o);
      $stap.innerHTML = `
        <div class="stap-uitleg" aria-live="polite">${uitlegVoor(st, i)}</div>
        <div class="stapper-raster">
          <div class="blok">${codeHTML(code, { nu: st.end ? null : st.l, vorige: vorigeRegel })}</div>
          <div class="blok">
            <div class="label">Variabelen</div>
            <div class="vars">${varsHTML(st, vorig)}</div>
            <div class="label">Uitvoer</div>
            ${uitvoerHTML(uit, "nog niets getoond")}
          </div>
        </div>
        <div class="rij">
          <button type="button" class="knop tweede klein" data-a="begin" ${i === 0 ? "disabled" : ""} aria-label="Naar het begin">⇤</button>
          <button type="button" class="knop tweede klein" data-a="terug" ${i === 0 ? "disabled" : ""}>← Vorige</button>
          <button type="button" class="knop klein" data-a="verder" ${i === n - 1 ? "disabled" : ""}>Volgende →</button>
          <button type="button" class="knop tweede klein" data-a="einde" ${i === n - 1 ? "disabled" : ""} aria-label="Naar het einde">⇥</button>
          <span class="label" style="margin-left:auto">stap ${i + 1} / ${n}</span>
        </div>`;
      $stap.querySelectorAll("[data-a]").forEach((b) =>
        b.addEventListener("click", () => {
          const a = b.dataset.a;
          if (a === "begin") i = 0;
          if (a === "terug") i = Math.max(0, i - 1);
          if (a === "verder") i = Math.min(n - 1, i + 1);
          if (a === "einde") i = n - 1;
          tekenStap();
          const focus = $stap.querySelector(`[data-a="${a}"]:not(:disabled)`) || $stap.querySelector('[data-a="verder"]:not(:disabled)') || $stap.querySelector('[data-a="terug"]');
          if (focus) focus.focus();
        })
      );
    }
    function tekenTabel() {
      const kolommen = [];
      const gezien = new Set();
      stappen.forEach((st) =>
        st.fr.forEach((f) =>
          f.v.forEach(([k]) => {
            const sleutel = f.f + ":" + k;
            if (!gezien.has(sleutel)) {
              gezien.add(sleutel);
              kolommen.push({ sleutel, kop: f.f ? `${k} (${f.f})` : k });
            }
          })
        )
      );
      const waarden = (st) => {
        const m = {};
        st.fr.forEach((f) => f.v.forEach(([k, v]) => (m[f.f + ":" + k] = v)));
        return m;
      };
      let rijen = "";
      let vorige = waarden(stappen[0]);
      for (let j = 1; j < n; j++) {
        const st = stappen[j];
        const w = waarden(st);
        const nieuweUit = (uitvoer || "").slice(stappen[j - 1].o, st.o);
        const veranderd = kolommen.some((c) => w[c.sleutel] !== vorige[c.sleutel]);
        const ret = stappen[j - 1].ret;
        if (!veranderd && !nieuweUit && !ret) {
          vorige = w;
          continue;
        }
        const regel = regelVanRij(stappen, j);
        const cellen = kolommen
          .map((c) => {
            const v = w[c.sleutel];
            if (v === undefined) return "<td></td>";
            const anders = v !== vorige[c.sleutel];
            return `<td class="${anders ? "veranderd" : "zelfde"}">${esc(v)}</td>`;
          })
          .join("");
        const uitCel = (ret ? `<em>${esc(ret[0])} geeft ${esc(ret[1])}</em> ` : "") + esc(nieuweUit.replace(/\n$/, "").replace(/\n/g, " ⏎ "));
        rijen += `<tr><td>${regel || ""}</td>${cellen}<td class="out">${uitCel}</td></tr>`;
        vorige = w;
      }
      $tabel.innerHTML = `
        <p class="stap-uitleg">Zo maak je het op papier: één kolom per variabele, een nieuwe rij telkens als er iets verandert. <b>Vet</b> = net veranderd.</p>
        <div class="tabelwrap"><table class="spoor"><thead><tr><th>regel</th>${kolommen.map((c) => `<th>${esc(c.kop)}</th>`).join("")}<th>uitvoer</th></tr></thead><tbody>${rijen || '<tr><td colspan="99">Geen variabelen veranderd.</td></tr>'}</tbody></table></div>`;
    }
    tekenStap();
  }

  // =====================================================================
  // Oefeningen
  // =====================================================================
  function hintsVoorUitvoer(ant, juist) {
    const a = norm(ant);
    const j = norm(juist);
    if (!a) return "Je hebt nog niets ingevuld.";
    if (a.replace(/["']/g, "") === j.replace(/["']/g, "") && /["']/.test(a)) return "Bijna! `print` toont tekst **zonder** aanhalingstekens.";
    if (a.toLowerCase() === j.toLowerCase()) return "Bijna! Let op hoofdletters, bijvoorbeeld `True` en `False`.";
    if (a.replace(/\s+/g, " ").trim() === j.replace(/\s+/g, " ").trim()) {
      if (a.split("\n").length !== j.split("\n").length) return "De waarden kloppen, maar niet op welke regel ze staan. Elke `print` begint op een **nieuwe regel** (tenzij er `end=` staat).";
      return "De waarden kloppen, maar let op de spaties. `print` met komma's zet er telkens **één** spatie tussen.";
    }
    if (a.replace(/\s+/g, "") === j.replace(/\s+/g, "")) return "Bijna! Kijk nog eens naar de spaties en de regels.";
    const al = a.split("\n");
    const jl = j.split("\n");
    if (al.length !== jl.length) return `Jouw antwoord heeft ${al.length} regel${al.length === 1 ? "" : "s"}, het juiste antwoord heeft er ${jl.length}.`;
    const fouteRegels = al.map((r, k) => (r !== jl[k] ? k + 1 : 0)).filter(Boolean);
    return `Regel${fouteRegels.length > 1 ? "s" : ""} ${fouteRegels.join(", ")} van je antwoord klopt niet.`;
  }

  function normAntw(s) {
    return String(s).replace(/\s+/g, "").replace(/"/g, "'");
  }

  /**
   * Toont één oefening in `houder`.
   * ctx.test = true: instaptest (één poging, knop "Ik weet het niet").
   * ctx.klaar(status) wordt opgeroepen als de oefening afgerond is.
   */
  function toonOefening(houder, oef, ctx) {
    ctx = ctx || {};
    let pogingen = 0;
    let hulpGebruikt = false;
    let afgerond = false;
    const vraag =
      oef.vraag ||
      (oef.t === "voorspel" ? "Wat verschijnt er op het scherm als je dit programma uitvoert?" : "");
    houder.innerHTML = `
      <div class="sectie">
        <div class="rij"><span class="soort">${esc(SOORT[oef.t])}</span>${oef.uitdaging ? '<span class="chip uitdaging">uitdaging</span>' : ""}</div>
        ${vraag ? `<div class="tekst">${md(vraag)}</div>` : ""}
        <div class="oef-lijf"></div>
        <div class="oef-acties rij"></div>
        <div class="oef-feedback" hidden></div>
        <div class="oef-stapper"></div>
        <div class="oef-volgende rij"></div>
      </div>`;
    const $lijf = houder.querySelector(".oef-lijf");
    const $acties = houder.querySelector(".oef-acties");
    const $fb = houder.querySelector(".oef-feedback");
    const $stapper = houder.querySelector(".oef-stapper");
    const $volg = houder.querySelector(".oef-volgende");

    function feedback(soort, html) {
      $fb.hidden = false;
      $fb.innerHTML = `<div class="feedback ${soort}">${html}</div>`;
    }
    function rond(status) {
      if (afgerond) return;
      afgerond = true;
      if (ctx.klaar) ctx.klaar(status);
    }
    function stapKnop(code, stappen, uitvoer, label, extra) {
      if (ctx.test || !stappen || !stappen.length) return null;
      const b = maak(`<button type="button" class="knop tweede">${esc(label || "Bekijk stap voor stap")}</button>`);
      b.addEventListener("click", () => {
        hulpGebruikt = true;
        maakStapper($stapper, code, stappen, uitvoer, Object.assign({ inputs: oef.inputs, fout: oef.fout }, extra || {}));
        b.remove();
        $stapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
      return b;
    }
    function tipKnop() {
      if (!oef.tip || ctx.test) return null;
      const b = maak(`<button type="button" class="knop stil">Tip</button>`);
      b.addEventListener("click", () => {
        b.replaceWith(maak(`<div class="papiertip"><span class="papierlabel">tip</span><div>${md(oef.tip)}</div></div>`));
      });
      return b;
    }
    function weetNiet(onKlik) {
      const b = maak(`<button type="button" class="knop stil">Ik weet het (nog) niet</button>`);
      b.addEventListener("click", onKlik);
      return b;
    }
    function invoerNoot() {
      if (!oef.inputs || !oef.inputs.length || oef.vraag) return "";
      return `<div class="papiertip">De gebruiker typt: <b>${oef.inputs.map(esc).join(", ")}</b></div>`;
    }

    // ------------------------------------------------ voorspel
    if (oef.t === "voorspel") {
      $lijf.innerHTML = `
        ${codeHTML(oef.code)}
        ${invoerNoot()}
        <div class="blok">
          <label class="label" for="antw-${oef.id}">Jouw antwoord</label>
          <textarea id="antw-${oef.id}" class="antwoordveld" rows="${Math.max(2, oef.uitvoer.split("\n").length)}" placeholder="Schrijf het eerst op papier en typ het dan hier over. Elke regel op het scherm = een regel hier." autocomplete="off" autocapitalize="off" spellcheck="false"></textarea>
        </div>`;
      const $ta = $lijf.querySelector("textarea");
      const $ctrl = maak(`<button type="button" class="knop">Controleer</button>`);
      $acties.append($ctrl);
      const tip = tipKnop();
      if (tip) $acties.append(tip);
      if (ctx.test) $acties.append(weetNiet(() => toonJuist("fout", true)));
      function toonJuist(status, weet) {
        $acties.innerHTML = "";
        $ta.readOnly = true;
        const kop = status === "goed" || status === "hulp" ? '<div class="notitie groen">Juist!</div>' : weet ? '<div class="notitie">Geen probleem, zo zit het:</div>' : '<div class="notitie rood">Dit is het juiste antwoord:</div>';
        feedback(status === "fout" ? "fout" : "goed", `${kop}<div class="blok"><div class="label">Uitvoer</div>${uitvoerHTML(oef.uitvoer)}</div><div class="tekst">${md(oef.uitleg)}</div>`);
        const sk = stapKnop(oef.code, oef.stappen, oef.uitvoer);
        if (sk) $fb.querySelector(".feedback").append(sk);
        rond(status);
      }
      $ctrl.addEventListener("click", () => {
        pogingen++;
        if (norm($ta.value) === norm(oef.uitvoer)) {
          toonJuist(pogingen === 1 && !hulpGebruikt ? "goed" : "hulp");
          return;
        }
        if (ctx.test) {
          toonJuist("fout");
          return;
        }
        feedback("fout", `<div class="notitie rood">Nog niet.</div><div class="tekst">${md(hintsVoorUitvoer($ta.value, oef.uitvoer))}</div>`);
        const r = maak('<div class="rij"></div>');
        const sk = stapKnop(oef.code, oef.stappen, oef.uitvoer, "Zoek het stap voor stap");
        if (sk) r.append(sk);
        const toon = maak(`<button type="button" class="knop stil">Toon het antwoord</button>`);
        toon.addEventListener("click", () => toonJuist("fout"));
        r.append(toon);
        $fb.querySelector(".feedback").append(r);
        $ctrl.textContent = "Controleer opnieuw";
      });
      $ta.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) $ctrl.click();
      });
    }

    // ------------------------------------------------ keuze / lees
    else if (oef.t === "keuze" || oef.t === "lees") {
      const letters = "ABCDEF";
      $lijf.innerHTML = `
        ${oef.code ? codeHTML(oef.code) : ""}
        ${invoerNoot()}
        <div class="opties" role="group" aria-label="Antwoorden">
          ${oef.opties.map((o, k) => `<button type="button" class="optie" data-k="${k}"><span class="letter">${letters[k]}</span><span>${inline(o)}</span></button>`).join("")}
        </div>`;
      const knoppen = [...$lijf.querySelectorAll(".optie")];
      function afsluiten(status, weet) {
        knoppen.forEach((b) => (b.disabled = true));
        knoppen[oef.juist].classList.add("juist");
        $acties.innerHTML = "";
        const kop = status !== "fout" ? '<div class="notitie groen">Juist!</div>' : weet ? '<div class="notitie">Geen probleem, zo zit het:</div>' : '<div class="notitie rood">Het juiste antwoord is ' + letters[oef.juist] + ".</div>";
        let extra = "";
        if (oef.code && oef.uitvoer !== undefined && oef.uitvoer !== "") extra = `<div class="blok"><div class="label">Uitvoer</div>${uitvoerHTML(oef.uitvoer)}</div>`;
        feedback(status === "fout" ? "fout" : "goed", `${kop}${extra}<div class="tekst">${md(oef.uitleg)}</div>`);
        if (oef.code && oef.stappen) {
          const sk = stapKnop(oef.code, oef.stappen, oef.uitvoer);
          if (sk) $fb.querySelector(".feedback").append(sk);
        }
        rond(status);
      }
      knoppen.forEach((b) =>
        b.addEventListener("click", () => {
          const k = +b.dataset.k;
          pogingen++;
          if (k === oef.juist) {
            afsluiten(pogingen === 1 ? "goed" : pogingen === 2 ? "hulp" : "fout");
          } else {
            b.classList.add("onjuist");
            b.disabled = true;
            if (ctx.test) {
              afsluiten("fout");
              return;
            }
            feedback("fout", `<div class="notitie rood">Nee, ${letters[k]} is het niet.</div><div class="tekst"><p>Probeer nog eens.${oef.code ? " Voer de code regel per regel uit op papier." : ""}</p></div>`);
          }
        })
      );
      if (ctx.test) $acties.append(weetNiet(() => afsluiten("fout", true)));
      const tip = tipKnop();
      if (tip) $acties.append(tip);
    }

    // ------------------------------------------------ fout
    else if (oef.t === "fout") {
      let gekozen = null;
      $lijf.innerHTML = `
        <p class="inleiding">Klik op de regel waar de fout zit.</p>
        ${codeHTML(oef.code, { klik: true })}`;
      const rijen = [...$lijf.querySelectorAll(".code .r")];
      const kies = (r) => {
        rijen.forEach((x) => x.classList.toggle("gekozen", x === r));
        gekozen = +r.dataset.l;
        $ctrl.disabled = false;
      };
      rijen.forEach((r) => {
        r.addEventListener("click", () => !afgerond && kies(r));
        r.addEventListener("keydown", (e) => {
          if ((e.key === "Enter" || e.key === " ") && !afgerond) {
            e.preventDefault();
            kies(r);
          }
        });
      });
      const $ctrl = maak(`<button type="button" class="knop" disabled>Controleer</button>`);
      $acties.append($ctrl);
      if (ctx.test) $acties.append(weetNiet(() => afsluiten("fout", true)));
      function afsluiten(status, weet) {
        $acties.innerHTML = "";
        rijen.forEach((x) => {
          x.classList.remove("gekozen");
          x.removeAttribute("tabindex");
          if (+x.dataset.l === oef.regel) x.classList.add("fout-regel");
        });
        $lijf.querySelector(".code").classList.remove("klikbaar");
        const origSet = new Set(oef.code.split("\n").map((s) => s.trim()));
        const nieuwe = oef.verbeterd.split("\n").map((s, k) => (origSet.has(s.trim()) ? 0 : k + 1)).filter(Boolean);
        const kop = status !== "fout" ? `<div class="notitie groen">Juist, regel ${oef.regel}!</div>` : weet ? '<div class="notitie">Geen probleem, zo zit het:</div>' : `<div class="notitie rood">De fout zit op regel ${oef.regel}.</div>`;
        feedback(status === "fout" ? "fout" : "goed", `${kop}<div class="tekst">${md(oef.uitleg)}</div><div class="blok"><div class="label">Verbeterd</div>${codeHTML(oef.verbeterd, { goed: nieuwe })}</div><div class="blok"><div class="label">Uitvoer van de verbeterde code</div>${uitvoerHTML(oef.uitvoer_verbeterd)}</div>`);
        const sk = stapKnop(oef.code, oef.stappen, oef.uitvoer, "Zo loopt de foute code, stap voor stap");
        if (sk) $fb.querySelector(".feedback").append(sk);
        rond(status);
      }
      $ctrl.addEventListener("click", () => {
        if (gekozen == null) return;
        pogingen++;
        if (gekozen === oef.regel) {
          afsluiten(pogingen === 1 ? "goed" : "hulp");
          return;
        }
        if (ctx.test || pogingen >= 3) {
          afsluiten("fout");
          return;
        }
        let hint;
        if (oef.fout) hint = `Tip: Python geeft deze foutmelding: <code>${esc(oef.fout[0])}: ${esc(oef.fout[1])}</code>`;
        else hint = `Tip: dit programma geeft geen foutmelding, maar toont: <code>${esc(norm(oef.uitvoer))}</code>. Is dat wat het moet doen?`;
        feedback("fout", `<div class="notitie rood">Niet regel ${gekozen}.</div><div class="tekst"><p>${hint}</p></div>`);
      });
    }

    // ------------------------------------------------ aanvullen
    else if (oef.t === "aanvullen") {
      $lijf.innerHTML = `${codeHTML(oef.code, { vakjes: true })}${invoerNoot()}`;
      const vakjes = [...$lijf.querySelectorAll(".vakje")];
      vakjes.forEach((v, k) => {
        const lang = Math.max(...oef.antwoorden[k].map((a) => a.length));
        v.style.width = Math.max(4, lang + 2) + "ch";
        v.addEventListener("keydown", (e) => {
          if (e.key === "Enter") $ctrl.click();
        });
      });
      const $ctrl = maak(`<button type="button" class="knop">Controleer</button>`);
      $acties.append($ctrl);
      const tip = tipKnop();
      if (tip) $acties.append(tip);
      if (ctx.test) $acties.append(weetNiet(() => afsluiten("fout", true)));
      function afsluiten(status, weet) {
        $acties.innerHTML = "";
        vakjes.forEach((v, k) => {
          if (status === "fout") v.value = oef.antwoorden[k][0];
          v.readOnly = true;
          v.classList.remove("nok");
          v.classList.add("ok");
        });
        const kop = status !== "fout" ? '<div class="notitie groen">Juist!</div>' : weet ? '<div class="notitie">Geen probleem, zo zit het:</div>' : '<div class="notitie rood">Zo moest het:</div>';
        const andere = oef.antwoorden.some((a) => a.length > 1) ? `<p class="inleiding">Ook goed: ${oef.antwoorden.map((a, k) => (a.length > 1 ? `vakje ${k + 1}: ${a.map((x) => "<code>" + esc(x) + "</code>").join(" of ")}` : "")).filter(Boolean).join("; ")}</p>` : "";
        feedback(status === "fout" ? "fout" : "goed", `${kop}<div class="tekst">${md(oef.uitleg)}</div>${andere}<div class="blok"><div class="label">Uitvoer</div>${uitvoerHTML(oef.uitvoer)}</div>`);
        const sk = stapKnop(oef.ingevuld, oef.stappen, oef.uitvoer);
        if (sk) $fb.querySelector(".feedback").append(sk);
        rond(status);
      }
      $ctrl.addEventListener("click", () => {
        pogingen++;
        let alles = true;
        vakjes.forEach((v, k) => {
          const ok = oef.antwoorden[k].some((a) => normAntw(a) === normAntw(v.value));
          v.classList.toggle("ok", ok);
          v.classList.toggle("nok", !ok);
          if (!ok) alles = false;
        });
        if (alles) {
          afsluiten(pogingen === 1 ? "goed" : "hulp");
          return;
        }
        if (ctx.test) {
          afsluiten("fout");
          return;
        }
        feedback("fout", `<div class="notitie rood">Nog niet.</div><div class="tekst"><p>De rode vakjes kloppen nog niet. Probeer opnieuw.</p></div>`);
        if (pogingen >= 2) {
          const toon = maak(`<button type="button" class="knop stil">Toon het antwoord</button>`);
          toon.addEventListener("click", () => afsluiten("fout"));
          $fb.querySelector(".feedback").append(toon);
        }
      });
    }

    // ------------------------------------------------ schrijf
    else if (oef.t === "schrijf") {
      let gecontroleerd = 0;
      let oplossingGezien = false;
      const testLijst = [];
      (oef.tests || []).forEach(([e, v]) => testLijst.push(`<li><code>${esc(e)}</code> moet <code>${esc(v)}</code> geven</li>`));
      (oef.ptests || []).forEach(([inp, v]) => {
        const invoer = inp.length ? `Invoer <code>${inp.map(esc).join(", ")}</code> → ` : "";
        testLijst.push(`<li>${invoer}uitvoer: <pre class="uitvoer" style="margin-top:4px">${esc(norm(v))}</pre></li>`);
      });
      $lijf.innerHTML = `
        <div class="stappenplan">
          <div class="stap"><span class="hand">1</span><span>Schrijf je oplossing <b>op papier</b>.</span></div>
          <div class="stap"><span class="hand">2</span><span>Test ze <b>met de hand</b> met de voorbeelden hieronder.</span></div>
          <div class="stap"><span class="hand">3</span><span>Typ ze <b>precies</b> over en laat de computer controleren.</span></div>
          <div class="stap"><span class="hand">4</span><span>Vergelijk met de modeloplossing.</span></div>
        </div>
        <div class="blok"><div class="label">Voorbeelden om mee te testen</div><ul class="lijstje">${testLijst.join("")}</ul></div>
        <details class="papiertip"><summary><b>Checklist voor op papier</b></summary>
          <ul class="checklist" style="margin-top:8px">
            <li>Dubbele punt na <code>def</code>, <code>if</code>, <code>elif</code>, <code>else</code>, <code>for</code>, <code>while</code></li>
            <li>Alles in een blok even ver ingesprongen</li>
            <li>Alle haakjes en aanhalingstekens gesloten</li>
            <li><code>==</code> om te vergelijken, <code>=</code> om iets in een variabele te steken</li>
            <li><code>return</code> (niet <code>print</code>) als er "teruggeven" staat</li>
            <li><code>range(a, b)</code> stopt vóór b</li>
            <li>Tellers en sommen krijgen een beginwaarde vóór de lus</li>
          </ul>
        </details>
        <div class="blok">
          <label class="label" for="ed-${oef.id}">Jouw oplossing (overgetypt van papier)</label>
          ${editorHTML("ed-" + oef.id, oef.start ? oef.start + (/:\s*$/.test(oef.start) ? "\n    " : "\n") : "")}
          <div class="label py-status" aria-live="polite"></div>
        </div>
        <div class="oef-resultaat"></div>`;
      const ed = koppelEditor($lijf.querySelector(".editor"));
      const $res = $lijf.querySelector(".oef-resultaat");
      const $pyst = $lijf.querySelector(".py-status");
      const zetSt = (s) => ($pyst.textContent = s === "klaar" || s === "uit" ? "" : pyStatusTekst(s));
      PY.luisteraars.add(zetSt);
      zetSt(PY.staat);
      const $ctrl = maak(`<button type="button" class="knop">Controleer met de computer</button>`);
      const $sol = maak(`<button type="button" class="knop tweede">Toon modeloplossing</button>`);
      $acties.append($ctrl, $sol);
      const tip = tipKnop();
      if (tip) $acties.append(tip);

      function toonOplossing(alGeslaagd) {
        oplossingGezien = true;
        $sol.remove();
        const zelf = alGeslaagd
          ? ""
          : `<div class="blok"><div class="label">Hoe ging het op papier?</div><div class="rij">
              <button type="button" class="knop tweede klein" data-z="goed">Mijn oplossing was juist</button>
              <button type="button" class="knop tweede klein" data-z="hulp">Bijna, een kleine fout</button>
              <button type="button" class="knop tweede klein" data-z="fout">Nog niet</button></div></div>`;
        const box = maak(`<div class="feedback info"><div class="label">Modeloplossing</div>${codeHTML(oef.oplossing)}<div class="tekst">${md(oef.uitleg)}</div>${zelf}</div>`);
        $stapper.before(box);
        box.querySelectorAll("[data-z]").forEach((b) =>
          b.addEventListener("click", () => {
            const z = b.dataset.z;
            box.querySelectorAll("[data-z]").forEach((x) => (x.disabled = true));
            b.classList.remove("tweede");
            rond(z);
            toonVolgende();
          })
        );
      }
      $sol.addEventListener("click", () => toonOplossing(false));
      $ctrl.addEventListener("click", async () => {
        const src = ed.waarde();
        if (!src.trim()) {
          $res.innerHTML = `<div class="feedback fout"><p>Typ eerst je oplossing in.</p></div>`;
          return;
        }
        $ctrl.disabled = true;
        $ctrl.textContent = "Bezig…";
        const r = await roepPython({ fn: "test", src, tests: oef.tests || [], ptests: oef.ptests || [] }, 6000);
        $ctrl.disabled = false;
        $ctrl.textContent = "Controleer opnieuw";
        gecontroleerd++;
        ed.markeerFout(null);
        if (r.onbeschikbaar) {
          $res.innerHTML = `<div class="feedback info"><p>${esc(pyStatusTekst("kapot"))}</p></div>`;
          $ctrl.remove();
          if (!oplossingGezien) toonOplossing(false);
          return;
        }
        if (r.tijd) {
          $res.innerHTML = `<div class="feedback fout"><div class="notitie rood">Je programma stopt niet.</div><p>Waarschijnlijk een <b>oneindige lus</b>: verandert de variabele in je while-lus wel? Of vraagt je programma meer invoer dan er is?</p></div>`;
          return;
        }
        if (r.jsfout) {
          $res.innerHTML = `<div class="feedback fout"><p>Er liep iets mis bij het controleren: ${esc(r.jsfout)}</p></div>`;
          return;
        }
        if (r.fout) {
          ed.markeerFout(r.fout[2]);
          $res.innerHTML = `<div class="feedback fout">${foutHTML(r.fout, src)}</div>`;
          return;
        }
        const tests = r.resultaten || [];
        const okAantal = tests.filter((x) => x.ok).length;
        const lijst = tests
          .map((x) => {
            const vraagT = x.vraag ? `<code>${esc(x.vraag)}</code>` : x.invoer && x.invoer.length ? `invoer <code>${x.invoer.map(esc).join(", ")}</code>` : "uitvoeren";
            let detail = "";
            if (!x.ok) {
              if (x.fout) detail = foutHTML(x.fout, src);
              else if (x.vraag) detail = `<div>verwacht <code>${esc(x.verwacht)}</code>, kreeg <code>${esc(x.kreeg)}</code></div>`;
              else detail = `<div class="verschil"><div class="blok"><div class="label">verwacht</div>${uitvoerHTML(x.verwacht)}</div><div class="blok"><div class="label">jouw programma toonde</div>${uitvoerHTML(x.kreeg, "(niets)")}</div></div>`;
            }
            return `<div class="test ${x.ok ? "ok" : "nok"}"><span class="ic">${x.ok ? "✓" : "✗"}</span><div class="blok">${vraagT}${detail}</div></div>`;
          })
          .join("");
        const verboden = (oef.verboden || []).filter((v) => src.includes(v));
        const allesOk = okAantal === tests.length && !verboden.length;
        let extra = "";
        if (verboden.length) extra = `<div class="foutuitleg"><div class="titel">Niet toegelaten</div><div>Je gebruikt <code>${esc(verboden.join(", "))}</code>. Deze opdracht vraagt het zonder.</div></div>`;
        const noneHint = tests.some((x) => !x.ok && x.kreeg === "None") ? `<div class="papiertip"><b>Je functie geeft None terug.</b> Vergeten om <code>return</code> te schrijven? Of staat er <code>print</code> in plaats van <code>return</code>?</div>` : "";
        $res.innerHTML = `<div class="feedback ${allesOk ? "goed" : "fout"}">${allesOk ? '<div class="notitie groen">Alle tests geslaagd!</div>' : `<div class="notitie rood">${okAantal} van ${tests.length} tests geslaagd.</div>`}${extra}${noneHint}<div class="testlijst">${lijst}</div></div>`;
        if (allesOk) {
          $ctrl.remove();
          rond(gecontroleerd === 1 && !oplossingGezien ? "goed" : "hulp");
          if (!oplossingGezien) toonOplossing(true);
          toonVolgende();
        }
      });
      // Python alvast laden zodra iemand begint te typen.
      $lijf.querySelector("textarea").addEventListener("focus", () => startPython(), { once: true });
    }

    function toonVolgende() {
      if (!ctx.volgende || $volg.childElementCount) return;
      $volg.append(ctx.volgende());
    }
    // Volgende-knop tonen zodra de oefening afgerond is.
    const origKlaar = ctx.klaar;
    ctx.klaar = (st) => {
      if (origKlaar) origKlaar(st);
      toonVolgende();
    };
  }

  // =====================================================================
  // Editor (textarea met regelnummers)
  // =====================================================================
  function editorHTML(id, start) {
    return `<div class="editor"><div class="gutter" aria-hidden="true">1</div><textarea id="${id}" spellcheck="false" autocomplete="off" autocapitalize="off" wrap="off">${esc(start || "")}</textarea></div>`;
  }
  function koppelEditor($ed) {
    const ta = $ed.querySelector("textarea");
    const gut = $ed.querySelector(".gutter");
    let foutRegel = null;
    function teken() {
      const n = ta.value.split("\n").length;
      let s = "";
      for (let i = 1; i <= n; i++) s += (i === foutRegel ? `<span class="fl">${i}</span>` : i) + "\n";
      gut.innerHTML = s;
      gut.scrollTop = ta.scrollTop;
      ta.rows = Math.max(7, n + 1);
    }
    ta.addEventListener("input", teken);
    ta.addEventListener("scroll", () => (gut.scrollTop = ta.scrollTop));
    ta.addEventListener("keydown", (e) => {
      if (e.key === "Tab" && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        voegIn("    ");
      } else if (e.key === "Enter" && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
        // Automatisch inspringen: zelfde als vorige regel, +4 na een dubbele punt.
        const pos = ta.selectionStart;
        const voor = ta.value.slice(0, pos);
        const regel = voor.split("\n").pop();
        let ins = (regel.match(/^\s*/) || [""])[0];
        if (/:\s*(#.*)?$/.test(regel)) ins += "    ";
        e.preventDefault();
        voegIn("\n" + ins);
      }
    });
    function voegIn(t) {
      const a = ta.selectionStart;
      const b = ta.selectionEnd;
      ta.setRangeText(t, a, b, "end");
      teken();
    }
    // Cursor na de startcode zetten.
    ta.addEventListener(
      "focus",
      () => {
        if (ta.selectionStart === 0 && ta.selectionEnd === 0 && ta.value) ta.setSelectionRange(ta.value.length, ta.value.length);
      },
      { once: true }
    );
    teken();
    return {
      waarde: () => ta.value,
      zet: (v) => {
        ta.value = v;
        teken();
      },
      markeerFout: (r) => {
        foutRegel = r || null;
        teken();
      },
      ta,
    };
  }

  // =====================================================================
  // Views
  // =====================================================================
  function zetTab(naam) {
    document.querySelectorAll(".tabs a").forEach((a) => {
      if (a.dataset.tab === naam) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }
  function wekenTotJanuari() {
    const nu = new Date();
    if (nu.getMonth() === 0) return 0;
    const jan = new Date(nu.getFullYear() + 1, 0, 1);
    return Math.max(1, Math.round((jan - nu) / (7 * 864e5)));
  }

  function viewStart() {
    zetTab("start");
    const vandaagN = S.days[vandaag()] || 0;
    const totaalOk = ALLE_OEF.filter((o) => gelukt(o.id)).length;
    const n = aanbevolenNiveau();
    const volgende = volgendeOef(n);
    const w = wekenTotJanuari();
    const examenTekst = w === 0 ? "Het examen is deze maand." : `Examen computationeel denken in januari: nog ongeveer ${w} weken.`;
    const testKaart = S.test
      ? ""
      : `<div class="kaart">
          <div class="oogje">Begin hier</div>
          <h2>De instaptest</h2>
          <p>12 korte vragen, ongeveer 10 minuten. Daarna weet je bij welk niveau je best begint. Weet je iets niet? Klik dan op <b>Ik weet het (nog) niet</b>. Dat is beter dan gokken.</p>
          <div class="rij"><a class="knop" href="#instaptest">Start de instaptest</a><a class="knop stil" href="#niveau-0">Nee, begin gewoon bij niveau 0</a></div>
        </div>`;
    const st = niveauStat(n);
    $app.innerHTML = `
      <section class="kop">
        <div class="groet">Dag <span class="onderlijn">Zeb</span>.</div>
        <p class="inleiding">${esc(examenTekst)} Elke dag een beetje werkt beter dan alles op het einde.</p>
      </section>
      ${testKaart}
      <div class="kaart">
        <div class="oogje">${S.test || totaalOk ? "Ga verder" : "Of begin meteen"}</div>
        <div class="rij tussen">
          <h2>Niveau ${n.nr}: ${esc(n.titel)}</h2>
          <span class="chip">${st.ok} / ${st.totaal} gelukt</span>
        </div>
        <div class="balkje"><span style="width:${Math.round((st.ok / st.totaal) * 100)}%"></span></div>
        <p class="inleiding">${inline(n.doel)}</p>
        <div class="rij">
          ${volgende ? `<a class="knop" href="#oef-${volgende.id}">${st.gedaan ? "Volgende oefening" : "Start met de oefeningen"}</a>` : ""}
          <a class="knop tweede" href="#niveau-${n.nr}">Lees eerst de uitleg</a>
        </div>
      </div>
      <div class="kaart vlak">
        <div class="cijfers">
          <div class="cijfer"><b>${vandaagN} / ${DAGDOEL}</b><span>oefeningen vandaag</span></div>
          <div class="cijfer"><b>${dagenOpRij()}</b><span>dagen op rij</span></div>
          <div class="cijfer"><b>${totaalOk}</b><span>van ${ALLE_OEF.length} oefeningen gelukt</span></div>
        </div>
        <div class="balkje groen" aria-label="dagdoel"><span style="width:${Math.min(100, (vandaagN / DAGDOEL) * 100)}%"></span></div>
      </div>
      <section class="sectie">
        <h2>Zo werk je</h2>
        <div class="stappenplan">
          <div class="stap"><span class="hand">1</span><span>Lees de <b>uitleg</b> van het niveau. Kort, met voorbeelden.</span></div>
          <div class="stap"><span class="hand">2</span><span>Maak elke oefening <b>eerst op papier</b>. Zo gaat het op het examen.</span></div>
          <div class="stap"><span class="hand">3</span><span>Typ je antwoord over en <b>controleer</b>.</span></div>
          <div class="stap"><span class="hand">4</span><span>Fout? Bekijk het <b>stap voor stap</b>. Daar leer je het meest van.</span></div>
        </div>
        <div class="papiertip"><div><b>Je spiekbrief</b> staat helemaal uitgelegd onder <a href="#spiekbrief">Spiekbrief</a>, met bij elk vak wat je echt moet kennen en wat je voorlopig mag overslaan.</div></div>
      </section>`;
  }

  function viewPad() {
    zetTab("pad");
    const aanbevolen = aanbevolenNiveau().nr;
    const kaarten = NIV.map((n) => {
      const st = niveauStat(n);
      const cls = ["niveau-kaart"];
      if (st.klaar) cls.push("klaar");
      if (n.nr === aanbevolen) cls.push("aanbevolen");
      const status = st.klaar ? '<span class="chip goed">klaar</span>' : n.nr === aanbevolen ? '<span class="chip">aanbevolen</span>' : st.gedaan ? '<span class="chip half">bezig</span>' : "";
      return `<a class="${cls.join(" ")}" href="#niveau-${n.nr}">
        <div class="nr">${n.nr}</div>
        <div class="niveau-info">
          <div class="rij tussen"><h3>${esc(n.titel)}</h3>${status}</div>
          <div class="sub">${esc(n.kort)} · ${n.uitleg.length} uitlegkaarten · ${n.oefeningen.length} oefeningen</div>
          <div class="balkje${st.klaar ? " groen" : ""}"><span style="width:${Math.round((st.ok / st.totaal) * 100)}%"></span></div>
          <div class="chips">${n.spiek.map((s) => `<span class="chip grijs">${esc(SPIEK_ID[s].naam)}</span>`).join("")}</div>
        </div>
      </a>`;
    }).join("");
    const later = LATER.map(
      (n) => `<div class="niveau-kaart later">
        <div class="nr">${n.nr}</div>
        <div class="niveau-info">
          <div class="rij tussen"><h3>${esc(n.titel)}</h3><span class="chip grijs">binnenkort</span></div>
          <div class="sub">${inline(n.inhoud)}</div>
        </div>
      </div>`
    ).join("");
    $app.innerHTML = `
      <section class="kop">
        <div class="oogje">Leerpad</div>
        <h1>Van nul naar het examen</h1>
        <p class="inleiding">Elk niveau bouwt verder op het vorige. Je mag overal beginnen, maar de volgorde helpt. Een niveau is <b>klaar</b> als 80% van de oefeningen gelukt is. De grijze vakjes zijn de vakken van je spiekbrief die erbij horen.</p>
      </section>
      <div class="pad">${kaarten}${later}</div>`;
  }

  let kladblokStart = null;
  function viewNiveau(nr) {
    const n = NIV.find((x) => x.nr === nr);
    if (!n) return viewPad();
    zetTab("pad");
    const st = niveauStat(n);
    const volgende = volgendeOef(n);
    const lessen = n.uitleg
      .map(
        (l, k) => `<article class="les" data-k="${k}">
        <h3><span class="hand">${k + 1}</span><span>${esc(l.titel)}</span></h3>
        <div class="tekst">${md(l.tekst)}</div>
        ${
          l.code
            ? `<div class="code-en-uitvoer">
                <div class="blok"><div class="label">Code</div>${codeHTML(l.code)}</div>
                <div class="blok"><div class="label">Uitvoer${l.inputs ? " (invoer: " + l.inputs.map(esc).join(", ") + ")" : ""}</div>${uitvoerHTML(l.uitvoer)}</div>
              </div>
              <div class="rij"><button type="button" class="knop tweede klein" data-stap="${k}">Stap voor stap</button><button type="button" class="knop stil klein" data-klad="${k}">Probeer in het kladblok</button></div>
              <div class="les-stapper"></div>`
            : ""
        }
        ${l.papier ? `<div class="papiertip"><span class="papierlabel">op papier</span><div>${md(l.papier)}</div></div>` : ""}
      </article>`
      )
      .join("");
    const tegels = n.oefeningen
      .map((o) => {
        const b = best(o.id);
        const stTekst = b === "goed" ? "gelukt" : b === "hulp" ? "gelukt met hulp" : b === "fout" ? "nog eens doen" : "nog niet gedaan";
        return `<a class="oef-tegel" href="#oef-${o.id}"><span class="t">${o.idx + 1}. ${esc(SOORT[o.t])}</span><span class="st"><span class="stip ${b || ""}"></span>${stTekst}${o.uitdaging ? " · uitdaging" : ""}</span></a>`;
      })
      .join("");
    const vorig = NIV.find((x) => x.nr === nr - 1);
    const volg = NIV.find((x) => x.nr === nr + 1);
    $app.innerHTML = `
      <section class="kop">
        <div class="oogje">Niveau ${n.nr}</div>
        <h1>${esc(n.titel)}</h1>
        <p class="inleiding">${inline(n.doel)}</p>
        <div class="chips">${n.spiek.map((s) => `<a class="chip grijs" href="#spiek-${s}">Spiekbrief: ${esc(SPIEK_ID[s].naam)}</a>`).join("")}</div>
      </section>
      <div class="kaart vlak">
        <div class="rij tussen"><b>${st.ok} van ${st.totaal} oefeningen gelukt</b>${st.klaar ? '<span class="chip goed">klaar</span>' : ""}</div>
        <div class="balkje${st.klaar ? " groen" : ""}"><span style="width:${Math.round((st.ok / st.totaal) * 100)}%"></span></div>
        <div class="rij">${volgende ? `<a class="knop" href="#oef-${volgende.id}">${st.gedaan ? "Ga verder met de oefeningen" : "Start de oefeningen"}</a>` : `<a class="knop" href="#oef-${n.oefeningen[0].id}">Oefeningen opnieuw doen</a>`}<a class="knop stil" href="#oefeningen">Naar de lijst</a></div>
      </div>
      <section class="sectie">
        <h2>Uitleg</h2>
        ${lessen}
      </section>
      <section class="sectie" id="oefeningen">
        <h2>Oefeningen</h2>
        <div class="oef-raster">${tegels}</div>
      </section>
      <div class="rij tussen">
        ${vorig ? `<a class="knop stil" href="#niveau-${vorig.nr}">← Niveau ${vorig.nr}: ${esc(vorig.titel)}</a>` : "<span></span>"}
        ${volg ? `<a class="knop stil" href="#niveau-${volg.nr}">Niveau ${volg.nr}: ${esc(volg.titel)} →</a>` : ""}
      </div>`;
    $app.querySelectorAll("[data-stap]").forEach((b) =>
      b.addEventListener("click", () => {
        const l = n.uitleg[+b.dataset.stap];
        const h = b.closest(".les").querySelector(".les-stapper");
        maakStapper(h, l.code, l.stappen, l.uitvoer, { inputs: l.inputs });
        b.remove();
      })
    );
    $app.querySelectorAll("[data-klad]").forEach((b) =>
      b.addEventListener("click", () => {
        const l = n.uitleg[+b.dataset.klad];
        kladblokStart = { code: l.code, inputs: (l.inputs || []).join("\n") };
        location.hash = "kladblok";
      })
    );
    $app.querySelector('a[href="#oefeningen"]').addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("oefeningen").scrollIntoView({ behavior: "smooth" });
    });
  }

  function viewOef(nr, k) {
    const n = NIV.find((x) => x.nr === nr);
    if (!n || !n.oefeningen[k - 1]) return viewPad();
    zetTab("pad");
    const oef = n.oefeningen[k - 1];
    const stippen = n.oefeningen
      .map((o) => {
        const b = best(o.id);
        return `<a href="#oef-${o.id}" class="${b || ""}${o === oef ? " hier" : ""}" aria-label="oefening ${o.idx + 1}${b ? ", " + b : ""}"${o === oef ? ' aria-current="step"' : ""}>${o.idx + 1}</a>`;
      })
      .join("");
    $app.innerHTML = `
      <section class="oef-kop">
        <div class="rij tussen">
          <a class="oogje" href="#niveau-${n.nr}" style="text-decoration:none">← Niveau ${n.nr} · ${esc(n.titel)}</a>
          <span class="label">oefening ${k} / ${n.oefeningen.length}</span>
        </div>
        <nav class="stippen" aria-label="Oefeningen van dit niveau">${stippen}</nav>
      </section>
      <div class="oef-plek"></div>`;
    const volgendeOefening = n.oefeningen[k] || null;
    toonOefening($app.querySelector(".oef-plek"), oef, {
      klaar: (status) => {
        markeer(oef.id, status);
        const a = $app.querySelector(`.stippen a[href="#oef-${oef.id}"]`);
        if (a) {
          a.classList.remove("goed", "hulp", "fout");
          a.classList.add(best(oef.id));
        }
      },
      volgende: () => {
        if (volgendeOefening) {
          return maak(`<a class="knop" href="#oef-${volgendeOefening.id}">Volgende oefening →</a>`);
        }
        const st = niveauStat(n);
        const volgNiv = NIV.find((x) => x.nr === n.nr + 1);
        return maak(`<div class="kaart" style="width:100%">
          <div class="notitie groen">Einde van niveau ${n.nr}!</div>
          <p>${st.ok} van de ${st.totaal} oefeningen zijn gelukt${st.meteen ? `, ${st.meteen} meteen juist` : ""}. ${st.klaar ? "Dit niveau is klaar." : "Doe de oefeningen met een rode of lege stip nog eens om het niveau af te werken."}</p>
          <div class="rij">${volgNiv ? `<a class="knop" href="#niveau-${volgNiv.nr}">Naar niveau ${volgNiv.nr}: ${esc(volgNiv.titel)}</a>` : `<a class="knop" href="#pad">Naar het leerpad</a>`}<a class="knop tweede" href="#niveau-${n.nr}">Terug naar dit niveau</a></div>
        </div>`);
      },
    });
  }

  // ---------------- Instaptest ----------------
  let TESTSTAAT = null;
  function viewInstaptest() {
    zetTab("start");
    if (!TESTSTAAT) TESTSTAAT = { i: -1, uitslag: {} };
    if (TESTSTAAT.i === -1) {
      $app.innerHTML = `
        <section class="kop">
          <div class="oogje">Instaptest</div>
          <h1>Waar sta je nu?</h1>
          <p class="inleiding">12 vragen, van heel makkelijk naar moeilijker. Er hangen geen punten aan: het is enkel om te zien waar je best begint.</p>
        </section>
        <div class="kaart">
          <ul class="lijstje">
            <li>Neem een blad papier en een pen. Schrijf je antwoord eerst op papier.</li>
            <li>Weet je het niet? Klik op <b>Ik weet het (nog) niet</b>. Gokken maakt het resultaat minder bruikbaar.</li>
            <li>Na elke vraag zie je meteen de uitleg.</li>
          </ul>
          <div class="rij"><button type="button" class="knop" id="start-test">Start</button></div>
        </div>`;
      document.getElementById("start-test").addEventListener("click", () => {
        TESTSTAAT.i = 0;
        viewInstaptest();
      });
      return;
    }
    if (TESTSTAAT.i >= TEST.length) return toonTestUitslag();
    const v = TEST[TESTSTAAT.i];
    $app.innerHTML = `
      <section class="oef-kop">
        <div class="rij tussen"><span class="oogje">Instaptest</span><span class="label">vraag ${TESTSTAAT.i + 1} / ${TEST.length}</span></div>
        <div class="balkje"><span style="width:${Math.round((TESTSTAAT.i / TEST.length) * 100)}%"></span></div>
      </section>
      <div class="oef-plek"></div>`;
    toonOefening($app.querySelector(".oef-plek"), v, {
      test: true,
      klaar: (status) => {
        TESTSTAAT.uitslag[v.id] = status === "goed";
      },
      volgende: () => {
        const b = maak(`<button type="button" class="knop">${TESTSTAAT.i + 1 < TEST.length ? "Volgende vraag →" : "Bekijk je resultaat"}</button>`);
        b.addEventListener("click", () => {
          TESTSTAAT.i++;
          viewInstaptest();
          window.scrollTo(0, 0);
        });
        return b;
      },
    });
  }
  function toonTestUitslag() {
    const per = {};
    TEST.forEach((v) => {
      per[v.n] = per[v.n] || [0, 0];
      per[v.n][1]++;
      if (TESTSTAAT.uitslag[v.id]) per[v.n][0]++;
    });
    const score = TEST.filter((v) => TESTSTAAT.uitslag[v.id]).length;
    let start = NIV.length - 1;
    for (const n of NIV) {
      if (per[n.nr] && per[n.nr][0] < per[n.nr][1]) {
        start = n.nr;
        break;
      }
    }
    S.test = { t: Date.now(), score, totaal: TEST.length, start, per };
    bewaar();
    const rijen = NIV.map((n) => {
      const p = per[n.nr];
      if (!p) return "";
      const ok = p[0] === p[1];
      return `<div class="vg-rij"><span>${n.nr}. ${esc(n.titel)}</span><div class="balkje${ok ? " groen" : ""}"><span style="width:${(p[0] / p[1]) * 100}%"></span></div><span class="cnt">${p[0]} / ${p[1]}</span></div>`;
    }).join("");
    const sn = NIV[start];
    $app.innerHTML = `
      <section class="kop">
        <div class="oogje">Instaptest: resultaat</div>
        <h1>${score} van de ${TEST.length} juist</h1>
        <p class="inleiding">${score === TEST.length ? "Knap! De basis zit goed. Begin bij de functies en oefen vooral het schrijven op papier." : "Prima startpunt. Elke fout hier is iets wat je in de app gaat leren."}</p>
      </section>
      <div class="kaart">
        <div class="oogje">Begin hier</div>
        <h2>Niveau ${sn.nr}: ${esc(sn.titel)}</h2>
        <p class="inleiding">${inline(sn.doel)}${start > 0 ? " De niveaus daarvoor mag je overslaan, of snel herhalen als je wil." : ""}</p>
        <div class="rij"><a class="knop" href="#niveau-${sn.nr}">Naar niveau ${sn.nr}</a><a class="knop stil" href="#pad">Bekijk het leerpad</a></div>
      </div>
      <section class="sectie"><h2>Per onderwerp</h2><div class="sectie" style="gap:10px">${rijen}</div></section>
      <div class="rij"><button type="button" class="knop stil" id="opnieuw-test">Test opnieuw doen</button></div>`;
    document.getElementById("opnieuw-test").addEventListener("click", () => {
      TESTSTAAT = { i: 0, uitslag: {} };
      viewInstaptest();
    });
  }

  // ---------------- Spiekbrief ----------------
  let spiekFilter = "alles";
  function viewSpiek(doel) {
    zetTab("spiekbrief");
    const sterren = (b) => `<span class="sterren" aria-label="belang ${b} van 3">${"★".repeat(b)}<span class="uit">${"★".repeat(3 - b)}</span></span>`;
    const belangTekst = { 3: "moet je kennen", 2: "handig", 1: "mag je voorlopig overslaan" };
    const zichtbaar = SPIEK.filter((v) => spiekFilter === "alles" || (spiekFilter === "3" && v.belang === 3) || spiekFilter === v.kant);
    const vakken = zichtbaar
      .map(
        (v) => `<article class="vak" id="spiek-${v.id}">
        <div class="vak-kop">
          <div class="blok"><span class="naam">${esc(v.naam)} · ${v.kant}</span><h3>${esc(v.nl)}</h3></div>
          <div class="blok" style="align-items:flex-end">${sterren(v.belang)}<span class="label">${belangTekst[v.belang]}</span></div>
        </div>
        <div class="tekst">${md(v.uitleg)}</div>
        <div class="twee-kol">
          <div class="blok"><div class="label">Dit moet je kennen</div><ul class="lijstje">${v.kennen.map((x) => `<li>${inline(x)}</li>`).join("")}</ul></div>
          ${v.overslaan.length ? `<div class="blok"><div class="label">Mag je voorlopig overslaan</div><ul class="lijstje weg">${v.overslaan.map((x) => `<li>${inline(x)}</li>`).join("")}</ul></div>` : ""}
        </div>
        ${v.code ? `<div class="code-en-uitvoer"><div class="blok"><div class="label">Voorbeeld</div>${codeHTML(v.code)}</div><div class="blok"><div class="label">Uitvoer</div>${uitvoerHTML(v.uitvoer)}</div></div>` : ""}
        <div class="rij">${v.niveau != null ? `<a class="knop tweede klein" href="#niveau-${v.niveau}">Oefenen in niveau ${v.niveau}</a>` : '<span class="chip grijs">komt in een later niveau</span>'}${v.code ? `<button type="button" class="knop stil klein" data-klad="${v.id}">Probeer in het kladblok</button>` : ""}</div>
      </article>`
      )
      .join("");
    const telMoet = SPIEK.filter((v) => v.belang === 3).length;
    $app.innerHTML = `
      <section class="kop">
        <div class="oogje">Spiekbrief</div>
        <h1>Je spiekbrief, in gewone taal</h1>
        <p class="inleiding">Het blad van de prof is de <i>Python 3 Mémento</i> van Laurent Pointal. Er staat veel op, maar je hebt niet alles nodig. Per vak zie je hoe belangrijk het is: <b>★★★</b> moet je kennen (${telMoet} vakken), <b>★★</b> is handig, <b>★</b> mag je voorlopig overslaan.</p>
        <div class="papiertip"><div><b>Tip voor het examen:</b> markeer de ★★★-vakken met fluo op je eigen blad. Dan vind je ze snel terug.</div></div>
      </section>
      <div class="filters" role="group" aria-label="Filter">
        ${[["alles", "Alles"], ["3", "Alleen ★★★"], ["voorkant", "Voorkant"], ["achterkant", "Achterkant"]].map(([k, l]) => `<button type="button" data-f="${k}" aria-pressed="${spiekFilter === k}">${l}</button>`).join("")}
      </div>
      <div class="sectie">${vakken}</div>`;
    $app.querySelectorAll("[data-f]").forEach((b) =>
      b.addEventListener("click", () => {
        spiekFilter = b.dataset.f;
        viewSpiek();
      })
    );
    $app.querySelectorAll("[data-klad]").forEach((b) =>
      b.addEventListener("click", () => {
        kladblokStart = { code: SPIEK_ID[b.dataset.klad].code, inputs: "" };
        location.hash = "kladblok";
      })
    );
    if (doel) {
      const el = document.getElementById(doel);
      if (!el && spiekFilter !== "alles") {
        spiekFilter = "alles";
        return viewSpiek(doel);
      }
      if (el) setTimeout(() => el.scrollIntoView({ block: "start" }), 0);
    }
  }

  // ---------------- Kladblok ----------------
  const KLAD_SLEUTEL = "pop-kladblok";
  function viewKladblok() {
    zetTab("kladblok");
    let start = kladblokStart;
    kladblokStart = null;
    if (!start) {
      try {
        start = JSON.parse(localStorage.getItem(KLAD_SLEUTEL) || "null");
      } catch (e) {}
    }
    if (!start) start = { code: 'naam = input("Hoe heet je? ")\nprint("Dag", naam)\nfor i in range(3):\n    print(i, "x", i, "=", i * i)', inputs: "Zeb" };
    $app.innerHTML = `
      <section class="kop">
        <div class="oogje">Kladblok</div>
        <h1>Probeer het uit</h1>
        <p class="inleiding">Hier kan je zelf Python uitvoeren. Op het examen heb je geen computer, dus gebruik dit om te <b>controleren</b> wat je op papier dacht. Eerst denken, dan pas uitvoeren.</p>
      </section>
      <div class="blok">
        <label class="label" for="klad-code">Code</label>
        ${editorHTML("klad-code", start.code)}
      </div>
      <div class="blok">
        <label class="label" for="klad-in">Invoer voor input() (één waarde per regel)</label>
        <textarea id="klad-in" class="antwoordveld" rows="2" style="min-height:3.4em" spellcheck="false">${esc(start.inputs || "")}</textarea>
      </div>
      <div class="rij">
        <button type="button" class="knop" id="klad-run">Voer uit</button>
        <button type="button" class="knop stil" id="klad-leeg">Leegmaken</button>
        <span class="label" id="klad-st" aria-live="polite"></span>
      </div>
      <div class="blok"><div class="label">Uitvoer</div><div id="klad-uit">${uitvoerHTML("", "Klik op Voer uit (of Ctrl+Enter).")}</div></div>`;
    const ed = koppelEditor($app.querySelector(".editor"));
    const $in = document.getElementById("klad-in");
    const $uit = document.getElementById("klad-uit");
    const $st = document.getElementById("klad-st");
    const $run = document.getElementById("klad-run");
    const zetSt = (s) => {
      if (document.body.contains($st)) $st.textContent = pyStatusTekst(s);
    };
    PY.luisteraars.add(zetSt);
    zetSt(PY.staat);
    const opslaan = () => {
      try {
        localStorage.setItem(KLAD_SLEUTEL, JSON.stringify({ code: ed.waarde(), inputs: $in.value }));
      } catch (e) {}
    };
    ed.ta.addEventListener("input", opslaan);
    $in.addEventListener("input", opslaan);
    async function voerUit() {
      opslaan();
      $run.disabled = true;
      $run.textContent = "Bezig…";
      ed.markeerFout(null);
      const inputs = $in.value === "" ? [] : $in.value.replace(/\r/g, "").split("\n");
      const r = await roepPython({ fn: "run", src: ed.waarde(), inputs }, 5000);
      $run.disabled = false;
      $run.textContent = "Voer uit";
      if (r.onbeschikbaar) {
        $uit.innerHTML = `<div class="feedback info"><p>${esc(pyStatusTekst("kapot"))}</p></div>`;
        return;
      }
      if (r.tijd) {
        $uit.innerHTML = `<div class="feedback fout"><div class="notitie rood">Je programma stopt niet.</div><p>Na 5 seconden is het afgebroken. Waarschijnlijk een <b>oneindige lus</b>, of het programma wacht op meer invoer.</p></div>`;
        return;
      }
      if (r.jsfout) {
        $uit.innerHTML = `<div class="feedback fout"><p>${esc(r.jsfout)}</p></div>`;
        return;
      }
      ed.markeerFout(r.fout ? r.fout[2] : null);
      $uit.innerHTML = uitvoerHTML(r.uit, r.fout ? "(niets getoond voor de fout)" : "(het programma toonde niets)") + (r.fout ? foutHTML(r.fout, ed.waarde()) : "");
    }
    $run.addEventListener("click", voerUit);
    ed.ta.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        voerUit();
      }
    });
    document.getElementById("klad-leeg").addEventListener("click", () => {
      ed.zet("");
      $in.value = "";
      opslaan();
      $uit.innerHTML = uitvoerHTML("", "Klik op Voer uit (of Ctrl+Enter).");
      ed.ta.focus();
    });
    startPython();
  }

  // ---------------- Voortgang ----------------
  function samenvattingTekst() {
    const d = new Date();
    const regels = [`Python op papier: voortgang van Zeb (${d.toLocaleDateString("nl-BE")})`, ""];
    if (S.test) regels.push(`Instaptest: ${S.test.score}/${S.test.totaal} juist, start bij niveau ${S.test.start}`);
    else regels.push("Instaptest: nog niet gedaan");
    regels.push("");
    NIV.forEach((n) => {
      const st = niveauStat(n);
      regels.push(`Niveau ${n.nr} ${n.titel}: ${st.ok}/${st.totaal} gelukt (${st.meteen} meteen juist)${st.klaar ? " ✓" : ""}`);
    });
    let week = 0;
    let actief = 0;
    for (let k = 0; k < 7; k++) {
      const x = new Date();
      x.setDate(x.getDate() - k);
      const c = S.days[vandaag(x)] || 0;
      week += c;
      if (c) actief++;
    }
    regels.push("", `Laatste 7 dagen: ${week} oefening${week === 1 ? "" : "en"}, ${actief} dag${actief === 1 ? "" : "en"} actief`);
    return regels.join("\n");
  }
  function viewVoortgang() {
    zetTab("voortgang");
    const totaalOk = ALLE_OEF.filter((o) => gelukt(o.id)).length;
    const gedaan = ALLE_OEF.filter((o) => S.ex[o.id]);
    const meteen = gedaan.filter((o) => S.ex[o.id].e === "goed").length;
    const lezen = ALLE_OEF.filter((o) => o.t !== "schrijf");
    const schrijven = ALLE_OEF.filter((o) => o.t === "schrijf");
    const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);
    const rij = (label, ok, tot, groen) => `<div class="vg-rij"><span>${label}</span><div class="balkje${groen ? " groen" : ""}"><span style="width:${pct(ok, tot)}%"></span></div><span class="cnt">${ok} / ${tot}</span></div>`;
    const dagen = [];
    for (let k = 13; k >= 0; k--) {
      const x = new Date();
      x.setDate(x.getDate() - k);
      const c = S.days[vandaag(x)] || 0;
      const lvl = c === 0 ? "" : c < 5 ? "n1" : c < DAGDOEL ? "n2" : "n3";
      dagen.push(`<div class="dag ${lvl}" title="${x.toLocaleDateString("nl-BE")}: ${c} oefeningen"></div>`);
    }
    $app.innerHTML = `
      <section class="kop">
        <div class="oogje">Voortgang</div>
        <h1>Hoe ver sta je?</h1>
      </section>
      <div class="kaart vlak">
        <div class="cijfers">
          <div class="cijfer"><b>${totaalOk}</b><span>van ${ALLE_OEF.length} oefeningen gelukt</span></div>
          <div class="cijfer"><b>${gedaan.length ? pct(meteen, gedaan.length) + "%" : "–"}</b><span>meteen juist</span></div>
          <div class="cijfer"><b>${dagenOpRij()}</b><span>dagen op rij</span></div>
        </div>
      </div>
      <section class="sectie">
        <h2>Per niveau</h2>
        <div class="sectie" style="gap:10px">${NIV.map((n) => {
          const st = niveauStat(n);
          return rij(`<a href="#niveau-${n.nr}">${n.nr}. ${esc(n.titel)}</a>`, st.ok, st.totaal, st.klaar);
        }).join("")}</div>
      </section>
      <section class="sectie">
        <h2>Lezen en schrijven</h2>
        <p class="inleiding">Op het examen moet je code kunnen <b>lezen</b> (wat doet dit, wat print dit) en <b>schrijven</b>. Schrijven is moeilijker en komt vanzelf als het lezen goed zit.</p>
        <div class="sectie" style="gap:10px">
          ${rij("Code lezen", lezen.filter((o) => gelukt(o.id)).length, lezen.length)}
          ${rij("Code schrijven", schrijven.filter((o) => gelukt(o.id)).length, schrijven.length)}
        </div>
      </section>
      <section class="sectie">
        <h2>Laatste 14 dagen</h2>
        <div class="dagen" role="img" aria-label="Activiteit van de laatste 14 dagen">${dagen.join("")}</div>
        <p class="label">Hoe donkerder, hoe meer oefeningen. Doel: ${DAGDOEL} per dag.</p>
      </section>
      <section class="sectie">
        <h2>Overzicht voor thuis</h2>
        <p class="inleiding">Kopieer dit overzicht en stuur het door, bijvoorbeeld via WhatsApp.</p>
        <pre class="overzicht-tekst" id="overzicht">${esc(samenvattingTekst())}</pre>
        <div class="rij"><button type="button" class="knop" id="kopieer">Kopieer overzicht</button></div>
      </section>
      <section class="sectie" id="gezin" hidden></section>
      <section class="sectie">
        <h2>Opnieuw beginnen</h2>
        <p class="inleiding">Wist alle voortgang op dit toestel. Dit kan je niet ongedaan maken.</p>
        <div class="rij" id="wis-rij"><button type="button" class="knop stil" id="wis">Wis mijn voortgang</button></div>
      </section>`;
    document.getElementById("kopieer").addEventListener("click", () => {
      const tekst = samenvattingTekst();
      const fallback = () => {
        const pre = document.getElementById("overzicht");
        const r = document.createRange();
        r.selectNodeContents(pre);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(r);
        toast("Tekst geselecteerd: kopieer hem nu zelf.");
      };
      try {
        navigator.clipboard.writeText(tekst).then(() => toast("Gekopieerd."), fallback);
      } catch (e) {
        fallback();
      }
    });
    document.getElementById("wis").addEventListener("click", () => {
      const rij = document.getElementById("wis-rij");
      rij.innerHTML = `<span>Zeker? Alles wordt gewist.</span><button type="button" class="knop" id="wis-ja" style="background:var(--rood);border-color:var(--rood)">Ja, wis alles</button><button type="button" class="knop stil" id="wis-nee">Annuleer</button>`;
      document.getElementById("wis-ja").addEventListener("click", () => {
        S = leeg();
        bewaar();
        TESTSTAAT = null;
        toast("Voortgang gewist.");
        viewVoortgang();
      });
      document.getElementById("wis-nee").addEventListener("click", viewVoortgang);
    });
    if (SYNC.db && SYNC.owner) toonGezin();
  }
  async function toonGezin() {
    const $g = document.getElementById("gezin");
    if (!$g) return;
    try {
      const qs = await SYNC.db.collection("voortgang").get();
      const docs = qs.docs.filter((d) => d.exists);
      if (!docs.length) return;
      const ids = docs.map((d) => d.id);
      const profielen = (await SYNC.user.profiles(ids)) || {};
      if (!document.body.contains($g)) return;
      $g.hidden = false;
      $g.innerHTML = `<h2>Iedereen die deze app gebruikt</h2><p class="inleiding">Deze lijst zie jij omdat je eigenaar bent van de app.</p><div class="sectie lijst-gezin" style="gap:10px"></div>`;
      const $l = $g.querySelector(".lijst-gezin");
      docs.forEach((d) => {
        const data = d.data() || {};
        const ex = data.ex || {};
        const ok = Object.keys(ex).filter((k) => OEF_ID[k] && (ex[k].b === "goed" || ex[k].b === "hulp")).length;
        const laatst = data.bijgewerkt ? new Date(data.bijgewerkt).toLocaleDateString("nl-BE") : "–";
        const r = maak(`<div class="vg-rij"><span class="nm"></span><div class="balkje"><span style="width:${Math.round((ok / ALLE_OEF.length) * 100)}%"></span></div><span class="cnt">${ok} / ${ALLE_OEF.length} · ${esc(laatst)}</span></div>`);
        const p = profielen[d.id];
        r.querySelector(".nm").textContent = (p && p.name) || (d.id === SYNC.id ? "Jij" : "Leerling");
        $l.append(r);
      });
    } catch (e) {}
  }

  // =====================================================================
  // Router
  // =====================================================================
  function route() {
    const h = decodeURIComponent(location.hash.slice(1)) || "start";
    let m;
    if (h === "start") viewStart();
    else if (h === "pad") viewPad();
    else if ((m = h.match(/^niveau-(\d+)$/))) viewNiveau(+m[1]);
    else if ((m = h.match(/^oef-(\d+)-(\d+)$/))) viewOef(+m[1], +m[2]);
    else if (h === "spiekbrief") viewSpiek();
    else if (h.startsWith("spiek-")) viewSpiek(h);
    else if (h === "kladblok") viewKladblok();
    else if (h === "voortgang") viewVoortgang();
    else if (h === "instaptest") viewInstaptest();
    else if (h === "oefeningen") return;
    else viewStart();
    if (!h.startsWith("spiek-")) window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", () => {
    PY.luisteraars.clear();
    route();
  });
  route();
  startSync();
})();
