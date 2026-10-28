from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_local_pipeline():
    signup=client.post('/api/auth/setup',json={'username':'qa_api','password':'strong-test-password-001'})
    assert signup.status_code==200,signup.text
    assert client.get('/api/health').json()['status']=='ok'
    with open('sample/consumer_survey_demo.csv','rb') as f:
        resp=client.post('/api/datasets',files={'file':('demo.csv',f,'text/csv')})
    assert resp.status_code==200,resp.text
    data=resp.json();did=data['id'];assert data['rows']==120
    desc=client.post('/api/analyze/descriptive',json={'dataset_id':did,'columns':['age','trust_1']})
    assert desc.status_code==200,desc.text
    assert len(desc.json()['result']['statistics'])==2
    reg=client.post('/api/analyze/regression',json={'dataset_id':did,'outcome':'purchase_intention','predictors':['trust_1','social_media_1']})
    assert reg.status_code==200,reg.text
    assert len(reg.json()['result']['coefficients'])==3
    reliability=client.post('/api/analyze/reliability',json={'dataset_id':did,'indicators':['trust_1','trust_2','trust_3']})
    assert reliability.status_code==200,reliability.text
    report=client.post('/api/reports/methodology',json={'dataset_id':did,'design':'cross-sectional survey','population':'students','sampling':'convenience sampling','collection_period':'May 2026','instrument':'Likert survey','ethical_process':'informed consent was collected','analysis_plan':'OLS'})
    assert report.status_code==200,report.text
    assert '120 rows' in report.json()['result']['draft']
    aid=reg.json()['analysis_id']
    assert client.get('/api/analyses/'+aid+'/export').status_code==200
