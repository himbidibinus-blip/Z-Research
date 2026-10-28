"""Provider adapters for researcher-supplied AI keys. No secret is persisted or logged.

Provider REST APIs are different: a valid secret is not proof a selected model is available.
Custom endpoint uses the OpenAI-compatible chat-completions contract, not arbitrary APIs.
"""
from __future__ import annotations
import ipaddress
import re
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException

CATALOG = {
    'ollama': {'label': 'Ollama (local, no key)', 'default_model': 'qwen3:8b'},
    'openai': {'label': 'OpenAI', 'default_model': 'gpt-5-mini'},
    'gemini': {'label': 'Google Gemini', 'default_model': 'gemini-2.5-flash'},
    'anthropic': {'label': 'Anthropic Claude', 'default_model': 'claude-sonnet-4-5'},
    'openrouter': {'label': 'OpenRouter', 'default_model': 'openai/gpt-4o-mini'},
    'groq': {'label': 'Groq', 'default_model': 'llama-3.3-70b-versatile'},
    'deepseek': {'label': 'DeepSeek', 'default_model': 'deepseek-chat'},
    'mistral': {'label': 'Mistral', 'default_model': 'mistral-small-latest'},
    'together': {'label': 'Together AI', 'default_model': 'meta-llama/Llama-3.3-70B-Instruct-Turbo'},
    'custom': {'label': 'Custom OpenAI-compatible endpoint', 'default_model': 'your-model-id'},
}
COMPAT_URLS = {
    'openrouter': 'https://openrouter.ai/api/v1',
    'groq': 'https://api.groq.com/openai/v1',
    'deepseek': 'https://api.deepseek.com/v1',
    'mistral': 'https://api.mistral.ai/v1',
    'together': 'https://api.together.xyz/v1',
}

def endpoint_for(provider, custom_url=''):
    if provider in COMPAT_URLS: return COMPAT_URLS[provider]
    if provider != 'custom': return ''
    url = custom_url.strip().rstrip('/')
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise HTTPException(422, 'Custom provider requires an HTTPS base URL, without user info, query or fragment')
    host = parsed.hostname.lower()
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_global: raise HTTPException(422, 'Private/local IP addresses are not allowed as custom AI endpoints')
    except ValueError:
        if host in ('localhost',) or host.endswith(('.localhost', '.local', '.internal')) or '.' not in host:
            raise HTTPException(422, 'Custom endpoint needs a public HTTPS hostname')
    if parsed.port not in (None, 443): raise HTTPException(422, 'Custom endpoint must use HTTPS on port 443')
    return url

def err_message(response, provider):
    """Return short provider diagnostic without leaking credentials, prompts or payloads."""
    code = response.status_code
    reason = {400: 'Bad request/model ID', 401: 'Invalid API key', 402: 'Billing required', 403: 'Forbidden/key permissions', 404: 'Model or endpoint unavailable', 429: 'Quota/rate limit'}.get(code, 'Provider request failed')
    return f'{provider} API: HTTP {code} ({reason}). Check provider key, model access and quota.'

async def verify_key(provider, api_key, custom_url='', model=''):
    if provider not in CATALOG: raise HTTPException(422, 'Unsupported provider')
    base = endpoint_for(provider, custom_url)
    # A custom OpenAI-compatible endpoint need not implement GET /models.
    if provider == 'ollama':
        try:
            async with httpx.AsyncClient(timeout=6, trust_env=False) as client:
                r=await client.get('http://127.0.0.1:11434/api/tags')
                r.raise_for_status()
                installed=[x.get('name','') for x in r.json().get('models',[])]
                if model and model not in installed:
                    raise HTTPException(422,f'Model {model} not installed in Ollama. Run: ollama pull {model}')
                return {'verified':True,'notice':'Ollama local server and selected model verified. No secret key needed.'}
        except httpx.HTTPError as ex:
            raise HTTPException(502,'Ollama is not reachable on 127.0.0.1:11434. Open Ollama and run ollama list.') from ex
    if provider == 'custom':
        return {'verified': False, 'notice': 'Custom endpoint saved for this session. Key/model cannot be verified without a generation call.'}
    if provider == 'gemini':
        url = 'https://generativelanguage.googleapis.com/v1beta/models'
        headers = {'x-goog-api-key': api_key}
    elif provider == 'anthropic':
        url = 'https://api.anthropic.com/v1/models'
        headers = {'x-api-key': api_key, 'anthropic-version': '2023-06-01'}
    elif provider == 'openai':
        url = 'https://api.openai.com/v1/models'
        headers = {'Authorization': 'Bearer '+api_key}
    elif provider == 'openrouter':
        # Unlike /models, /key is authenticated and checks the provided credential.
        url = 'https://openrouter.ai/api/v1/key'
        headers = {'Authorization': 'Bearer '+api_key}
    else:
        url = base+'/models'
        headers = {'Authorization': 'Bearer '+api_key}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            r = await client.get(url, headers=headers)
    except httpx.HTTPError as e:
        raise HTTPException(502, f'Cannot contact {provider} API. Check connection.') from e
    if r.status_code >= 400: raise HTTPException(400, err_message(r,provider))
    return {'verified': True, 'notice': 'Provider accepted API credential; model selection verified only during generation.'}

async def generate_text(provider, api_key, model, system, prompt, max_tokens=1800, custom_url=''):
    if provider not in CATALOG: raise HTTPException(422, 'Choose a supported provider')
    if provider == 'ollama':
        # Hard-coded loopback only: never expose a generic local-network fetch endpoint.
        if not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,120}',model):raise HTTPException(422,'Invalid local model name')
        url='http://127.0.0.1:11434/api/chat'
        headers={}
        payload={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'stream':False,'think':False,'options':{'num_predict':max_tokens}}
    elif provider == 'openai':
        url='https://api.openai.com/v1/responses'
        headers={'Authorization': 'Bearer '+api_key}
        payload={'model':model, 'instructions':system, 'input':prompt, 'store':False, 'max_output_tokens':max_tokens}
    elif provider == 'gemini':
        # Gemini is not an OpenAI-compatible endpoint; use its native generateContent schema.
        if not re.fullmatch(r'[\w.\-]+', model): raise HTTPException(422, 'Invalid Gemini model ID')
        url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        headers={'x-goog-api-key': api_key}
        payload={'systemInstruction': {'parts': [{'text':system}]}, 'contents':[{'role':'user','parts':[{'text':prompt}]}], 'generationConfig':{'maxOutputTokens':max_tokens}}
    elif provider == 'anthropic':
        url='https://api.anthropic.com/v1/messages'
        headers={'x-api-key':api_key,'anthropic-version':'2023-06-01'}
        payload={'model':model,'system':system,'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens}
    else:
        url=endpoint_for(provider,custom_url)+'/chat/completions'
        headers={'Authorization':'Bearer '+api_key}
        payload={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'max_tokens':max_tokens,'stream':False}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3600.0,connect=12.0) if provider=='ollama' else 180,follow_redirects=False,trust_env=False if provider=='ollama' else True) as client:
            r=await client.post(url,headers=headers,json=payload)
    except httpx.HTTPError as e:
        raise HTTPException(502,f'{provider} API unavailable or timed out') from e
    if r.status_code>=400: raise HTTPException(502,err_message(r,provider))
    try:
        data=r.json()
        if provider=='ollama':
            content=data.get('message',{}).get('content','')
        elif provider=='openai':
            chunks=[p.get('text','') for item in data.get('output',[]) if item.get('type')=='message' for p in item.get('content',[]) if p.get('type')=='output_text']
            content='\n'.join(chunks)
        elif provider=='gemini':
            content='\n'.join(p.get('text','') for candidate in data.get('candidates',[]) for p in candidate.get('content',{}).get('parts',[]) if 'text' in p)
        elif provider=='anthropic':
            content='\n'.join(p.get('text','') for p in data.get('content',[]) if p.get('type')=='text')
        else:
            chunks=[c.get('message',{}).get('content','') for c in data.get('choices',[])]
            content='\n'.join(x if isinstance(x,str) else '' for x in chunks)
    except (ValueError,KeyError,TypeError,AttributeError) as e:
        raise HTTPException(502,f'Unexpected response format from {provider}; verify endpoint compatibility') from e
    content=content.strip()
    if not content: raise HTTPException(502,f'{provider} returned no text; check model, completion limit or safety filters')
    return content
