from typing import TypedDict
from app.services.clinical import get_patient_details,get_patient_reports,compare_historical_reports,explain_to_patient,mask_pii_phi
from app.services.retrieval import retrieve_relevant_report_chunks
from app.services.documents import has_documents,answer_from_documents

class AgentState(TypedDict,total=False):
    mrn:str; message:str; patient:dict; reports:list[dict]; comparison:str; clinician_summary:str; patient_explanation:str; tools_used:list[str]

def load_context(state): return {**state,"patient":get_patient_details(state["mrn"]),"reports":get_patient_reports(state["mrn"]),"tools_used":["get_patient_details","get_patient_reports"]}

def clinical_reasoning(state):
    chunks=retrieve_relevant_report_chunks(state["mrn"],state.get("message",""),k=3); comparison=compare_historical_reports(state.get("reports",[])); masked=mask_pii_phi(comparison)
    return {**state,"retrieved_chunks":chunks,"comparison":comparison,"clinician_summary":masked,"tools_used":state["tools_used"]+["retrieve_relevant_report_chunks","compare_historical_reports","mask_pii_phi"]}

def patient_language(state): return {**state,"patient_explanation":explain_to_patient(state["comparison"]),"tools_used":state["tools_used"]+["explain_report_to_patient"]}

try:
    from langgraph.graph import StateGraph,END
    builder=StateGraph(AgentState); builder.add_node("load_context",load_context); builder.add_node("clinical_reasoning",clinical_reasoning); builder.add_node("patient_language",patient_language); builder.set_entry_point("load_context"); builder.add_edge("load_context","clinical_reasoning"); builder.add_edge("clinical_reasoning","patient_language"); builder.add_edge("patient_language",END); workflow=builder.compile()
    def invoke(initial): return workflow.invoke(initial)
except ImportError:
    def invoke(initial): return patient_language(clinical_reasoning(load_context(initial)))

def run_agent(mrn,message):
    patient=get_patient_details(mrn)
    if not patient: return {"answer":"Patient not found.","clinician_summary":None,"patient_explanation":None,"tools_used":[],"sources":[]}
    if has_documents(mrn):
        rag=answer_from_documents(mrn,message); masked=mask_pii_phi(rag["answer"])
        return {"answer":masked,"clinician_summary":masked,"patient_explanation":explain_to_patient(masked),"tools_used":["get_patient_details","retrieve_uploaded_pdf_chunks","answer_from_uploaded_pdf","mask_pii_phi","explain_report_to_patient"],"sources":rag["sources"]}
    state=invoke({"mrn":mrn,"message":message,"tools_used":[]})
    return {"answer":state["clinician_summary"],"clinician_summary":state["clinician_summary"],"patient_explanation":state["patient_explanation"],"tools_used":state["tools_used"],"sources":[]}
