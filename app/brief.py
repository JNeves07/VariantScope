"""Orchestrator: query -> Brief (always partial-tolerant; every source reports its own status)."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from .cache import CacheBackend, chave_consulta
from .config import settings
from .http import Http, SourceError
from .normalize import ParsedQuery, parse_query
from .ranking import build_trials
from .sources import ctgov_variant_term, fetch_dbsnp, fetch_pubmed, fetch_trials_raw, pubmed_term

DISCLAIMER = {
    "en": "Research and information tool — not medical advice, diagnosis or a treatment recommendation. "
          "Trial listings do not imply eligibility or efficacy. Discuss any option with your treating physician.",
    "pt": "Ferramenta de pesquisa e informação — não é aconselhamento médico, diagnóstico nem recomendação de "
          "tratamento. A presença em um ensaio não implica elegibilidade nem eficácia. Converse com seu médico.",
}


class NotFound(Exception):
    pass


class UpstreamDown(Exception):
    pass


async def build_brief(http: Http, raw_query: str, condition: str | None, country: str | None,
                      demo: bool = False, cache: CacheBackend | None = None,
                      ttl: int | None = None) -> dict:
    q: ParsedQuery = parse_query(raw_query)
    condition = (condition or "").strip()[:80] or None
    country = (country or "").strip()[:60] or None

    chave = None
    if cache is not None:
        chave = chave_consulta(raw_query, condition, country, demo)
        em_cache = await cache.get(chave)
        if em_cache is not None:
            return {**em_cache, "cached": True}

    sources: list[dict] = []
    warnings: list[dict] = []
    now = datetime.now(UTC).isoformat(timespec="seconds")

    # 1. Resolve variant
    variant: dict
    if q.kind == "rsid":
        try:
            variant = await fetch_dbsnp(http, q.rsid)
            sources.append({"name": "dbSNP / ClinVar", "status": "ok", "fetched_at": now})
        except SourceError as e:
            if e.status == 404:
                raise NotFound(
                    f"{q.rsid} was not found in dbSNP. Check the number, or search by gene + protein change."
                ) from e
            raise UpstreamDown(
                "dbSNP is unreachable right now. Search by gene + protein change (e.g. BRAF V600E) or retry shortly."
            ) from e
        if variant["merged_into"]:
            warnings.append({"code": "merged_rsid", "args": {"into": variant["merged_into"][0]}})
        if not variant["gene"] or not variant["change"]:
            raise NotFound(f"{q.rsid} is not a protein-coding (missense/nonsense) variant that this MVP can search. "
                           "Intronic, synonymous, structural variants and fusions are not supported yet.")
        if variant["isoform_alternatives"]:
            warnings.append({"code": "isoform_numbering", "args": {"alts": variant["isoform_alternatives"][:4]}})
    else:
        variant = {"rsid": None, "merged_into": [], "gene": q.gene, "change": q.change, "hgvs_c": None,
                   "protein_accession": None, "isoform_alternatives": [], "clinvar": None}
        sources.append({"name": "User input", "status": "ok", "fetched_at": now})

    gene, ch = variant["gene"], variant["change"]

    # 2. Literature + trials in parallel; one failing never blanks the page.
    pub_res, tr_res = await asyncio.gather(
        fetch_pubmed(http, gene, ch, variant["rsid"], condition),
        fetch_trials_raw(http, gene, ch, condition, country),
        return_exceptions=True,
    )
    publications = {"total": 0, "items": [], "query": pubmed_term(gene, ch, variant["rsid"], condition)}
    trials = {"items": [], "by_status": {}, "total_variant_query": 0, "total_gene_active": 0, "capped": False, "agents": []}
    if isinstance(pub_res, Exception):
        sources.append({"name": "PubMed", "status": "error", "fetched_at": now})
        warnings.append({"code": "source_down", "args": {"source": "PubMed"}})
    else:
        publications = pub_res
        sources.append({"name": "PubMed", "status": "ok", "fetched_at": now})
    if isinstance(tr_res, Exception):
        sources.append({"name": "ClinicalTrials.gov", "status": "error", "fetched_at": now})
        warnings.append({"code": "source_down", "args": {"source": "ClinicalTrials.gov"}})
    else:
        trials = build_trials(tr_res, gene, ch)
        sources.append({"name": "ClinicalTrials.gov", "status": "ok", "fetched_at": now})
        if trials["capped"]:
            warnings.append({"code": "results_capped", "args": {}})

    if variant["clinvar"] is not None:
        warnings.append({"code": "germline_vs_somatic", "args": {}})

    ch_d = {"short": ch.short, "long": ch.long, "codon": ch.codon}
    resultado = {
        "query": {"raw": raw_query, "kind": q.kind, "condition": condition, "country": country},
        "variant": {**{k: v for k, v in variant.items() if k != "change"}, "change": ch_d},
        "publications": publications, "trials": trials,
        "search_strings": {"pubmed": publications["query"], "ctgov": ctgov_variant_term(gene, ch)},
        "warnings": warnings, "sources": sources, "generated_at": now,
        "demo": demo, "disclaimer": DISCLAIMER, "cached": False,
    }
    if cache is not None and chave is not None:
        await cache.set(chave, resultado, ttl or settings.cache_ttl)
    return resultado
