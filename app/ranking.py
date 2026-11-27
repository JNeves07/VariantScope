"""Trial classification.

Registries describe variants in free text ('BRAF V600E', 'V600 mutation', 'BRAF-mutant'), never by rsID,
and often mention a variant only in the EXCLUSION criteria or as wild-type. We classify the ROLE of the
mention, not just its presence:

  variant    exact change named in title/summary/conditions/keywords/inclusion criteria
  codon      same codon (e.g. V600K, 'V600 mutation')
  gene       gene named, variant not
  condition  fallback (no gene mention at all)

A mention in exclusion criteria, or negated ('wild-type', 'negative'), never counts toward the tier and is
surfaced as a flag instead.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from .normalize import ProteinChange

TIERS = {"variant": 0, "codon": 1, "gene": 2, "condition": 3}
STATUS_ORDER = {"RECRUITING": 0, "NOT_YET_RECRUITING": 1, "ENROLLING_BY_INVITATION": 2,
                "ACTIVE_NOT_RECRUITING": 3, "COMPLETED": 4}
PHASE_RANK = {"PHASE4": 5, "PHASE3": 4, "PHASE2": 3, "PHASE1": 2, "EARLY_PHASE1": 1, "NA": 0}
_NEG = re.compile(r"(wild[\s-]?type|\bwt\b|negative|non[\s-]?mutated|without|absence of|\bno\b|\bnot\b)", re.I)
_EXCL = re.compile(r"exclusion criteria", re.I)
_INCL = re.compile(r"inclusion criteria", re.I)


def _pats(gene: str, ch: ProteinChange):
    # ch.short pode conter '*' (nonsense): cada token é literal, não regex.
    exact = re.compile(
        rf"(?<![A-Za-z0-9])(?:p\.)?\(?(?:{re.escape(ch.short)}|{re.escape(ch.long)})\)?(?![A-Za-z0-9])",
        re.I,
    )
    codon = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(ch.ref)}{ch.pos}(?![0-9])|codon\s*{ch.pos}(?![0-9])", re.I
    )
    gene_re = re.compile(rf"(?<![A-Za-z0-9]){re.escape(gene)}(?![A-Za-z0-9])", re.I)
    return exact, codon, gene_re


def _positive_hits(rx: re.Pattern, text: str) -> list[re.Match]:
    hits = []
    for m in rx.finditer(text):
        window = text[max(0, m.start() - 40): m.end() + 30]
        if not _NEG.search(window):
            hits.append(m)
    return hits


def _snippet(text: str, m: re.Match, n: int = 110) -> str:
    s = re.sub(r"\s+", " ", text[max(0, m.start() - n): m.end() + n]).strip()
    return ("…" if m.start() > n else "") + s + ("…" if m.end() + n < len(text) else "")


def split_eligibility(text: str) -> tuple[str, str]:
    """Return (inclusion, exclusion) text. If no exclusion heading, everything is 'inclusion'."""
    m = _EXCL.search(text or "")
    if not m:
        return text or "", ""
    return text[: m.start()], text[m.start():]


def classify(study: dict, gene: str, ch: ProteinChange) -> dict | None:
    p = study.get("protocolSection") or {}
    ident, status = p.get("identificationModule") or {}, p.get("statusModule") or {}
    design, sponsor = p.get("designModule") or {}, p.get("sponsorCollaboratorsModule") or {}
    cond, arms = p.get("conditionsModule") or {}, p.get("armsInterventionsModule") or {}
    loc, elig = p.get("contactsLocationsModule") or {}, p.get("eligibilityModule") or {}
    desc = p.get("descriptionModule") or {}
    nct = ident.get("nctId")
    if not nct:
        return None

    title = ident.get("briefTitle") or ""
    inclusion, exclusion = split_eligibility(elig.get("eligibilityCriteria") or "")
    front = " \n".join([title, desc.get("briefSummary") or "", " ".join(cond.get("conditions") or []),
                        " ".join(cond.get("keywords") or []), " ".join(i.get("name", "") for i in arms.get("interventions") or [])])
    scope = front + " \n" + inclusion
    exact, codon, gene_re = _pats(gene, ch)

    tier, snippet, flags = "condition", None, []
    hits = _positive_hits(exact, scope)
    if hits:
        tier, snippet = "variant", _snippet(scope, hits[0])
    else:
        hits = _positive_hits(codon, scope)
        if hits:
            tier, snippet = "codon", _snippet(scope, hits[0])
        else:
            hits = list(gene_re.finditer(scope))
            if hits:
                tier, snippet = "gene", _snippet(scope, hits[0])
    # Role flags
    if exclusion and (exact.search(exclusion) or codon.search(exclusion)):
        flags.append("variant_in_exclusion")
    if tier in ("gene", "condition") and (_pats(gene, ch)[0].search(scope) or _pats(gene, ch)[1].search(scope)):
        flags.append("variant_negated")  # mentioned only as wild-type/negative -> likely the opposite population
    if tier == "gene" and not gene_re.search(scope) and gene_re.search(exclusion):
        flags.append("gene_in_exclusion")

    locations = loc.get("locations") or []
    countries = sorted({l.get("country") for l in locations if l.get("country")})
    sites = [{"country": l.get("country"), "city": l.get("city"), "facility": l.get("facility")} for l in locations]
    interventions = [{"name": i.get("name", "").strip(), "type": (i.get("type") or "").upper()}
                     for i in arms.get("interventions") or [] if i.get("name")]
    start = (status.get("startDateStruct") or {}).get("date") or ""
    phases = design.get("phases") or []
    return {
        "nct": nct, "title": title, "status": status.get("overallStatus") or "UNKNOWN",
        "phases": phases, "phase_rank": max((PHASE_RANK.get(x, 0) for x in phases), default=0),
        "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
        "sponsor": (sponsor.get("leadSponsor") or {}).get("name"),
        "start_year": int(start[:4]) if start[:4].isdigit() else None,
        "conditions": (cond.get("conditions") or [])[:4],
        "interventions": interventions[:8], "countries": countries, "sites": sites[:40],
        "tier": tier, "match_snippet": snippet, "flags": flags,
        "study_type": design.get("studyType"),
    }


def build_trials(raw: dict, gene: str, ch: ProteinChange) -> dict:
    items = [t for t in (classify(s, gene, ch) for s in raw["studies"]) if t]
    items.sort(key=lambda t: (TIERS[t["tier"]], STATUS_ORDER.get(t["status"], 9), -t["phase_rank"],
                              -(t["start_year"] or 0)))
    by_status = Counter(t["status"] for t in items)
    return {"items": items, "by_status": dict(by_status), "total_variant_query": raw["total_variant_query"],
            "total_gene_active": raw["total_gene_active"], "capped": raw["capped"], "agents": aggregate_agents(items)}


_GENERIC = {"placebo", "standard of care", "standard care", "observation", "questionnaire", "surgery",
            "radiation", "radiotherapy", "quality-of-life assessment", "laboratory biomarker analysis"}


def aggregate_agents(items: list[dict]) -> list[dict]:
    """Agents under investigation in variant/codon-matched trials. NOT a treatment recommendation."""
    agg: dict[str, dict] = defaultdict(lambda: {"trials": set(), "max_phase": 0, "open": 0})
    for t in items:
        if t["tier"] not in ("variant", "codon"):
            continue
        for i in t["interventions"]:
            if i["type"] not in ("DRUG", "BIOLOGICAL", "COMBINATION_PRODUCT", "GENETIC"):
                continue
            name = re.sub(r"\s+", " ", i["name"]).strip().lower()
            if not name or name in _GENERIC:
                continue
            a = agg[name]
            if t["nct"] not in a["trials"]:
                a["trials"].add(t["nct"])
                a["max_phase"] = max(a["max_phase"], t["phase_rank"])
                a["open"] += t["status"] in ("RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION")
    out = [{"name": k, "trials": len(v["trials"]), "open_trials": v["open"], "max_phase_rank": v["max_phase"]}
           for k, v in agg.items()]
    out.sort(key=lambda a: (-a["open_trials"], -a["trials"], -a["max_phase_rank"], a["name"]))
    return out[:15]
