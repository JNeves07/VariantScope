"""SYNTHETIC offline demo transport (VTS_DEMO=1) and test fixtures.

Everything here is invented to exercise the pipeline: IDs are 'DEMO-…'/'9000…', never real registry
records. The UI shows a banner and disables outbound links when demo data is served.
"""
from __future__ import annotations

import random

import httpx


def _spdi(seq, pos, d, i):
    return {"seq_id": seq, "position": pos, "deleted_sequence": d, "inserted_sequence": i}


DBSNP_BRAF = {
    "refsnp_id": "113488022",
    "primary_snapshot_data": {"allele_annotations": [
        {"assembly_annotation": [{"genes": [{"locus": "BRAF", "rnas": [
            {"hgvs": "NM_004333.6:c.1799T>A", "protein": {"variant": {"spdi": _spdi("NP_004324.2", 599, "V", "E")}}},
            {"hgvs": "NM_001374258.1:c.1919T>A", "protein": {"variant": {"spdi": _spdi("NP_001361187.1", 639, "V", "E")}}},
            {"hgvs": "NM_001378474.1:c.1919T>A", "protein": {"variant": {"spdi": _spdi("NP_001365403.1", 639, "V", "E")}}},
        ]}]}],
         "clinical": [{"clinical_significances": ["pathogenic"], "disease_names": ["Cardiofaciocutaneous syndrome", "Melanoma"],
                       "review_status": "criteria provided, multiple submitters, no conflicts",
                       "accession_version": "RCV-DEMO.1", "citations": [9000001]}]},
        {"assembly_annotation": [], "clinical": []},
    ]},
}


def _study(nct, title, status, phase, year, n, sponsor, interv, country, summary="", incl="", excl="", cond=("Thyroid Cancer",)):
    return {"protocolSection": {
        "identificationModule": {"nctId": nct, "briefTitle": title},
        "statusModule": {"overallStatus": status, "startDateStruct": {"date": f"{year}-03"}},
        "designModule": {"phases": phase, "enrollmentInfo": {"count": n}, "studyType": "INTERVENTIONAL"},
        "sponsorCollaboratorsModule": {"leadSponsor": {"name": sponsor}},
        "conditionsModule": {"conditions": list(cond)},
        "armsInterventionsModule": {"interventions": [{"name": a, "type": "DRUG"} for a in interv]},
        "contactsLocationsModule": {"locations": [{"country": c, "city": ci, "facility": "Demo site"} for c, ci in country]},
        "descriptionModule": {"briefSummary": summary},
        "eligibilityModule": {"eligibilityCriteria": f"Inclusion Criteria:\n{incl}\nExclusion Criteria:\n{excl}"},
    }}


def demo_studies():
    S = []
    S.append(_study("DEMO-001", "[DEMO] Targeted therapy for BRAF V600E-mutant thyroid cancer", "RECRUITING", ["PHASE2"], 2024, 80,
                    "Demo University", ["demo-braf-inhibitor", "demo-mek-inhibitor"], [("Brazil", "São Paulo"), ("France", "Paris")],
                    incl="Histologically confirmed disease with BRAF V600E mutation."))
    S.append(_study("DEMO-002", "[DEMO] Neoadjuvant therapy, real-world study", "NOT_YET_RECRUITING", ["PHASE4"], 2026, 335,
                    "Demo Medical University", ["demo-braf-inhibitor"], [("China", "Fuzhou")],
                    summary="Genotype-driven neoadjuvant therapy in patients carrying BRAF V600E."))
    S.append(_study("DEMO-003", "[DEMO] Any BRAF V600 mutation solid tumours", "RECRUITING", ["PHASE1", "PHASE2"], 2023, 120,
                    "Demo Pharma", ["demo-pan-raf"], [("Brazil", "Porto Alegre")], incl="BRAF V600 mutation (V600K or V600R)."))
    S.append(_study("DEMO-004", "[DEMO] BRAF-mutated cancers basket", "ACTIVE_NOT_RECRUITING", ["PHASE2"], 2021, 60,
                    "Demo Pharma", ["demo-braf-inhibitor"], [("United States", "Boston")], incl="Tumour harbouring a BRAF alteration."))
    S.append(_study("DEMO-005", "[DEMO] Immunotherapy in BRAF wild-type melanoma", "RECRUITING", ["PHASE3"], 2022, 400,
                    "Demo Group", ["demo-pd1"], [("Brazil", "Campinas")], cond=("Melanoma",),
                    incl="BRAF wild-type melanoma. Patients with V600E excluded.", excl="BRAF V600E mutation."))
    S.append(_study("DEMO-006", "[DEMO] Chemotherapy regimen", "RECRUITING", ["PHASE3"], 2022, 200, "Demo Group",
                    ["demo-chemo"], [("Brazil", "Recife")], excl="Known BRAF V600E mutation."))
    rnd = random.Random(7)
    st = ["COMPLETED", "ACTIVE_NOT_RECRUITING", "COMPLETED", "TERMINATED", "RECRUITING"]
    for i in range(7, 31):
        yr = rnd.choice(range(2009, 2026))
        S.append(_study(f"DEMO-{i:03d}", f"[DEMO] BRAF V600E study {i}", rnd.choice(st), [rnd.choice(["PHASE1", "PHASE2", "PHASE3"])],
                        yr, rnd.randint(20, 300), "Demo Sponsor", [rnd.choice(["demo-braf-inhibitor", "demo-mek-inhibitor", "demo-combo"])],
                        [(rnd.choice(["United States", "France", "Germany", "Brazil"]), "Demo City")], incl="BRAF V600E mutation."))
    return S


PUBS = {
    "9000001": {"title": "[DEMO] Randomised trial of BRAF/MEK inhibition in BRAF V600E tumours.", "src": "Demo J Oncol", "date": "2024 Jan",
                "types": ["Randomized Controlled Trial", "Journal Article"]},
    "9000002": {"title": "[DEMO] Meta-analysis of BRAF V600E targeted therapy outcomes.", "src": "Demo Rev", "date": "2023 Jun",
                "types": ["Meta-Analysis", "Systematic Review"]},
    "9000003": {"title": "[DEMO] Case report: response in BRAF V600E thyroid carcinoma.", "src": "Demo Case Rep", "date": "2025 Feb",
                "types": ["Case Reports"]},
    "9000004": {"title": "[DEMO] Preclinical BRAF V600E signalling.", "src": "Demo Bio", "date": "2020 Nov", "types": ["Journal Article"]},
    "9000005": {"title": "[DEMO] Retracted study on BRAF V600E.", "src": "Demo J", "date": "2019 Mar",
                "types": ["Journal Article", "Retracted Publication"]},
}


def _json(d: dict, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=d)


def _handler(request: httpx.Request) -> httpx.Response:
    u, p = request.url, request.url.params
    j = _json
    if "/variation/v0/refsnp/" in u.path:
        return j(DBSNP_BRAF) if u.path.rstrip("/").endswith("113488022") else j({"error": "nf"}, 404)
    if u.path.endswith("esearch.fcgi"):
        ids = list(PUBS)
        if p.get("sort") == "date":
            ids = ["9000003", "9000001"]
        return j({"esearchresult": {"count": "1234", "idlist": ids}})
    if u.path.endswith("esummary.fcgi"):
        ids = p.get("id", "").split(",")
        res = {"uids": ids}
        for i in ids:
            d = PUBS[i]
            res[i] = {"uid": i, "title": d["title"], "source": d["src"], "pubdate": d["date"], "pubtype": d["types"],
                      "authors": [{"name": "Demo A"}, {"name": "Demo B"}, {"name": "Demo C"}, {"name": "Demo D"}], "articleids": []}
        return j({"result": res})
    if u.host == "clinicaltrials.gov":
        studies = demo_studies()
        term = p.get("query.term", "")
        if "AND" not in term:  # gene-only active query
            studies = [s for s in studies if s["protocolSection"]["statusModule"]["overallStatus"] in
                       ("RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION")]
        loc = p.get("query.locn")
        if loc:
            studies = [s for s in studies if any(l["country"] == loc for l in s["protocolSection"]["contactsLocationsModule"]["locations"])]
        return j({"totalCount": len(studies), "studies": studies})
    return j({}, 404)


def demo_transport() -> httpx.MockTransport:
    return httpx.MockTransport(_handler)
