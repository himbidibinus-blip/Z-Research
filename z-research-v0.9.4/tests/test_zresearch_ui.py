"""Branding, UI assets and upload flow for the Z-Research personal MVP."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


def test_branding_assets_and_api():
    client=TestClient(app)
    html=client.get('/legacy')
    assert html.status_code==200
    assert '<title>Z-Research' in html.text
    assert 'Z-Research' in html.text
    assert 'id="loadSampleBtn"' in html.text
    for name in ['style.css','app.js','v05.js','zresearch.css','zresearch.js','sample_survey.csv']:
        assert client.get('/static/'+name).status_code==200,name
    assert client.get('/api/health').json()['status']=='ok'


def test_sample_upload_and_statistics():
    client=TestClient(app)
    assert client.post('/api/auth/setup',json={'username':'qa_ui','password':'strong-test-password-002'}).status_code==200
    response=client.post('/api/datasets',files={'file':('Z_Research_Demo_Survey.csv',Path('sample/consumer_survey_demo.csv').read_bytes(),'text/csv')})
    assert response.status_code==200,response.text
    data=response.json()
    assert data['rows']==120
    preview=client.get('/api/datasets/'+data['id'])
    assert preview.status_code==200
    assert 'social_media_1' in preview.json()['columns']
    result=client.post('/api/analyze/descriptive',json={'dataset_id':data['id'],'columns':['social_media_1','trust_1']})
    assert result.status_code==200,result.text
