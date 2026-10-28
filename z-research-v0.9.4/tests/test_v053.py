"""Local Ollama wiring, chapters 1-4, news evidence, Word outputs and UI contract.
No external AI API or live web calls.
"""
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import ai_features,providers


def login():
 c=TestClient(app)
 r=c.post('/api/auth/setup',json={'username':'localowner','password':'local-testing-password'})
 assert r.status_code==200,r.text
 return c


def sample(c):
 p=Path('sample/consumer_survey_demo.csv')
 r=c.post('/api/datasets',files={'file':('survey.csv',p.read_bytes(),'text/csv')})
 assert r.status_code==200,r.text
 return r.json()['id']


def test_local_ollama_no_secret_and_chapter_generation(monkeypatch):
 c=login();did=sample(c)
 calls=[]
 class Mock:
  def __init__(self,*a,**kw):self.kw=kw
  async def __aenter__(self):return self
  async def __aexit__(self,*args):return False
  async def get(self,url,**kwargs):
   calls.append(('GET',url));return httpx.Response(200,json={'models':[{'name':'qwen3:8b'}]},request=httpx.Request('GET',url))
  async def post(self,url,**kwargs):
   calls.append(('POST',url,kwargs))
   assert kwargs['json']['model']=='qwen3:8b'
   assert kwargs['json']['stream'] is False
   assert 'Authorization' not in kwargs['headers']
   return httpx.Response(200,json={'message':{'role':'assistant','content':'# Grounded chapter draft\n[RESEARCHER TO CONFIRM]'}})
 monkeypatch.setattr(providers.httpx,'AsyncClient',Mock)
 res=c.post('/api/ai/connect',json={'provider':'ollama','api_key':'','model':'qwen3:8b'})
 assert res.status_code==200,res.text
 assert c.get('/api/auth/status').json()['provider_connected'] is True
 assert ai_features.SESSIONS[c.cookies['qr_session']]['api_key'] is None
 for n in (1,2,3,4):
  req={'chapter':n,'dataset_id':did,'research_facts':'Survey data provenance not yet confirmed'}
  preview=c.post('/api/v05/chapters/preview',json=req)
  assert preview.status_code==200,preview.text
  assert f'CHAPTER {n}' in preview.json()['prompt']
  generated=c.post('/api/v05/chapters/generate',json=req)
  assert generated.status_code==200,generated.text
  assert generated.json()['body'].startswith('# Grounded')
  cid=generated.json()['id']
  edited=c.put('/api/v05/chapters/'+cid,json={'body':'# Updated chapter\nUpdated text'})
  assert edited.status_code==200
  doc=c.post('/api/v05/chapters/export-word',json={'chapter':n,'body':'# Test Chapter\nText for Word export'})
  assert doc.status_code==200,doc.text
  assert doc.content.startswith(b'PK')
 assert all(x[1].startswith('http://127.0.0.1:11434/') for x in calls)
 assert len(calls)==5
 assert c.post('/api/ai/disconnect').status_code==200
 assert c.get('/api/auth/status').json()['provider_connected'] is False


def test_phenomena_news_and_literature_evidence():
 c=login();did=sample(c)
 sug=c.get('/api/v05/phenomena/suggestions',params={'dataset_id':did})
 assert sug.status_code==200,sug.text
 result=sug.json();assert result['themes']
 assert all('EXPLORATORY_' in t['status'] for t in result['themes'])
 invalid=c.post('/api/v05/news',json={'title':'Source headline','url':'http://insecure.example/story'})
 assert invalid.status_code==422
 added=c.post('/api/v05/news',json={'title':'Published report on e-commerce','url':'https://example.org/story','source':'News Source','published':'2026-09-09'})
 assert added.status_code==200,added.text
 assert c.get('/api/v05/news').json()[0]['title']=='Published report on e-commerce'
 uploaded=c.post('/api/v05/news/upload',files={'file':('article.txt',b'An example article with no confirmed authorship or date.','text/plain')})
 assert uploaded.status_code==200,uploaded.text
 ref=c.post('/api/v05/references/manual',json={'title':'Evidence source','authors':'Researcher','year':2025})
 assert ref.status_code==200,ref.text
 p1=c.post('/api/v05/chapters/preview',json={'chapter':1,'dataset_id':did})
 p2=c.post('/api/v05/chapters/preview',json={'chapter':2,'dataset_id':did})
 assert 'Published report on e-commerce' in p1.json()['prompt']
 assert 'example article' in p1.json()['prompt']
 assert 'Evidence source' in p2.json()['prompt']
 assert 'FULL TEXT REVIEW NEEDED' in p2.json()['prompt']
 saved=c.post('/api/v05/chapters/save-edited',json={'chapter':2,'body':'# Literature\nDrafted by researcher','dataset_id':did})
 assert saved.status_code==200,saved.text
 history=c.get('/api/v05/chapters').json()
 assert history[0]['chapter']==2
 assert c.get('/api/v05/chapters/'+saved.json()['id']).json()['body'].startswith('# Literature')
 assert c.delete('/api/v05/news/'+added.json()['id']).status_code==200
 assert c.get('/api/v05/news').json()==[]


def test_new_navigation_has_unique_ids_and_new_chapter_controls():
 from bs4 import BeautifulSoup
 doc=BeautifulSoup(Path('app/static/legacy.html').read_text(),'html.parser')
 ids=[t['id'] for t in doc.select('[id]')]
 assert len(ids)==len(set(ids))
 menu=[t.get('data-page') for t in doc.select('#nav [data-page]')]
 assert menu==['overview','model','pls','intro','references','literature','methods','results']
 assert 'analysis' not in menu and 'chapters' not in menu
 for i in [1,2,3,4]:
  for postfix in ('Generate','Save','Preview','Word','RefUpload','Guide','Analysis'):
   assert doc.select_one('#c'+str(i)+postfix)
 assert doc.select_one('#page-pls #runStats')
 assert doc.select_one('#page-pls #plsOutput')
 assert doc.select_one('#aiProvider option[value="ollama"]')
