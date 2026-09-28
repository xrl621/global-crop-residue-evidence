"""Extract exact rice-season arm means/SDs from open primary JATS Table 2.

One randomized block experiment, not 18 independent studies. Excludes the
non-rice wheat/oil-rape columns and cross-year average rows. Publisher JATS
is distributed by Europe PMC; the expected XML SHA is pinned below.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path
import re
from urllib.request import urlopen
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'literature/primary_extractions/xiong2015_rice_season_table2.csv'
AUDIT=ROOT/'data/processed/xiong2015_review_20260928/source_numeric_audit.csv'
SECONDARY=ROOT/'data/external/figshare_29817482_rice_ghg/data_Full.csv'
XML_URL='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4667221/fullTextXML'
XML_SHA='6b4ae3f91ed840809b04a4c48efadc0efad21b33dcfbceb827ed9b9fa82e9678'
DOI='10.1038/srep17774'
STUDY='xiong_moling_2008_2011'
TITLE='Differences in net global warming potential and greenhouse gas intensity between major rice-based cropping systems in China'
FIELDS=['effect_id','study_id','paper_doi','paper_title','publication_year','experiment_year',
    'country','location','latitude','longitude','crop_core','crop_as_reported','season',
    'residue_as_reported','pathway','outcome','outcome_unit','treatment_arm','control_arm',
    'treatment_mean','control_mean','treatment_sd','control_sd','treatment_n','control_n',
    'shared_control_group','source_locator','nitrogen_rate','water_regime','system_boundary',
    'quality_flags','sensitivity_note']
METRICS={'CH4':(1,2,'kg CH4 ha-1 rice-season-1'),
         'N2O':(4,5,'kg N2O-N ha-1 rice-season-1'),
         'yield':(7,8,'t rice grain ha-1')}
YEAR_LABELS={'2008–2009':2009,'2009–2010':2010,'2010–2011':2011}
NUM_RE=re.compile(r'^\s*([+\-−]?\d+(?:\.\d+)?)\s*±\s*([+\-−]?\d+(?:\.\d+)?)')


def cell_text(cell):
    return ' '.join(''.join(cell.itertext()).split())


def number_sd(cell):
    match=NUM_RE.match(cell_text(cell).replace('−','-'))
    if not match:
        raise ValueError(f'Mean ± SD not parseable: {cell_text(cell)!r}')
    mean,sd=map(float,match.groups())
    if not math.isfinite(mean) or mean<=0 or not math.isfinite(sd) or sd<0:
        raise ValueError(f'Invalid source mean/SD: {cell_text(cell)!r}')
    return format(mean,'.12g'),format(sd,'.12g')


def read_xml(path=None):
    body=Path(path).read_bytes() if path else urlopen(XML_URL,timeout=30).read()
    digest=hashlib.sha256(body).hexdigest()
    if digest!=XML_SHA:
        raise ValueError(f'Primary XML version changed: {digest}; do not silently re-extract')
    return ET.fromstring(body)


def extract(root):
    table=root.find(".//table-wrap[@id='t2']")
    if table is None:
        raise ValueError('Primary Table 2 not found')
    foot=' '.join(''.join(table.find('table-wrap-foot').itertext()).split())
    if 'Mean' not in foot or 'SD' not in foot:
        raise ValueError('Table 2 does not explicitly state SD')
    arms={}
    year=None
    for tr in table.findall('.//tr'):
        cells=[c for c in tr if c.tag in ('th','td')]
        if not cells:
            continue
        label=cell_text(cells[0])
        if label in YEAR_LABELS:
            year=YEAR_LABELS[label]
            continue
        if label.startswith('Average'):
            break
        if label not in ('UR-S0','UR-S1','UR-S2','DR-S0','DR-S1','DR-S2'):
            continue
        if year is None or len(cells)!=10:
            raise ValueError(f'Unexpected Table 2 row structure: {year} {label} {len(cells)}')
        arms[(year,label)]=cells[1:]
    if len(arms)!=18:
        raise ValueError(f'Expected 18 year × treatment rows, got {len(arms)}')
    output=[]
    for year in (2009,2010,2011):
        for system,season,col in [('UR','single_rice',0),('DR','early_rice',0),('DR','late_rice',1)]:
            control=f'{system}-S0'
            for dose,level in [(3,'S1'),(6,'S2')]:
                treatment=f'{system}-{level}'
                for outcome,(first,second,unit) in METRICS.items():
                    ix=first if col==0 else second
                    # Values refer to data cells after the row label; the
                    # three 3-column blocks are CH4, N2O and grain yield.
                    tc=arms[(year,treatment)][ix]
                    cc=arms[(year,control)][ix]
                    tm,ts=number_sd(tc);cm,cs=number_sd(cc)
                    shared=f'xiong_{system}_{year}_{season}_S0_{outcome}'
                    output.append(dict(effect_id=f'xiong_{system}_{year}_{season}_{level}_{outcome}',
                        study_id=STUDY,paper_doi=DOI,paper_title=TITLE,publication_year='2015',
                        experiment_year=str(year),country='China',
                        location='Mo ling town, Nanjing, Jiangsu',latitude='31.866667',
                        longitude='118.833333',crop_core='rice',
                        crop_as_reported='wheat–single rice rotation' if system=='UR' else 'oil rape–early rice–late rice rotation',
                        season=season,
                        residue_as_reported=f'{dose} t ha-1 crop straw incorporated before rice transplanting; feedstock species unreported',
                        pathway='direct_return',outcome=outcome,outcome_unit=unit,
                        treatment_arm=treatment,control_arm=control,
                        treatment_mean=tm,control_mean=cm,treatment_sd=ts,control_sd=cs,
                        treatment_n='3',control_n='3',shared_control_group=shared,
                        source_locator=f'Table 2, {year-1}–{year} annual cycle, {season}',
                        nitrogen_rate='250 kg N ha-1' if system=='UR' else '200 kg N ha-1',
                        water_regime='continuous flooding with midseason drainage',
                        system_boundary=f'{season} field rice-season {outcome}; excludes non-rice season and upstream',
                        quality_flags='straw_feedstock_species_unreported',
                        sensitivity_note='One fixed three-year experiment; year/dose/season arms and shared S0 control are dependent. Straw species not named in primary Methods or Tables S1–S2.'))
    if len(output)!=54 or len({r['effect_id'] for r in output})!=54:
        raise ValueError('Expected 18 pairs × 3 endpoints, unique IDs')
    return output


def audit_secondary(primary_rows, secondary_path=SECONDARY):
    """Compare candidate arm cells to primary table; never repair by averaging."""
    with Path(secondary_path).open(encoding='utf-8-sig',newline='') as stream:
        secondary=[r for r in csv.DictReader(stream) if r['StudyID']=='96']
    if len(secondary)!=27:
        raise ValueError(f'Expected 27 source StudyID 96 arms, found {len(secondary)}')
    sea={'single_rice':'','early_rice':'Early_Season','late_rice':'Late_Season'}
    field={'CH4':'CH4','N2O':'N2O','yield':'GY'}
    results=[]
    for pair in primary_rows:
        for arm in ('control','treatment'):
            is_control=arm=='control'
            year=pair['experiment_year'];season=sea[pair['season']]
            dose='NA' if is_control else str(int(pair['residue_as_reported'].split(' t ')[0])*1000)
            management='Removed' if is_control else 'Incorporated_Straw'
            hits=[r for r in secondary if r['ExY']==year and r['Sea']==season and
                  r['ReM']==management and r['ReQ']==dose]
            if len(hits)!=1:
                raise ValueError(f'Nonunique secondary arm: {year} {season} {management} {dose}: {len(hits)}')
            source=hits[0]
            end=pair['outcome'];col=field[end]
            unit_factor=1000 if end=='yield' else 1
            for statistic,secondary_field in [('mean',col),('sd','SD.'+col)]:
                p=float(pair[f'{arm}_{statistic}'])
                s=float(source[secondary_field])/unit_factor
                match=math.isclose(p,s,rel_tol=0,abs_tol=.000001)
                results.append(dict(effect_id=pair['effect_id'],arm=arm,outcome=end,
                    statistic=statistic,source_ES_ID=source['ES_ID'],
                    primary_value=p,secondary_value_in_primary_unit=s,
                    status='matches_primary' if match else 'secondary_numeric_conflict',
                    primary_locator=pair['source_locator']))
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--xml',type=Path,help='Local copy of exact primary XML (optional)')
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--audit-output',type=Path,default=AUDIT)
    parser.add_argument('--audit-secondary',type=Path,metavar='LOCAL_CSV',
        help='Optional local Figshare candidate table; never required to reproduce primary extraction')
    args=parser.parse_args()
    rows=extract(read_xml(args.xml))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    message=f'primary_effects={len(rows)} trial_keys=1 source={XML_URL} xml_sha256={XML_SHA}'
    if args.audit_secondary:
        audit=audit_secondary(rows,args.audit_secondary)
        args.audit_output.parent.mkdir(parents=True,exist_ok=True)
        with args.audit_output.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(audit[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(audit)
        conflicts=sum(r['status']=='secondary_numeric_conflict' for r in audit)
        message+=f' secondary_conflicts={conflicts}'
    print(message)


if __name__=='__main__':main()
