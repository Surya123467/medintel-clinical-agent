from fastapi import FastAPI,HTTPException,Depends,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import authenticate,create_token,current_user
from app.models.schemas import LoginRequest,AgentRequest,AgentResponse
from app.data.synthetic import PATIENTS
from app.agent.workflow import run_agent
from app.services.documents import ingest_pdf,list_documents

app=FastAPI(title=settings.app_name,version="1.1.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins.split(","),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.get("/health")
def health(): return {"status":"ok","pdf_rag":True}

@app.post("/auth/login")
def login(body:LoginRequest):
    user=authenticate(body.email,body.password)
    if not user: raise HTTPException(401,"Invalid credentials")
    return {"access_token":create_token(user),"token_type":"bearer","user":user}

@app.get("/patients")
def patients(user=Depends(current_user)): return [{k:v for k,v in p.items() if k!="reports"} for p in PATIENTS.values()]

@app.get("/patients/{mrn}/reports")
def reports(mrn:str,user=Depends(current_user)):
    if mrn not in PATIENTS: raise HTTPException(404,"Patient not found")
    return PATIENTS[mrn]["reports"]

@app.get("/patients/{mrn}/documents")
def documents(mrn:str,user=Depends(current_user)):
    if mrn not in PATIENTS: raise HTTPException(404,"Patient not found")
    return list_documents(mrn)

@app.post("/patients/{mrn}/documents")
async def upload_document(mrn:str,file:UploadFile=File(...),user=Depends(current_user)):
    if mrn not in PATIENTS: raise HTTPException(404,"Patient not found")
    if not file.filename or not file.filename.lower().endswith(".pdf"): raise HTTPException(400,"Only PDF files are supported")
    payload=await file.read()
    if len(payload)>10*1024*1024: raise HTTPException(413,"PDF must be 10 MB or smaller")
    try: return ingest_pdf(mrn,file.filename,payload)
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
    except Exception as exc: raise HTTPException(400,f"Unable to read PDF: {exc}") from exc

@app.post("/agent",response_model=AgentResponse)
def agent(body:AgentRequest,user=Depends(current_user)):
    result=run_agent(body.mrn,body.message)
    return {**result,"disclaimer":"AI-assisted workflow only. Not a medical diagnosis or substitute for clinician judgment."}
