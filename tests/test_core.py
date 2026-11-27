import asyncio

import pytest

from app.brief import NotFound, build_brief
from app.demo_data import demo_transport
from app.http import Http
from app.normalize import InputError, parse_query
from app.ranking import split_eligibility


@pytest.mark.parametrize("raw,kind", [("rs113488022", "rsid"), ("113488022", "rsid"), ("RS113488022", "rsid"),
                                      ("BRAF V600E", "protein"), ("braf p.Val600Glu", "protein"), ("BRAF:p.V600E", "protein"),
                                      ("KRAS G12C", "protein"), ("EGFR p.(Leu858Arg)", "protein")])
def test_parse_ok(raw, kind):
    assert parse_query(raw).kind == kind


def test_parse_equivalence():
    a, b = parse_query("BRAF V600E"), parse_query("BRAF p.Val600Glu")
    assert a.change == b.change and a.gene == "BRAF" and a.change.long == "Val600Glu"


@pytest.mark.parametrize("raw", ["", "hello world", "BRAF V600V", "BRAF c.1799T>A", "x" * 100, "BRAF Z600E"])
def test_parse_bad(raw):
    with pytest.raises(InputError):
        parse_query(raw)


def run(coro):
    return asyncio.run(coro)


async def _brief(q, **kw):
    h = Http(transport=demo_transport())
    try:
        return await build_brief(h, q, kw.get("condition"), kw.get("country"), demo=True)
    finally:
        await h.aclose()


def test_rsid_resolves_canonical_isoform():
    b = run(_brief("rs113488022"))
    assert b["variant"]["gene"] == "BRAF" and b["variant"]["change"]["short"] == "V600E"  # not V640E
    assert "BRAF V640E" in b["variant"]["isoform_alternatives"]
    assert {w["code"] for w in b["warnings"]} >= {"isoform_numbering", "germline_vs_somatic"}
    assert b["variant"]["clinvar"]["significance"] == ["pathogenic"]


def test_unknown_rsid():
    with pytest.raises(NotFound):
        run(_brief("rs999999999"))


def test_trial_tiers_and_exclusion_logic():
    b = run(_brief("BRAF V600E"))
    t = {x["nct"]: x for x in b["trials"]["items"]}
    assert t["DEMO-001"]["tier"] == "variant"
    assert t["DEMO-003"]["tier"] == "codon"            # 'V600 mutation' + V600K
    assert t["DEMO-004"]["tier"] == "gene"
    assert t["DEMO-005"]["tier"] != "variant"           # wild-type melanoma must not count as variant trial
    assert "variant_in_exclusion" in t["DEMO-005"]["flags"]
    assert "variant_in_exclusion" in t["DEMO-006"]["flags"] and t["DEMO-006"]["tier"] == "condition"


def test_sorting_puts_variant_first_then_recruiting():
    items = run(_brief("BRAF V600E"))["trials"]["items"]
    assert items[0]["tier"] == "variant"
    first_variant = [i for i in items if i["tier"] == "variant"]
    assert first_variant[0]["status"] == "RECRUITING"


def test_country_filter_and_agents():
    b = run(_brief("BRAF V600E", country="Brazil"))
    assert all("Brazil" in t["countries"] for t in b["trials"]["items"])
    names = [a["name"] for a in b["trials"]["agents"]]
    assert "demo-braf-inhibitor" in names and "demo-pd1" not in names  # wild-type trial's drug excluded


def test_publications_tiers_and_retraction():
    p = run(_brief("BRAF V600E"))["publications"]["items"]
    by = {x["pmid"]: x for x in p}
    assert by["9000002"]["tier"] == 1 and by["9000001"]["tier"] == 2 and by["9000004"]["tier"] == 5
    assert by["9000005"]["retracted"] is True


def test_split_eligibility():
    inc, exc = split_eligibility("Inclusion Criteria: a\nExclusion Criteria: b")
    assert "a" in inc and "b" not in inc and "b" in exc


def test_padrao_regex_trata_asterisco_como_literal():
    from app.ranking import _pats

    q = parse_query("BRAF V600*")
    exata, codon, _gene = _pats("BRAF", q.change)
    assert exata.search("BRAF V600E") is None
    assert exata.search("BRAF V600*") is not None
    assert codon.search("BRAF V600E") is not None

    q2 = parse_query("BRAF p.Tyr640Ter")
    exata2, _, _ = _pats("BRAF", q2.change)
    assert q2.change.short == "Y640*"
    assert exata2.search("BRAF p.(Y640*)") is not None
    assert exata2.search("BRAF Y640E") is None


def test_consulta_com_asterisco_nao_gera_falso_match_variante():
    b = run(_brief("BRAF V600*"))
    t = {x["nct"]: x for x in b["trials"]["items"]}
    assert t["DEMO-001"]["tier"] != "variant"
    assert t["DEMO-001"]["tier"] == "codon"


def test_notacao_tradicional_tyr640ter_e_segura():
    b = run(_brief("BRAF p.Tyr640Ter"))
    assert b["variant"]["change"]["short"] == "Y640*"
    assert all(isinstance(x["tier"], str) for x in b["trials"]["items"])


def test_clinvar_esummary_sucesso_e_falha_parcial():
    import httpx

    from app.demo_data import CLINVAR_REVIEW, _handler
    from app.http import SourceError
    from app.sources import fetch_clinvar_review

    def sucesso(req):
        uid = req.url.params.get("id")
        return httpx.Response(200, json={"result": {"uids": [uid], uid: CLINVAR_REVIEW[uid]}})

    def falha(req):
        if req.url.path.endswith("esummary.fcgi") and req.url.params.get("db") == "clinvar":
            return httpx.Response(404)
        return _handler(req)

    async def direto(transport):
        http = Http(transport=transport)
        try:
            return await fetch_clinvar_review(http, "rs113488022")
        finally:
            await http.aclose()

    revisao = asyncio.run(direto(httpx.MockTransport(sucesso)))
    assert revisao["review_status"].startswith("criteria provided")
    assert revisao["last_evaluated"] == "2025-04-12"
    assert revisao["stars"] == 2
    with pytest.raises(SourceError):
        asyncio.run(direto(httpx.MockTransport(lambda req: httpx.Response(404))))

    async def parcial():
        http = Http(transport=httpx.MockTransport(falha))
        try:
            return await build_brief(http, "rs113488022", None, None)
        finally:
            await http.aclose()

    b = asyncio.run(parcial())
    assert b["variant"]["clinvar_review"] is None
    assert any(w["code"] == "source_down" and w["args"]["source"] == "ClinVar (esummary)"
               for w in b["warnings"])
    assert b["publications"]["items"] and b["trials"]["items"]


def test_source_failure_is_partial():
    import httpx

    from app.demo_data import _handler
    def h(req):
        if req.url.host == "clinicaltrials.gov":
            return httpx.Response(503)
        return _handler(req)
    async def go():
        http = Http(transport=httpx.MockTransport(h))
        try:
            return await build_brief(http, "BRAF V600E", None, None)
        finally:
            await http.aclose()
    import app.http as ah
    orig = asyncio.sleep
    async def fast(_): return None
    ah.asyncio.sleep = fast
    try:
        b = run(go())
    finally:
        ah.asyncio.sleep = orig
    assert any(w["code"] == "source_down" for w in b["warnings"]) and b["publications"]["items"]
