"""v0.5.2: provider-specific routing, moderation and re-estimation, numeric audit editing.
All provider requests are mocked; no API key or user data leaves the test environment.
"""
from fastapi.testclient import TestClient
from app.main import app
from app import ai_features as ai
from app import providers
import numpy as np
import pandas as pd
import httpx


def owner():
    cl=TestClient(app)
    r=cl.post('/api/auth/setup',json={'username':'owner_v052','password':'a-secure-test-password'})
    assert r.status_code==200,r.text
    return cl

def demo(cl):
    from pathlib import Path
    r=cl.post('/api/datasets',files={'file':('sample.csv',Path('sample/consumer_survey_demo.csv').read_bytes())})
    assert r.status_code==200,r.text
    return r.json()['id']

def example_model():
    nodes=[{'id':'x','label':'Social','indicators':['social_media_1','social_media_2','social_media_3'],'measurement':'reflective'},
           {'id':'m','label':'Trust','indicators':['trust_1','trust_2','trust_3'],'measurement':'reflective'},
           {'id':'y','label':'Intent','indicators':['purchase_intention'],'measurement':'reflective'}]
    edges=[{'source':'x','target':'y','label':'H1'},
           {'source':'m','target':'y','label':'H2'},
           {'source':'x','target':'m','label':'H3'},
           {'source':'x','target':'y','moderator':'m','kind':'moderation','label':'H4'}]
    return nodes,edges


def test_live_model_moderation_and_data_edit():
    cl=owner();did=demo(cl);nodes,edges=example_model()
    query={'dataset_id':did,'nodes':nodes,'edges':edges,'bootstraps':40,'seed':17}
    a=cl.post('/api/v05/pls/preview',json=query)
    assert a.status_code==200,a.text
    assert a.json()['analysis_id'] is None
    out=a.json()['result']; assert 'Social × Trust -> Intent' in out['paths']
    assert out['bootstraps_successful']>=30
    original=cl.get('/api/v05/datasets/'+did+'/rows?offset=0&limit=10')
    assert original.status_code==200,original.text
    initial=original.json()['rows'][0]['social_media_1']
    newvalue=1.0 if initial > 3 else 5.0
    e=cl.post(f'/api/v05/datasets/{did}/edit-cell',json={'row':0,'column':'social_media_1','value':newvalue})
    assert e.status_code==200,e.text
    assert cl.get('/api/v05/datasets/'+did+'/rows?offset=0&limit=10').json()['rows'][0]['social_media_1']==newvalue
    b=cl.post('/api/v05/pls/preview',json=query)
    assert b.status_code==200,b.text
    assert b.json()['result']['paths']!=out['paths']
    persisted=cl.post('/api/v05/pls/run',json=query)
    assert persisted.status_code==200,persisted.text
    assert persisted.json()['analysis_id']
    from app.main import DATA
    assert (DATA/(did+'.original.csv')).exists()
    assert pd.read_csv(DATA/(did+'.original.csv')).loc[0,'social_media_1']==initial
    bad=cl.post(f'/api/v05/datasets/{did}/edit-cell',json={'row':0,'column':'nonexistent','value':1})
    assert bad.status_code==422


def test_gemini_connect_and_generation_without_openai(monkeypatch):
    cl=owner();sid=cl.cookies['qr_session'];calls=[]
    class MockClient:
        def __init__(self,*a,**kw):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):return False
        async def get(self,url,**kw):
            calls.append(('GET',url,kw))
            assert 'generativelanguage.googleapis.com' in url
            assert kw['headers']['x-goog-api-key']=='gemini-test-secret-key'
            return httpx.Response(200,json={'models':[]})
        async def post(self,url,**kw):
            calls.append(('POST',url,kw))
            assert 'generativelanguage.googleapis.com' in url
            assert kw['json']['contents'][0]['role']=='user'
            assert 'systemInstruction' in kw['json']
            return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'Verified cautious research draft.'}]}}]})
    monkeypatch.setattr(providers.httpx,'AsyncClient',MockClient)
    r=cl.post('/api/ai/connect',json={'provider':'gemini','api_key':'gemini-test-secret-key','model':'gemini-2.5-flash'})
    assert r.status_code==200,r.text
    assert r.json()['provider']=='gemini'
    assert ai.SESSIONS[sid]['provider']=='gemini'
    assert cl.get('/api/auth/status').json()['provider_label']=='Google Gemini'
    draft=cl.post('/api/ai/generate',json={'kind':'methodology','section':'design','research_facts':{'design':'Not reported'}})
    assert draft.status_code==200,draft.text
    assert draft.json()['text']=='Verified cautious research draft.'
    assert [x[0] for x in calls]==['GET','POST']
    assert all('api.openai.com' not in x[1] for x in calls)
    # Credentials must not be exposed by the login status endpoint.
    assert 'gemini-test-secret-key' not in str(cl.get('/api/auth/status').json())


def test_claude_and_openai_compatible_formats(monkeypatch):
    calls=[]
    class MockClient:
        def __init__(self,*a,**k):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def post(self,url,**kwargs):
            calls.append((url,kwargs))
            if 'anthropic.com' in url:return httpx.Response(200,json={'content':[{'type':'text','text':'Claude draft'}]})
            return httpx.Response(200,json={'choices':[{'message':{'content':'OpenRouter draft'}}]})
    monkeypatch.setattr(providers.httpx,'AsyncClient',MockClient)
    import asyncio
    assert asyncio.run(providers.generate_text('anthropic','sk-demo','claude-sonnet-4-5','System','Research prompt'))=='Claude draft'
    assert asyncio.run(providers.generate_text('openrouter','sk-demo','openai/gpt-4o-mini','System','Research prompt'))=='OpenRouter draft'
    assert calls[0][1]['json']['messages'][0]['role']=='user'
    assert calls[1][1]['json']['messages'][0]['role']=='system'
    try:providers.endpoint_for('custom','http://localhost:9999/v1')
    except Exception:pass
    else:assert False,'Local HTTP endpoint unexpectedly allowed'


def test_ui_has_builder_and_provider_controls():
    cl=TestClient(app)
    r=cl.get('/legacy')
    for expected in ('id="autoIV"','id="autoDV"','id="autoMediator"','id="autoModerator"','id="hypothesisEditor"','id="numericEditor"','id="aiProvider"','/static/auto.js'):
        assert expected in r.text
    assert cl.get('/static/auto.js').status_code==200
    provider_list=cl.get('/api/ai/providers')
    assert provider_list.status_code==200
    assert {'openai','gemini','anthropic','openrouter','groq','custom'} <= set(provider_list.json())
