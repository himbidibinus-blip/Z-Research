"""Portable, reference-ID anchored citation tokens for plain-text chapter drafts.

This is a deliberately narrow local formatter, NOT a full CSL citation processor.
Tokens are first-class document data; rendered numbers are derived at export/preview.
"""
import re
from dataclasses import dataclass

TOKEN = re.compile(r'\[@ref:([A-Za-z0-9_-]{1,128})\]')
BIBLIO = '[@bibliography]'
LEGACY_NUMERIC = re.compile(r'(?<!\[)\[(\d+(?:\s*[-,]\s*\d+)*)\](?!\])')


def cited_ids(text):
    return list(dict.fromkeys(TOKEN.findall(text or '')))


def validate_linked_sources(text, selected_ids):
    """Reject orphan tokens (e.g. source deselected or fabricated)."""
    refs = set(selected_ids)
    missing = sorted(set(cited_ids(text)) - refs)
    return missing


def _author_people(raw, author_parts=None):
    """Mirror the lightweight frontend parser for common comma-form author fields."""
    if isinstance(author_parts,list) and author_parts:
        return [{'family':str(a.get('family') or '').strip(),
                 'given':str(a.get('given') or '').strip(),
                 'organization':bool(a.get('organization',False))} for a in author_parts if isinstance(a,dict)]
    source = (raw or '').strip()
    if not source:
        return []
    if source.startswith('{') and source.endswith('}'):
        return [{'family':source[1:-1],'given':'','organization':True}]
    names = [n.strip() for n in re.split(r'\s*;\s*|\s+and\s+',source,flags=re.I) if n.strip()]
    if len(names) == 1:
        bits=[x.strip() for x in source.split(',') if x.strip()]
        if len(bits)>=4 and len(bits)%2==0:
            names=[bits[i]+', '+bits[i+1] for i in range(0,len(bits),2)]
        elif len(bits)==2 and all(len(x.split())>=2 for x in bits):
            names=bits
        elif len(bits)>=3:
            names=bits
    names_out=[]
    for n in names:
        if n.startswith('{') and n.endswith('}'):
            names_out.append({'family':n[1:-1],'given':'','organization':True})
            continue
        if ',' in n:
            family,given=n.split(',',1)
        elif n.startswith(('World ','United ','European ','American ','International ')) and n.endswith(('Organization','Association','Institute','Commission','University','Nations','Bank','Council')):
            names_out.append({'family':n,'given':'','organization':True})
            continue
        else:
            words=n.split()
            if len(words)==1:
                family=words[0];given=''
            else:
                family=words.pop()
                while words and words[-1].lower() in ('de','del','da','di','van','von','der','la','le','bin','al'):
                    family=words.pop()+' '+family
                given=' '.join(words)
        names_out.append({'family':family.strip(),'given':given.strip(),'organization':False})
    return names_out


def _initials(given):
    return ' '.join(x[0].upper()+'.' for x in re.split(r'[\s-]+',given) if x)


def cite(ref, style, num):
    if style == 'ieee':
        return f'[{num}]'
    people = [p['family'] for p in _author_people(ref.get('authors'),ref.get('author_parts'))]
    year = ref.get('year') or 'n.d.'
    if not people:
        name = (ref.get('title') or 'Unknown')[:45]
    elif len(people) == 1:
        name = people[0]
    elif len(people) == 2:
        name = f'{people[0]} & {people[1]}'
    else:
        name = people[0] + ' et al.'
    return f'({name}, {year})'


def bibliography(ref, style, num):
    title = ref.get('title') or 'Untitled'
    venue = ref.get('venue') or ''
    year = ref.get('year') or 'n.d.'
    people = _author_people(ref.get('authors'),ref.get('author_parts'))
    if style == 'ieee':
        names = ', '.join(p['family'] if p['organization'] else ' '.join(filter(None,(_initials(p['given']),p['family']))) for p in people) or 'Unknown author'
    else:
        names = ', '.join(p['family'] if p['organization'] else ', '.join(filter(None,(p['family'],_initials(p['given'])))) for p in people) or 'Unknown author'
    doi=str(ref.get('doi') or '')
    link=('https://doi.org/'+re.sub(r'^https?://(?:dx\.)?doi\.org/','',doi,flags=re.I)) if doi else (ref.get('url') or '')
    if style == 'ieee':
        return f'[{num}] {names}, "{title}," {venue}, {year}. {link}'.strip()
    return f'{names} ({year}). {title}. {venue}. {link}'.strip()


def render_document(body, style, refs):
    """Return rendered in-text citations and bibliography in first-mention order.

    Missing references are kept explicit; this never silently changes source IDs.
    """
    keys = cited_ids(body)
    used = {r['id']: dict(r) for r in refs}
    order = {rid: i + 1 for i, rid in enumerate(keys)}
    missing = [rid for rid in keys if rid not in used]
    rendered = TOKEN.sub(lambda match: cite(used[match.group(1)], style, order[match.group(1)]) if match.group(1) in used else '[MISSING SOURCE: '+match.group(1)+']', body)
    lines = [bibliography(used[rid], style, order[rid]) for rid in keys if rid in used]
    bibliotext = '\n'.join(lines)
    if BIBLIO in rendered:
        rendered = rendered.replace(BIBLIO, 'References\n' + bibliotext)
    elif lines:
        rendered = rendered.rstrip() + '\n\nReferences\n' + bibliotext
    return {'body': rendered, 'cited_reference_ids': keys, 'missing_reference_ids': missing,
            'legacy_numeric': bool(LEGACY_NUMERIC.search(TOKEN.sub('', body))),
            'bibliography': bibliotext}
