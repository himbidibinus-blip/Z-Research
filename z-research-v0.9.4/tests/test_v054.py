"""UX/backend contracts for reference idempotency, selected AI citations, local branding."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app import v05
from bs4 import BeautifulSoup


def client():
 c=TestClient(app)
 r=c.post('/api/auth/setup',json={'username':'owner','password':'local-testing-password'})
 assert r.status_code==200,r.text
 return c


def test_repeated_reference_clicks_do_not_duplicate_and_selection_is_scoped():
 c=client()
 record={'title':'Credible Study on Digital Research','year':2025,'authors':'Jane Doe','doi':'10.3344/EXAMPLE','venue':'Journal of Examples'}
 a=c.post('/api/v05/references/manual',json=record)
 b=c.post('/api/v05/references/manual',json=record)
 assert a.status_code==200 and b.status_code==200
 assert a.json()['already_saved'] is False
 assert b.json()['already_saved'] is True
 assert a.json()['id']==b.json()['id']
 # title/year fallback is useful when DOI metadata is missing or differs
 alternate=c.post('/api/v05/references/manual',json={**record,'doi':''})
 assert alternate.json()['already_saved'] is True
 other=c.post('/api/v05/references/manual',json={'title':'Unselected Study','year':2024,'authors':'Smith'})
 assert other.status_code==200
 assert len(c.get('/api/v05/references').json())==2
 selected=c.post('/api/v05/chapters/preview',json={'chapter':2,'reference_ids':[a.json()['id']]})
 assert selected.status_code==200,selected.text
 text=selected.json()['prompt']
 assert 'Credible Study on Digital Research' in text
 assert 'Unselected Study' not in text
 empty=c.post('/api/v05/chapters/preview',json={'chapter':2,'reference_ids':[]})
 assert empty.status_code==200 and 'Credible Study' not in empty.json()['prompt']
 old=c.post('/api/v05/chapters/preview',json={'chapter':2})
 assert old.status_code==200 and 'Unselected Study' in old.json()['prompt']
 invalid=c.post('/api/v05/chapters/preview',json={'chapter':2,'reference_ids':['unknown']})
 assert invalid.status_code==422


def test_logo_upload_accepted_and_exposed_locally(monkeypatch,tmp_path):
 c=client()
 monkeypatch.setattr(v05,'BRANDING_DIR',tmp_path)
 png=b'\x89PNG\r\n\x1a\n'+b'\x00'*100
 r=c.post('/api/v05/branding/logo',files={'file':('original.png',png,'image/png')})
 assert r.status_code==200,r.text
 got=c.get('/api/v05/branding/logo')
 assert got.status_code==200 and got.content==png
 bad=c.post('/api/v05/branding/logo',files={'file':('wrong.svg',b'<svg><script>hi</script></svg>','image/svg+xml')})
 assert bad.status_code==422
 assert c.get('/api/v05/branding/logo').content==png
 too_big=c.post('/api/v05/branding/logo',files={'file':('big.png',png+bytes(2_000_000),'image/png')})
 assert too_big.status_code==413


def test_new_writer_controls_and_links_exist():
 doc=BeautifulSoup(Path('app/static/legacy.html').read_text(),'html.parser')
 ids=[x.get('id') for x in doc.select('[id]')]
 assert len(ids)==len(set(ids))
 for n in range(1,5):
  for suffix in ('RefList','RefFilter','SelectAllRefs','RefCount','Bibliography','Text'):
   assert doc.select_one('#c'+str(n)+suffix)
  assert doc.select_one('#c'+str(n)+'Text').find_parent('div',class_='zr-studio-grid')
 assert doc.select_one('#brandLogoUpload')
 assert doc.select_one('#newsSearchResults').find_parent('div',class_='zr-news-viewport')
 assert 'research_v054.css' in str(doc)


def test_hour_ollama_timeout_in_source():
 src=Path('app/providers.py').read_text()
 assert 'httpx.Timeout(3600.0,connect=12.0)' in src
