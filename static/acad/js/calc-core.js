// Moteur des calculateurs (US-26, C12) : mêmes formules que referentiel/calculs.py, au franc près.
// Fonctions pures, sans DOM : chargé par le navigateur (window.AcadCalc) et par Node pour le test de parité
// (referentiel/tests/test_calculs_parity.py sur referentiel/tests/vectors.json). Taux en pourcentage (17.5 = 17,5 %).
(function (root) {
  "use strict";
  function n(v) { return v === null || v === undefined ? null : Number(v); }
  // Arrondi au franc le plus proche, demi-franc vers le haut (montants positifs).
  function franc(x) { return Math.floor(x + 0.5 + 1e-9); }
  function millierInferieur(x) { return Math.floor(x / 1000 + 1e-9) * 1000; }

  function tva_depuis_ht(ht, tauxTva, tauxCac) {
    ht = n(ht);
    var tva = franc(ht * n(tauxTva) / 100), cac = franc(tva * n(tauxCac) / 100);
    return { ht: ht, tva: tva, cac: cac, taxes: tva + cac, ttc: ht + tva + cac };
  }
  function tva_depuis_ttc(ttc, tauxTva, tauxCac) {
    ttc = n(ttc);
    // ttc / (1 + t × (1 + c)) sur des entiers mis à l'échelle : 1 192 500 × 10 000 / 11 925.
    var ht = franc(ttc * 10000 / (10000 + n(tauxTva) * (100 + n(tauxCac))));
    return { ht: ht, taxes: ttc - ht, ttc: ttc };
  }
  function taux_is(ca, seuil, tauxNormal, tauxReduit) { return n(ca) <= n(seuil) ? n(tauxReduit) : n(tauxNormal); }
  function impot_societes(benefice, baseMinimum, tauxIs, tauxMinimum, tauxCac) {
    var impot = franc(millierInferieur(Math.max(n(benefice), 0)) * n(tauxIs) / 100);
    var minimum = franc(millierInferieur(n(baseMinimum)) * n(tauxMinimum) / 100);
    var isTotal = impot + franc(impot * n(tauxCac) / 100), minimumTotal = minimum + franc(minimum * n(tauxCac) / 100);
    return { is: impot, cac: isTotal - impot, is_total: isTotal, minimum: minimum, minimum_total: minimumTotal,
             du: Math.max(isTotal, minimumTotal) };
  }
  function amortissement_lineaire(valeur, annees, moisDebut) {
    valeur = n(valeur);
    var total = n(annees) * 12, restant = total, mois = 13 - (n(moisDebut) || 1), cumul = 0, plan = [];
    while (restant > 0) {
      mois = Math.min(mois, restant);
      var dotation = mois === restant ? valeur - cumul : franc(valeur * mois / total);
      cumul += dotation; restant -= mois;
      plan.push({ dotation: dotation, cumul: cumul, vnc: valeur - cumul });
      mois = 12;
    }
    return plan;
  }
  function amortissement_degressif(valeur, annees, coefficient) {
    valeur = n(valeur); annees = n(annees);
    var vnc = valeur, plan = [];
    for (var rang = 0; rang < annees; rang++) {
      var restant = annees - rang;
      var dotation = restant === 1 ? vnc : franc(Math.max(vnc * n(coefficient) / annees, vnc / restant));
      vnc -= dotation;
      plan.push({ dotation: dotation, cumul: valeur - vnc, vnc: vnc });
    }
    return plan;
  }
  function facture(brut, remise, rabais, ristourne, escompte, tauxTva) {
    var net = n(brut);
    [remise, rabais, ristourne].forEach(function (t) { net = franc(net * (100 - n(t)) / 100); });
    var montantEscompte = franc(net * n(escompte) / 100), netFinancier = net - montantEscompte;
    var tva = franc(netFinancier * n(tauxTva) / 100);
    return { brut: n(brut), net_commercial: net, escompte: montantEscompte, net_financier: netFinancier, tva: tva,
             ttc: netFinancier + tva };
  }
  function lots(entries) { return entries.map(function (l) { return [n(l[0]), n(l[1])]; }); }
  function verifier(stock, quantite) {
    var total = stock.reduce(function (s, l) { return s + l[0]; }, 0);
    if (quantite > total) throw new RangeError("Sortie supérieure au stock disponible.");
    return total;
  }
  function sortie_cmup(entries, quantite) {
    var stock = lots(entries); quantite = n(quantite);
    var total = verifier(stock, quantite);
    var cout = franc(stock.reduce(function (s, l) { return s + l[0] * l[1]; }, 0) / total);
    return { cout_unitaire: cout, valeur_sortie: cout * quantite, valeur_stock: cout * (total - quantite) };
  }
  function sortie_peps(entries, quantite) {
    var stock = lots(entries), reste = n(quantite), valeur = 0, restant = [];
    verifier(stock, reste);
    stock.forEach(function (l) {
      var prise = Math.min(l[0], reste);
      valeur += prise * l[1]; reste -= prise;
      if (l[0] > prise) restant.push([l[0] - prise, l[1]]);
    });
    return { valeur_sortie: valeur, valeur_stock: restant.reduce(function (s, l) { return s + l[0] * l[1]; }, 0),
             stock: restant };
  }
  function bareme_progressif(base, bareme) {
    var impot = 0, plancher = 0;
    for (var i = 0; i < bareme.length; i++) {
      var plafond = n(bareme[i][0]), haut = plafond === null ? base : Math.min(base, plafond);
      if (haut > plancher) impot += (haut - plancher) * n(bareme[i][1]) / 100;
      if (plafond === null || base <= plafond) break;
      plancher = plafond;
    }
    return franc(impot);
  }
  function irpp_salaire(brutAnnuel, cnpsAnnuelle, tauxFrais, plafondFrais, abattement, bareme, tauxCac) {
    var brut = n(brutAnnuel);
    var frais = Math.min(franc(brut * n(tauxFrais) / 100), n(plafondFrais));
    var net = brut - frais - n(cnpsAnnuelle), imposable = Math.max(net - n(abattement), 0);
    var irpp = bareme_progressif(imposable, bareme), cac = franc(irpp * n(tauxCac) / 100);
    return { frais: frais, net: net, imposable: imposable, irpp: irpp, cac: cac, total: irpp + cac };
  }
  function forfait_par_tranche(base, tranches) {
    for (var i = 0; i < tranches.length; i++) {
      if (tranches[i][0] === null || n(base) <= n(tranches[i][0])) return n(tranches[i][1]);
    }
    throw new RangeError("Barème sans tranche supérieure.");
  }
  function credit_foncier(salaire, taux) { return franc(millierInferieur(n(salaire)) * n(taux) / 100); }

  // Saisie d'un nombre, mêmes règles que assessments/scoring.py (C11) : « 1 250 000 », « 1.250.000 », « 1,000,000 »,
  // « 19,25 », « 1.250.000,50 » ; NaN pour une saisie ambiguë, fausse ou suivie d'une unité.
  function grouped(digits, sep) {
    return new RegExp("^\\d{1,3}(" + (sep === "." ? "\\." : sep) + "\\d{3})+$").test(digits);
  }
  function lire_nombre(text) {
    text = String(text).replace(/[  ]/g, " ").replace(/−/g, "-").trim();
    var m = text.match(/^([+-]?)(\d[\d .,]*?)\s*$/);
    if (!m) return NaN;
    var sign = m[1], digits = m[2].replace(/ +/g, " ").trim(), dots = (digits.match(/\./g) || []).length;
    var commas = (digits.match(/,/g) || []).length, number;
    if (digits.indexOf(" ") >= 0) {
      if (!/^\d{1,3}( \d{3})+([.,]\d+)?$/.test(digits)) return NaN;
      number = digits.replace(/ /g, "").replace(",", ".");
    } else if (dots && commas) {
      var decimal = digits.lastIndexOf(".") > digits.lastIndexOf(",") ? "." : ",", thousands = decimal === "." ? "," : ".";
      var cut = digits.lastIndexOf(decimal), whole = digits.slice(0, cut), fraction = digits.slice(cut + 1);
      if (!/^\d+$/.test(fraction) || !grouped(whole, thousands)) return NaN;
      number = whole.split(thousands).join("") + "." + fraction;
    } else if (dots > 1 || commas > 1) {
      var sep = dots > 1 ? "." : ",";
      if (!grouped(digits, sep)) return NaN;
      number = digits.split(sep).join("");
    } else if (dots === 1 && /^\d{1,3}\.\d{3}$/.test(digits)) {
      number = digits.replace(".", ""); // un seul point suivi de trois chiffres : milliers (usage français)
    } else {
      number = digits.replace(",", ".");
    }
    return Number(sign + number);
  }

  var api = { franc: franc, tva_depuis_ht: tva_depuis_ht, tva_depuis_ttc: tva_depuis_ttc, taux_is: taux_is,
              impot_societes: impot_societes, amortissement_lineaire: amortissement_lineaire,
              amortissement_degressif: amortissement_degressif, facture: facture, sortie_cmup: sortie_cmup,
              sortie_peps: sortie_peps, bareme_progressif: bareme_progressif, irpp_salaire: irpp_salaire,
              forfait_par_tranche: forfait_par_tranche, credit_foncier: credit_foncier, lire_nombre: lire_nombre };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.AcadCalc = api;
})(this);
