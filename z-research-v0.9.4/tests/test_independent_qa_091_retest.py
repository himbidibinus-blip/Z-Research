# Adapted QA v0.9.1 independent probes: the original bug-13 characterization
# expects the defect; here it asserts the intended v0.9.2 behavior.
"""Independent read-only-release QA; tests execute against temporary database via conftest."""
import io, json, hashlib
from pathlib import Path
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
from app.main import app
from app import ai_features, main, v09

SAMPLE=Path('sample/consumer_survey_demo.csv').read_bytes()
def client_owner():
 c=TestClient(app)
 assert c.post('/api/auth/setup',json={'username':'auditor','password':'secure-qa-pass-1234'}).status_code==200
 return c

def upload(c,raw=SAMPLE,name='data.csv'):
 r=c.post('/api/datasets',files={'file':(name,raw)})
 assert r.status_code==200,r.text
 return r.json()['id']

def project(c,did):
 r=c.post('/api/v09/projects',json={'name':'Independent Audit', 'dataset_id':did})
 assert r.status_code==200,r.text
 return r.json()['id']

def addref(c,title='Reference alpha'):
 r=c.post('/api/v05/references/manual',json={'title':title,'authors':'Smith, J','year':2025,'doi':'10.7777/'+title.lower().replace(' ','-')})
 assert r.status_code==200,r.text
 return r.json()['id']

def test_ind_01_owner_route_enforcement_get_post_patch_delete_export():
 c=client_owner();did=upload(c);pid=project(c,did);rid=addref(c)
 paths=[('GET','/api/datasets'),('GET',f'/api/datasets/{did}'),('GET',f'/api/datasets/{did}/provenance'),('GET',f'/api/v09/projects/{pid}'),('GET','/api/v05/references'),('GET','/api/v09/projects'),('GET',f'/api/v09/projects/{pid}/chapters/1/docx'),('DELETE',f'/api/v05/references/{rid}'),('PATCH',f'/api/v09/projects/{pid}')]
 anon=TestClient(app)
 for method,path in paths:
  r=anon.request(method,path,json={} if method=='PATCH' else None)
  assert r.status_code==401,(method,path,r.status_code,r.text[:150])


def test_ind_02_owner_origin_fetch_metadata_host_checks():
 c=client_owner();did=upload(c)
 for headers in ({'Origin':'https://malicious.example'},{'Sec-Fetch-Site':'cross-site'},{'Origin':'null'}):
  r=c.post('/api/analyze/descriptive',json={'dataset_id':did,'columns':['trust_1']},headers=headers)
  assert r.status_code==403,(headers,r.text)
 bad=TestClient(app,base_url='http://attack.example')
 assert bad.get('/api/datasets').status_code==403 or bad.get('/api/datasets').status_code==401


def test_ind_03_xlsx_bytes_preserved_and_hash_tamper_detected():
 c=client_owner()
 buf=io.BytesIO();pd.DataFrame({'a':[1,2,3],'b':[2,3,4]}).to_excel(buf,index=False)
 raw=buf.getvalue();did=upload(c,raw,'orig.xlsx')
 meta=c.get(f'/api/datasets/{did}/provenance').json()
 assert meta['archive_status']=='VERIFIED'
 assert meta['sha256']==hashlib.sha256(raw).hexdigest()
 rawpath=main.DATA/'raw_uploads'/f'{did}.xlsx'
 assert rawpath.read_bytes()==raw
 rawpath.write_bytes(raw+b'BAD')
 assert c.get(f'/api/datasets/{did}/provenance').json()['archive_status']=='HASH_MISMATCH'


def test_ind_04_reference_mutation_and_deletion_alerts():
 c=client_owner();did=upload(c);pid=project(c,did);rid=addref(c)
 save=f'/api/v09/projects/{pid}/chapters/2/save'
 assert c.post(save,json={'body':'Academic draft','reference_ids':[rid],'style':'ieee'}).status_code==200
 assert c.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['citation_style']=='ieee'
 with ai_features.db() as db:db.execute('UPDATE research_references SET authors=? WHERE id=?',('Doe, Jane',rid))
 assert c.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['status']=='stale'
 assert c.delete(f'/api/v05/references/{rid}').status_code==200
 assert c.get(f'/api/v09/projects/{pid}/audit').json()['draft_status']['2']=='broken_citation'


def test_ind_05_reject_reference_list_mixed_duplicate_and_invalid():
 c=client_owner();did=upload(c);pid=project(c,did);rid=addref(c)
 for ids in ([rid,rid],[rid,'missing'],['missing']):
  for endpoint in (f'/api/v09/projects/{pid}/chapters/1/save',f'/api/v09/projects/{pid}/chapters/1/draft'):
   payload={'body':'Research draft','reference_ids':ids} if endpoint.endswith('save') else {'reference_ids':ids}
   assert c.post(endpoint,json=payload).status_code==422


def test_ind_06_data_change_stales_model_analysis_and_chapter():
 c=client_owner();did=upload(c);pid=project(c,did)
 model={'nodes':[{'id':'x','label':'Trust','indicators':['trust_1'],'measurement':'reflective'},{'id':'y','label':'Loyalty','indicators':['purchase_intention'],'measurement':'reflective'}],'edges':[{'source':'x','target':'y','kind':'direct'}]}
 r=c.patch(f'/api/v09/projects/{pid}',json={'model':model});assert r.status_code==200,r.text
 r=c.post(f'/api/v09/projects/{pid}/analyze',json={'bootstraps':35,'seed':11});assert r.status_code==200,r.text
 assert c.post(f'/api/v09/projects/{pid}/chapters/4/save',json={'body':'Results draft'}).status_code==200
 assert c.get(f'/api/v09/projects/{pid}').json()['analysis']['status']=='current'
 r=c.post(f'/api/v05/datasets/{did}/edit-cell',json={'row':0,'column':'trust_1','value':4.0});assert r.status_code==200,r.text
 projectdata=c.get(f'/api/v09/projects/{pid}').json()
 assert projectdata['analysis']['status']=='stale'
 assert projectdata['chapters']['4']['status']=='stale'
 assert c.post(f'/api/v09/projects/{pid}/chapters/4/draft',json={'reference_ids':[]}).status_code==409


def test_ind_07_independent_single_item_math():
 from app.sem_engine import estimate
 rng=np.random.default_rng(1609);x=rng.normal(size=120);y=.7*x+rng.normal(size=120)
 df=pd.DataFrame({'x':x,'y':y})
 nodes=[{'id':'x','label':'X','indicators':['x'],'measurement':'reflective'},{'id':'y','label':'Y','indicators':['y'],'measurement':'reflective'}]
 edges=[{'source':'x','target':'y','kind':'direct','label':'H1'}]
 out=estimate(df,nodes,edges,bootstraps=50,seed=14)
 correlation=float(np.corrcoef(x,y)[0,1]);assert abs(out['paths']['X -> Y']-correlation)<1e-12
 assert abs(out['r_squared']['Y']-correlation**2)<1e-12
 assert out['bootstrap']['X -> Y']['samples']==50
 assert out['bootstrap']['X -> Y']==estimate(df,nodes,edges,bootstraps=50,seed=14)['bootstrap']['X -> Y']


def test_ind_08_missing_and_nonfinite_observations_are_excluded():
 from app.sem_engine import estimate
 rng=np.random.default_rng(8);df=pd.DataFrame({'x':rng.normal(size=55),'y':rng.normal(size=55)})
 df.loc[3,'x']=np.nan;df.loc[4,'y']=np.inf
 nodes=[{'id':'x','label':'X','indicators':['x']},{'id':'y','label':'Y','indicators':['y']}]
 out=estimate(df,nodes,[{'source':'x','target':'y'}],bootstraps=0)
 assert out['n']==53 and out['excluded_rows']==2


def test_ind_09_legacy_unhashed_chapter_requires_review():
 c=client_owner();did=upload(c);pid=project(c,did);rid=addref(c)
 with ai_features.db() as db:
  db.execute('INSERT INTO v09_chapters (id,project_id,user_id,chapter,body,source_fingerprint,analysis_id,reference_ids,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)',('old',pid,next(iter(ai_features.SESSIONS.values()))['user_id'],2,'Old draft',v09.fingerprint(v09.project_owned(pid,next(iter(ai_features.SESSIONS.values()))['user_id'])),None,json.dumps([rid]),'2026-01-01','2026-01-01'))
 assert c.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['status']=='needs_review'


def test_ind_10_resaved_empty_reference_chapter_reports_current_without_cross_validation():
 c=client_owner();did=upload(c);pid=project(c,did)
 r=c.post(f'/api/v09/projects/{pid}/chapters/2/save',json={'body':'Claim: (MissingAuthor, 2025) proves novelty.','reference_ids':[]})
 assert r.status_code==200
 status=c.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['status']
 # This is intentional limited evidence semantics; document human verification risk.
 assert status=='current'

def test_ind_11_independent_three_construct_mediation_ols():
 from app.sem_engine import estimate
 rng=np.random.default_rng(2026)
 x=rng.normal(size=150);m=.55*x+rng.normal(scale=.8,size=150);y=.2*x+.7*m+rng.normal(scale=.7,size=150)
 df=pd.DataFrame({'x':x,'m':m,'y':y})
 nodes=[{'id':c,'label':c.upper(),'indicators':[c]} for c in ['x','m','y']]
 edges=[{'source':'x','target':'m'},{'source':'x','target':'y'},{'source':'m','target':'y'}]
 res=estimate(df,nodes,edges,bootstraps=50,seed=123)
 z=(df-df.mean())/df.std(ddof=1)
 bmx=np.linalg.lstsq(np.column_stack([np.ones(len(z)),z.x]),z.m,rcond=None)[0][1]
 coeffs=np.linalg.lstsq(np.column_stack([np.ones(len(z)),z.x,z.m]),z.y,rcond=None)[0][1:]
 assert abs(res['paths']['X -> M']-bmx)<1e-12
 assert abs(res['paths']['X -> Y']-coeffs[0])<1e-12
 assert abs(res['paths']['M -> Y']-coeffs[1])<1e-12
 assert abs(res['indirect_effects']['X -> M -> Y']['estimate']-bmx*coeffs[1])<1e-12


def test_ind_12_alpha_two_items_independent_formula():
 from app.sem_engine import estimate
 rng=np.random.default_rng(124)
 latent=rng.normal(size=200);x1=latent+rng.normal(scale=.5,size=200);x2=latent+rng.normal(scale=.5,size=200);y=latent+rng.normal(size=200)
 df=pd.DataFrame({'x1':x1,'x2':x2,'y':y})
 nodes=[{'id':'x','label':'X','indicators':['x1','x2'],'measurement':'reflective'},{'id':'y','label':'Y','indicators':['y']}]
 res=estimate(df,nodes,[{'source':'x','target':'y'}],bootstraps=0)
 rho=np.corrcoef(x1,x2)[0,1]
 expected_alpha=2*rho/(1+rho)
 assert abs(res['reliability_validity']['X']['alpha']-expected_alpha)<1e-10


def test_ind_13_duplicate_csv_header_is_rejected_before_pandas():
 c=client_owner()
 r=c.post('/api/datasets',files={'file':('duplicate.csv',b'age,age,target\n1,2,3\n2,3,4\n','text/csv')})
 # Remediation acceptance: no implicit header mangling and no persisted data.
 assert r.status_code==422, r.text
 assert 'Duplicate' in r.text


def test_ind_14_saved_narrative_can_be_current_with_unlinked_in_text_citations():
 c=client_owner();did=upload(c);pid=project(c,did)
 r=c.post(f'/api/v09/projects/{pid}/chapters/2/save',json={'body':'Claim based on fabricated text (Doe, 2024).','reference_ids':[]})
 assert r.status_code==200
 assert c.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['status']=='current'
