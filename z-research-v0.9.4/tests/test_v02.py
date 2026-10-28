"""Offline validation, no real OpenAI calls or API charges."""
from fastapi.testclient import TestClient
from app.main import app
from app import ai_features as ai
from app.prompts import METHODOLOGY, build_prompt


def test_local_auth_prompt_and_visual_model(monkeypatch):
    client=TestClient(app)
    assert client.get('/api/auth/status').status_code==200
    assert client.post('/api/ai/prompt-preview',json={'kind':'methodology','section':'design'}).status_code==401
    signup=client.post('/api/auth/setup',json={'username':'research_owner','password':'secure-local-test-234'})
    assert signup.status_code==200,signup.text
    assert client.get('/api/auth/status').json()['authenticated']
    with open('sample/consumer_survey_demo.csv','rb') as handle:
        uploaded=client.post('/api/datasets',files={'file':('demo.csv',handle,'text/csv')})
    assert uploaded.status_code==200,uploaded.text
    did=uploaded.json()['id']
    assert set(METHODOLOGY)=={'design','population','sampling','collection_period','instrument','ethical_process','analysis_plan'}
    for section in METHODOLOGY:
        p=client.post('/api/ai/prompt-preview',json={'kind':'methodology','section':section,'dataset_id':did,'style':'ieee','research_facts':{'sampling':'not documented'}})
        assert p.status_code==200,p.text
        assert '120' in p.json()['prompt']
        assert 'raw_responses' in p.json()['prompt'] or 'no_raw_responses_shared' in p.json()['prompt']
        assert 'consent' in p.json()['system'].lower()
    assert client.post('/api/ai/generate',json={'kind':'methodology','section':'design','dataset_id':did}).status_code==403
    # Fake a session connection; the external provider is never contacted in the test.
    ai.SESSIONS[client.cookies['qr_session']]['api_key']='test-only-key'
    ai.SESSIONS[client.cookies['qr_session']]['model']='test-model'
    async def mocked_generate(key,model,system,prompt):
        assert '120' in prompt
        assert 'OpenAI' not in key
        return 'A cautious academic draft. Verification needed: sampling documentation.'
    monkeypatch.setattr(ai,'openai_generate',mocked_generate)
    gen=client.post('/api/ai/generate',json={'kind':'methodology','section':'sampling','dataset_id':did})
    assert gen.status_code==200,gen.text
    draft=client.get('/api/ai/drafts/'+gen.json()['draft_id'])
    assert draft.status_code==200
    assert len(client.get('/api/ai/drafts').json())>=1
    model=client.post('/api/models',json={'name':'Research framework','dataset_id':did,'nodes':[{'id':'trust','label':'Brand Trust','type':'latent','indicators':['trust_1','trust_2'],'x':230,'y':160},{'id':'pi','label':'Purchase intention','type':'observed','x':650,'y':160,'indicators':[]}],'edges':[{'source':'trust','target':'pi','label':'H1'}]})
    assert model.status_code==200,model.text
    assert len(client.get('/api/models/'+model.json()['id']).json()['edges'])==1
    invalid=client.post('/api/models',json={'name':'Broken','nodes':[],'edges':[{'source':'x','target':'y'}]})
    assert invalid.status_code==422
    analysis=client.post('/api/analyze/regression',json={'dataset_id':did,'outcome':'purchase_intention','predictors':['trust_1']})
    assert analysis.status_code==200
    result_prompt=client.post('/api/ai/prompt-preview',json={'kind':'results','section':'regression','dataset_id':did,'analysis_id':analysis.json()['analysis_id']})
    assert result_prompt.status_code==200
    assert 'r_squared' in result_prompt.json()['prompt']
    mismatch=client.post('/api/ai/prompt-preview',json={'kind':'results','section':'reliability','dataset_id':did,'analysis_id':analysis.json()['analysis_id']})
    assert mismatch.status_code==422
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/ai/drafts').status_code==401


def test_prompt_unsupported_type():
    try:
        build_prompt('results','plsem',{}, {},'ieee','','')
        assert False
    except ValueError:
        pass
