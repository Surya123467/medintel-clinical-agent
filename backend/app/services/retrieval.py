import hashlib, math, re
from app.data.synthetic import PATIENTS
DIM=128
def _tokens(text): return re.findall(r"[a-z0-9]+",text.lower())
def embed(text):
    vec=[0.0]*DIM
    for token in _tokens(text): vec[int(hashlib.sha256(token.encode()).hexdigest()[:8],16)%DIM]+=1.0
    norm=math.sqrt(sum(x*x for x in vec)) or 1.0; return [x/norm for x in vec]
def _chunk(text,max_words=45,overlap=8):
    words=text.split()
    if len(words)<=max_words:return [text]
    chunks=[]; step=max_words-overlap
    for i in range(0,len(words),step):
        part=words[i:i+max_words]
        if part: chunks.append(" ".join(part))
        if i+max_words>=len(words): break
    return chunks
def retrieve_relevant_report_chunks(mrn,query,k=3):
    patient=PATIENTS.get(mrn)
    if not patient:return []
    docs=[]
    for report in patient["reports"]:
        for chunk in _chunk(report["text"]): docs.append({"text":chunk,"report_id":report["id"],"date":report["date"],"type":report["type"]})
    q=embed(query); vectors=[embed(d["text"]) for d in docs]
    try:
        import faiss, numpy as np
        mat=np.array(vectors,dtype="float32"); index=faiss.IndexFlatIP(DIM); index.add(mat); scores,ids=index.search(np.array([q],dtype="float32"),min(k,len(docs)))
        return [{**docs[i],"score":float(s)} for s,i in zip(scores[0],ids[0]) if i>=0]
    except ImportError:
        scored=[(d,sum(a*b for a,b in zip(q,v))) for d,v in zip(docs,vectors)]; scored.sort(key=lambda x:x[1],reverse=True); return [{**d,"score":s} for d,s in scored[:k]]
