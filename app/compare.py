"""Comparação leve entre dois briefs já resolvidos (sem consultas adicionais)."""
from __future__ import annotations

from .ranking import TIERS

TIER_LABELS = {
    "variant": "variante exata",
    "codon": "mesmo códon",
    "gene": "apenas gene",
    "condition": "apenas condição",
}


def _ncts(brief: dict) -> list[str]:
    return [t["nct"] for t in brief.get("trials", {}).get("items", []) if t.get("nct")]


def _tiers(brief: dict) -> list[str]:
    presentes = {t["tier"] for t in brief.get("trials", {}).get("items", []) if t.get("tier") in TIERS}
    return [tier for tier in TIERS if tier in presentes]


def _rotulo(brief: dict) -> str:
    v = brief.get("variant") or {}
    gene, change = v.get("gene"), v.get("change") or {}
    if gene and change.get("short"):
        return f"{gene} {change['short']}"
    return v.get("rsid") or "variante"


def comparar_briefs(a: dict, b: dict) -> dict:
    """Produz o bloco `comparacao` a partir de dois briefs, sem acessar fontes."""
    ncts_a, ncts_b = _ncts(a), _ncts(b)
    comuns = sorted(set(ncts_a) & set(ncts_b))
    unicos_a = sorted(set(ncts_a) - set(ncts_b))
    unicos_b = sorted(set(ncts_b) - set(ncts_a))
    tiers_a, tiers_b = _tiers(a), _tiers(b)
    divergencias: list[str] = []

    if _rotulo(a) != _rotulo(b):
        divergencias.append(f"Variantes diferentes: {_rotulo(a)} x {_rotulo(b)}.")
    if unicos_a or unicos_b:
        divergencias.append(f"Ensaios exclusivos: {len(unicos_a)} em A e {len(unicos_b)} em B.")
    for tier in TIERS:
        if tier in tiers_a and tier not in tiers_b:
            divergencias.append(f"Nível {TIER_LABELS[tier]} presente apenas em A.")
        elif tier in tiers_b and tier not in tiers_a:
            divergencias.append(f"Nível {TIER_LABELS[tier]} presente apenas em B.")
    if not divergencias:
        divergencias.append("Nenhuma divergência relevante entre os dois briefs.")

    return {
        "ensaios_comuns": comuns,
        "ensaios_unicos_a": unicos_a,
        "ensaios_unicos_b": unicos_b,
        "tiers_a": tiers_a,
        "tiers_b": tiers_b,
        "divergencias": divergencias,
    }
