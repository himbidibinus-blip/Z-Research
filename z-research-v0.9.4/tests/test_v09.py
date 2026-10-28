"""Connected project regression tests. All state stays in pytest temporary folders."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


def get_client():
    from app import v09, main
    v09.DATA = main.DATA
    v09.initialize()
    cl = TestClient(app)
    a=cl.post('/api/auth/setup',json={'username':'owner09','password':'long-secure-password-2026'})
    assert a.status_code == 200,a.text
    upload=cl.post('/api/datasets',files={'file':('sample.csv',Path('sample/consumer_survey_demo.csv').read_bytes(),'text/csv')})
    assert upload.status_code==200,upload.text
    did=upload.json()['id']
    project=cl.post('/api/v09/projects',json={'name':'Consumer model study','dataset_id':did})
    assert project.status_code==200,project.text
    return cl,did,project.json()['id']


def build_model(client,pid):
    constructs=client.get(f'/api/v09/projects/{pid}/constructs')
    assert constructs.status_code==200,constructs.text
    keys={g['key'] for g in constructs.json()['groups']}
    assert {'trust','social media','purchase intention'} <= keys
    r=client.post(f'/api/v09/projects/{pid}/auto-model',json={'independent':['social media'],'dependent':'purchase intention','mediators':['trust']})
    assert r.status_code==200,r.text
    return r.json()['model']


def test_v09_ui_scripts_and_legacy_compatibility():
    cl=TestClient(app)
    assert 'studio09.js' in cl.get('/').text
    assert cl.get('/static/studio09.js').status_code==200
    assert cl.get('/static/studio09.css').status_code==200
    assert 'autoIV' in cl.get('/legacy').text
    assert cl.get('/api/health').json()['version']=='0.9.4'


def test_project_autobuilder_analysis_chapters_and_staleness():
    cl,did,pid=get_client()
    model=build_model(cl,pid)
    assert len(model['nodes'])==3
    assert len(model['edges'])==3
    quick=cl.post(f'/api/v09/projects/{pid}/preview')
    assert quick.status_code==200,quick.text
    assert quick.json()['status']=='LIVE_PREVIEW_NO_INFERENCE'
    run=cl.post(f'/api/v09/projects/{pid}/analyze',json={'bootstraps':35,'seed':123})
    assert run.status_code==200,run.text
    result=run.json()['result']
    assert result['bootstrap_seed']==123
    assert 'indicator_descriptives' in result
    assert result['quality_review']['method_status']=='EXPERIMENTAL_NOT_BENCHMARK_VALIDATED'
    assert cl.get(f'/api/v09/projects/{pid}').json()['analysis']['status']=='current'
    p=cl.post(f'/api/v09/projects/{pid}/chapters/4/draft',json={'mode':'preview','research_facts':'Survey with verified approval documents.'})
    assert p.status_code==200,p.text
    assert 'prompt' in p.json()
    chapter=cl.post(f'/api/v09/projects/{pid}/chapters/4/save',json={'body':'The structural model was estimated as an experimental analysis.','reference_ids':[]})
    assert chapter.status_code==200,chapter.text
    assert cl.get(f'/api/v09/projects/{pid}/chapters/4').json()[0]['status']=='current'
    model['edges'][0]['label']='H1 revised'
    mutation=cl.patch(f'/api/v09/projects/{pid}',json={'model':model})
    assert mutation.status_code==200,mutation.text
    assert mutation.json()['analysis']['status']=='stale'
    assert mutation.json()['chapters']['4']['status']=='stale'
    blocked=cl.post(f'/api/v09/projects/{pid}/chapters/4/draft',json={'mode':'preview'})
    assert blocked.status_code==409
    audit=cl.get(f'/api/v09/projects/{pid}/audit')
    assert audit.status_code==200
    assert audit.json()['analysis_status']=='stale'
    reproduce=cl.get(f'/api/v09/projects/{pid}/reproducibility.json')
    assert reproduce.status_code==200
    assert reproduce.json()['analysis_status']=='stale'


def test_evidence_and_duplicate_reference_and_owner_authorization():
    cl,did,pid=get_client()
    model=build_model(cl,pid)
    article={'title':'Digital Media and Purchase Intention','authors':'A. Researcher','year':2025,'doi':'10.0000/unique-research-09'}
    first=cl.post('/api/v05/references/manual',json=article)
    again=cl.post('/api/v05/references/manual',json=article)
    assert first.status_code==again.status_code==200
    assert not first.json()['already_saved']
    assert again.json()['already_saved']
    assert first.json()['id']==again.json()['id']
    assert len(cl.get('/api/v05/references').json())==1
    map_result=cl.get(f'/api/v09/projects/{pid}/evidence')
    assert map_result.status_code==200,map_result.text
    assert len(map_result.json()['research_gap_prompts'])==3
    assert map_result.json()['construct_matrix']
    invalid=cl.patch(f'/api/v09/projects/{pid}',json={'model':{'nodes':model['nodes'],'edges':[{'source':'bogus','target':'v_3'}]}})
    assert invalid.status_code==422
    denied=TestClient(app).get(f'/api/v09/projects/{pid}')
    assert denied.status_code==401


def test_docx_export_creates_valid_office_document():
    """Word exports use the saved draft and contain the correct text."""
    import io
    from docx import Document
    cl, did, pid = get_client()
    draft = '## Research Procedure\nThe dataset was uploaded by the researcher.\nAll statistics need validation.'
    saved = cl.post(f'/api/v09/projects/{pid}/chapters/3/save', json={'body':draft,'reference_ids':[]})
    assert saved.status_code == 200, saved.text
    response = cl.get(f'/api/v09/projects/{pid}/chapters/3/docx')
    assert response.status_code == 200,response.text
    assert response.content[:2] == b'PK'
    doc = Document(io.BytesIO(response.content))
    paragraphs = '\n'.join(x.text for x in doc.paragraphs)
    assert 'Research Procedure' in paragraphs
    assert 'All statistics need validation' in paragraphs
    assert 'independent verification' in paragraphs


def test_dataset_cell_edit_marks_run_stale_without_erasing_results():
    cl,did,pid=get_client()
    build_model(cl,pid)
    run=cl.post(f'/api/v09/projects/{pid}/analyze',json={'bootstraps':15,'seed':42})
    assert run.status_code==200,run.text
    before=cl.get(f'/api/v09/projects/{pid}').json()
    edit=cl.post(f'/api/v05/datasets/{did}/edit-cell',json={'row':0,'column':'trust_1','value':1.0})
    assert edit.status_code==200,edit.text
    after=cl.get(f'/api/v09/projects/{pid}').json()
    assert before['fingerprint']!=after['fingerprint']
    assert after['analysis']['status']=='stale'
    assert cl.get(f'/api/v09/projects/{pid}/analysis').json()['run']['status']=='stale'
    from app import main
    assert (main.DATA/(did+'.original.csv')).exists()


def test_word_export_and_dataset_edit_invalidate_provenance():
    cl,did,pid=get_client()
    build_model(cl,pid)
    run=cl.post(f'/api/v09/projects/{pid}/analyze',json={'bootstraps':0,'seed':42})
    assert run.status_code==200,run.text
    save=cl.post(f'/api/v09/projects/{pid}/chapters/3/save',json={'body':'# Research Methodology\n\nDocumented empirical procedures.', 'reference_ids':[]})
    assert save.status_code==200,save.text
    word=cl.get(f'/api/v09/projects/{pid}/chapters/3/docx')
    assert word.status_code==200,word.text[:200] if word.status_code!=200 else ''
    assert word.content.startswith(b'PK')
    assert 'wordprocessingml.document' in word.headers['content-type']
    changed=cl.post(f'/api/v05/datasets/{did}/edit-cell',json={'row':0,'column':'trust_1','value':4.66})
    assert changed.status_code==200,changed.text
    assert cl.get(f'/api/v09/projects/{pid}').json()['analysis']['status']=='stale'
    assert cl.get(f'/api/v09/projects/{pid}').json()['chapters']['3']['status']=='stale'
    assert cl.post(f'/api/v09/projects/{pid}/chapters/4/draft',json={'mode':'preview'}).status_code==409
