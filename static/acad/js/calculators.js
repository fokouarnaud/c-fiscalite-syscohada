// Calculateurs du cours (US-26, C12), non notés. Le serveur place des emplacements inertes
// <div class="calc" data-calc="tva|is|amortissement|reduction|stock|paie"> ; les formules sont dans calc-core.js
// (window.AcadCalc, vérifié contre referentiel/calculs.py), les taux en vigueur dans #calc-params (json_script)
// et les libellés traduits dans #calc-labels. Aucun script en ligne, aucun taux écrit ici.
(function () {
  "use strict";
  var slots = document.querySelectorAll(".calc[data-calc]");
  if (!slots.length || !window.AcadCalc) return;
  var C = window.AcadCalc;
  var L = (document.getElementById("calc-labels") || { dataset: {} }).dataset;
  var paramsNode = document.getElementById("calc-params");
  var P = paramsNode ? JSON.parse(paramsNode.textContent) : {};
  var lang = document.documentElement.lang || "fr";
  var money = new Intl.NumberFormat(lang, { maximumFractionDigits: 0 });

  function param(key) { return P[key]; }
  function bareme(prefix, valueSuffix) {
    var rows = [], i = 1;
    while (P[prefix + i + valueSuffix] !== undefined) {
      rows.push([P[prefix + i + "_plafond"] === undefined ? null : P[prefix + i + "_plafond"], P[prefix + i + valueSuffix]]);
      i++;
    }
    return rows;
  }
  // Même lecture que la correction serveur (calc-core.js, vérifiée contre assessments/scoring.py).
  function read(input) { return C.lire_nombre(input.value); }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text !== undefined) e.textContent = text;
    return e;
  }
  var uid = 0;
  function field(box, label, value) {
    var id = "calc-" + (++uid);
    var wrap = el("div", { "class": "field" });
    wrap.appendChild(el("label", { "for": id }, label));
    var input = el("input", { id: id, type: "text", inputmode: "decimal", autocomplete: "off" });
    if (value !== undefined) input.value = value;
    wrap.appendChild(input);
    box.appendChild(wrap);
    return input;
  }
  function choice(box, label, options) {
    var id = "calc-" + (++uid);
    var wrap = el("div", { "class": "field" });
    wrap.appendChild(el("label", { "for": id }, label));
    var select = el("select", { id: id });
    options.forEach(function (text, i) { select.appendChild(el("option", { value: String(i) }, text)); });
    wrap.appendChild(select);
    box.appendChild(wrap);
    return select;
  }
  function frame(slot, title, hint) {
    var box = el("section", { "class": "calc-box", "aria-label": title });
    box.appendChild(el("h3", {}, title));
    if (hint) box.appendChild(el("p", { "class": "hint" }, hint));
    slot.appendChild(box);
    var out = el("dl", { "class": "calc-out", "aria-live": "polite" });
    return { box: box, out: out };
  }
  function show(out, rows) {
    out.textContent = "";
    if (!rows) { out.appendChild(el("dd", {}, L.fillAll)); return; }
    rows.forEach(function (row) {
      out.appendChild(el("dt", {}, row[0]));
      out.appendChild(el("dd", {}, typeof row[1] === "number" ? money.format(row[1]) + " FCFA" : row[1]));
    });
  }
  function wire(f, inputs, compute) {
    f.box.appendChild(f.out);
    var run = function () {
      var values = inputs.map(function (i) { return i.tagName === "SELECT" ? Number(i.value) : read(i); });
      show(f.out, values.some(isNaN) ? null : compute(values));
    };
    inputs.forEach(function (i) { i.addEventListener("input", run); i.addEventListener("change", run); });
  }

  var BUILD = {
    tva: function (slot) {
      var f = frame(slot, L.tvaTitle, L.tvaHint);
      var mode = choice(f.box, L.amount, L.tvaModes.split(",")), amount = field(f.box, L.amount);
      wire(f, [mode, amount], function (v) {
        var principal = param("tva.taux_principal"), cac = param("cac.taux");
        if (v[0] === 0) {
          var r = C.tva_depuis_ht(v[1], principal, cac);
          return [[L.ht, r.ht], [L.tvaPrincipal, r.tva], [L.cac, r.cac], [L.taxes, r.taxes], [L.ttc, r.ttc]];
        }
        var t = C.tva_depuis_ttc(v[1], principal, cac);
        return [[L.ht, t.ht], [L.taxes, t.taxes], [L.ttc, t.ttc]];
      });
    },
    is: function (slot) {
      var f = frame(slot, L.isTitle, L.isHint);
      var profit = field(f.box, L.profit), turnover = field(f.box, L.turnover);
      wire(f, [profit, turnover], function (v) {
        var rate = C.taux_is(v[1], param("is.seuil_taux_reduit"), param("is.taux"), param("is.taux_reduit"));
        var r = C.impot_societes(v[0], v[1], rate, param("is.taux_minimum_perception"), param("cac.taux"));
        return [[L.rate, rate + " %"], [L.isTotal, r.is_total], [L.minimum, r.minimum_total], [L.due, r.du]];
      });
    },
    amortissement: function (slot) {
      var f = frame(slot, L.amortTitle);
      var method = choice(f.box, L.methods.split(",")[0] + " / " + L.methods.split(",")[1], L.methods.split(","));
      var cost = field(f.box, L.cost), years = field(f.box, L.years), month = field(f.box, L.startMonth, "1");
      var coefficient = field(f.box, L.coefficient, "2");
      wire(f, [method, cost, years, month, coefficient], function (v) {
        var plan = v[0] === 0 ? C.amortissement_lineaire(v[1], v[2], v[3]) : C.amortissement_degressif(v[1], v[2], v[4]);
        return plan.map(function (row, i) {
          return [L.year + " " + (i + 1), money.format(row.dotation) + " FCFA · " + L.nbv + " " + money.format(row.vnc)];
        });
      });
    },
    reduction: function (slot) {
      var f = frame(slot, L.reductionTitle);
      var inputs = [field(f.box, L.gross), field(f.box, L.remise, "0"), field(f.box, L.rabais, "0"),
                    field(f.box, L.ristourne, "0"), field(f.box, L.escompte, "0")];
      wire(f, inputs, function (v) {
        var r = C.facture(v[0], v[1], v[2], v[3], v[4], param("tva.taux_global"));
        return [[L.netCommercial, r.net_commercial], [L.escompte.replace(/\s*\(%\)$/, ""), r.escompte], [L.netFinancier, r.net_financier],
                [L.tva, r.tva], [L.ttc, r.ttc]];
      });
    },
    stock: function (slot) {
      var f = frame(slot, L.stockTitle, L.stockHint);
      var id = "calc-" + (++uid), wrap = el("div", { "class": "field" });
      wrap.appendChild(el("label", { "for": id }, L.lots));
      var lots = el("textarea", { id: id, rows: "3" });
      wrap.appendChild(lots);
      f.box.appendChild(wrap);
      var method = choice(f.box, L.stockMethods, L.stockMethods.split(",")), quantity = field(f.box, L.quantity);
      f.box.appendChild(f.out);
      var run = function () {
        var entries = lots.value.split("\n").filter(function (line) { return line.trim(); }).map(function (line) {
          return line.trim().split(/\s+/).map(Number);
        });
        var qty = read(quantity);
        if (!entries.length || isNaN(qty) || entries.some(function (e) { return e.length !== 2 || e.some(isNaN); })) {
          show(f.out, null); return;
        }
        try {
          var r = method.value === "0" ? C.sortie_cmup(entries, qty) : C.sortie_peps(entries, qty);
          var rows = [[L.issueValue, r.valeur_sortie], [L.stockValue, r.valeur_stock]];
          if (r.cout_unitaire !== undefined) rows.unshift([L.unitCost, r.cout_unitaire]);
          show(f.out, rows);
        } catch (error) { show(f.out, null); }
      };
      [lots, method, quantity].forEach(function (i) { i.addEventListener("input", run); i.addEventListener("change", run); });
    },
    paie: function (slot) {
      var f = frame(slot, L.paieTitle, L.paieHint);
      var gross = field(f.box, L.grossMonthly), base = field(f.box, L.baseMonthly), cnps = field(f.box, L.cnpsMonthly, "0");
      wire(f, [gross, base, cnps], function (v) {
        var scale = [[param("irpp.tranche1_plafond"), param("irpp.tranche1_taux")],
                     [param("irpp.tranche2_plafond"), param("irpp.tranche2_taux")],
                     [param("irpp.tranche3_plafond"), param("irpp.tranche3_taux")], [null, param("irpp.tranche4_taux")]];
        var irpp = C.irpp_salaire(v[0] * 12, v[2] * 12, param("irpp.taux_frais_professionnels"),
                                  param("irpp.plafond_frais_professionnels"), param("irpp.abattement_salaires"), scale,
                                  param("cac.taux"));
        var monthlyIrpp = C.franc(irpp.total / 12), cfc = C.credit_foncier(v[0], param("cfc.taux_salarie"));
        var rav = C.forfait_par_tranche(v[0], bareme("rav.tranche", "_montant"));
        var tdl = C.franc(C.forfait_par_tranche(v[1], bareme("tdl.tranche", "_montant")) / 12);
        return [[L.irpp, monthlyIrpp], [L.cfc, cfc], [L.rav, rav], [L.tdl, tdl],
                [L.withheld, v[2] + monthlyIrpp + cfc + rav + tdl]];
      });
    }
  };
  Array.prototype.forEach.call(slots, function (slot) {
    var build = BUILD[slot.getAttribute("data-calc")];
    if (build) build(slot);
  });
})();
