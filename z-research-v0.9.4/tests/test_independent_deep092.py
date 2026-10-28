"""Independent adversarial QA probes; isolated by the project's autouse fixture."""
import io, threading, concurrent.futures, json, re
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import v05, ai_features


def owner():
    c=TestClient(app)
    r=c.post('/api/auth/setup',json={'username':'audit_owner','password':'securepass-2026'})
    assert r.status_code==200, r.text
    return c


def upload(c, data=b'X,Y\n1,2\n3,4\n5,6\n'):
    r=c.post('/api/datasets',files={'file':('d.csv',data)})
    assert r.status_code==200, r.text
    return r.json()['id']


def test_header_normalization_unicode_compatibility():
    c=owner()
    for payload in [b'X,x\n1,2\n', 'A,\xef\xbc\xa1\n1,2\n'.encode('latin1')]:
        r=c.post('/api/datasets',files={'file':('d.csv',payload)})
        assert r.status_code==422, (payload,r.status_code,r.text)


def test_unauthenticated_api_access_denied_and_cross_origin_mutation():
    c=owner(); did=upload(c)
    anon=TestClient(app)
    for route in ['/api/datasets','/api/datasets/'+did,'/api/datasets/'+did+'/provenance','/api/v05/datasets/'+did+'/rows']:
        assert anon.get(route).status_code==401, route
    r=c.post('/api/v05/datasets/'+did+'/edit-cell',json={'row':0,'column':'X','value':99},headers={'Origin':'https://evil.example'})
    assert r.status_code==403
    assert c.get('/api/datasets/'+did).json()['preview'][0]['X']==1


def test_export_linked_citation_docx_consistent_with_saved_source():
    from docx import Document
    c=owner(); did=upload(c)
    pid=c.post('/api/v09/projects',json={'name':'Citation audit','dataset_id':did}).json()['id']
    r1=c.post('/api/v05/references/manual',json={'title':'Alpha','authors':'Doe, Jane','year':2025}).json()['id']
    r2=c.post('/api/v05/references/manual',json={'title':'Beta','authors':'Smith, John','year':2026}).json()['id']
    body=f'First [@ref:{r2}]; second [@ref:{r1}]; first again [@ref:{r2}]. [@bibliography]'
    r=c.post(f'/api/v09/projects/{pid}/chapters/2/save',json={'body':body,'reference_ids':[r1,r2],'style':'ieee'})
    assert r.status_code==200, r.text
    out=c.get(f'/api/v09/projects/{pid}/chapters/2/docx')
    assert out.status_code==200, out.text
    text='\n'.join(p.text for p in Document(io.BytesIO(out.content)).paragraphs)
    assert 'First [1]; second [2]; first again [1]' in text
    assert text.index('[1] J. Smith')<text.index('[2] J. Doe')


def test_two_simultaneous_cell_edits_are_not_both_preserved(monkeypatch):
    """Two clients read same working CSV, then edit different cells concurrently."""
    c=owner(); did=upload(c)
    old=v05.read_df
    gate=threading.Barrier(2)
    def both_read_before_write(dataset_id):
        result=old(dataset_id)
        gate.wait(timeout=10)
        return result
    monkeypatch.setattr(v05,'read_df',both_read_before_write)
    def edit(row,value):
        try:
            return c.post(f'/api/v05/datasets/{did}/edit-cell',json={'row':row,'column':'X','value':value})
        except Exception as ex:
            return ex
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        a=ex.submit(edit,0,111)
        b=ex.submit(edit,1,222)
        results=[a.result(timeout=15),b.result(timeout=15)]
    monkeypatch.setattr(v05,'read_df',old)
    preview=c.get('/api/datasets/'+did).json()['preview']
    both_preserved=(preview[0]['X']==111 and preview[1]['X']==222)
    statuses=[r.status_code if hasattr(r,'status_code') else type(r).__name__ for r in results]
    assert both_preserved, f'LOST UPDATE: statuses={statuses}, values={[preview[0]["X"],preview[1]["X"]]}'

def test_malformed_xlsx_is_handled_as_4xx_not_uncaught_500():
    c=owner()
    r=c.post('/api/datasets',files={'file':('invalid.xlsx',b'not an xlsx file')})
    assert r.status_code in (400,415,422), r.text

def test_python_word_renderer_matches_browser_for_uppercase_and():
    """Browser treats AND case-insensitively; Word renderer must agree."""
    from app.citations import render_document
    r={'id':'ref1','title':'Study','authors':'Smith, John AND Doe, Jane','year':2025,'venue':'Journal'}
    body='[@ref:ref1] [@bibliography]'
    result=render_document(body,'apa',[r])['body']
    assert '(Smith & Doe, 2025)' in result, result

def test_audit_flags_unlinked_author_year_citation_even_without_selected_refs():
    c=owner(); did=upload(c)
    pid=c.post('/api/v09/projects',json={'name':'Plain citation audit','dataset_id':did}).json()['id']
    r=c.post(f'/api/v09/projects/{pid}/chapters/2/save',json={'body':'Prior work (Smith, 2025) reported the relationship.','reference_ids':[],'style':'apa'})
    assert r.status_code==200, r.text
    chapter=c.get(f'/api/v09/projects/{pid}').json()['chapters']['2']
    audit=c.get(f'/api/v09/projects/{pid}/audit').json()
    assert chapter['citation_integrity']=='unverified_plain_text'
    assert any('Chapter 2' in x['message'] and 'citation' in x['message'].lower() for x in audit['alerts']), audit['alerts']
