// Questions interactives (US-17, US-18). Amélioration progressive : sans ce script, les boutons radio
// (zone cliquable) et les listes déroulantes (appariement) suffisent, au clavier comme au toucher.
(function () {
  "use strict";

  // Prévient HTMX (hx-trigger="change" sur le formulaire) comme le ferait une saisie manuelle.
  function changed(field) { field.dispatchEvent(new Event("change", { bubbles: true })); }

  // --- Zone cliquable : un bouton transparent par zone, posé sur le schéma (coordonnées du viewBox). ---
  document.querySelectorAll("[data-hotspot]").forEach(function (figure) {
    var svg = figure.querySelector("svg");
    var labels = figure.parentNode.querySelectorAll(".choice[data-zone]");
    if (!svg || !labels.length) return;
    var box = (svg.getAttribute("viewBox") || "").split(/[\s,]+/).map(Number);
    if (box.length !== 4 || !box[2] || !box[3]) return;

    function sync() {
      figure.querySelectorAll(".zone").forEach(function (zone) {
        zone.classList.toggle("is-selected", zone._radio.checked);
      });
    }
    labels.forEach(function (label) {
      var z = label.dataset.zone.split(",").map(Number);
      var radio = label.querySelector("input");
      if (z.some(isNaN) || !radio) return;
      var zone = document.createElement("button");
      zone.type = "button";
      zone.className = "zone";
      zone.tabIndex = -1; // les boutons radio restent le chemin clavier
      zone.setAttribute("aria-hidden", "true");
      zone.style.left = ((z[0] - box[0]) / box[2] * 100) + "%";
      zone.style.top = ((z[1] - box[1]) / box[3] * 100) + "%";
      zone.style.width = (z[2] / box[2] * 100) + "%";
      zone.style.height = (z[3] / box[3] * 100) + "%";
      zone._radio = radio;
      zone.addEventListener("click", function () {
        radio.checked = true;
        changed(radio);
        sync();
      });
      figure.appendChild(zone);
      radio.addEventListener("change", sync);
    });
    figure.classList.add("is-live");
    sync();
  });

  // --- Appariement : étiquettes déplaçables vers chaque ligne (souris) ; la liste déroulante reste la référence. ---
  document.querySelectorAll("[data-matching]").forEach(function (box) {
    var first = box.querySelector("select");
    if (!first || !("draggable" in document.createElement("span"))) return;
    var pool = document.createElement("div");
    pool.className = "match-pool";
    pool.setAttribute("aria-hidden", "true");
    Array.prototype.forEach.call(first.options, function (option) {
      if (!option.value) return;
      var chip = document.createElement("span");
      chip.className = "match-chip";
      chip.draggable = true;
      chip.textContent = option.textContent;
      chip.addEventListener("dragstart", function (e) {
        e.dataTransfer.setData("text/plain", option.value);
        e.dataTransfer.effectAllowed = "copy";
      });
      pool.appendChild(chip);
    });
    box.insertBefore(pool, box.firstChild);

    box.querySelectorAll(".match-row").forEach(function (row) {
      var select = row.querySelector("select");
      row.addEventListener("dragover", function (e) { e.preventDefault(); row.classList.add("is-over"); });
      row.addEventListener("dragleave", function () { row.classList.remove("is-over"); });
      row.addEventListener("drop", function (e) {
        e.preventDefault();
        row.classList.remove("is-over");
        select.value = e.dataTransfer.getData("text/plain");
        changed(select);
      });
    });
  });
})();
