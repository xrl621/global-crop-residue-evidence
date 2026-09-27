"""Read-only evidence inventory and bounded reproducible cross-source discovery.

No candidate is promoted into the effect database. Bibliographic search hits
are not studies or effect observations. Crossref first-page and DataCite page
limits are logged explicitly.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import re
import time
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/search_inventory_20260927"
QUERIES = [
    "straw return meta-analysis yield soil carbon greenhouse gas",
    "crop residue retention removal yield meta-analysis",
    "straw biochar yield greenhouse gas field experiment",
    "crop residue burning yield soil organic carbon",
    "maize stover removal yield soil carbon long term",
    "residue incorporation nitrous oxide meta-analysis",
    "biochar field maize wheat soil carbon Africa Europe America",
    "straw management global dataset yield climate",
]


def dump(name, data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")


def doi_key(s):
    return re.sub(r"^https?://(?:dx\.)?doi.org/", "", str(s).strip().lower()).rstrip("/ .")


def inventory():
    d = pd.read_csv(ROOT/"literature/evidence_database.csv",keep_default_na=False)
    s = pd.read_csv(ROOT/"data/processed/stage_20260927/screened_effects.csv",keep_default_na=False)
    records=[]
    for name,df in [("main",d),("screened_descriptive",s)]:
        papers=df.apply(lambda r:doi_key(r.paper_doi) or r.source_url or r.paper_title,axis=1)
        records.append(dict(layer=name,rows=len(df),trial_keys=df.study_id.nunique(),
                            paper_identity_keys=papers.nunique(),countries=sorted(set(df.country)-{""})))
        df.groupby(["pathway","outcome"]).agg(rows=("effect_id","size"),trials=("study_id","nunique")).reset_index().to_csv(OUT/f"{name}_pathway_outcome.csv",index=False)
        df.groupby("country").agg(rows=("effect_id","size"),trials=("study_id","nunique")).reset_index().to_csv(OUT/f"{name}_countries.csv",index=False)
    candidate_path=ROOT/"data/enrichment/outputs/additional_meta_v1/expanded_public_effect_registry_NOT_FINAL.csv"
    c=pd.read_csv(candidate_path,keep_default_na=False,low_memory=False)
    group=[]
    for ds,g in c.groupby("dataset"):
        row=dict(dataset=ds,rows=len(g),source_dois="|".join(sorted(set(g.source_doi)-{""})),
                 title_keys=g.loc[g.title_key!="","title_key"].nunique(),
                 source_study_ids=g.loc[g.source_study_id!="","source_study_id"].nunique(),
                 outcomes="|".join(sorted(set(g.outcome)-{""})))
        for field in ["repeated_view","source_exact_duplicate","possible_repeated_numeric_record","approved_for_main_analysis","core_crop_explicit"]:
            row[field+"_true"] = int(g[field].astype(str).str.lower().eq("true").sum())
        group.append(row)
    pd.DataFrame(group).to_csv(OUT/"existing_candidate_sources.csv",index=False)
    c.groupby("outcome").size().rename("candidate_rows_not_independent_trials").reset_index().to_csv(OUT/"candidate_outcomes_NOT_FINAL.csv",index=False)
    dump("candidate_field_audit.json",{field:c[field].astype(str).value_counts().head(20).to_dict() for field in ["feedstock_scope","admission_status","contrast_scope","variance_provenance","view_dedup_status","cross_dataset_title_overlap"]})
    raw=ROOT/"data/external/figshare_29817482_rice_ghg/data_Full.csv"
    rice=pd.read_csv(raw,keep_default_na=False)
    rice.groupby("ReM").agg(observations=("StudyID","size"),source_study_ids=("StudyID","nunique")).reset_index().to_csv(OUT/"rice_raw_residue_management.csv",index=False)
    paths=[ROOT/"literature/evidence_database.csv",candidate_path,raw]
    dump("inventory.json",dict(as_of="2026-09-27",main_layers=records,
         expanded_candidate_rows=len(c),expanded_candidate_unique_nonempty_title_keys=c.loc[c.title_key!="","title_key"].nunique(),
         rice_raw_observations=len(rice),rice_source_study_ids=rice.StudyID.nunique(),
         checksums={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
         warning="Different layers and datasets overlap; row counts cannot be summed into independent studies"))


def request_source(job):
    provider,query=job
    if provider=="crossref":
        url="https://api.crossref.org/works"
        params={"query.bibliographic":query,"rows":100,"filter":"until-pub-date:2026-09-27"}
    else:
        url="https://api.datacite.org/dois"
        params={"query":query,"page[size]":100}
    start=time.time()
    try:
        resp=requests.get(url,params=params,timeout=40,headers={"User-Agent":"CropResidueEvidenceResearch/1.0 (public bibliographic inventory)"})
        if resp.status_code == 429:
            time.sleep(3)
            resp=requests.get(url,params=params,timeout=40)
        resp.raise_for_status()
        data=resp.json()
        hits=data["message"]["items"] if provider=="crossref" else data["data"]
        total=data["message"].get("total-results") if provider=="crossref" else data.get("meta",{}).get("total")
        pages=1
        page_errors=[]
        if provider=="datacite":
            for page in range(2,min(10,(int(total or 0)+99)//100)+1):
                try:
                    extra=requests.get(url,params={**params,"page[number]":page},timeout=40)
                    extra.raise_for_status()
                    hits.extend(extra.json()["data"])
                    pages+=1
                except Exception as exc:
                    page_errors.append({"page":page,"error":str(exc)})
        normalized=[]
        for h in hits:
            if provider=="crossref":
                title=" ".join(h.get("title",[])); doi=h.get("DOI","")
                year=(h.get("published",{}).get("date-parts") or [[None]])[0][0]
                authors=h.get("author",[]); first=authors[0].get("family","") if authors else ""
                typ=h.get("type",""); link=h.get("URL","")
                journal=" | ".join(h.get("container-title",[]))
            else:
                a=h["attributes"]; title=" ".join(t.get("title","") for t in a.get("titles",[]));doi=a.get("doi","")
                year=a.get("publicationYear"); authors=a.get("creators",[]);first=authors[0].get("name","") if authors else ""
                typ=a.get("types",{}).get("resourceTypeGeneral","");link=a.get("url","");journal=a.get("publisher","")
            title=re.sub("<[^>]+>","",title)
            core=bool(re.search(r"straw|stover|crop residu|cereal residu|biochar|stubble",title,re.I))
            outcome=bool(re.search(r"yield|carbon|soil|greenhouse|methane|nitrous|emission|productiv|dataset|data set|database|management",title,re.I))
            normalized.append(dict(provider=provider,query=query,doi=doi_key(doi),title=title,year=year,first_author=first,
                                   source=journal,type=typ,url=link,title_screen=core and outcome))
        return dict(provider=provider,query=query,url=resp.url,status="ok",returned=len(hits),total_hits=total,
                    retrieval_cap=100 if provider=="crossref" else 1000,pages_retrieved=pages,
                    page_errors=page_errors,elapsed_seconds=round(time.time()-start,2)),normalized
    except Exception as exc:
        return dict(provider=provider,query=query,status="failed",error=str(exc),elapsed_seconds=round(time.time()-start,2)),[]


def search():
    jobs=[("crossref",q) for q in QUERIES]+[("datacite",q) for q in [
        '(titles.title:straw OR titles.title:"crop residue") AND (titles.title:meta OR titles.title:dataset)',
        'titles.title:biochar AND (titles.title:yield OR titles.title:emissions)',
        'titles.title:"crop residue" AND (titles.title:burning OR titles.title:removal)',
    ]]
    results=list(ThreadPoolExecutor(max_workers=3).map(request_source,jobs))
    dump("api_search_log.json",[x[0] for x in results])
    all_rows=[row for _,rows in results for row in rows]
    table=pd.DataFrame(all_rows)
    table.to_csv(OUT/"api_hits_all_NOT_SCREENED.csv",index=False)
    eligible=table[table.title_screen & pd.to_numeric(table.year,errors="coerce").le(2026)].copy()
    # DOI exact deduplication; unresolved title variants remain distinct for audit.
    eligible["identity"]=eligible.doi.where(eligible.doi!="",eligible.title.str.lower()+"|"+eligible.first_author.str.lower())
    merged=[]
    for _,g in eligible.groupby("identity",sort=False):
        r=g.iloc[0].to_dict();r["providers"]="|".join(sorted(set(g.provider)));r["matched_queries"]=" || ".join(sorted(set(g["query"])))
        r["status"]="TITLE_SCREEN_ONLY_NOT_FORMAL_EVIDENCE";merged.append(r)
    final=pd.DataFrame(merged)
    main=pd.read_csv(ROOT/"literature/evidence_database.csv",keep_default_na=False)
    final["doi_already_in_main"]=final.doi.isin(set(main.paper_doi.map(doi_key))-{""})
    final.to_csv(OUT/"api_candidates_deduplicated_NOT_ADMITTED.csv",index=False)
    print(json.dumps({"requests":len(jobs),"successful_requests":sum(x[0]["status"]=="ok" for x in results),
                      "returned_metadata_hits":len(table),"title_screen_deduplicated":len(final),
                      "already_in_main_by_doi":int(final.doi_already_in_main.sum())},indent=2))


if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    inventory()
    search()
