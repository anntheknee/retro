import json, glob, os, re, collections, sys
root=os.path.expanduser('~/.claude/projects')
PROMPT_MAX=int(sys.argv[1]) if len(sys.argv)>1 else 300
def text_of(c):
    if isinstance(c,str): return c
    return ' '.join(x.get('text','') for x in c if isinstance(x,dict) and x.get('type')=='text')
def digest(path):
    d={'file':os.path.relpath(path,root),'versions':set(),'models':collections.Counter(),'effort':collections.Counter(),
       'tokens':collections.Counter(),'peak_ctx':0,'tools':collections.Counter(),'bash_heads':collections.Counter(),
       'skills_invoked':collections.Counter(),'slash':collections.Counter(),'attrib_skill_out':collections.Counter(),
       'tool_errors':[],'denials':collections.Counter(),'interrupts':0,'compactions':[],'api_errors':0,
       'informational':[],'turns':[],'skills_available':None,'perm_modes':collections.Counter()}
    reqs={}; cur=None; first=last=None
    for line in open(path):
        r=json.loads(line); t=r.get('type'); ts=r.get('timestamp')
        if ts: first=first or ts; last=ts
        if r.get('version'): d['versions'].add(r['version'])
        for k in ('cwd','gitBranch','agentId'):
            if r.get(k) and k not in d: d[k]=r[k]
        if t=='ai-title': d['title']=r['aiTitle']
        elif t=='permission-mode': d['perm_modes'][r['permissionMode']]+=1
        elif t=='cost-state': d['cost_usd']=max(d.get('cost_usd',0),r['totalCostUSD'])
        elif t=='assistant':
            m=r['message']; reqs[r.get('requestId')]=(m.get('model'),m.get('usage',{}),r.get('attributionSkill'))
            d['effort'][str(r.get('effort'))]+=1
            if r.get('isApiErrorMessage'): d['api_errors']+=1
            for c in m.get('content',[]):
                if c.get('type')=='tool_use':
                    n=c['name']; d['tools'][n]+=1
                    if cur: cur['tools'][n]+=1
                    if n=='Skill': d['skills_invoked'][c['input'].get('skill')]+=1
                    if n=='Bash':
                        cmd=c['input'].get('command','').strip().split()
                        if cmd: d['bash_heads'][' '.join(cmd[:2]) if cmd[0] in('git','gh','npm','uv','claude','openspec') else cmd[0]]+=1
        elif t=='user':
            msg=r['message']; c=msg.get('content')
            if r.get('toolDenialKind'): d['denials'][r['toolDenialKind']]+=1
            pdx=r.get('permissionDecision') or {}
            if pdx.get('decision')=='reject' or pdx.get('source','').startswith('user'): d['denials']['pd:%s/%s'%(pdx.get('decision'),pdx.get('source'))]+=1
            if isinstance(c,list):
                for x in c:
                    if isinstance(x,dict) and x.get('type')=='tool_result' and x.get('is_error'):
                        cc=x.get('content'); s=cc if isinstance(cc,str) else json.dumps(cc)
                        d['tool_errors'].append(s[:80])
            s=text_of(c) if c else ''
            if s.startswith('[Request interrupted'): d['interrupts']+=1; cur and cur.__setitem__('interrupted',True); continue
            if r.get('isMeta') or r.get('toolUseResult') is not None or r.get('origin',{}).get('kind','human')!='human' or r.get('isCompactSummary'): continue
            mm=re.search(r'<command-name>/?(.*?)</command-name>',s)
            if mm: d['slash'][mm.group(1)]+=1; continue
            if not s or s.startswith('<'): continue
            cur={'ts':ts,'len':len(s),'prompt':s[:PROMPT_MAX],'tools':collections.Counter()}; d['turns'].append(cur)
        elif t=='system':
            st=r.get('subtype')
            if st=='turn_duration' and cur: cur['ms']=r.get('durationMs')
            elif st=='compact_boundary':
                cm=r.get('compactMetadata',{}); d['compactions'].append({k:cm.get(k) for k in('trigger','preTokens','postTokens')})
            elif st=='informational': d['informational'].append(r.get('content','')[:80])
        elif t=='attachment':
            a=r['attachment']
            if a.get('type')=='skill_listing' and a.get('isInitial'): d['skills_available']=a.get('names')
    for model,u,sk in reqs.values():
        d['models'][model]+=1
        tok={'in':u.get('input_tokens',0),'cache_read':u.get('cache_read_input_tokens',0),'cache_write':u.get('cache_creation_input_tokens',0),
             'out':u.get('output_tokens',0),'thinking':(u.get('output_tokens_details') or {}).get('thinking_tokens',0)}
        d['tokens'].update(tok); d['peak_ctx']=max(d['peak_ctx'],tok['in']+tok['cache_read']+tok['cache_write'])
        if sk: d['attrib_skill_out'][sk]+=tok['out']
    d['start'],d['end']=first,last; d['requests']=len(reqs); d['versions']=sorted(d['versions'])
    ec=collections.Counter(d['tool_errors']); d['tool_errors']=ec.most_common(10)
    d['bash_heads']=dict(d['bash_heads'].most_common(15))
    return d
if __name__=='__main__':
    files=glob.glob(root+'/**/*.jsonl',recursive=True)
    raw=sum(os.path.getsize(f) for f in files)
    ds=[digest(f) for f in files]
    out=json.dumps(ds,default=lambda o: dict(o) if isinstance(o,collections.Counter) else list(o),separators=(',',':'))
    no_prompts=json.dumps([{k:v for k,v in d.items() if k not in('turns','skills_available')}|{'n_turns':len(d['turns'])} for d in ds],default=lambda o: dict(o) if isinstance(o,collections.Counter) else list(o),separators=(',',':'))
    print('files',len(files),'raw bytes',raw,'digest bytes',len(out),'ratio %.4f'%(len(out)/raw),'no-prompt stats only',len(no_prompts))
    print('turns',sum(len(d['turns']) for d in ds),'prompt chars kept',sum(len(t['prompt']) for d in ds for t in d['turns']))
    big=max(ds,key=lambda d:len(json.dumps(d,default=str)))
    print('largest digest',big['file'],len(json.dumps(big,default=str)))
    open(os.path.join(os.path.dirname(__file__),'digest_out.json'),'w').write(out)
