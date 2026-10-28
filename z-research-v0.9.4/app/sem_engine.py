"""Experimental transparent PLS path modelling (reflective Mode A; formative Mode B).
Algorithm: standardized manifest variables; centroid inner weights; iterative outer weights;
OLS structural paths; nonparametric bootstrap. Not certified as SmartPLS-equivalent.
"""
import numpy as np
import pandas as pd
from scipy import stats

class SEMError(ValueError): pass

def corr(x,y):
    a=np.asarray(x,dtype=float); b=np.asarray(y,dtype=float)
    if np.std(a)<1e-10 or np.std(b)<1e-10:return 0.
    return float(np.corrcoef(a,b)[0,1])

def ols(y,x):
    if x.shape[1]==0:return np.array([]),0.,np.zeros(len(y))
    X=np.column_stack([np.ones(len(y)),x]); params=np.linalg.lstsq(X,y,rcond=None)[0]
    pred=X@params; den=np.sum((y-y.mean())**2)
    r2=1-float(np.sum((y-pred)**2)/den) if den>1e-10 else 0.
    return params[1:],r2,pred

def validate_model(df,nodes,edges):
    if len(nodes)<2 or len(nodes)>24:raise SEMError('Model requires 2–24 constructs')
    ids=[str(n.get('id','')) for n in nodes]
    if len(set(ids))!=len(ids) or '' in ids:raise SEMError('Construct IDs must be unique')
    labels=[str(n.get('label','')).strip() for n in nodes]
    if len(set(labels))!=len(labels) or '' in labels:raise SEMError('Construct names must be unique')
    mapping=dict(zip(ids,labels)); modes={}
    seen=[]
    for n in nodes:
        l=n['label']; cols=n.get('indicators',[])
        if not cols or len(set(cols))!=len(cols):raise SEMError(f'{l}: supply unique indicators')
        if any(c not in df.columns for c in cols):raise SEMError(f'{l}: one or more indicators do not exist in dataset')
        seen.extend(cols)
        m=n.get('measurement','reflective')
        if m not in ('reflective','formative'):raise SEMError(f'{l}: measurement must be reflective or formative')
        if m=='formative' and len(cols)<2:raise SEMError(f'{l}: formative construct requires at least 2 indicators')
        modes[l]=m
    if len(set(seen))!=len(seen):raise SEMError('Indicators may belong to only one construct in this estimator')
    adj={k:[] for k in labels}; pred={k:[] for k in labels}; structural=[]; moderations=[]; explicitly_defined=set()
    for e in edges:
        a=mapping.get(e.get('source'));b=mapping.get(e.get('target'))
        if not a or not b or a==b:raise SEMError('Path uses an unknown construct or a self-link')
        if e.get('kind')=='moderation':
            m=mapping.get(e.get('moderator'))
            if not m or m in (a,b):raise SEMError('Moderation requires three distinct constructs')
            if (a,m,b) in moderations:raise SEMError('Duplicate moderated path')
            moderations.append((a,m,b))
            # The two-stage interaction is estimated alongside main effects.
            for parent in (a,m):
                if b not in adj[parent]:adj[parent].append(b);pred[b].append(parent);structural.append((parent,b))
            continue
        if (a,b) in explicitly_defined:raise SEMError('Duplicate structural path')
        explicitly_defined.add((a,b))
        if b not in adj[a]:adj[a].append(b);pred[b].append(a);structural.append((a,b))
    if not structural:raise SEMError('At least one structural path is required')
    # Topological order enforces a recursive SEM.
    temp=set(); done=set()
    def walk(k):
        if k in temp:raise SEMError('Cycles are not supported in structural paths')
        if k in done:return
        temp.add(k)
        for v in adj[k]:walk(v)
        temp.remove(k);done.add(k)
    for k in labels:walk(k)
    return labels,modes,pred,structural,moderations

def complete_data(df,nodes):
    cols=list(dict.fromkeys(c for n in nodes for c in n['indicators']))
    d=df[cols].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan).dropna()
    if len(d)<30:raise SEMError('At least 30 complete observations are required for this prototype estimator')
    if d.shape[1]>len(d)-2:raise SEMError('Too many indicators relative to observations')
    if any(float(d[c].std(ddof=1))<1e-10 for c in cols):raise SEMError('An indicator has no variance')
    return d,cols

def fit_pls(d,nodes,edges,max_iter=300,tol=1e-7):
    labels,modes,pred,structural,moderations=validate_model(d,nodes,edges)
    n=len(d)
    standardized={c:((d[c].to_numpy(dtype=float)-d[c].mean())/d[c].std(ddof=1)) for c in d.columns}
    x={node['label']:np.column_stack([standardized[c] for c in node['indicators']]) for node in nodes}
    weights={l:np.ones(x[l].shape[1])/np.sqrt(x[l].shape[1]) for l in labels}
    neighbor={l:set() for l in labels}
    for a,b in structural:neighbor[a].add(b);neighbor[b].add(a)
    converged=False; iters=0
    for step in range(max_iter):
        scores={l:x[l]@weights[l] for l in labels}
        scores={l:v/(np.std(v,ddof=1)+1e-20) for l,v in scores.items()}
        new={}
        for l in labels:
            z=np.zeros(n)
            for oth in neighbor[l]:
                s=corr(scores[l],scores[oth]);z+=np.sign(s)*scores[oth] if abs(s)>1e-12 else scores[oth]
            if np.std(z)<1e-10:z=scores[l]
            if modes[l]=='formative':
                w=np.linalg.lstsq(x[l],z,rcond=None)[0]
            else:
                w=x[l].T@z/n
            if np.linalg.norm(w)<1e-10:raise SEMError(f'{l}: outer weighting failed; indicators might be collinear')
            w=w/np.linalg.norm(w)
            if np.dot(w,weights[l])<0:w=-w
            new[l]=w
        delta=max(np.linalg.norm(new[l]-weights[l]) for l in labels)
        weights=new; iters=step+1
        if delta<tol:converged=True;break
    scores={l:x[l]@weights[l] for l in labels}
    scores={l:(v-v.mean())/v.std(ddof=1) for l,v in scores.items()}
    paths={};r2={};f2={};resid={}
    for target,parents in pred.items():
        interactions=[(a,m) for a,m,b in moderations if b==target]
        if not parents and not interactions:continue
        terms=list(parents)
        arrays=[scores[p] for p in parents]
        for a,m in interactions:
            # Experimental two-stage approximation: standardized latent-score product.
            interaction=scores[a]*scores[m]
            interaction=(interaction-interaction.mean())/(interaction.std(ddof=1)+1e-20)
            if np.std(interaction)<1e-10:raise SEMError('Interaction term has no variance')
            arrays.append(interaction);terms.append(f'{a} × {m}')
        y=scores[target];X=np.column_stack(arrays)
        if np.linalg.matrix_rank(np.column_stack([np.ones(len(y)),X]))<X.shape[1]+1:
            raise SEMError(f'{target}: structural predictors are perfectly collinear')
        b,R,prediction=ols(y,X)
        r2[target]=R;resid[target]=np.asarray(y-prediction)
        for i,a in enumerate(terms):
            paths[f'{a} -> {target}']=float(b[i])
            if len(terms)>1:
                _,r_red,_=ols(y,np.delete(X,i,axis=1))
            else:r_red=0.
            f2[f'{a} -> {target}']=float((R-r_red)/(1-R)) if R<.999999 else None
    outer=[]; validity={};formative={}
    for node in nodes:
        l=node['label']; inds=node['indicators'];loads=[corr(standardized[c],scores[l]) for c in inds]
        outer.extend({'construct':l,'indicator':c,'loading':float(v),'weight':float(w),'measurement':modes[l]} for c,v,w in zip(inds,loads,weights[l]))
        if modes[l]=='reflective':
            av=float(np.mean(np.array(loads)**2)); su=sum(loads)
            cr=float(su**2/(su**2+sum(1-v*v for v in loads))) if len(loads)>1 else None
            if len(inds)>1:
                mat=x[l];total=np.var(mat.sum(axis=1),ddof=1)
                alpha=float(len(inds)/(len(inds)-1)*(1-np.var(mat,axis=0,ddof=1).sum()/total)) if total>1e-10 else None
            else:alpha=None
            validity[l]={'alpha':alpha,'composite_reliability':cr,'ave':av,'single_item':len(inds)==1}
        else:
            if len(inds)>1:
                cm=np.corrcoef(x[l],rowvar=False)
                vif=[]
                for j in range(len(inds)):
                    rest=np.delete(x[l],j,axis=1);_,rr,_=ols(x[l][:,j],rest)
                    vif.append(float(1/(1-rr)) if rr<.999999 else None)
                formative[l]={'indicator_vif':dict(zip(inds,vif)),'note':'Formative weights are algorithmic estimates; assess their significance by bootstrap.'}
    # HTMT: mean absolute cross-construct correlation / geometric mean monotrait corr.
    htmt={};fl={}
    cross_loadings=[{'indicator':row['indicator'],'own_construct':row['construct'],**{f'loading_on_{l}':corr(standardized[row['indicator']],scores[l]) for l in labels}} for row in outer]
    inner_vif={}
    for target,parents in pred.items():
        if len(parents)<2:continue
        X=np.column_stack([scores[p] for p in parents])
        for j,par in enumerate(parents):
            _,rr,_=ols(X[:,j],np.delete(X,j,axis=1))
            inner_vif[f'{par} -> {target}']=float(1/(1-rr)) if rr<.999999 else None
    reflective=[n['label'] for n in nodes if modes[n['label']]=='reflective']
    for i,a in enumerate(reflective):
        for b in reflective[i+1:]:
            fl[f'{a} | {b}']={'correlation':corr(scores[a],scores[b]),'sqrt_ave_a':float(np.sqrt(validity[a]['ave'])),'sqrt_ave_b':float(np.sqrt(validity[b]['ave']))}
            xa=x[a];xb=x[b]
            if xa.shape[1]<2 or xb.shape[1]<2:continue
            across=np.abs(np.corrcoef(xa.T,xb.T)[:xa.shape[1],xa.shape[1]:]).mean()
            ma=np.abs(np.corrcoef(xa,rowvar=False)[np.triu_indices(xa.shape[1],1)]).mean()
            mb=np.abs(np.corrcoef(xb,rowvar=False)[np.triu_indices(xb.shape[1],1)]).mean()
            htmt[f'{a} | {b}']=float(across/np.sqrt(ma*mb)) if ma*mb>1e-14 else None
    # Composite-based in-sample Q2-like score not offered: true blindfolding isn't implemented.
    return {'n':n,'converged':converged,'iterations':iters,'paths':paths,'r_squared':r2,'f_squared':f2,'outer_model':outer,'reliability_validity':validity,'formative_diagnostics':formative,'htmt':htmt,'fornell_larcker':fl,'cross_loadings':cross_loadings,'inner_vif':inner_vif,'scores':scores}

def estimate(df,nodes,edges,bootstraps=200,seed=42):
    labels,modes,pred,structural,moderations=validate_model(df,nodes,edges)
    clean,cols=complete_data(df,nodes)
    base=fit_pls(clean,nodes,edges)
    if not base['converged']:raise SEMError('PLS algorithm did not converge; revise measurement specification')
    requested=int(bootstraps)
    if requested<0 or requested>2000:raise SEMError('Bootstrap count must be between 0 and 2000')
    rng=np.random.default_rng(seed); boots={k:[] for k in base['paths']}; outer_boot={f"{r['construct']}:{r['indicator']}":[] for r in base['outer_model']}
    # indirect effects for all two-hop edges.
    indirect={}
    for a,b in structural:
        for bb,c in structural:
            if b==bb and a!=c:indirect[f'{a} -> {b} -> {c}']=[]
    failed=0
    for _ in range(requested):
        inds=rng.integers(0,len(clean),len(clean));sample=clean.iloc[inds].reset_index(drop=True)
        try:
            f=fit_pls(sample,nodes,edges,max_iter=250)
            if not f['converged']:failed+=1;continue
            for k,v in f['paths'].items():boots[k].append(v)
            for row in f['outer_model']:outer_boot[f"{row['construct']}:{row['indicator']}"].append(row['weight'])
            for k in indirect:
                a,b,c=k.split(' -> ');indirect[k].append(f['paths'][f'{a} -> {b}']*f['paths'][f'{b} -> {c}'])
        except (SEMError,ValueError,np.linalg.LinAlgError,ZeroDivisionError):failed+=1
    bootstrap={};formative_boot={};indirect_results={}
    def details(value,arr):
        if len(arr)<30:return {'estimate':float(value),'samples':len(arr),'ci95':None,'bootstrap_se':None,'p_approx':None}
        a=np.asarray(arr,dtype=float);se=a.std(ddof=1); ci=np.quantile(a,[.025,.975]);t=abs(value/se) if se>1e-12 else None
        p=2*stats.norm.sf(t) if t is not None else None
        return {'estimate':float(value),'samples':len(arr),'bootstrap_se':float(se),'t_approx':t,'p_approx':float(p) if p is not None else None,'ci95':[float(v) for v in ci],'supported_at_5pct':bool(ci[0]*ci[1]>0)}
    for k,v in base['paths'].items():bootstrap[k]=details(v,boots[k])
    for row in base['outer_model']:
        if row['measurement']=='formative':
            key=f"{row['construct']}:{row['indicator']}";formative_boot[key]=details(row['weight'],outer_boot[key])
    for k,v in indirect.items():
        a,b,c=k.split(' -> ');val=base['paths'][f'{a} -> {b}']*base['paths'][f'{b} -> {c}']
        indirect_results[k]=details(val,v)
    # Hypothesis labels are researcher-editable metadata; numerical values always come from fit_pls.
    by_id={n['id']:n['label'] for n in nodes}
    hypothesis_summary=[]
    for i,e in enumerate(edges):
        src=by_id.get(e.get('source'),'');dst=by_id.get(e.get('target'),'')
        if e.get('kind')=='moderation':
            md=by_id.get(e.get('moderator'),'');path=f'{src} × {md} -> {dst}'
        else:path=f'{src} -> {dst}'
        result=bootstrap.get(path,{})
        hypothesis_summary.append({'hypothesis':e.get('label') or 'H'+str(i+1),'kind':e.get('kind') or 'direct','path':path,'estimate':base['paths'].get(path),'ci95':result.get('ci95'),'p_approx':result.get('p_approx'),'supported_at_5pct':result.get('supported_at_5pct')})
    base['hypotheses']=hypothesis_summary
    # no respondent-level score arrays leave API
    base.pop('scores')
    base.update({'raw_rows':len(df),'excluded_rows':len(df)-len(clean),'bootstrap':bootstrap,'formative_bootstrap':formative_boot,'indirect_effects':indirect_results,'moderation_method':'Two-stage standardized latent-score interaction (experimental)' if moderations else None,'bootstraps_requested':requested,'bootstraps_successful':requested-failed,'bootstrap_seed':seed,'method':'Experimental centroid inner weighting PLS path modelling, reflective Mode A / formative Mode B, OLS structural equations; complete-case deletion; percentile nonparametric bootstrap. Not independently validated against SmartPLS/cSEM.','limitations':['Bootstrap p-values use normal approximations; percentile confidence intervals are preferred.','Moderation is a two-stage latent-score product approximation; results require benchmarking against established PLS-SEM implementations.','No PLSc consistent correction, rho_A, HTMT bootstrap CI, blindfolding, PLSpredict, MICOM, MGA, higher-order constructs, SRMR, or nonlinear latent interactions.','Results are experimental and must be cross-validated against established PLS-SEM software before publication.']})
    return base
