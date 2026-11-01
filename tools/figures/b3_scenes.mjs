// Scènes isométriques du parcours B3 (S33) : SVG statiques FR et EN, sans script, dans static/content/simulation/b3/.
// Usage, depuis la racine du projet : node tools/figures/b3_scenes.mjs
// Node ne sert qu'à l'écriture du contenu (kit anatomy recopié dans tools/figures/kit) ; rien n'est déployé côté Node.
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "./kit/iso-kit.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = join(ROOT, "static", "content", "simulation", "b3");
const W = 720;
const H = 390;

// Le SVG suit le thème du système, comme le site (static/acad/css/app.css, prefers-color-scheme).
const DARK = k.ISO_CSS.match(/\.iso\{([\s\S]*?)\}/)[1];
const THEMED = `@media (prefers-color-scheme: dark){.iso[data-theme="light"]{${DARK}}}`
  + `.cap{font:600 17px system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--anatomy-strong)}`
  + `.sub{font:12px system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--anatomy-text)}`
  + `.bg{fill:var(--anatomy-card)}`;

const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (points, style) => k.dotsSvg(points, style);

function frame(P, lang, title, caption, body, label) {
  const svg = k.figureSvg({ width: W, height: H, standalone: "light", label, body: [
    `<rect class="bg" width="${W}" height="${H}" rx="14"/>`,
    `<text class="cap" x="24" y="34">${title}</text>`,
    ...body,
    // Pas de légende dans l'image : le texte de la scène l'explique, en taille lisible.
  ] });
  return svg.replace("</style>", `${THEMED}</style>`).replace("<svg ", `<svg width="${W}" height="${H}" lang="${lang}" `);
}

// ---------------------------------------------------------------- figure 1 : le circuit des casiers

const PLATE = { x: -230, y: -80, w: 460, d: 175, r: 10 };
const PLATE_H = 8;
const ROAD = { x: -215, y: 38, w: 430, d: 40, r: 4 };
const LANE_FULL = 48;   // y du couloir des pleins (vers le snack-bar)
const LANE_EMPTY = 68;  // y du couloir des vides (retour vers la brasserie)
const BREW = { x: -215, y: -70, w: 95, d: 70, r: 3 };
const DEPOT = { x: -55, y: -70, w: 110, d: 82, r: 3 };
const SNACK = { x: 125, y: -55, w: 72, d: 55, r: 3 };

function crate(x, y, z, full, P) {
  const plan = { x, y, w: 13, d: 9, r: 1 };
  const out = [S(k.slabOf(plan, z, 5, P, 2, 0.3), { tone: full ? "hi" : "mid", crease: "lo", lit: full })];
  out.push(L(k.sideSeam(plan, z + 2.5, P, 2), { tone: "faint" }));
  const necks = [];
  for (let i = 0; i < 4; i++) for (let j = 0; j < 3; j++) necks.push([x + 2 + i * 3, y + 1.8 + j * 2.7]);
  if (full) {
    out.push(D(necks.map(([a, b]) => k.iso([a, b, z + 5.6], P)), { size: 0.55, tone: "hi" }));
  } else {
    out.push(L(necks.map(([a, b]) => k.ring(a, b, 0.7, z + 5, P, 8)).join(""), { tone: "lo" }));
  }
  return { depth: k.depthOf([x + 6.5, y + 4.5, z], P), svg: out.join("") };
}

function brewery(P) {
  const items = [];
  const hall = { x: BREW.x + 30, y: BREW.y, w: 65, d: 50, r: 2 };
  items.push({ depth: k.depthOf([hall.x + 30, hall.y + 25, 0], P), svg: [
    `<path class="iso-halo" d="${k.haloOf(hall, 0, 42, P)}"/>`,
    S(k.slabOf(hall, 0, 42, P, 3, 0.6), { tone: "mid" }),
    L(k.sideSeam(hall, 14, P, 3) + k.sideSeam(hall, 28, P, 3), { tone: "faint" }),
    S(k.slabOf(k.insetPlan(hall, -2), 42, 3, P, 3, 0.5), { tone: "mid" }),
    L(k.planOutline(k.insetPlan(hall, 6), 45, P, 3), { tone: "lo" }),
    D(k.corners(hall, 4).map(([a, b]) => k.iso([a, b, 45], P)), { size: 0.45 }),
    k.faceTextSvg(k.sideMatrix([hall.x + 32, hall.y + hall.d], 36, P, "left"), "BRASSERIE", { size: 7.6, tone: "hi", anchor: "middle" }),
  ].join("") });
  // Porte de chargement sur la façade avant.
  const dock = { x: hall.x + 10, y: hall.y + hall.d, w: 40, d: 12, r: 1 };
  items.push({ depth: k.depthOf([dock.x + 20, dock.y + 6, 0], P), svg: [
    S(k.slabOf(dock, 0, 6, P, 2, 0.4), { tone: "mid" }),
    L(k.topTicks(dock.x + 3, dock.x + dock.w - 3, 3, 5, dock.y + 1, 6, [1.5, 3], P).minor, { tone: "faint" }),
  ].join("") });
  // Deux cuves de fermentation et une cheminée.
  for (const [cx, cy, r, h] of [[BREW.x + 12, BREW.y + 14, 10, 62], [BREW.x + 12, BREW.y + 42, 10, 62], [hall.x + 52, hall.y + 10, 4, 74]]) {
    items.push({ depth: k.depthOf([cx, cy, 0], P), svg: [
      S(k.cylinder(cx, cy, r, 0, h, P, 40, 0.5), { tone: "mid" }),
      L([0.25, 0.5, 0.75].map((f) => k.sideArc(cx, cy, r, h * f, P, 24)).join(""), { tone: "faint" }),
      S(k.cylinder(cx, cy, r * 0.55, h, 3, P, 24), { tone: "mid" }),
    ].join("") });
  }
  return items;
}

function depot(P) {
  const items = [];
  const floor = DEPOT;
  items.push({ depth: -1e6 + 1, svg: [
    `<path class="iso-halo" d="${k.haloOf(floor, 0, 2, P)}"/>`,
    S(k.slabOf(floor, 0, 2, P, 3, 0.4), { tone: "mid" }),
    L(k.planOutline(k.insetPlan(floor, 4), 2, P, 3), { tone: "faint" }),
  ].join("") });
  const back = { x: floor.x, y: floor.y, w: floor.w, d: 5, r: 1 };
  const side = { x: floor.x, y: floor.y, w: 5, d: floor.d - 30, r: 1 };
  items.push({ depth: -1e6 + 2, svg: [
    S(k.slabOf(back, 2, 40, P, 2, 0.4), { tone: "mid" }),
    S(k.slabOf(side, 2, 40, P, 2, 0.4), { tone: "mid" }),
    L(k.sideSeam(back, 22, P, 2), { tone: "faint" }),
    S(k.slabOf({ x: floor.x - 3, y: floor.y - 3, w: floor.w + 6, d: 34, r: 1 }, 42, 3, P, 2, 0.5), { tone: "lo" }),
    k.faceTextSvg(k.sideMatrix([floor.x + 55, floor.y + 5], 38, P, "left"), "ATEBA BOISSONS", { size: 6.6, tone: "hi", anchor: "middle" }),
  ].join("") });
  for (const [px, py] of [[floor.x + floor.w - 5, floor.y + 29], [floor.x + 2, floor.y + 29]]) {
    items.push({ depth: k.depthOf([px, py, 0], P), svg: S(k.slabOf({ x: px - 2, y: py - 2, w: 4, d: 4, r: 0.6 }, 2, 40, P, 2), { tone: "mid" }) });
  }
  // Piles de casiers : pleins à gauche, vides à droite.
  for (let col = 0; col < 4; col++) for (let row = 0; row < 3; row++) for (let lev = 0; lev < 3; lev++) {
    const full = col < 2;
    const c = crate(floor.x + 10 + col * 15 + (col > 1 ? 14 : 0), floor.y + 12 + row * 11, 2 + lev * 5.2, full, P);
    items.push({ ...c, depth: c.depth + lev * 0.01 });
  }
  return items;
}

function snackbar(P) {
  const items = [];
  const kiosk = { x: SNACK.x, y: SNACK.y, w: SNACK.w, d: 26, r: 2 };
  items.push({ depth: k.depthOf([kiosk.x + 36, kiosk.y + 13, 0], P), svg: [
    `<path class="iso-halo" d="${k.haloOf(kiosk, 0, 30, P)}"/>`,
    S(k.slabOf(kiosk, 0, 30, P, 3, 0.5), { tone: "mid" }),
    L(k.sideSeam(kiosk, 12, P, 3), { tone: "faint" }),
  ].join("") });
  const awning = { x: SNACK.x - 3, y: SNACK.y + 18, w: SNACK.w + 6, d: 16, r: 1 };
  items.push({ depth: k.depthOf([awning.x + 36, awning.y + 8, 30], P) + 40, svg: [
    S(k.slabOf(awning, 31, 2, P, 2, 0.4), { tone: "lo" }),
    L(Array.from({ length: 11 }, (_, i) => k.lineOnTop([awning.x + 3 + i * 7, awning.y], [awning.x + 3 + i * 7, awning.y + awning.d], 33, P)).join(""), { tone: "faint" }),
  ].join("") });
  const counter = { x: SNACK.x + 4, y: SNACK.y + 28, w: SNACK.w - 8, d: 7, r: 1 };
  items.push({ depth: k.depthOf([counter.x + 30, counter.y + 3, 0], P), svg: [
    S(k.slabOf(counter, 0, 14, P, 2, 0.4), { tone: "mid" }),
    ...[10, 22, 34, 46].map((dx) => S(k.cylinder(counter.x + dx, counter.y + 3.5, 1.2, 14, 6, P, 12), { tone: "hi", lit: true })),
  ].join("") });
  for (const dx of [12, 32, 52]) {
    const [cx, cy] = [SNACK.x + dx, SNACK.y + 44];
    items.push({ depth: k.depthOf([cx, cy, 0], P), svg: [
      S(k.cylinder(cx, cy, 1.3, 0, 9, P, 12), { tone: "mid" }),
      S(k.cylinder(cx, cy, 3.6, 9, 1.4, P, 20, 0.3), { tone: "mid" }),
    ].join("") });
  }
  for (const [dx, lev] of [[60, 0], [60, 1]]) items.push(crate(SNACK.x + dx, SNACK.y + 30, lev * 5.2, false, P));
  return items;
}

function circuitFigure(lang) {
  const t = {
    fr: { title: "Le circuit des casiers et des consignes", full: "PLEINS", empty: "VIDES",
          cap: ["La brasserie consigne chaque casier livré (créance 4094) ; le dépôt consigne à son tour les casiers livrés",
                "au snack-bar (dette 4194). Les vides reviennent et la consigne est remboursée, moins un mali ou un boni."],
          label: "Maquette isométrique : une brasserie, le dépôt Ateba Boissons et le snack-bar Le Rond-Point, reliés par une route à deux couloirs ; les casiers pleins vont vers le snack-bar, les casiers vides reviennent vers la brasserie ; plaques 4094 côté brasserie et 4194 côté snack-bar." },
    en: { title: "The crate and deposit circuit", full: "FULL", empty: "EMPTY",
          cap: ["The brewery charges a deposit on each crate delivered (receivable 4094); the depot charges one on crates",
                "delivered to the snack bar (debt 4194). Empties come back and deposits are refunded, less any loss or gain."],
          label: "Isometric model: a brewery, the Ateba Boissons depot and the Le Rond-Point snack bar, linked by a two-lane road; full crates go to the snack bar and empty crates return to the brewery; plates 4094 on the brewery side and 4194 on the snack-bar side." },
  }[lang];
  const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - 4, 0), [BREW.x + 82, BREW.y + 10, 76], [DEPOT.x, DEPOT.y, 48]], W, H - 40,
    { pad: 20, azimuth: 72 });
  P.origin = [P.origin[0], P.origin[1] + 36];
  const base = [
    `<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - 4, PLATE_H, P)}"/>`,
    ...k.corners(PLATE, 18).sort((a, b) => k.depthOf([...a, 0], P) - k.depthOf([...b, 0], P))
      .map(([x, y]) => S(k.cylinder(x, y, 6, -PLATE_H - 4, 4, P, 24), { tone: "lo" })),
    S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.2), { tone: "mid" }),
    L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "faint" }),
    D(k.corners(PLATE, 10).map(([x, y]) => k.iso([x, y, 0], P)), { size: 0.5 }),
    S(k.slabOf({ x: PLATE.x + 20, y: PLATE.y + PLATE.d - 11, w: PLATE.w - 40, d: 6, r: 1 }, 0, 0.6, P, 3), { tone: "lo", crease: "none" }),
    ...(() => { const r = k.topTicks(PLATE.x + 24, PLATE.x + PLATE.w - 24, 5, 5, PLATE.y + PLATE.d - 10.4, 0.6, [1.6, 3.2], P);
      return [L(r.minor, { tone: "lo" }), L(r.major, { tone: "mid" })]; })(),
    S(k.slabOf(ROAD, 0, 0.8, P, 3), { tone: "lo", crease: "none" }),
    L(k.lineOnTop([ROAD.x + 4, (LANE_FULL + LANE_EMPTY) / 2 + 0], [ROAD.x + ROAD.w - 4, (LANE_FULL + LANE_EMPTY) / 2], 0.8, P), { tone: "mid", dashed: true }),
    L(k.planOutline(k.insetPlan(ROAD, 2), 0.8, P, 3), { tone: "faint" }),
  ];
  const items = [...brewery(P), ...depot(P), ...snackbar(P)];
  // Couloir des pleins (avant du dépôt vers le snack-bar et de la brasserie vers le dépôt) et des vides (retour).
  for (const x of [-170, -140, -110, 75, 100, 145, 175]) items.push(crate(x, LANE_FULL - 4.5, 0.8, true, P));
  for (const x of [-185, -125, -95, 85, 120, 160]) items.push(crate(x, LANE_EMPTY - 4.5, 0.8, false, P));
  // Panneaux des comptes de consigne et des couloirs, debout au bord de la route (texte sur la face avant).
  const sign = (x, text, wide, tone) => {
    const y = ROAD.y + ROAD.d + 5;
    const board = { x: x - wide / 2, y, w: wide, d: 2, r: 0.4 };
    return { depth: k.depthOf([x, y, 0], P) + 200, svg: [
      S(k.cylinder(x - wide / 2 + 3, y + 1, 0.9, 0, 9, P, 10), { tone: "mid" }),
      S(k.cylinder(x + wide / 2 - 3, y + 1, 0.9, 0, 9, P, 10), { tone: "mid" }),
      S(k.slabOf(board, 9, 11, P, 2, 0.3), { tone: "hi", lit: tone === "lit" }),
      D([[x - wide / 2 + 2, y + 2, 16.5], [x + wide / 2 - 2, y + 2, 16.5]].map((p) => k.iso(p, P)), { size: 0.35 }),
      k.faceTextSvg(k.sideMatrix([x, y + 2], 11.6, P, "left"), text, { size: 7.4, tone: "hi", anchor: "middle" }),
    ].join("") };
  };
  items.push(sign(-80, `${t.full} → 4094`, 74, "lit"), sign(100, `4194 ← ${t.empty}`, 74, "lit"));
  // Camion de la brasserie sur le couloir des pleins : châssis, cabine, plateau chargé, roues.
  const tx = -60, ty = LANE_FULL - 9;
  const truck = [];
  for (const wx of [tx + 6, tx + 20, tx + 40]) {
    for (const wy of [ty - 0.5, ty + 15.5]) truck.push(S(k.slabOf({ x: wx - 4, y: wy - 1.5, w: 8, d: 3, r: 1.4 }, 0.8, 7, P, 3), { tone: "lo" }));
  }
  truck.push(S(k.slabOf({ x: tx, y: ty, w: 52, d: 18, r: 1 }, 5, 3, P, 2, 0.4), { tone: "mid" }));
  truck.push(S(k.slabOf({ x: tx + 40, y: ty + 0.5, w: 12, d: 17, r: 2 }, 8, 13, P, 3, 0.5), { tone: "mid" }));
  truck.push(S(k.slabOf({ x: tx + 46, y: ty + 2, w: 5.6, d: 14, r: 1 }, 15, 4.5, P, 2), { tone: "lo", crease: "none" }));
  truck.push(L(k.sideSeam({ x: tx + 40, y: ty + 0.5, w: 12, d: 17, r: 2 }, 12, P, 3), { tone: "faint" }));
  const bed = [];
  for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) for (let lev = 0; lev < 2; lev++) {
    bed.push(crate(tx + 2 + i * 12.5, ty + 0.5 + j * 9, 8 + lev * 5.2, true, P));
  }
  bed.sort((a, b) => a.depth - b.depth);
  truck.push(...bed.map((c) => c.svg));
  truck.push(S(k.slabOf({ x: tx, y: ty + 17, w: 39, d: 1, r: 0.2 }, 8, 4, P, 2), { tone: "mid" }));
  items.push({ depth: k.depthOf([tx + 26, ty + 9, 0], P), svg: `<path class="iso-halo" d="${k.haloOf({ x: tx, y: ty, w: 52, d: 18, r: 2 }, 0.8, 1, P)}"/>` + truck.join("") });
  // Lampadaires le long de la route, côté bâtiments.
  for (const x of [-200, -120, -20, 70, 170]) {
    items.push({ depth: k.depthOf([x, ROAD.y - 3, 0], P), svg: [
      S(k.cylinder(x, ROAD.y - 3, 2.2, 0, 1.2, P, 16), { tone: "lo" }),
      S(k.cylinder(x, ROAD.y - 3, 0.8, 1.2, 26, P, 10), { tone: "mid" }),
      S(k.slabOf({ x: x - 1.2, y: ROAD.y - 3.5, w: 2.4, d: 8, r: 0.6 }, 27, 1.6, P, 2), { tone: "mid" }),
      D([k.iso([x, ROAD.y + 3.5, 27], P)], { size: 0.6, tone: "hi" }),
    ].join("") });
  }
  // Enseigne du snack-bar sur le toit du kiosque.
  const board = { x: SNACK.x + 8, y: SNACK.y + 12, w: 56, d: 2, r: 0.4 };
  items.push({ depth: k.depthOf([SNACK.x + 36, SNACK.y + 12, 30], P) + 30, svg: [
    S(k.cylinder(board.x + 4, board.y + 1, 0.8, 30, 3, P, 10), { tone: "mid" }),
    S(k.cylinder(board.x + board.w - 4, board.y + 1, 0.8, 30, 3, P, 10), { tone: "mid" }),
    S(k.slabOf(board, 33, 9, P, 2, 0.3), { tone: "hi" }),
    k.faceTextSvg(k.sideMatrix([board.x + board.w / 2, board.y + 2], 35.6, P, "left"), "LE ROND-POINT", { size: 6.4, tone: "hi", anchor: "middle" }),
  ].join("") });
  items.sort((a, b) => a.depth - b.depth);
  return frame(P, lang, t.title, t.cap, [...base, ...items.map((i) => i.svg)], t.label);
}

// ---------------------------------------------------------------- figure 2 : les trois caisses du dépôt

const BENCH = { x: -200, y: -70, w: 400, d: 150, r: 10 };

function signAt(x, y, z, text, wide, P, lit = false, from = null) {
  const board = { x: x - wide / 2, y, w: wide, d: 2, r: 0.4 };
  const posts = from === null ? [] : [x - wide / 2 + 4, x + wide / 2 - 4].map((px) => S(k.cylinder(px, y + 1, 0.9, from, z - from, P, 10), { tone: "mid" }));
  return [
    ...posts,
    S(k.slabOf(board, z, 12, P, 2, 0.3), { tone: "hi", lit }),
    D([[x - wide / 2 + 2, y + 2, z + 8.5], [x + wide / 2 - 2, y + 2, z + 8.5]].map((p) => k.iso(p, P)), { size: 0.35 }),
    k.faceTextSvg(k.sideMatrix([x, y + 2], z + 2.6, P, "left"), text, { size: 7.6, tone: "hi", anchor: "middle" }),
  ].join("");
}

function tillsFigure(lang) {
  const t = {
    fr: { title: "Les trois caisses du dépôt et le virement interne", counter: "CAISSE 5711", phone: "ORANGE MONEY 5522",
          bank: "BANQUE 521", hub: "585 VIREMENTS DE FONDS",
          cap: ["La recette du comptoir (5711) et le solde Orange Money (5522) partent vers la banque (521) en passant par 585 :",
                "on crédite la caisse à la sortie, on débite la banque à l'arrivée, et 585 revient à zéro."],
          label: "Maquette isométrique : un comptoir avec tiroir-caisse (5711), un téléphone Orange Money sur son socle (5522) et une agence bancaire (521), reliés par deux rails qui convergent vers une boîte de transit marquée 585, d'où un rail mène à la banque." },
    en: { title: "The depot's three tills and the internal transfer", counter: "CASH 5711", phone: "ORANGE MONEY 5522",
          bank: "BANK 521", hub: "585 FUNDS IN TRANSIT",
          cap: ["Counter takings (5711) and the Orange Money balance (5522) go to the bank (521) through 585:",
                "the till is credited when the money leaves, the bank debited when it arrives, and 585 returns to zero."],
          label: "Isometric model: a counter with a cash drawer (5711), an Orange Money phone on its stand (5522) and a bank branch (521), linked by two rails that meet at a transit box marked 585, from which a rail runs to the bank." },
  }[lang];
  const P = k.fitProjection([...k.boxCorners(BENCH, -12, 0), [120, -40, 70]], W, H - 40, { pad: 22, azimuth: 62 });
  P.origin = [P.origin[0], P.origin[1] + 36];
  const items = [];
  const base = [
    `<path class="iso-halo" d="${k.haloOf(BENCH, -12, 8, P)}"/>`,
    ...k.corners(BENCH, 18).sort((a, b) => k.depthOf([...a, 0], P) - k.depthOf([...b, 0], P))
      .map(([x, y]) => S(k.cylinder(x, y, 6, -12, 4, P, 24), { tone: "lo" })),
    S(k.slabOf(BENCH, -8, 8, P, 8, 1.2), { tone: "mid" }),
    L(k.planOutline(k.insetPlan(BENCH, 5), 0, P), { tone: "faint" }),
    D(k.corners(BENCH, 10).map(([x, y]) => k.iso([x, y, 0], P)), { size: 0.5 }),
  ];
  // Rails : comptoir → 585, téléphone → 585, 585 → banque ; billets (lit) posés dessus.
  const HUB = [10, 10];
  const rails = [[[-140, 40], HUB], [[-110, -35], HUB], [HUB, [110, 10]]];
  for (const [[ax, ay], [bx, by]] of rails) {
    const len = Math.hypot(bx - ax, by - ay);
    const ux = (bx - ax) / len, uy = (by - ay) / len;
    for (const side of [-3, 3]) {
      base.push(L(k.lineOnTop([ax - uy * side, ay + ux * side], [bx - uy * side, by + ux * side], 0.4, P), { tone: "mid" }));
    }
    for (let s = 6; s < len - 4; s += 6) {
      const [cx, cy] = [ax + ux * s, ay + uy * s];
      base.push(L(k.lineOnTop([cx - uy * 4, cy + ux * 4], [cx + uy * 4, cy - ux * 4], 0.2, P), { tone: "faint" }));
    }
    for (const f of [0.3, 0.65]) {
      const [cx, cy] = [ax + (bx - ax) * f, ay + (by - ay) * f];
      items.push({ depth: k.depthOf([cx, cy, 1], P), svg: [
        S(k.slabOf({ x: cx - 4, y: cy - 2.5, w: 8, d: 5, r: 0.4 }, 0.4, 2.4, P, 2, 0.3), { tone: "hi", lit: true }),
        L(k.ring(cx, cy, 1.3, 2.8, P, 12), { tone: "mid" }),
      ].join("") });
    }
  }
  // Comptoir et tiroir-caisse (5711).
  const counter = { x: -175, y: 25, w: 60, d: 26, r: 2 };
  items.push({ depth: k.depthOf([counter.x + 30, counter.y + 13, 0], P), svg: [
    signAt(counter.x + 30, counter.y - 4, 40, t.counter, 64, P, false, 0),
    `<path class="iso-halo" d="${k.haloOf(counter, 0, 26, P)}"/>`,
    S(k.slabOf(counter, 0, 26, P, 3, 0.6), { tone: "mid" }),
    L(k.sideSeam(counter, 9, P, 3), { tone: "faint" }),
    S(k.slabOf({ x: counter.x + 14, y: counter.y + 4, w: 30, d: 18, r: 1.5 }, 26, 7, P, 3, 0.5), { tone: "hi", lit: true }),
    S(k.slabOf({ x: counter.x + 14, y: counter.y + 22, w: 30, d: 9, r: 1 }, 18, 6, P, 2, 0.4), { tone: "mid" }),
    L(k.planOutline({ x: counter.x + 17, y: counter.y + 7, w: 24, d: 11, r: 1 }, 33, P, 2), { tone: "lo" }),
    D(k.dotGrid(counter.x + 19, counter.y + 9, 5, 2, 4, 33, P), { size: 0.5, tone: "mid" }),
  ].join("") });
  // Téléphone Orange Money sur son socle (5522).
  const stand = { x: -132, y: -60, w: 40, d: 26, r: 3 };
  items.push({ depth: k.depthOf([stand.x + 20, stand.y + 13, 0], P), svg: [
    signAt(stand.x + 20, stand.y - 4, 18, t.phone, 90, P, false, 0),
    `<path class="iso-halo" d="${k.haloOf(stand, 0, 8, P)}"/>`,
    S(k.slabOf(stand, 0, 8, P, 3, 0.6), { tone: "mid" }),
    S(k.slabOf({ x: stand.x + 8, y: stand.y + 6, w: 24, d: 14, r: 2 }, 8, 3, P, 3, 0.4), { tone: "hi", lit: true }),
    S(k.slabOf({ x: stand.x + 10, y: stand.y + 8, w: 20, d: 10, r: 1 }, 11, 0.4, P, 2), { tone: "lo", crease: "none", flat: true }),
    D(k.dotGrid(stand.x + 13, stand.y + 10, 4, 2, 4, 11.4, P), { size: 0.45, tone: "hi" }),
  ].join("") });
  // Boîte de transit 585 au carrefour des rails.
  const hub = { x: HUB[0] - 16, y: HUB[1] - 12, w: 32, d: 24, r: 2 };
  items.push({ depth: k.depthOf([HUB[0], HUB[1], 0], P), svg: [
    signAt(HUB[0], hub.y - 4, 26, t.hub, 132, P, true, 0),
    `<path class="iso-halo" d="${k.haloOf(hub, 0, 18, P)}"/>`,
    S(k.slabOf(hub, 0, 18, P, 3, 0.6), { tone: "mid" }),
    S(k.slabOf(k.insetPlan(hub, 4), 18, 2, P, 3, 0.4), { tone: "mid" }),
    L(k.lineOnTop([hub.x + 8, HUB[1]], [hub.x + hub.w - 8, HUB[1]], 20, P), { tone: "lo" }),
    D(k.corners(hub, 2.5).map(([a, b]) => k.iso([a, b, 18], P)), { size: 0.4 }),
  ].join("") });
  // Agence bancaire (521) : bâtiment à colonnes, perron, coffre.
  const bank = { x: 105, y: -50, w: 80, d: 70, r: 3 };
  items.push({ depth: k.depthOf([bank.x + 40, bank.y + 35, 0], P), svg: [
    `<path class="iso-halo" d="${k.haloOf(bank, 0, 50, P)}"/>`,
    S(k.slabOf(k.insetPlan(bank, -4), 0, 4, P, 3, 0.5), { tone: "mid" }),
    S(k.slabOf({ x: bank.x, y: bank.y, w: bank.w, d: bank.d - 16, r: 2 }, 4, 44, P, 3, 0.6), { tone: "mid" }),
    L(k.sideSeam({ x: bank.x, y: bank.y, w: bank.w, d: bank.d - 16, r: 2 }, 24, P, 3), { tone: "faint" }),
    S(k.slabOf(k.insetPlan(bank, -3), 48, 4, P, 3, 0.6), { tone: "mid" }),
    L(k.planOutline(k.insetPlan(bank, 6), 52, P, 3), { tone: "lo" }),
  ].join("") });
  for (const cx of [bank.x + 8, bank.x + 24, bank.x + 40, bank.x + 56, bank.x + 72]) {
    items.push({ depth: k.depthOf([cx, bank.y + bank.d - 8, 0], P), svg: [
      S(k.cylinder(cx, bank.y + bank.d - 8, 2.6, 4, 44, P, 20), { tone: "hi" }),
      L(k.knurl(cx, bank.y + bank.d - 8, 2.6, 8, 44, 8, P), { tone: "faint" }),
    ].join("") });
  }
  items.push({ depth: k.depthOf([bank.x + 40, bank.y + bank.d, 60], P) + 100, svg: signAt(bank.x + 40, bank.y + 30, 52, t.bank, 62, P, false, 52) });
  items.sort((a, b) => a.depth - b.depth);
  return frame(P, lang, t.title, t.cap, [...base, ...items.map((i) => i.svg)], t.label);
}

mkdirSync(OUT, { recursive: true });
for (const lang of ["fr", "en"]) {
  writeFileSync(join(OUT, `circuit-casiers.${lang}.svg`), circuitFigure(lang));
  writeFileSync(join(OUT, `trois-caisses.${lang}.svg`), tillsFigure(lang));
}
console.log("wrote", OUT);
