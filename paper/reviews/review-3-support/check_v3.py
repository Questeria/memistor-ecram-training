"""Independent saved-record audit; no project code is imported or executed."""
from pathlib import Path
import collections, hashlib, itertools, json, math, statistics as st

P=Path(r'paper')
OUT=Path(__file__).parent
R=P/'records/revision'
rep=json.loads((P/'records/revision2/RESULTS-REV2.json').read_text())
old=json.loads((OUT.parent/'paper-review-v2/raw-record-manifest.json').read_text())
audit={'old_records_checked':len(old),'old_records_changed':[], 'errors':[], 'fidelity':{}, 'fixedsp':{}, 'probes':[]}
manifest={}
for f,h in old.items():
    if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=h:audit['old_records_changed'].append(f)
raw={}
for ph in ('e3','e4','e5','fid','e5fix','fidprobe','fidprobe-probes'):
    raw[ph]=[]
    for f in sorted((R/'runs'/ph).glob('*.json')):
        b=f.read_bytes();manifest[str(f)]=hashlib.sha256(b).hexdigest()
        z=json.loads(b);z['_file']=str(f);raw[ph].append(z)
audit['counts']={k:len(v) for k,v in raw.items()}

def metric(r):return r['metric'].get('acc',r['metric'].get('bpb'))
def gap(a,b):return 100*(metric(b)/metric(a)-1) if a['task']=='lm' else 100*(metric(a)-metric(b))
def ci(xs):
    n=len(xs);m=st.mean(xs);sd=st.stdev(xs);h={3:4.303,5:2.776}[n]*sd/math.sqrt(n)
    return dict(n=n,mean=m,sd=sd,lo=m-h,hi=m+h)
def lab(t,c):
    lim=5 if t=='lm' else 2
    return 'PASS' if c['hi']<=lim else 'FAIL' if c['lo']>lim else 'UNRESOLVED'
def group(rs,key):
    d=collections.defaultdict(list)
    for r in rs:d[key(r)].append(r)
    return d
def check_num(tag,a,b):
    if abs(a-b)>1e-10:audit['errors'].append([tag,a,b])
def check_ci(tag,a,b):
    for k in ('mean','lo','hi','sd','n'):check_num(tag+' '+k,a[k],b[k])

fp={(r['task'],r['seed']):r for r in raw['e3'] if r['arm']=='fp_sgd' and r['algo']=='sgd'}
sur={(r['task'],r['spec']['name'],r['algo'],r['seed']):r for r in raw['e3'] if r['arm']=='device'}
audit['matched_new_records']=0
for r in raw['fid']+raw['e5fix']+raw['fidprobe']:
    base=fp[(r['task'],r['seed'])]
    if any(r[k]!=base[k] for k in ('init_sha256','data_sha256')):audit['errors'].append(['unmatched init/data',r['_file']])
    else:audit['matched_new_records']+=1
for key,rs in group(raw['fid'],lambda r:(r['task'],r['spec']['name'],r['algo'])).items():
    t,d,a=key;rs.sort(key=lambda r:r['seed']);nm='__'.join(key)
    gs=[];gq=[]
    for r in rs:
        s=r['seed'];b=sur[(t,d,a,s)]
        for k in ('budget','lr','spec','ucfg','width','init_sha256','data_sha256'):
            if r[k]!=b[k]:audit['errors'].append(['fid config mismatch',nm,s,k])
        if r['pulse_mode']!='seq' or r['seq_layers']!=('all' if t=='mnist' else '3,4'):audit['errors'].append(['wrong routing',nm])
        gs.append(gap(fp[t,s],b));gq.append(gap(fp[t,s],r))
    dg=[b-a for a,b in zip(gs,gq)];c=ci(dg)
    row=dict(gap_sur=ci(gs),gap_seq=ci(gq),diff=c,material=abs(c['mean'])>1,
             label_sur=lab(t,ci(gs)),label_seq=lab(t,ci(gq)),gaps_sur=gs,gaps_seq=gq)
    audit['fidelity'][nm]=row
    want=rep['fid']['cells'][nm]
    check_ci(nm,c,want['dgap_ci'])
    check_num(nm+' sur',st.mean(gs),want['gap_sur_mean']);check_num(nm+' seq',st.mean(gq),want['gap_seq_mean'])
audit['ranking_swaps']=[]
for t in ('mnist','cifar'):
    cells=[(k,v) for k,v in audit['fidelity'].items() if k.startswith(t+'__')]
    for (a,x),(b,y) in itertools.combinations(cells,2):
        s=x['gap_sur']['mean']-y['gap_sur']['mean'];q=x['gap_seq']['mean']-y['gap_seq']['mean']
        if s*q<0:audit['ranking_swaps'].append(dict(a=a,b=b,sur_separation=s,seq_separation=q,registered_material=abs(s)>1))
audit['label_changes']={k:{'sur':v['label_sur'],'seq':v['label_seq']} for k,v in audit['fidelity'].items() if v['label_sur']!=v['label_seq']}

e5base={(r['task'],r['algo'],r['seed']):r for r in raw['e5'] if r['spec']['name']=='base'}
for (t,a,nm),rs in group(raw['e5fix'],lambda r:(r['task'],r['algo'],r['spec']['name'])).items():
    xs=[gap(fp[t,r['seed']],r) for r in sorted(rs,key=lambda r:r['seed'])];c=ci(xs)
    if not all(r['spec']['recenter_sp'] for r in rs):audit['errors'].append(['fixedsp not recentred',t,a,nm])
    key='__'.join((t,a,nm));audit['fixedsp'][key]=dict(gap=c,label=lab(t,c),gaps=xs)
    if nm=='asym_fixedsp0.05':
        ds=[gap(fp[t,r['seed']],r)-gap(fp[t,r['seed']],e5base[t,a,r['seed']]) for r in rs]
        audit['fixedsp'][key]['recentred_minus_unrecentred']=ci(ds)

for file in raw['fidprobe-probes']:
    run=next(r for r in raw['fidprobe'] if Path(r['_file']).name==file['run'])
    for p in file['probes']:
        q=dict(task=run['task'],layer=p['layer'],update=p['update'],draws=p['draws'],lost_frac=p['lost_frac'])
        for nm,gl,el,vl,vh in [('surrogate',.10,.10,.5,2),('seq',.05,.05,.8,1.25)]:
            v=p[nm];g=v['gain_req']/p['slot']['gain_req']-1;e=math.sqrt(max(0,v['vs_slot_rel_mean_err']**2-v['vs_slot_noise_floor']**2));vr=v['vs_slot_var_ratio_median']
            passed=abs(g)<=gl and e<=el and vl<=vr<=vh
            q[nm]=dict(gain_difference=g,raw_mean_difference=v['vs_slot_rel_mean_err'],noise_floor=v['vs_slot_noise_floor'],excess=e,variance_ratio=vr,passes=passed)
            want=next(x for x in rep['probes'] if x['task']==q['task'] and x['layer']==q['layer'] and x['update']==q['update'])[nm]
            for k,value in [('gain_ratio_minus1',g),('excess',e),('var_ratio',vr)]:check_num(str(q)[:40]+nm+k,value,want[k])
            if passed!=want['passes']:audit['errors'].append(['probe label mismatch',q])
        audit['probes'].append(q)

res=json.loads((R/'RESULTS-REVISION.json').read_text())
for key,v in audit['fixedsp'].items():
    t,a,nm=key.split('__');value=float(nm.removeprefix('asym_fixedsp'))
    ax=res['e5'][a+'__'+t]['axes']['asym_fixedsp']
    want=next(z for k,z in ax['points'].items() if float(k)==value)
    check_ci(key,v['gap'],want['gap'])
    if v['label']!=want['label']:audit['errors'].append(['fixedsp label',key])
audit['paired_width']={}
e4={(r['task'],r['width'],r['spec']['name']+'__'+r['algo'] if r['arm']=='device' else 'fp',r['seed']):r for r in raw['e4']}
for t,task in res['e4'].items():
    w0,w1=task['widths'][0],task['widths'][-1]
    for arm,cell in task['arms'].items():
        ds=[gap(e4[t,w1,'fp',s],e4[t,w1,arm,s])-gap(e4[t,w0,'fp',s],e4[t,w0,arm,s]) for s in range(5)]
        m=st.mean(ds);h=2.132*st.stdev(ds)/math.sqrt(5);c=[m-h,m+h]
        check_num(t+arm+' D',m,cell['paired']['D'])
        for i in (0,1):check_num(t+arm+str(i),c[i],cell['paired']['ci90'][i])
        audit['paired_width'][t+'__'+arm]=dict(D=m,ci90=c)

# Explicit counterexample to the independent sampling-floor formula on paired draws.
# Reference mean 1, shared noise alternating -1,+1, comparison adds fixed bias .2.
x=[0.,2.]*8;y=[v+.2 for v in x];d=[b-a for a,b in zip(x,y)]
rawerr=abs(st.mean(y)-st.mean(x))/abs(st.mean(x))
indfloor=math.sqrt((st.variance(x)+st.variance(y))/len(x))/abs(st.mean(x))
pairedfloor=math.sqrt(st.variance(d)/len(d))/abs(st.mean(x))
audit['paired_floor_counterexample']=dict(rawerr=rawerr,independent_floor=indfloor,paired_floor=pairedfloor,
    reported_excess=math.sqrt(max(0,rawerr**2-indfloor**2)),paired_excess=math.sqrt(max(0,rawerr**2-pairedfloor**2)))
# Exact Bernoulli shared-line covariance with p_x=p_d=.5 and balanced update signs.
rho=(.5*.5*.5*(1-.5))/(.25*(1-.25))
audit['correlation_counterexample']=dict(cells=128,p=.5,absolute_pairwise_correlation=rho,signed_mean=-rho/127,
    unequal_sd_perfect_correlation_normalized_covariance=2*100/(100**2+1))

(OUT/'new-record-manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'record-audit-v3.json').write_text(json.dumps(audit,indent=2))
print(json.dumps({k:v for k,v in audit.items() if k not in ('fidelity','probes','fixedsp')},indent=2))
print('FIDELITY')
for k,v in audit['fidelity'].items():print(k,v['gap_sur'],v['label_sur'],'=>',v['gap_seq'],v['label_seq'])
print('FIXEDSP')
for k,v in audit['fixedsp'].items():print(k,v)
