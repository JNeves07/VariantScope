"""Input normalisation: rsID or 'GENE p.Xnnn Y' -> ParsedQuery.

Lab reports rarely quote rsIDs; clinicians and patients usually have a gene + protein
change (e.g. "BRAF V600E"). Both must work.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

AA3 = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C", "Gln": "Q", "Glu": "E",
    "Gly": "G", "His": "H", "Ile": "I", "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F",
    "Pro": "P", "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V", "Ter": "*",
}
AA1 = {v: k for k, v in AA3.items()}


class InputError(ValueError):
    """User-facing input problem (HTTP 422)."""


@dataclass(frozen=True)
class ProteinChange:
    ref: str  # one-letter
    pos: int
    alt: str  # one-letter or '*'

    @property
    def short(self) -> str:
        return f"{self.ref}{self.pos}{self.alt}"

    @property
    def long(self) -> str:
        return f"{AA1[self.ref]}{self.pos}{AA1[self.alt]}"

    @property
    def codon(self) -> str:
        return f"{self.ref}{self.pos}"


@dataclass(frozen=True)
class ParsedQuery:
    raw: str
    kind: str  # 'rsid' | 'protein'
    rsid: str | None = None
    gene: str | None = None
    change: ProteinChange | None = None


_RS = re.compile(r"^\s*(?:rs)?\s*(\d{3,12})\s*$", re.I)
_PROT = re.compile(
    r"^\s*([A-Za-z][A-Za-z0-9-]{1,14})\s*[:\s_-]\s*(?:p\.)?\(?"
    r"([A-Za-z]{1,3})(\d{1,5})([A-Za-z]{1,3}|\*)\)?\s*$"
)


def _aa(token: str) -> str:
    if len(token) == 1:
        t = token.upper() if token != "*" else "*"
        if t in AA1:
            return t
    t3 = token.capitalize()
    if t3 in AA3:
        return AA3[t3]
    raise InputError(f"Unrecognised amino acid '{token}'.")


def parse_query(raw: str) -> ParsedQuery:
    raw = (raw or "").strip()
    if not raw:
        raise InputError("Enter an rsID (e.g. rs113488022) or a gene + protein change (e.g. BRAF V600E).")
    if len(raw) > 60:
        raise InputError("Input too long.")
    m = _RS.match(raw)
    if m:
        return ParsedQuery(raw=raw, kind="rsid", rsid=f"rs{m.group(1)}")
    m = _PROT.match(raw)
    if m:
        gene, ref, pos, alt = m.groups()
        if re.fullmatch(r"(?i)rs", gene):
            raise InputError("Incomplete rsID.")
        change = ProteinChange(_aa(ref), int(pos), _aa(alt))
        if change.ref == change.alt:
            raise InputError("Reference and alternate amino acids are identical.")
        return ParsedQuery(raw=raw, kind="protein", gene=gene.upper(), change=change)
    raise InputError(
        "Format not recognised. Supported: rsID (rs113488022) or gene + protein change "
        "(BRAF V600E, BRAF p.Val600Glu). Fusions, copy-number and c. (cDNA) notation are not supported yet."
    )
