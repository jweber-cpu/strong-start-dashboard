/* FY27 Summer Strong Start — dashboard renderer (Phase 3, present).
   Reads window.METRICS (from metrics.js). No external dependencies. */
(function () {
  "use strict";
  var M = window.METRICS;
  if (!M) { document.getElementById("meta").textContent = "metrics.js not found — run: python metrics.py"; return; }

  var weeks = M.weeks;
  var state = { week: defaultWeek(), view: "school", region: "", sortKey: "completion_pct", sortAsc: false, selected: [] };
  // distinct line colors for the multi-select trend (cycles if more entities than colors)
  var PALETTE = ["#2f6db0", "#c0392b", "#1a7f4b", "#c98a00", "#7d4fc0", "#d6457e",
                 "#0f9aa8", "#8c564b", "#5aa02c", "#e07b00", "#3b5bdb", "#9c36b5"];

  // ---- helpers ----
  function defaultWeek() {
    // pick the week containing "today" if in range, else the first week
    var now = new Date();
    var y = now.getUTCFullYear();
    var jan1 = new Date(Date.UTC(y, 0, 1));
    var wk = Math.ceil((((now - jan1) / 86400000) + jan1.getUTCDay() + 1) / 7);
    var label = y + "-W" + String(wk).padStart(2, "0");
    return weeks.indexOf(label) >= 0 ? label : weeks[0];
  }
  function pct(v) { return v === null || v === undefined ? "—" : v.toFixed(1) + "%"; }
  function color(v) { return v === null ? "var(--muted)" : v >= 80 ? "var(--good)" : v >= 50 ? "var(--mid)" : "var(--bad)"; }

  // entities for the current view: schools (optionally region-filtered) or regions
  function entities() {
    if (state.view === "region") {
      return Object.keys(M.regions).sort().map(function (r) {
        return { key: r, name: r, region: r, manager_group: "", weekly: M.regions[r].weekly };
      });
    }
    return M.schools
      .filter(function (s) { return !state.region || s.region === state.region; })
      .map(function (s) {
        return { key: s.gid, name: s.name, region: s.region, manager_group: s.manager_group, weekly: s.weekly };
      });
  }
  function wk(e) { return e.weekly[state.week] || { cohort: 0, completed: 0, completion_pct: null, on_time: 0, on_time_pct: null, backlog: 0 }; }

  // ---- renderers ----
  function renderMeta() {
    var m = M.meta || {};
    var note = m.sample ? " · " + (m.sample_note || "DEV SAMPLE") : "";
    document.getElementById("meta").textContent =
      M.schools.length + " schools · weeks " + weeks[0] + "–" + weeks[weeks.length - 1] +
      (m.pulled_at ? " · pulled " + m.pulled_at.slice(0, 10) : "") + note;
  }

  function renderCards() {
    var es = entities(), tot = { cohort: 0, completed: 0, on_time: 0, backlog: 0 };
    es.forEach(function (e) { var s = wk(e); tot.cohort += s.cohort; tot.completed += s.completed; tot.on_time += s.on_time; tot.backlog += s.backlog || 0; });
    var cp = tot.cohort ? (tot.completed / tot.cohort * 100) : null;
    var op = tot.cohort ? (tot.on_time / tot.cohort * 100) : null;
    var cards = [
      ["Tasks due " + state.week, tot.cohort],
      ["Completed", tot.completed],
      ["Completion %", pct(cp)],
      ["On-time %", pct(op)],
      ["Backlog (overdue & open)", tot.backlog]
    ];
    document.getElementById("cards").innerHTML = cards.map(function (c) {
      return '<div class="card"><div class="n">' + c[1] + '</div><div class="l">' + c[0] + '</div></div>';
    }).join("");
  }

  function renderBars() {
    var es = entities().map(function (e) { return { e: e, s: wk(e) }; });
    es.sort(function (a, b) { return (b.s.completion_pct || -1) - (a.s.completion_pct || -1); });
    document.getElementById("barTitle").textContent = "Due-week completion % — " + state.week +
      (state.view === "region" ? " (by region)" : "");
    document.getElementById("bars").innerHTML = es.map(function (o) {
      var s = o.s, w = s.completion_pct || 0, w2 = s.on_time_pct || 0;
      var label = s.cohort === 0 ? '<span class="muted">— none due</span>' : pct(s.completion_pct) + ' <span class="muted">(' + s.completed + '/' + s.cohort + ')</span>';
      return '<div class="barrow"><div class="nm">' + o.e.name + '</div>' +
        '<div class="bartrack">' +
        '<div class="barfill" style="width:' + w + '%;background:var(--bar)"></div>' +
        '<div class="barfill" style="width:' + w2 + '%;background:var(--bar2);position:absolute;top:0;left:0;opacity:.55"></div>' +
        '</div><div class="v">' + label + '</div></div>';
    }).join("");
  }

  var COLS = [
    { k: "name", t: "Name", num: false },
    { k: "region", t: "Region", num: false },
    { k: "manager_group", t: "Manager", num: false },
    { k: "cohort", t: "Due", num: true },
    { k: "completed", t: "Done", num: true },
    { k: "completion_pct", t: "Completion %", num: true, pill: true },
    { k: "on_time_pct", t: "On-time %", num: true, pill: true },
    { k: "backlog", t: "Backlog", num: true }
  ];

  function rowVal(e, k) {
    if (k === "name" || k === "region" || k === "manager_group") return e[k] || "";
    return wk(e)[k];
  }

  function renderTable() {
    var thead = document.querySelector("#tbl thead");
    thead.innerHTML = "<tr>" + COLS.map(function (c) {
      var cls = c.k === state.sortKey ? "sorted" + (state.sortAsc ? " asc" : "") : "";
      return '<th class="' + cls + '" data-k="' + c.k + '">' + c.t + "</th>";
    }).join("") + "</tr>";

    var es = entities();
    es.sort(function (a, b) {
      var va = rowVal(a, state.sortKey), vb = rowVal(b, state.sortKey);
      if (va === null || va === undefined) va = -1;
      if (vb === null || vb === undefined) vb = -1;
      if (va < vb) return state.sortAsc ? -1 : 1;
      if (va > vb) return state.sortAsc ? 1 : -1;
      return a.name < b.name ? -1 : 1; // stable tiebreak
    });

    var tbody = document.querySelector("#tbl tbody");
    tbody.innerHTML = es.map(function (e) {
      var s = wk(e);
      return '<tr data-k="' + e.key + '" class="' + (state.selected.indexOf(e.key) >= 0 ? "sel" : "") + '">' +
        COLS.map(function (c) {
          var v = rowVal(e, c.k);
          if (c.pill) {
            if (v === null || s.cohort === 0) return '<td class="muted">—</td>';
            return '<td><span class="pill" style="background:' + color(v) + '">' + v.toFixed(1) + '%</span></td>';
          }
          if (c.num) return "<td>" + (s.cohort === 0 && (c.k === "completed") ? "0" : (v === null ? "—" : v)) + "</td>";
          return "<td>" + v + "</td>";
        }).join("") + "</tr>";
    }).join("");
  }

  function renderTrend() {
    var es = entities(), byKey = {};
    es.forEach(function (e) { byKey[e.key] = e; });
    var sel = state.selected.filter(function (k) { return byKey[k]; }); // keep only entities valid in this view
    var title = document.getElementById("trendTitle");
    var box = document.getElementById("trend");
    if (!sel.length) {
      title.textContent = "Trend across weeks — completion % by due-week";
      box.innerHTML = '<div class="muted">Click one or more rows above to overlay their weekly completion trends. ' +
        'Tip: switch View to <b>By region</b> then <b>Select all shown</b> to compare all four regions.</div>';
      return;
    }
    title.textContent = "Trend across weeks — completion % by due-week (" + sel.length + " selected)";

    var W = 1100, H = 240, padL = 36, padB = 28, padT = 12, padR = 12;
    var n = weeks.length, iw = (W - padL - padR) / Math.max(1, n - 1);
    function x(i) { return padL + i * iw; }
    function y(v) { return padT + (1 - v / 100) * (H - padT - padB); }

    var grid = [0, 25, 50, 75, 100].map(function (g) {
      return '<line x1="' + padL + '" y1="' + y(g) + '" x2="' + (W - padR) + '" y2="' + y(g) + '" stroke="var(--line)"/>' +
        '<text x="4" y="' + (y(g) + 3) + '">' + g + '</text>';
    }).join("");
    var labels = weeks.map(function (wkl, i) {
      return '<text x="' + x(i) + '" y="' + (H - 8) + '" text-anchor="middle">' + wkl.slice(5) + '</text>';
    }).join("");

    var series = sel.map(function (k, idx) {
      var ent = byKey[k], col = PALETTE[idx % PALETTE.length], pts = [], dots = "";
      weeks.forEach(function (wkl, i) {
        var s = ent.weekly[wkl] || { completion_pct: null };
        if (s.completion_pct === null) return;
        pts.push(x(i) + "," + y(s.completion_pct));
        dots += '<circle cx="' + x(i) + '" cy="' + y(s.completion_pct) + '" r="2.5" fill="' + col + '"><title>' +
          ent.name + " " + wkl + ": " + s.completion_pct + "%</title></circle>";
      });
      var poly = pts.length ? '<polyline fill="none" stroke="' + col + '" stroke-width="2" points="' + pts.join(" ") + '"/>' : "";
      return poly + dots;
    }).join("");

    var legend = sel.map(function (k, idx) {
      return '<span><span class="sw" style="background:' + PALETTE[idx % PALETTE.length] + '"></span>' + byKey[k].name + "</span>";
    }).join("");

    box.innerHTML =
      '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" preserveAspectRatio="xMidYMid meet">' + grid + series + labels + "</svg>" +
      '<div class="legend">' + legend + "</div>";
  }

  function renderManagers() {
    var M2 = M.managers || {};
    var keys = Object.keys(M2).sort();
    var head = ["Manager", "Schools", "Approved", "On-time", "Late", "Unknown", "On-time %", "Avg days (− late)"];
    var thead = document.querySelector("#mgrTbl thead");
    thead.innerHTML = "<tr>" + head.map(function (h, i) { return "<th" + (i === 0 || i === 1 ? ' style="text-align:left"' : "") + ">" + h + "</th>"; }).join("") + "</tr>";
    var rows = keys.map(function (k) {
      var v = M2[k];
      var otp = v.on_time_pct;
      var otCell = otp === null ? '<td class="muted">—</td>' : '<td><span class="pill" style="background:' + color(otp) + '">' + otp.toFixed(1) + '%</span></td>';
      var adj = v.avg_days_delta;
      var adCell = adj === null ? '<td class="muted">—</td>' : '<td style="color:' + (adj < 0 ? "var(--bad)" : "var(--good)") + '">' + (adj > 0 ? "+" : "") + adj + "</td>";
      return "<tr><td>" + k + '</td><td style="text-align:left" class="muted">' + (v.schools || []).join(", ") + "</td>" +
        "<td>" + v.approved + "</td><td>" + v.on_time + "</td><td>" + v.late + "</td><td>" + v.unknown + "</td>" +
        otCell + adCell + "</tr>";
    }).join("");
    document.querySelector("#mgrTbl tbody").innerHTML = rows;
  }

  function renderPipeline() {
    var sr = M.school_review || {};
    var order = ["Approved", "Ready for Review", "Draft", "Not set"];
    var colors = { "Approved": "var(--good)", "Ready for Review": "var(--bar2)", "Draft": "var(--mid)", "Not set": "#cbd5df" };
    var schools = Object.keys(sr).map(function (g) { return sr[g]; });
    if (state.region) schools = schools.filter(function (r) { return M.schools.some(function (s) { return s.name === r.name && s.region === state.region; }); });
    schools.sort(function (a, b) { return (b.counts.Approved) - (a.counts.Approved); });
    document.getElementById("pipe").innerHTML = schools.map(function (r) {
      var total = order.reduce(function (a, k) { return a + r.counts[k]; }, 0) || 1;
      var seg = order.map(function (k) {
        var w = r.counts[k] / total * 100;
        return w > 0 ? '<div style="width:' + w + '%;background:' + colors[k] + ';height:100%" title="' + k + ': ' + r.counts[k] + '"></div>' : "";
      }).join("");
      return '<div class="barrow"><div class="nm">' + r.name + '</div>' +
        '<div class="bartrack" style="display:flex;overflow:hidden">' + seg + '</div>' +
        '<div class="v">' + r.counts.Approved + "/" + total + "</div></div>";
    }).join("");
  }

  function renderAll() { renderCards(); renderBars(); renderTable(); renderManagers(); renderPipeline(); renderTrend(); }

  // ---- wiring ----
  function init() {
    renderMeta();
    var wsel = document.getElementById("week");
    wsel.innerHTML = weeks.map(function (w) { return '<option value="' + w + '"' + (w === state.week ? " selected" : "") + ">" + w + "</option>"; }).join("");
    wsel.addEventListener("change", function () { state.week = this.value; renderAll(); });

    var regions = Array.from(new Set(M.schools.map(function (s) { return s.region; }))).sort();
    var rf = document.getElementById("regionFilter");
    rf.innerHTML = '<option value="">All regions</option>' + regions.map(function (r) { return '<option value="' + r + '">' + r + "</option>"; }).join("");
    rf.addEventListener("change", function () { state.region = this.value; state.selected = []; renderAll(); });

    document.getElementById("view").addEventListener("click", function (e) {
      if (e.target.tagName !== "BUTTON") return;
      state.view = e.target.getAttribute("data-v"); state.selected = []; // keys differ between views
      Array.prototype.forEach.call(this.children, function (b) { b.classList.toggle("active", b === e.target); });
      document.getElementById("regionFilter").disabled = (state.view === "region");
      renderAll();
    });

    document.getElementById("trendAll").addEventListener("click", function () {
      state.selected = entities().map(function (e) { return e.key; });
      renderTable(); renderTrend();
    });
    document.getElementById("trendClear").addEventListener("click", function () {
      state.selected = []; renderTable(); renderTrend();
    });

    document.querySelector("#tbl thead").addEventListener("click", function (e) {
      var k = e.target.getAttribute("data-k"); if (!k) return;
      if (state.sortKey === k) state.sortAsc = !state.sortAsc;
      else { state.sortKey = k; state.sortAsc = false; }
      renderTable();
    });
    document.querySelector("#tbl tbody").addEventListener("click", function (e) {
      var tr = e.target.closest("tr"); if (!tr) return;
      var k = tr.getAttribute("data-k"), i = state.selected.indexOf(k);
      if (i >= 0) state.selected.splice(i, 1); else state.selected.push(k); // toggle
      renderTable(); renderTrend();
    });

    renderAll();
  }
  init();
})();
