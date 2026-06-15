#!/usr/bin/env python3
"""Convert a ComfyUI litegraph UI workflow → API prompt, queue it, return outputs.
Reusable for drift rebuilds. Usage: ui2api_render.py <ui.json> [overrides_json]"""
import json, sys, urllib.request, time, uuid
COMFY="http://localhost:8188"
OBJ=json.load(urllib.request.urlopen(f"{COMFY}/object_info", timeout=60))


def combo_opts(ctype, field):
    spec=OBJ.get(ctype,{}).get("input",{})
    for sect in ("required","optional"):
        if field in spec.get(sect,{}):
            v=spec[sect][field][0]
            if isinstance(v,list): return v
            if isinstance(v,str) and v=="COMBO":
                cfg=spec[sect][field][1] if len(spec[sect][field])>1 else {}
                return cfg.get("options",[])
    return None
def fix_combo(ctype, field, val):
    opts=combo_opts(ctype, field)
    if opts and val not in opts:
        m=[o for o in opts if o.endswith("/"+str(val)) or o.endswith(str(val))]
        if m: return m[0]
    return val
def prune(prompt, keep):
    seen=set(); stack=[str(keep)]
    while stack:
        nid=stack.pop()
        if nid in seen or nid not in prompt: continue
        seen.add(nid)
        for v in prompt[nid]["inputs"].values():
            if isinstance(v,list) and len(v)==2 and isinstance(v[0],str): stack.append(v[0])
    return {k:v for k,v in prompt.items() if k in seen}

def input_order(ctype):
    spec=OBJ.get(ctype,{}).get("input",{})
    return list(spec.get("required",{}).keys())+list(spec.get("optional",{}).keys())

def convert(ui):
    nodes={n["id"]:n for n in ui["nodes"]}
    links={l[0]:(l[1],l[2]) for l in ui.get("links",[])}   # link_id -> (from_node, from_slot)
    prompt={}
    for nid,n in nodes.items():
        ctype=n["type"]
        if ctype in ("Note","MarkdownNote","Reroute"): continue
        if ctype not in OBJ: continue
        inputs={}
        linkslots={i["name"]:i.get("link") for i in n.get("inputs",[])}
        wv=n.get("widgets_values")
        is_dict=isinstance(wv,dict)                     # VHS_VideoCombine etc. use dict widgets
        widgets=wv if is_dict else list(wv or [])
        wi=0
        for field in input_order(ctype):
            if field in linkslots:                      # it's a link input slot
                lk=linkslots[field]
                if lk is not None and lk in links:
                    src,slot=links[lk]; inputs[field]=[str(src),slot]
            elif is_dict:                               # dict widgets: map by field name
                if field in widgets:
                    inputs[field]=fix_combo(ctype,field,widgets[field])
            else:                                       # positional list widgets
                if wi < len(widgets):
                    inputs[field]=fix_combo(ctype,field,widgets[wi]); wi+=1
                    if field in ("seed","noise_seed") and wi < len(widgets) and widgets[wi] in ("fixed","increment","decrement","randomize"):
                        wi+=1                            # skip control_after_generate
        prompt[str(nid)]={"class_type":ctype,"inputs":inputs}
    return prompt

ui=json.load(open(sys.argv[1]))
prompt=convert(ui)
_ov=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
if "__keep__" in _ov:
    prompt=prune(prompt,_ov.pop("__keep__"))
if _ov:                                     # apply overrides {node_id: {field: val}}
    for nid,fields in _ov.items():
        if nid in prompt: prompt[nid]["inputs"].update(fields)
cid=str(uuid.uuid4())
body=json.dumps({"prompt":prompt,"client_id":cid}).encode()
try:
    r=json.loads(urllib.request.urlopen(urllib.request.Request(f"{COMFY}/prompt",body,{"Content-Type":"application/json"}),timeout=60).read())
except urllib.error.HTTPError as e:
    print("QUEUE ERROR:",e.read().decode()[:1200]); sys.exit(1)
pid=r["prompt_id"]; print("queued:",pid); t0=time.time()
while time.time()-t0<1800:
    time.sleep(10)
    try:                                    # ComfyUI HTTP can block during heavy LoRA-merge ops
        h=json.loads(urllib.request.urlopen(f"{COMFY}/history/{pid}",timeout=60).read())
    except Exception as e:
        print(f"  ...{int(time.time()-t0)}s (poll retry: {type(e).__name__})"); continue
    if pid in h:
        st=h[pid]["status"]; outs=h[pid].get("outputs",{})
        imgs=[i for nd in outs.values() for i in nd.get("images",[])]
        print(f"STATUS={st.get('status_str')} frames={len(imgs)}")
        if imgs: print("first:",imgs[0]["filename"])
        for m in st.get("messages",[]):
            if 'error' in str(m).lower(): print("ERR:",str(m)[:400])
        sys.exit(0)
    print(f"  ...{int(time.time()-t0)}s")
print("TIMEOUT")
