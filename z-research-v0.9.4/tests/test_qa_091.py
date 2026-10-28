"""QA gate replay of ZR-QA-001..007, isolated fixture provided by conftest.
No real API keys, external services, or installed Ollama required.
"""
import hashlib
import io
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app import ai_features, main, v09

SAMPLE=Path('sample/consumer_survey_demo.csv').read_bytes()

def owner():
    client=TestClient(app)
    res=client.post('/api/auth/setup',json={'username':'qa_owner_091','password':'strong-qa-091-password'})
    assert res.status_code==200, res.text
    return client

def uploaded(client, content=SAMPLE, name='original.csv'):
    res=client.post('/api/datasets', files={'file':(name,content,'text/csv')})
    assert res.status_code==200, res.text
    return res.json()['id']

def project(client,did):
    res=client.post('/api/v09/projects',json={'name':'QA integrity project','dataset_id':did})
    assert res.status_code==200,res.text
    return res.json()['id']

def reference(client, title='Smith study', authors='Smith, John', doi='10.0000/qa-smith'):
    res=client.post('/api/v05/references/manual',json={'title':title,'authors':authors,'year':2025,'doi':doi})
    assert res.status_code==200,res.text
    return res.json()['id']


def test_qa_001_legacy_data_and_analysis_need_owner_session():
    anon=TestClient(app)
    assert anon.get('/api/datasets').status_code==401
    assert anon.post('/api/datasets',files={'file':('private.csv',SAMPLE,'text/csv')}).status_code==401
    assert anon.post('/api/analyze/descriptive',json={'dataset_id':'any','columns':['x']}).status_code==401
    assert anon.post('/api/analyze/regression',json={'dataset_id':'any','outcome':'y','predictors':['x']}).status_code==401
    assert anon.post('/api/analyze/reliability',json={'dataset_id':'any','indicators':['x','y']}).status_code==401
    cl=owner();did=uploaded(cl)
    assert anon.get('/api/datasets/'+did).status_code==401
    assert anon.get('/api/datasets/'+did+'/provenance').status_code==401
    assert anon.get('/api/analyses/unknown').status_code==401
    assert anon.get('/api/analyses/unknown/export').status_code==401
    assert anon.get('/api/v05/analyses').status_code==401
    bad_origin={'Origin':'https://external.example'}
    assert cl.post('/api/datasets',headers=bad_origin,files={'file':('evil.csv',SAMPLE,'text/csv')}).status_code==403
    assert cl.post('/api/analyze/descriptive',headers=bad_origin,json={'dataset_id':did,'columns':['trust_1']}).status_code==403
    assert cl.post('/api/analyze/descriptive',headers={'Sec-Fetch-Site':'cross-site'},json={'dataset_id':did,'columns':['trust_1']}).status_code==403
    assert cl.get('/api/datasets/'+did).status_code==200
    assert cl.post('/api/analyze/descriptive',json={'dataset_id':did,'columns':['trust_1']}).status_code==200


def test_qa_002_reference_removal_invalidates_chapter_and_audit():
    cl=owner();did=uploaded(cl);pid=project(cl,did);rid=reference(cl)
    res=cl.post(f'/api/v09/projects/{pid}/chapters/2/save',json={'body':'A cited result (Smith, 2025).','reference_ids':[rid]})
    assert res.status_code==200,res.text
    assert cl.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['status']=='current'
    assert cl.delete('/api/v05/references/'+rid).status_code==200
    project_details=cl.get(f'/api/v09/projects/{pid}').json()
    assert project_details['chapters']['2']['status']=='broken_citation'
    revisions=cl.get(f'/api/v09/projects/{pid}/chapters/2').json()
    assert revisions[0]['status']=='broken_citation'
    assert rid in revisions[0]['broken_reference_ids']
    audit=cl.get(f'/api/v09/projects/{pid}/audit').json()
    assert audit['draft_status']['2']=='broken_citation'
    assert any('broken_citation' in a['message'] for a in audit['alerts'])
    assert cl.get(f'/api/v09/projects/{pid}/reproducibility.json').json()['chapter_status']['2']=='broken_citation'
    exported=cl.get(f'/api/v09/projects/{pid}/chapters/2/docx')
    assert exported.status_code==200
    from docx import Document
    paragraphs='\n'.join(p.text for p in Document(io.BytesIO(exported.content)).paragraphs)
    assert 'INTEGRITY WARNING' in paragraphs


def test_qa_003_reject_missing_foreign_and_duplicate_reference_ids():
    cl=owner();did=uploaded(cl);pid=project(cl,did);rid=reference(cl)
    url=f'/api/v09/projects/{pid}/chapters/2/save'
    for selection in [['fictional'],[rid,rid],[rid,'fictional']]:
        r=cl.post(url,json={'body':'Test paragraph','reference_ids':selection})
        assert r.status_code==422,(selection,r.text)
        d=cl.post(f'/api/v09/projects/{pid}/chapters/2/draft',json={'mode':'preview','reference_ids':selection})
        assert d.status_code==422,(selection,d.text)
    assert cl.get(f'/api/v09/projects/{pid}/chapters/2').json()==[]
    okay=cl.post(url,json={'body':'Test paragraph','reference_ids':[rid]})
    assert okay.status_code==200,okay.text


def test_qa_006_byte_identical_originals_checksum_and_edit_separation():
    cl=owner()
    content=b'trust_1,trust_2\r\n1,2\r\n2,3\r\n3,4\r\n'
    did=uploaded(cl,content,'survey-special.csv')
    meta=cl.get('/api/datasets/'+did+'/provenance').json()
    assert meta['archive_status']=='VERIFIED'
    assert meta['sha256']==hashlib.sha256(content).hexdigest()
    assert meta['byte_size']==len(content)
    archive=main.DATA/'raw_uploads'/(did+'.csv')
    assert archive.read_bytes()==content
    working=main.DATA/(did+'.csv')
    assert working.read_bytes()!=content
    edit=cl.post(f'/api/v05/datasets/{did}/edit-cell',json={'row':0,'column':'trust_1','value':4.0})
    assert edit.status_code==200,edit.text
    assert archive.read_bytes()==content
    assert cl.get('/api/datasets/'+did+'/provenance').json()['archive_status']=='VERIFIED'


def test_old_chapters_without_evidence_are_needs_review():
    cl=owner();did=uploaded(cl);pid=project(cl,did);rid=reference(cl)
    # Simulate legacy v0.9 record imported before v0.9.1 evidence migrations.
    with ai_features.db() as db:
        db.execute('INSERT INTO v09_chapters (id,project_id,user_id,chapter,body,source_fingerprint,analysis_id,reference_ids,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
                   ('legacy',pid,next(iter(ai_features.SESSIONS.values()))['user_id'],2,'Legacy paragraph',v09.fingerprint(v09.project_owned(pid,next(iter(ai_features.SESSIONS.values()))['user_id'])),None,json.dumps([rid]),'2026-10-19','2026-10-19'))
    assert cl.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['status']=='needs_review'


def test_reference_metadata_change_invalidates_snapshot():
    cl=owner();did=uploaded(cl);pid=project(cl,did);rid=reference(cl)
    assert cl.post(f'/api/v09/projects/{pid}/chapters/2/save',json={'body':'Draft','reference_ids':[rid]}).status_code==200
    with ai_features.db() as db:db.execute('UPDATE research_references SET title=? WHERE id=?',('Different bibliographic title',rid))
    assert cl.get(f'/api/v09/projects/{pid}').json()['chapters']['2']['status']=='stale'
