import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Activity,Bot,ShieldCheck,Stethoscope} from 'lucide-react';
import './styles.css';
const API=import.meta.env.VITE_API_URL || 'http://localhost:8000';
function App(){
 const [token,setToken]=useState(''); const [patients,setPatients]=useState([]); const [mrn,setMrn]=useState('MRN-1023'); const [result,setResult]=useState(null); const [loading,setLoading]=useState(false);
 async function login(){const r=await fetch(API+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'doctor@medintel.demo',password:'doctor123'})});const d=await r.json();setToken(d.access_token)}
 useEffect(()=>{login()},[]);
 useEffect(()=>{if(token) fetch(API+'/patients',{headers:{Authorization:'Bearer '+token}}).then(r=>r.json()).then(setPatients)},[token]);
 async function run(){setLoading(true);const r=await fetch(API+'/agent',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({mrn,message:'Compare the latest chest X-ray with the previous report and tell me whether the condition improved.'})});setResult(await r.json());setLoading(false)}
 return <div className="shell"><aside><div className="brand"><Stethoscope/> MedIntel</div><p>Clinical Workflow AI</p><nav><span><Activity/> Patient workspace</span><span><Bot/> Agent activity</span><span><ShieldCheck/> PHI controls</span></nav></aside><main><header><div><h1>Clinical Workflow Agent</h1><p>Synthetic demo · Agentic RAG workflow</p></div><span className="badge">Protected demo</span></header><section className="grid"><div className="card"><h3>Patient Context</h3><select value={mrn} onChange={e=>setMrn(e.target.value)}>{patients.map(p=><option key={p.mrn}>{p.mrn}</option>)}</select><div className="patient">{patients.find(p=>p.mrn===mrn)?.name || 'Loading patient…'}<small>{patients.find(p=>p.mrn===mrn)?.age} yrs · {patients.find(p=>p.mrn===mrn)?.sex}</small></div><button onClick={run} disabled={!token||loading}>{loading?'Agent working…':'Compare latest vs previous'}</button></div><div className="card"><h3>Agent Activity</h3>{result?<div className="tools">{result.tools_used.map(t=><span key={t}>{t}</span>)}</div>:<p className="muted">Run the workflow to see tool execution.</p>}</div></section>{result&&<><section className="card"><h3>Clinician Summary</h3><p>{result.clinician_summary}</p></section><section className="card"><h3>Patient-Friendly Explanation</h3><p>{result.patient_explanation}</p><div className="warning">{result.disclaimer}</div></section></>}</main></div>
}
createRoot(document.getElementById('root')).render(<App/>);
