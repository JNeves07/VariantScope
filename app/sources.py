"""Clients + parsers for dbSNP (Variation Services), PubMed (E-utilities) and ClinicalTrials.gov v2."""
from __future__ import annotations

import re
from collections import Counter

from .http import Http, SourceError
from .normalize import AA1, ProteinChange

NCBI_VAR = "https://api.ncbi.nlm.nih.gov/variation/v0/refsnp/"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"

# ---------------------------------------------------------------- dbSNP -----

_REVIEW_STARS = [
    ("practice guideline", 4), ("reviewed by expert panel", 3),
    ("multiple submitters, no conflicts", 2), ("single submitter", 1), ("conflicting", 1),
]


def _stars(status: str) -> int:
    s = (status or "").lower()
    for key, n in _REVIEW_STARS:
        if key in s:
            return n
    return 0


def _np_rank(acc: str) -> tuple:
    # Prefer curated NP_0xxxxx (older, canonical isoform) over NP_001xxxxx+.
    m = re.match(r"NP_(\d+)", acc or "")
    return (0, int(m.group(1))) if m else (1, 0)


def parse_refsnp(data: dict, rsid: str) -> dict:
    """Extract gene, protein-change candidates and ClinVar-derived significance."""
    merged = (data.get("merged_snapshot_data") or {}).get("merged_into") or []
    snap = data.get("primary_snapshot_data") or {}
    cands: dict[tuple, dict] = {}
    clinical: list[dict] = []
    for ann in snap.get("allele_annotations") or []:
        for asm in ann.get("assembly_annotation") or []:
            for g in asm.get("genes") or []:
                symbol = g.get("locus")
                for rna in g.get("rnas") or []:
                    spdi = ((rna.get("protein") or {}).get("variant") or {}).get("spdi") or {}
                    d, i = spdi.get("deleted_sequence", ""), spdi.get("inserted_sequence", "")
                    if len(d) == 1 and len(i) == 1 and d != i and d in AA1 and i in AA1 and symbol:
                        key = (symbol, d, int(spdi["position"]) + 1, i)
                        c = cands.setdefault(key, {"gene": symbol, "ref": d, "pos": key[2], "alt": i,
                                                   "n": 0, "np": spdi.get("seq_id", ""), "hgvs_c": rna.get("hgvs")})
                        c["n"] += 1
                        if _np_rank(spdi.get("seq_id", "")) < _np_rank(c["np"]):
                            c["np"], c["hgvs_c"] = spdi.get("seq_id", ""), rna.get("hgvs")
        for cl in ann.get("clinical") or []:
            clinical.append({
                "significance": [s.lower() for s in cl.get("clinical_significances") or []],
                "conditions": [d for d in cl.get("disease_names") or [] if d and d.lower() != "not provided"],
                "stars": _stars(cl.get("review_status", "")),
                "review_status": cl.get("review_status", ""),
                "accession": cl.get("accession_version"),
                "pmids": [str(p) for p in cl.get("citations") or []][:5],
            })
    ranked = sorted(cands.values(), key=lambda c: (_np_rank(c["np"]), -c["n"]))
    primary = ranked[0] if ranked else None
    aliases = [f'{c["gene"]} {ProteinChange(c["ref"], c["pos"], c["alt"]).short}' for c in ranked[1:]]
    sig_counter = Counter(s for c in clinical for s in c["significance"])
    conds = Counter(d for c in clinical for d in c["conditions"])
    return {
        "rsid": rsid,
        "merged_into": [f"rs{m}" if not str(m).startswith("rs") else str(m) for m in merged],
        "gene": primary["gene"] if primary else None,
        "change": ProteinChange(primary["ref"], primary["pos"], primary["alt"]) if primary else None,
        "hgvs_c": primary["hgvs_c"] if primary else None,
        "protein_accession": primary["np"] if primary else None,
        "isoform_alternatives": sorted(set(aliases)),
        "clinvar": {
            "significance": [s for s, _ in sig_counter.most_common()],
            "conditions": [d for d, _ in conds.most_common(8)],
            "max_review_stars": max((c["stars"] for c in clinical), default=0),
            "records": len(clinical),
            "pmids": sorted({p for c in clinical for p in c["pmids"]})[:8],
        },
    }


async def fetch_dbsnp(http: Http, rsid: str) -> dict:
    num = rsid.lower().removeprefix("rs")
    try:
        data = await http.get_json("dbSNP", f"{NCBI_VAR}{num}")
    except SourceError as e:
        if e.status == 404:
            raise SourceError("dbSNP", f"{rsid} not found", 404) from e
        raise
    return parse_refsnp(data, rsid)


# ------------------------------------------------------ ClinVar esummary ----

def parse_clinvar_review(data: dict, rsid: str) -> dict | None:
    """Extrai status de revisão e data da última avaliação do ClinVar por rsID."""
    uid = rsid.lower().removeprefix("rs")
    res = data.get("result") or {}
    entry = res.get(uid) or res.get(rsid) or {}
    status = str(entry.get("review_status") or "").strip() or None
    avaliado = str(entry.get("last_evaluated") or entry.get("last_updated") or "").strip()[:10] or None
    if not status and not avaliado:
        return None
    return {
        "rsid": rsid,
        "review_status": status,
        "last_evaluated": avaliado,
        "stars": _stars(status or ""),
    }


async def fetch_clinvar_review(http: Http, rsid: str) -> dict:
    """Enriquecimento opcional: falha nunca apaga o restante do brief."""
    data = await http.get_json(
        "ClinVar", EUTILS + "esummary.fcgi",
        {"db": "clinvar", "id": rsid.lower().removeprefix("rs"), "retmode": "json"},
    )
    revisao = parse_clinvar_review(data, rsid)
    if revisao is None:
        raise SourceError("ClinVar", "review summary unavailable", 404)
    return revisao


# --------------------------------------------------------------- PubMed -----

def evidence_tier(pubtypes: list[str]) -> tuple[int, str]:
    t = {p.lower() for p in pubtypes}
    if t & {"meta-analysis", "systematic review", "practice guideline", "guideline"}:
        return 1, "Meta-analysis / review / guideline"
    if "randomized controlled trial" in t:
        return 2, "Randomised trial"
    if t & {"clinical trial", "clinical trial, phase i", "clinical trial, phase ii", "clinical trial, phase iii",
            "clinical trial, phase iv", "controlled clinical trial", "multicenter study", "observational study"}:
        return 3, "Clinical study"
    if t & {"case reports", "review"}:
        return 4, "Case report / narrative review"
    return 5, "Other / preclinical"


def parse_esummary(data: dict) -> list[dict]:
    res = data.get("result") or {}
    out = []
    for uid in res.get("uids") or []:
        r = res.get(uid) or {}
        pubtypes = r.get("pubtype") or []
        tier, label = evidence_tier(pubtypes)
        doi = next((a["value"] for a in r.get("articleids") or [] if a.get("idtype") == "doi"), None)
        year = (re.match(r"(\d{4})", r.get("pubdate") or "") or [None, None])[1]
        authors = [a.get("name") for a in r.get("authors") or [] if a.get("name")]
        out.append({
            "pmid": str(uid), "title": (r.get("title") or "").rstrip("."), "journal": r.get("source"),
            "year": int(year) if year else None,
            "authors": authors[:3] + (["et al."] if len(authors) > 3 else []),
            "pubtypes": pubtypes, "tier": tier, "tier_label": label, "doi": doi,
            "retracted": "retracted publication" in {p.lower() for p in pubtypes},
            "preprint": "preprint" in {p.lower() for p in pubtypes},
        })
    return out


def pubmed_term(gene: str, ch: ProteinChange, rsid: str | None, condition: str | None) -> str:
    variant = f'"{gene} {ch.short}"[tiab] OR "{gene} {ch.long}"[tiab] OR "{gene} p.{ch.short}"[tiab] OR "{gene} p.{ch.long}"[tiab]'
    if rsid:
        variant += f' OR "{rsid}"[All Fields]'
    term = f"({variant})"
    if condition:
        term += f' AND "{condition}"[tiab]'
    return term


async def fetch_pubmed(http: Http, gene: str, ch: ProteinChange, rsid: str | None, condition: str | None) -> dict:
    term = pubmed_term(gene, ch, rsid, condition)
    base = {"db": "pubmed", "term": term, "retmode": "json"}
    rel = await http.get_json("PubMed", EUTILS + "esearch.fcgi", {**base, "retmax": 25, "sort": "relevance"})
    new = await http.get_json("PubMed", EUTILS + "esearch.fcgi", {**base, "retmax": 10, "sort": "date"})
    total = int((rel.get("esearchresult") or {}).get("count", 0))
    ids: list[str] = []
    for r in (rel, new):
        for i in (r.get("esearchresult") or {}).get("idlist") or []:
            if i not in ids:
                ids.append(i)
    items: list[dict] = []
    if ids:
        summ = await http.get_json("PubMed", EUTILS + "esummary.fcgi",
                                   {"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
        items = parse_esummary(summ)
        order = {i: n for n, i in enumerate(ids)}
        items.sort(key=lambda x: order[x["pmid"]])
    return {"total": total, "items": items, "query": term}


# -------------------------------------------------------- ClinicalTrials ----

FIELDS = ",".join([
    "NCTId", "BriefTitle", "OverallStatus", "StartDate", "Phase", "EnrollmentCount", "LeadSponsorName",
    "Condition", "Keyword", "InterventionName", "InterventionType", "LocationCountry", "LocationCity",
    "LocationFacility", "EligibilityCriteria", "BriefSummary", "StudyType",
])
ACTIVE = "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION"


def ctgov_variant_term(gene: str, ch: ProteinChange) -> str:
    return f'{gene} AND ("{ch.short}" OR "{ch.long}" OR "{ch.codon}")'


async def _ct_page(http: Http, params: dict, size: int) -> tuple[int, list[dict]]:
    d = await http.get_json("ClinicalTrials.gov", CTGOV,
                            {**params, "pageSize": size, "countTotal": "true", "format": "json", "fields": FIELDS})
    return int(d.get("totalCount", 0)), d.get("studies") or []


async def fetch_trials_raw(http: Http, gene: str, ch: ProteinChange, condition: str | None,
                           country: str | None) -> dict:
    common: dict = {}
    if condition:
        common["query.cond"] = condition
    if country:
        common["query.locn"] = country
    import asyncio
    (t1, s1), (t2, s2) = await asyncio.gather(
        _ct_page(http, {**common, "query.term": ctgov_variant_term(gene, ch)}, 300),
        _ct_page(http, {**common, "query.term": gene, "filter.overallStatus": ACTIVE}, 100),
    )
    seen: dict[str, dict] = {}
    for s in s1 + s2:
        nct = ((s.get("protocolSection") or {}).get("identificationModule") or {}).get("nctId")
        if nct and nct not in seen:
            seen[nct] = s
    return {"studies": list(seen.values()), "total_variant_query": t1, "total_gene_active": t2,
            "capped": t1 > len(s1) or t2 > len(s2)}
