"""Local owner login, ephemeral OpenAI connection, audited AI drafts and research model editor.

Not a hosted multi-tenant authentication implementation. All writes remain bound to localhost.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional
import httpx
from fastapi import APIRouter, Cookie, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from .prompts import SYSTEM, METHODOLOGY, RESULTS, STYLE, build_prompt
from .providers import CATALOG, endpoint_for, verify_key, generate_text

ROOT = Path(__file__).resolve().parents[1]
DBPATH = ROOT / 'local_data' / 'quantresearch.db'
router = APIRouter(prefix='/api')
SESSIONS = {}  # sid -> {'user_id', 'api_key', 'model', 'expires'}; never persisted
SESSION_SECONDS = 8 * 3600

def db():
    c=sqlite3.connect(DBPATH)
    c.row_factory=sqlite3.Row
    return c

def setup_db():
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS local_users (id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS ai_drafts (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, dataset_id TEXT, analysis_id TEXT, category TEXT NOT NULL, section TEXT NOT NULL, style TEXT NOT NULL, model TEXT NOT NULL, prompt TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS research_models (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, dataset_id TEXT, name TEXT NOT NULL, model_json TEXT NOT NULL, updated_at TEXT NOT NULL)')
setup_db()

def pwd_hash(passwd, salt):
    return hashlib.pbkdf2_hmac('sha256',passwd.encode(),bytes.fromhex(salt),350_000).hex()

def now(): return datetime.now(timezone.utc).isoformat()

def get_session(sid):
    session=SESSIONS.get(sid or '')
    if not session: raise HTTPException(401,'Please log in to Z-Research first')
    if time.time()>session['expires']:
        SESSIONS.pop(sid,None)
        raise HTTPException(401,'Session expired; please log in again')
    return session

def local_only(request:Request):
    if request.url.hostname not in ('127.0.0.1','localhost','testserver','::1'):
        raise HTTPException(403,'Invalid local host name')
    if request.client and request.client.host not in ('127.0.0.1','::1','testclient'):
        raise HTTPException(403,'Local prototype only: access from the local computer')
    origin=request.headers.get('origin','')
    port=request.url.port or 80
    allowed={'http://127.0.0.1:'+str(port),'http://localhost:'+str(port),'http://testserver'}
    if origin and origin not in allowed:
        raise HTTPException(403,'Cross-site requests are not allowed')
    if request.method.upper() not in ('GET','HEAD','OPTIONS'):
        if request.headers.get('sec-fetch-site','').lower() == 'cross-site':
            raise HTTPException(403,'Cross-site mutations are not allowed')

def auth(request:Request, session_id:Optional[str]):
    local_only(request)
    return get_session(session_id)

class AccountRequest(BaseModel):
    username:str=Field(min_length=3,max_length=60,pattern=r'^[a-zA-Z0-9_.@-]+$')
    password:str=Field(min_length=10,max_length=200)

@router.get('/auth/status')
def auth_status(session_id:Optional[str]=Cookie(None,alias='qr_session')):
    with db() as c: count=c.execute('SELECT COUNT(*) FROM local_users').fetchone()[0]
    session=SESSIONS.get(session_id or '')
    return {'configured':count>0,'authenticated':bool(session and session['expires']>time.time()),'provider_connected':bool(session and (session.get('api_key') or session.get('provider')=='ollama')),'model':session.get('model','gpt-5-mini') if session else None,'provider':session.get('provider','openai') if session else None,'provider_label':CATALOG.get(session.get('provider','openai') if session else 'openai',{}).get('label','AI')}

@router.post('/auth/setup')
def create_owner(req:AccountRequest,response:Response,request:Request):
    local_only(request)
    salt=os.urandom(16).hex()
    with db() as c:
        if c.execute('SELECT COUNT(*) FROM local_users').fetchone()[0]:raise HTTPException(409,'Owner already configured; log in')
        uid=uuid.uuid4().hex
        c.execute('INSERT INTO local_users VALUES (?,?,?,?,?)',(uid,req.username,salt,pwd_hash(req.password,salt),now()))
    sid=secrets.token_urlsafe(32)
    SESSIONS[sid]={'user_id':uid,'api_key':None,'provider':'openai','base_url':'','model':'gpt-5-mini','expires':time.time()+SESSION_SECONDS}
    response.set_cookie('qr_session',sid,httponly=True,samesite='strict',max_age=SESSION_SECONDS,path='/')
    return {'ok':True,'username':req.username}

@router.post('/auth/login')
def login(req:AccountRequest,response:Response,request:Request):
    local_only(request)
    with db() as c: u=c.execute('SELECT * FROM local_users WHERE username=?',(req.username,)).fetchone()
    if not u or not hmac.compare_digest(pwd_hash(req.password,u['salt']),u['password_hash']):
        raise HTTPException(401,'Invalid username or password')
    sid=secrets.token_urlsafe(32)
    SESSIONS[sid]={'user_id':u['id'],'api_key':None,'provider':'openai','base_url':'','model':'gpt-5-mini','expires':time.time()+SESSION_SECONDS}
    response.set_cookie('qr_session',sid,httponly=True,samesite='strict',max_age=SESSION_SECONDS,path='/')
    return {'ok':True,'username':req.username}

@router.post('/auth/logout')
def logout(response:Response,request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    local_only(request)
    SESSIONS.pop(session_id or '',None)
    response.delete_cookie('qr_session',path='/')
    return {'ok':True}

class ConnectRequest(BaseModel):
    provider:str=Field(default='openai',max_length=30)
    api_key:str=Field(default='',max_length=1500)
    model:str=Field(default='gpt-5-mini',min_length=2,max_length=200)
    base_url:str=Field(default='',max_length=500)

@router.get('/ai/providers')
def list_providers():
    return CATALOG

@router.post('/ai/connect')
async def connect_ai(req:ConnectRequest,request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    session=auth(request,session_id)
    if req.provider not in CATALOG:raise HTTPException(422,'Unsupported provider')
    if req.provider!='ollama' and len(req.api_key)<8:raise HTTPException(422,'API key required for cloud providers')
    if any(x in req.api_key for x in ('\n','\r',' ')):raise HTTPException(422,'Malformed API key')
    endpoint_for(req.provider,req.base_url)  # validate before request
    status=await verify_key(req.provider,req.api_key,req.base_url,req.model)
    session.update({'api_key':None if req.provider=='ollama' else req.api_key,'provider':req.provider,'base_url':req.base_url.strip().rstrip('/'),'model':req.model})
    return {'connected':True,'provider':req.provider,'model':req.model,'verified_key':status['verified'],'notice':status['notice'],'secret_storage':'RAM only; reconnect after server restart'}

@router.post('/ai/disconnect')
def disconnect(request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    s=auth(request,session_id)
    s['api_key']=None
    s['provider']='openai'
    s['base_url']=''
    return {'connected':False}

@router.get('/ai/templates')
def templates(request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    auth(request,session_id)
    return {'methodology':{k:{'label':v[0],'guidance':v[1]} for k,v in METHODOLOGY.items()},'results':RESULTS,'styles':STYLE}

class DraftRequest(BaseModel):
    kind:Literal['methodology','results']
    section:str=Field(min_length=3,max_length=35)
    dataset_id:Optional[str]=None
    analysis_id:Optional[str]=None
    research_facts:dict[str,str]=Field(default_factory=dict)
    style:Literal['ieee','apa','generic','custom']='ieee'
    custom_style:str=Field(default='',max_length=6000)
    user_prompt:str=Field(default='',max_length=6000)
    language:Literal['English','Indonesian']='English'
    @field_validator('research_facts')
    @classmethod
    def bound_facts(cls,v):
        if len(v)>30 or any(len(str(k))>80 or len(str(a))>4000 for k,a in v.items()): raise ValueError('Research facts too large')
        return v


def build_context(req):
    context={}
    if req.dataset_id:
        with db() as c: d=c.execute('SELECT * FROM datasets WHERE id=?',(req.dataset_id,)).fetchone()
        if not d: raise HTTPException(404,'Dataset not found')
        context['dataset']={'name':d['name'],'row_count':d['rows'],'columns':json.loads(d['columns_json']),'note':'Row count is not verified participant count'}
        import pandas as pd
        data_file=ROOT / 'local_data' / (req.dataset_id+'.csv')
        if data_file.exists():
            df=pd.read_csv(data_file)
            context['dataset']['missing_by_variable']={str(k):int(v) for k,v in df.isna().sum().items()}
            context['dataset']['numeric_variables']=[str(col) for col in df.select_dtypes(include='number').columns]
            context['dataset']['no_raw_responses_shared']=True
    if req.kind=='results':
        if not req.analysis_id: raise HTTPException(422,'Select an actual completed analysis to draft results')
        with db() as c: a=c.execute('SELECT * FROM analyses WHERE id=?',(req.analysis_id,)).fetchone()
        if not a: raise HTTPException(404,'Analysis not found')
        if a['analysis_type'] != req.section: raise HTTPException(422,'Analysis type and selected results section do not match')
        if req.dataset_id and a['dataset_id']!=req.dataset_id:raise HTTPException(422,'Analysis and dataset do not match')
        context['computed_analysis']={'type':a['analysis_type'],'configuration':json.loads(a['configuration']),'results':json.loads(a['result']),'analysis_id':a['id']}
    return context

@router.post('/ai/prompt-preview')
def prompt_preview(req:DraftRequest,request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    auth(request,session_id)
    context=build_context(req)
    try:p=build_prompt(req.kind,req.section,context,req.research_facts,req.style,req.custom_style,req.user_prompt)
    except ValueError as e:raise HTTPException(422,str(e))
    return {'system':SYSTEM,'prompt':p+'\nLANGUAGE: '+req.language,'warning':'Preview only; no external API call and no generated text'}

async def openai_generate(api_key,model,system,user_prompt,max_tokens=1800):
    """Compatibility wrapper used by earlier add-ons; new code uses generate_text."""
    return await generate_text('openai',api_key,model,system,user_prompt,max_tokens)

@router.post('/ai/generate')
async def generate(req:DraftRequest,request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    session=auth(request,session_id)
    if not (session.get('api_key') or session.get('provider')=='ollama'):raise HTTPException(403,'Connect Ollama or an AI provider in Settings first')
    context=build_context(req)
    try:prompt=build_prompt(req.kind,req.section,context,req.research_facts,req.style,req.custom_style,req.user_prompt)
    except ValueError as e:raise HTTPException(422,str(e))
    prompt += '\nLANGUAGE: '+req.language
    text=(await openai_generate(session['api_key'],session['model'],SYSTEM,prompt) if session.get('provider','openai')=='openai' else await generate_text(session['provider'],session['api_key'],session['model'],SYSTEM,prompt,custom_url=session.get('base_url','')))
    draft_id=uuid.uuid4().hex
    with db() as c:
        c.execute('INSERT INTO ai_drafts VALUES (?,?,?,?,?,?,?,?,?,?,?)',(draft_id,session['user_id'],req.dataset_id,req.analysis_id,req.kind,req.section,req.style,session['model'],prompt,text,now()))
    return {'draft_id':draft_id,'text':text,'style':req.style,'model':session['model'],'disclaimer':'AI-generated writing draft; verify claims, calculations and journal compliance before submission.'}

@router.get('/ai/drafts')
def list_drafts(request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    s=auth(request,session_id)
    with db() as c: rows=c.execute('SELECT id,category,section,style,model,created_at,substr(content,1,180) AS excerpt FROM ai_drafts WHERE user_id=? ORDER BY created_at DESC LIMIT 50',(s['user_id'],)).fetchall()
    return [dict(r) for r in rows]

class ResearchModel(BaseModel):
    dataset_id:Optional[str]=None
    name:str=Field(default='Untitled Research Model',min_length=1,max_length=120)
    nodes:list[dict]=Field(default_factory=list,max_length=60)
    edges:list[dict]=Field(default_factory=list,max_length=120)
    @field_validator('nodes','edges')
    @classmethod
    def restrict_payload(cls,items):
        if len(json.dumps(items))>50000:raise ValueError('Model too large')
        return items

@router.post('/models')
def save_model(req:ResearchModel,request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    s=auth(request,session_id)
    ids=[n.get('id') for n in req.nodes]
    if not all(isinstance(x,str) and 0<len(x)<80 for x in ids) or len(set(ids))!=len(ids):raise HTTPException(422,'Unique nonempty node IDs required')
    for n in req.nodes:
        if not isinstance(n.get('label'),str) or len(n['label'])>100:raise HTTPException(422,'Invalid node label')
        if n.get('type') not in ('latent','observed'):raise HTTPException(422,'Invalid node type')
        if not all(isinstance(n.get(d),(int,float)) and -5000<=n[d]<=5000 for d in ('x','y')):raise HTTPException(422,'Invalid node position')
        if not isinstance(n.get('indicators',[]),list) or len(n.get('indicators',[]))>30:raise HTTPException(422,'Invalid indicators')
    for e in req.edges:
        if e.get('source') not in ids or e.get('target') not in ids or e.get('source')==e.get('target'):raise HTTPException(422,'Invalid structural edge')
    if req.dataset_id:
        with db() as c:
            if not c.execute('SELECT 1 FROM datasets WHERE id=?',(req.dataset_id,)).fetchone():raise HTTPException(404,'Dataset not found')
    mid=uuid.uuid4().hex
    with db() as c:c.execute('INSERT INTO research_models VALUES (?,?,?,?,?,?)',(mid,s['user_id'],req.dataset_id,req.name,json.dumps({'nodes':req.nodes,'edges':req.edges}),now()))
    return {'id':mid,'name':req.name}

@router.get('/models')
def list_models(request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    s=auth(request,session_id)
    with db() as c:rs=c.execute('SELECT id,name,dataset_id,updated_at FROM research_models WHERE user_id=? ORDER BY updated_at DESC LIMIT 50',(s['user_id'],)).fetchall()
    return [dict(r) for r in rs]

@router.get('/models/{model_id}')
def get_model(model_id:str,request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    s=auth(request,session_id)
    with db() as c:r=c.execute('SELECT * FROM research_models WHERE id=? AND user_id=?',(model_id,s['user_id'])).fetchone()
    if not r:raise HTTPException(404,'Model not found')
    return {'id':r['id'],'name':r['name'],'dataset_id':r['dataset_id'],**json.loads(r['model_json'])}

@router.get('/ai/analyses')
def available_analyses(request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    auth(request,session_id)
    with db() as c: r=c.execute('SELECT id,dataset_id,analysis_type,created_at FROM analyses WHERE analysis_type IN ("descriptive","regression","reliability","methodology") ORDER BY created_at DESC LIMIT 70').fetchall()
    return [dict(x) for x in r]

@router.get('/ai/drafts/{draft_id}')
def get_draft(draft_id:str,request:Request,session_id:Optional[str]=Cookie(None,alias='qr_session')):
    s=auth(request,session_id)
    with db() as c:r=c.execute('SELECT id,category,section,style,model,content,created_at FROM ai_drafts WHERE id=? AND user_id=?',(draft_id,s['user_id'])).fetchone()
    if not r: raise HTTPException(404,'Draft not found')
    return dict(r)
