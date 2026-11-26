"use strict";
const COUNTRIES = ["", "Brazil", "France", "Portugal", "United States", "Argentina", "Spain", "Italy", "Germany", "United Kingdom", "Canada", "Mexico", "Chile", "Colombia"];
const I18N = {
  en: {
    patient: "Patient", clinician: "Clinician", eyebrow: "For patients, families and clinicians", h1: "From mutation to trial brief.",
    lede: "Enter an rsID or a gene + protein change. Get the papers, the trial landscape and the studies recruiting near you — every line linked to its source.",
    lq: "Variant", lc: "Condition (optional)", lco: "Country", go: "Build brief", try: "Try", any: "Any country", loading: "Building brief from public sources…",
    disc: "", privacy: "Privacy: queries are sent to public NCBI and ClinicalTrials.gov APIs. No accounts, no cookies, queries are not logged.",
    variant: "Variant", gene: "Gene", change: "Protein change", clinvar: "Clinical significance (ClinVar)", conds: "Reported conditions", stars: "Review", none: "No ClinVar record",
    at_glance: "At a glance", s_rec: "Recruiting now", s_soon: "Not yet recruiting", s_total: "Trials matched to this variant", s_pubs: "PubMed papers", s_site: "Recruiting in",
    trials: "Clinical trials", status: "Status", match: "Match level", phase: "Phase", all: "All",
    st_RECRUITING: "Recruiting", st_NOT_YET_RECRUITING: "Not yet recruiting", st_ACTIVE_NOT_RECRUITING: "Active, not recruiting", st_ENROLLING_BY_INVITATION: "Enrolling by invitation", st_COMPLETED: "Completed", st_TERMINATED: "Terminated", st_WITHDRAWN: "Withdrawn", st_SUSPENDED: "Suspended", st_UNKNOWN: "Unknown status",
    tab_recruiting: "Recruiting", tab_soon: "Not yet recruiting", tab_active: "Active", tab_closed: "Completed / other", tab_all: "All",
    m_variant: "Exact variant", m_codon: "Same codon", m_gene: "Gene only", m_condition: "Condition only",
    m_variant_d: "Names this exact variant as part of the study or its inclusion criteria", m_codon_d: "Targets the same codon (e.g. other V600 changes)", m_gene_d: "Mentions the gene, not this variant", m_condition_d: "No variant mention found",
    pipeline: "Development pipeline — click a phase to filter", byyear: "Trials by start year", table: "Table view", chart: "Chart view",
    g_open: "Open or opening", g_active: "Active, not recruiting", g_closed: "Completed / other", year: "Year", trials_n: "trials",
    no_trials: "No trials match these filters.", more: "Show more", sponsor: "Sponsor", enrol: "patients", sites: "Sites", countries: "Countries",
    f_variant_in_exclusion: "Variant appears in EXCLUSION criteria — check carefully", f_variant_negated: "Variant mentioned only as wild-type/negative — likely the opposite population",
    why: "Why it matched", agents: "Agents under investigation", agents_note: "Drugs listed in matched trials. Being studied does not mean effective or approved.",
    pubs: "Literature", evid: "Evidence level", retracted: "RETRACTED", preprint: "Preprint", pubs_total: "papers found; top results shown",
    t1: "Reviews / guidelines", t2: "Randomised", t3: "Clinical studies", t4: "Cases / narrative", t5: "Other",
    sources: "Sources & freshness", queries: "Exact search strings", print: "Print / save PDF", copylink: "Copy link", copied: "Copied",
    qd_title: "Questions to ask your doctor", qd: ["Is this variant germline (inherited) or somatic (in the tumour)? Was it confirmed by a clinical-grade lab?", "Does an approved targeted therapy exist for this variant and my condition?", "Am I eligible for any of these trials (stage, prior treatments, organ function)?", "Who can contact the trial site for me?"],
    w_merged_rsid: a => `This rsID was merged into ${a.into}. Showing results for the current record.`,
    w_isoform_numbering: a => `Different transcripts number this change differently (also: ${a.alts.join(", ")}). We searched the canonical numbering. Confirm against your lab report.`,
    w_germline_vs_somatic: () => "ClinVar classifications mostly describe inherited (germline) significance. Significance in a tumour (somatic) is assessed differently (e.g. AMP/ASCO/CAP tiers, OncoKB, CIViC) — ask your oncologist.",
    w_source_down: a => `${a.source} did not respond, so that section is incomplete. Try again shortly.`,
    w_results_capped: () => "Very many trials matched; the 300 most relevant were analysed. Narrow by condition or country.",
    demo: "DEMO MODE — synthetic data for testing. Nothing here is real.", err: "Something went wrong. Please retry.", ok: "OK", down: "Unavailable",
    open_in: "Open", of: "of"
  },
  pt: {
    patient: "Paciente", clinician: "Profissional", eyebrow: "Para pacientes, famílias e profissionais de saúde", h1: "Da mutação ao relatório de estudos.",
    lede: "Digite um rsID ou gene + alteração de proteína. Veja artigos, o panorama de ensaios clínicos e os estudos recrutando perto de você — cada linha com sua fonte.",
    lq: "Variante", lc: "Condição (opcional)", lco: "País", go: "Gerar relatório", try: "Exemplos", any: "Qualquer país", loading: "Montando relatório a partir de fontes públicas…",
    disc: "", privacy: "Privacidade: as consultas vão para APIs públicas do NCBI e ClinicalTrials.gov. Sem contas, sem cookies, consultas não são registradas.",
    variant: "Variante", gene: "Gene", change: "Alteração na proteína", clinvar: "Significado clínico (ClinVar)", conds: "Condições relatadas", stars: "Revisão", none: "Sem registro no ClinVar",
    at_glance: "Resumo", s_rec: "Recrutando agora", s_soon: "Ainda não recrutando", s_total: "Ensaios ligados a esta variante", s_pubs: "Artigos no PubMed", s_site: "Recrutando em",
    trials: "Ensaios clínicos", status: "Situação", match: "Nível de correspondência", phase: "Fase", all: "Todos",
    st_RECRUITING: "Recrutando", st_NOT_YET_RECRUITING: "Ainda não recrutando", st_ACTIVE_NOT_RECRUITING: "Ativo, sem recrutar", st_ENROLLING_BY_INVITATION: "Inscrição por convite", st_COMPLETED: "Concluído", st_TERMINATED: "Encerrado", st_WITHDRAWN: "Retirado", st_SUSPENDED: "Suspenso", st_UNKNOWN: "Situação desconhecida",
    tab_recruiting: "Recrutando", tab_soon: "Em breve", tab_active: "Ativos", tab_closed: "Concluídos / outros", tab_all: "Todos",
    m_variant: "Variante exata", m_codon: "Mesmo códon", m_gene: "Só o gene", m_condition: "Só a condição",
    m_variant_d: "Cita exatamente esta variante no estudo ou nos critérios de inclusão", m_codon_d: "Mira o mesmo códon (ex.: outras alterações V600)", m_gene_d: "Cita o gene, não esta variante", m_condition_d: "Nenhuma menção à variante",
    pipeline: "Pipeline de desenvolvimento — clique numa fase para filtrar", byyear: "Ensaios por ano de início", table: "Ver tabela", chart: "Ver gráfico",
    g_open: "Abertos ou abrindo", g_active: "Ativos, sem recrutar", g_closed: "Concluídos / outros", year: "Ano", trials_n: "ensaios",
    no_trials: "Nenhum ensaio com estes filtros.", more: "Mostrar mais", sponsor: "Patrocinador", enrol: "pacientes", sites: "Centros", countries: "Países",
    f_variant_in_exclusion: "A variante aparece nos critérios de EXCLUSÃO — leia com atenção", f_variant_negated: "Variante citada só como selvagem/negativa — provavelmente a população oposta",
    why: "Por que apareceu", agents: "Agentes em investigação", agents_note: "Medicamentos citados nos ensaios encontrados. Estar em estudo não significa eficaz nem aprovado.",
    pubs: "Literatura", evid: "Nível de evidência", retracted: "RETRATADO", preprint: "Preprint", pubs_total: "artigos encontrados; mostrando os principais",
    t1: "Revisões / diretrizes", t2: "Randomizados", t3: "Estudos clínicos", t4: "Casos / narrativas", t5: "Outros",
    sources: "Fontes e atualização", queries: "Termos de busca exatos", print: "Imprimir / salvar PDF", copylink: "Copiar link", copied: "Copiado",
    qd_title: "Perguntas para levar ao seu médico", qd: ["Esta variante é germinativa (hereditária) ou somática (no tumor)? Foi confirmada por laboratório de grau clínico?", "Existe terapia-alvo aprovada para esta variante e a minha condição?", "Posso participar de algum destes ensaios (estágio, tratamentos prévios, função dos órgãos)?", "Quem pode contatar o centro do estudo em meu nome?"],
    w_merged_rsid: a => `Este rsID foi unido a ${a.into}. Mostrando o registro atual.`,
    w_isoform_numbering: a => `Transcritos diferentes numeram esta alteração de formas diferentes (também: ${a.alts.join(", ")}). Buscamos a numeração canônica. Confirme no laudo do seu laboratório.`,
    w_germline_vs_somatic: () => "As classificações do ClinVar descrevem principalmente o significado germinativo (hereditário). O significado no tumor (somático) é avaliado de outra forma (ex.: níveis AMP/ASCO/CAP, OncoKB, CIViC) — pergunte ao seu oncologista.",
    w_source_down: a => `${a.source} não respondeu; esta seção está incompleta. Tente de novo em instantes.`,
    w_results_capped: () => "Muitos ensaios encontrados; os 300 mais relevantes foram analisados. Restrinja por condição ou país.",
    demo: "MODO DEMO — dados sintéticos para teste. Nada aqui é real.", err: "Algo deu errado. Tente novamente.", ok: "OK", down: "Indisponível",
    open_in: "Abrir", of: "de"
  },
};
const DISCLAIMER_FALLBACK = {
  en: "Research and information tool — not medical advice, diagnosis or a treatment recommendation. Trial listings do not imply eligibility or efficacy. Discuss any option with your treating physician.",
  pt: "Ferramenta de pesquisa e informação — não é aconselhamento médico, diagnóstico nem recomendação de tratamento. A presença em um ensaio não implica elegibilidade nem eficácia. Converse com seu médico.",
};
const PHASES = [["EARLY_PHASE1", "Early Ph.1"], ["PHASE1", "Phase 1"], ["PHASE2", "Phase 2"], ["PHASE3", "Phase 3"], ["PHASE4", "Phase 4"], ["NA", "N/A"]];
const GROUPS = ["open", "active", "closed"];

const state = { lang: "en", aud: "patient", data: null, tab: "recruiting", tiers: new Set(["variant", "codon"]), phase: null, shown: 8, tableView: false, pubTier: 0 };
const $ = (s, r = document) => r.querySelector(s);
const t = (k, a) => { const v = I18N[state.lang][k] ?? I18N.en[k] ?? k; return typeof v === "function" ? v(a || {}) : v; };

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v; else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "text") el.textContent = v; else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) el.append(c.nodeType ? c : document.createTextNode(String(c)));
  return el;
}
function ext(href, text, cls) { // demo data never links out
  if (state.data?.demo) return h("span", { class: cls }, text);
  return h("a", { href, target: "_blank", rel: "noopener noreferrer", class: cls }, text);
}
const statusGroup = s => s === "RECRUITING" || s === "ENROLLING_BY_INVITATION" ? "recruiting" : s === "NOT_YET_RECRUITING" ? "soon" : s === "ACTIVE_NOT_RECRUITING" ? "active" : "closed";
const chartGroup = s => { const g = statusGroup(s); return g === "recruiting" || g === "soon" ? "open" : g; };
const phaseLabels = ps => (ps || []).map(p => (PHASES.find(x => x[0] === p) || [0, p])[1]).join(" / ") || "N/A";

/* ---------- static text / i18n ---------- */
function applyI18n() {
  document.documentElement.lang = state.lang === "pt" ? "pt-BR" : "en";
  document.querySelectorAll("[data-i18n]").forEach(el => { const k = el.dataset.i18n; if (k === "disc") return; el.textContent = t(k); });
  $("#disc").textContent = state.data?.disclaimer?.[state.lang] || DISCLAIMER_FALLBACK[state.lang];
  const sel = $("#country"), cur = sel.value; sel.replaceChildren(...COUNTRIES.map(c => h("option", { value: c }, c || t("any")))); sel.value = cur;
  const d = $("#demo"); d.hidden = !state.data?.demo && !window.__demo; d.textContent = t("demo");
  document.querySelectorAll("#lang button").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === state.lang));
  document.querySelectorAll("#aud button").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === state.aud));
  document.body.dataset.aud = state.aud;
}

/* ---------- filtering ---------- */
function filtered({ ignoreStatus = false, ignorePhase = false } = {}) {
  return state.data.trials.items.filter(x => {
    if (!state.tiers.has(x.tier)) return false;
    if (!ignoreStatus && state.tab !== "all" && statusGroup(x.status) !== state.tab) return false;
    if (!ignorePhase && state.phase && !(x.phases.includes(state.phase) || (state.phase === "NA" && !x.phases.length))) return false;
    return true;
  });
}

/* ---------- sections ---------- */
function variantCard(d) {
  const v = d.variant, cv = v.clinvar;
  const sig = cv && cv.significance.length ? cv.significance.map(s => h("span", { class: "badge " + (/pathogenic/.test(s) ? "b-bad" : /benign/.test(s) ? "b-ok" : "b-warn") }, s)) : [h("span", { class: "badge" }, t("none"))];
  return h("section", { class: "card" },
    h("div", { class: "vhead" },
      h("div", { class: "vname" }, `${v.gene} ${v.change.short} `, h("small", { class: "mono" }, `p.${v.change.long}`)),
      v.rsid ? ext(`https://www.ncbi.nlm.nih.gov/snp/${v.rsid}`, v.rsid, "mono") : null),
    h("div", { class: "kv" },
      v.hgvs_c ? h("span", {}, "cDNA ", h("b", { class: "mono" }, v.hgvs_c)) : null,
      v.protein_accession ? h("span", {}, "Protein ", h("b", { class: "mono" }, v.protein_accession)) : null),
    cv ? h("div", { class: "kv" }, h("span", {}, t("clinvar") + ": "), sig,
      cv.max_review_stars ? h("span", {}, `${t("stars")}: ${"★".repeat(cv.max_review_stars)}${"☆".repeat(4 - cv.max_review_stars)}`) : null) : null,
    cv && cv.conditions.length ? h("div", { class: "kv" }, h("span", {}, t("conds") + ": "), h("b", {}, cv.conditions.slice(0, 4).join(" · "))) : null);
}
function stat(n, l) { return h("div", { class: "stat" }, h("div", { class: "n" }, String(n)), h("div", { class: "l" }, l)); }
function glance(d) {
  const spec = d.trials.items.filter(x => ["variant", "codon"].includes(x.tier));
  const c = g => spec.filter(x => statusGroup(x.status) === g).length;
  const kids = [stat(spec.length, t("s_total")), stat(c("recruiting"), t("s_rec")), stat(c("soon"), t("s_soon")), stat(d.publications.total.toLocaleString(), t("s_pubs"))];
  if (d.query.country) kids.push(stat(spec.filter(x => x.status === "RECRUITING" && x.countries.includes(d.query.country)).length, `${t("s_site")} ${d.query.country}`));
  return h("section", { class: "card" }, h("h2", {}, t("at_glance")), h("div", { class: "stats" }, kids));
}

function chip(label, pressed, onclick, title) { return h("button", { class: "chip", "aria-pressed": String(pressed), title, onclick }, label); }

function pipeline() {
  const base = filtered({ ignorePhase: true });
  return h("div", { class: "pipe" }, PHASES.map(([k, label]) => {
    const n = base.filter(x => x.phases.includes(k) || (k === "NA" && !x.phases.length)).length;
    return h("button", { class: "ph", "aria-pressed": String(state.phase === k), onclick: () => { state.phase = state.phase === k ? null : k; state.shown = 8; renderTrials(); } },
      h("span", { class: "n" }, String(n)), h("span", { class: "l" }, label));
  }));
}

function yearChart() {
  const items = filtered({ ignoreStatus: true });
  const box = h("div", { class: "chartbox" });
  if (!items.length) return box;
  const years = items.map(x => x.start_year).filter(Boolean);
  if (!years.length) return box;
  const y0 = Math.min(...years), y1 = Math.max(...years), span = [];
  for (let y = y0; y <= y1; y++) span.push(y);
  const data = Object.fromEntries(span.map(y => [y, { open: 0, active: 0, closed: 0 }]));
  items.forEach(x => { if (x.start_year) data[x.start_year][chartGroup(x.status)]++; });
  const max = Math.max(1, ...span.map(y => GROUPS.reduce((a, g) => a + data[y][g], 0)));
  const names = { open: t("g_open"), active: t("g_active"), closed: t("g_closed") };
  const legend = h("div", { class: "legend" }, GROUPS.map(g => h("span", {}, h("i", { style: `background:var(--s-${g === "open" ? "open" : g === "active" ? "active" : "other"})` }), names[g])));
  if (state.tableView) {
    const rows = span.slice().reverse().map(y => h("tr", {}, h("td", {}, y), GROUPS.map(g => h("td", {}, data[y][g]))));
    box.append(h("table", { class: "t" }, h("tr", {}, h("th", {}, t("year")), GROUPS.map(g => h("th", {}, names[g]))), rows));
    return box;
  }
  const W = 720, H = 190, L = 28, B = 22, T = 8, bw = Math.max(4, Math.min(30, (W - L) / span.length - 4)), step = (W - L) / span.length;
  const NS = "http://www.w3.org/2000/svg", s = document.createElementNS(NS, "svg");
  s.setAttribute("viewBox", `0 0 ${W} ${H}`); s.setAttribute("role", "img"); s.setAttribute("width", "100%");
  s.setAttribute("aria-label", `${t("byyear")}: ${items.length} ${t("trials_n")}`);
  const el = (n, a, tx) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (tx != null) e.textContent = tx; s.append(e); return e; };
  const ys = v => H - B - (v / max) * (H - B - T);
  for (const v of [...new Set([0, Math.ceil(max / 2), max])]) { el("line", { x1: L, x2: W, y1: ys(v), y2: ys(v), class: "grid" }); el("text", { x: L - 6, y: ys(v) + 4, "text-anchor": "end" }, v); }
  const tip = h("div", { class: "tip", hidden: true });
  span.forEach((y, i) => {
    const x = L + i * step + (step - bw) / 2; let acc = 0;
    GROUPS.forEach(g => {
      const v = data[y][g]; if (!v) return;
      const top = ys(acc + v), hgt = ys(acc) - top;
      el("rect", { x, y: top, width: bw, height: Math.max(0, hgt - 2), rx: 2, fill: `var(--s-${g === "open" ? "open" : g === "active" ? "active" : "other"})` });
      acc += v;
    });
    const hit = el("rect", { x: L + i * step, y: T, width: step, height: H - B - T, fill: "transparent" });
    const show = () => { const tot = GROUPS.reduce((a, g) => a + data[y][g], 0); tip.hidden = false; tip.textContent = `${y}: ${tot} ${t("trials_n")} (${GROUPS.map(g => data[y][g]).join(" / ")})`; tip.style.left = `${((x + bw / 2) / W) * 100}%`; tip.style.top = `${(ys(tot) / H) * 100}%`; };
    hit.addEventListener("mouseenter", show); hit.addEventListener("mouseleave", () => tip.hidden = true); hit.addEventListener("click", show);
    if (span.length <= 14 || i % 4 === 0 || i === span.length - 1) el("text", { x: x + bw / 2, y: H - 6, "text-anchor": "middle" }, "'" + String(y).slice(2));
  });
  box.append(s, tip, legend);
  return box;
}

function trialCard(x) {
  const country = state.data.query.country;
  const cities = country ? [...new Set(x.sites.filter(s => s.country === country).map(s => s.city).filter(Boolean))].slice(0, 4) : [];
  const badgeCls = x.status === "RECRUITING" ? "b-ok" : x.status === "NOT_YET_RECRUITING" ? "b-warn" : "";
  return h("article", { class: `trial t-${x.tier}` },
    h("div", { class: "row" },
      h("span", { class: "badge " + badgeCls }, t("st_" + x.status)),
      h("span", { class: "badge" }, t("m_" + x.tier)),
      h("span", { class: "badge" }, phaseLabels(x.phases)),
      ext(`https://clinicaltrials.gov/study/${x.nct}`, x.nct, "mono")),
    h("h3", {}, x.title),
    h("div", { class: "meta" }, [x.sponsor, x.enrollment ? `${x.enrollment} ${t("enrol")}` : null, x.start_year ? String(x.start_year) : null].filter(Boolean).join(" · ")),
    x.countries.length ? h("div", { class: "meta" }, `${t("countries")}: ${x.countries.slice(0, 6).join(", ")}${x.countries.length > 6 ? ` +${x.countries.length - 6}` : ""}${cities.length ? ` — ${country}: ${cities.join(", ")}` : ""}`) : null,
    x.flags.filter(f => f !== "gene_in_exclusion").map(f => h("div", { class: "alert", style: "margin-top:8px" }, "⚠ " + t("f_" + f))),
    x.match_snippet ? h("div", { class: "why clin-only" }, h("b", {}, t("why") + ": "), x.match_snippet) : null,
    x.interventions.length ? h("div", { class: "meta clin-only" }, x.interventions.map(i => i.name).join(" · ")) : null);
}

function renderTrials() {
  const d = state.data, host = $("#trials"); host.replaceChildren();
  const tabs = ["recruiting", "soon", "active", "closed", "all"];
  const base = tabs.map(k => [k, state.data.trials.items.filter(x => state.tiers.has(x.tier) && (k === "all" || statusGroup(x.status) === k)).length]);
  const list = filtered();
  host.append(h("div", {},
    h("div", { class: "filters" }, h("span", { class: "lbl" }, t("status")), base.map(([k, n]) => chip(`${t("tab_" + k)} (${n})`, state.tab === k, () => { state.tab = k; state.shown = 8; renderTrials(); }))),
    h("div", { class: "filters" }, h("span", { class: "lbl" }, t("match")), ["variant", "codon", "gene", "condition"].map(k => chip(t("m_" + k), state.tiers.has(k), () => { state.tiers.has(k) ? state.tiers.delete(k) : state.tiers.add(k); if (!state.tiers.size) state.tiers.add(k); state.shown = 8; renderTrials(); }, t("m_" + k + "_d")))),
    h("h2", { style: "margin-top:18px" }, t("pipeline")), pipeline(),
    h("div", { class: "row", style: "display:flex;justify-content:space-between;align-items:center" }, h("h2", { style: "margin:0" }, t("byyear")),
      h("button", { class: "link", onclick: () => { state.tableView = !state.tableView; renderTrials(); } }, state.tableView ? t("chart") : t("table"))),
    yearChart(),
    h("div", { style: "margin-top:18px" }, list.length ? list.slice(0, state.shown).map(trialCard) : h("p", { class: "muted" }, t("no_trials"))),
    list.length > state.shown ? h("button", { class: "more", onclick: () => { state.shown += 8; renderTrials(); } }, `${t("more")} (${list.length - state.shown})`) : null));
}

function agentsCard(d) {
  const a = d.trials.agents; if (!a.length) return null;
  return h("section", { class: "card" }, h("h2", {}, t("agents")), h("p", { class: "muted", style: "margin-top:-4px" }, t("agents_note")),
    h("div", { class: "agents" }, a.map(x => h("span", { class: "agent" }, x.name, " ", h("small", {}, `${x.trials} · ${x.open_trials} ${t("tab_recruiting").toLowerCase()}`)))));
}

function pubsCard(d) {
  const p = d.publications, host = h("section", { class: "card" });
  const items = p.items.filter(x => !state.pubTier || x.tier === state.pubTier);
  host.append(h("h2", {}, t("pubs")), h("p", { class: "muted", style: "margin-top:-4px" }, `${p.total.toLocaleString()} ${t("pubs_total")}`),
    h("div", { class: "filters" }, h("span", { class: "lbl" }, t("evid")), chip(t("all"), !state.pubTier, () => { state.pubTier = 0; renderPubs(); }),
      [1, 2, 3, 4, 5].map(k => chip(t("t" + k), state.pubTier === k, () => { state.pubTier = k; renderPubs(); }))));
  items.sort((a, b) => a.retracted - b.retracted || a.tier - b.tier).slice(0, 20).forEach(x => host.append(h("div", { class: "pub" },
    ext(`https://pubmed.ncbi.nlm.nih.gov/${x.pmid}/`, x.title),
    h("div", { class: "meta muted", style: "font-size:14px" }, [x.authors.join(", "), x.journal, x.year].filter(Boolean).join(" · "), " ",
      h("span", { class: "badge" }, t("t" + x.tier)), " ", x.retracted ? h("span", { class: "badge b-bad" }, t("retracted")) : null, x.preprint ? h("span", { class: "badge b-warn" }, t("preprint")) : null,
      " ", h("span", { class: "mono muted" }, "PMID " + x.pmid)))));
  return host;
}
function renderPubs() { const old = $("#pubs"); const n = pubsCard(state.data); n.id = "pubs"; old.replaceWith(n); }

function sourcesCard(d) {
  return h("section", { class: "card" }, h("h2", {}, t("sources")),
    h("div", { class: "sources" }, d.sources.map(s => h("div", {}, h("span", { class: "badge " + (s.status === "ok" ? "b-ok" : "b-bad") }, s.status === "ok" ? t("ok") : t("down")), " ", s.name, " ", h("span", { class: "muted" }, new Date(s.fetched_at).toLocaleString())))),
    h("details", { class: "clin-only", style: "margin-top:10px" }, h("summary", {}, t("queries")), h("pre", {}, `PubMed:\n${d.search_strings.pubmed}\n\nClinicalTrials.gov (query.term):\n${d.search_strings.ctgov}`)));
}

function render(d) {
  state.data = d; state.tab = "recruiting"; state.phase = null; state.shown = 8; state.pubTier = 0; state.tiers = new Set(["variant", "codon"]);
  applyI18n();
  const out = $("#out"); out.hidden = false; out.replaceChildren(h("div", {},
    h("div", { class: "toolbar" },
      h("button", { class: "link", onclick: async e => { try { await navigator.clipboard.writeText(location.href); e.target.textContent = t("copied"); } catch { } } }, t("copylink")),
      h("button", { class: "link", onclick: () => print() }, t("print"))),
    variantCard(d),
    d.warnings.map(w => h("div", { class: "alert" + (w.code === "germline_vs_somatic" ? " info" : "") }, t("w_" + w.code, w.args))),
    glance(d),
    h("section", { class: "card" }, h("h2", {}, t("trials")), h("div", { id: "trials" })),
    agentsCard(d),
    (() => { const s = pubsCard(d); s.id = "pubs"; return s; })(),
    h("section", { class: "card pat-only" }, h("h2", {}, t("qd_title")), h("ul", {}, t("qd").map(q => h("li", {}, q)))),
    sourcesCard(d)));
  renderTrials();
}

/* ---------- data ---------- */
async function run(q, cond, country, push = true) {
  const st = $("#status"), btn = $(".primary"); st.className = ""; st.textContent = t("loading"); btn.disabled = true;
  try {
    const u = new URLSearchParams({ q }); if (cond) u.set("condition", cond); if (country) u.set("country", country);
    const r = await fetch("/api/brief?" + u);
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(typeof body.detail === "string" ? body.detail : body.message || t("err"));
    if (push) history.replaceState(null, "", "?" + u);
    st.textContent = ""; render(body);
  } catch (e) { st.className = "err"; st.textContent = e.message || t("err"); $("#out").hidden = true; }
  finally { btn.disabled = false; }
}
$("#form").addEventListener("submit", e => { e.preventDefault(); run($("#q").value.trim(), $("#cond").value.trim(), $("#country").value); });
document.querySelectorAll("[data-ex]").forEach(b => b.addEventListener("click", e => { e.preventDefault(); $("#q").value = b.dataset.ex; $("#form").requestSubmit(); }));
$("#lang").addEventListener("click", e => { const v = e.target.dataset?.v; if (v) { state.lang = v; try { localStorage.setItem("vts_lang", v); } catch { } applyI18n(); if (state.data) render(state.data); } });
$("#aud").addEventListener("click", e => { const v = e.target.dataset?.v; if (v) { state.aud = v; applyI18n(); } });

/* ---------- tema e atalhos de teclado ---------- */
(function () {
  const raiz = document.documentElement;
  try { const salvo = localStorage.getItem("vts_theme"); if (salvo === "light" || salvo === "dark") raiz.dataset.theme = salvo; } catch { }
  document.getElementById("tema")?.addEventListener("click", () => {
    const atual = raiz.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const proximo = atual === "dark" ? "light" : "dark";
    raiz.dataset.theme = proximo;
    try { localStorage.setItem("vts_theme", proximo); } catch { }
  });
  document.addEventListener("keydown", e => {
    const tag = document.activeElement?.tagName || "";
    if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) { e.preventDefault(); document.getElementById("q")?.focus(); }
    if (e.key === "Escape" && document.activeElement === document.getElementById("q")) document.activeElement.blur();
  });
})();

(async function init() {
  try { const l = localStorage.getItem("vts_lang"); if (l === "pt" || l === "en") state.lang = l; else if ((navigator.language || "").startsWith("pt")) state.lang = "pt"; } catch { }
  try { window.__demo = (await (await fetch("/api/health")).json()).demo; } catch { }
  applyI18n();
  const p = new URLSearchParams(location.search);
  if (p.get("q")) { $("#q").value = p.get("q"); $("#cond").value = p.get("condition") || ""; $("#country").value = p.get("country") || ""; run(p.get("q"), p.get("condition") || "", p.get("country") || "", false); }
})();
