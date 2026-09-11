import re
from app.data.synthetic import PATIENTS
def get_patient_details(mrn: str):
    p=PATIENTS.get(mrn)
    if not p: return None
    return {k:v for k,v in p.items() if k != "reports"}
def get_patient_reports(mrn: str):
    p=PATIENTS.get(mrn); return sorted(p["reports"],key=lambda r:r["date"]) if p else []
def mask_pii_phi(text: str):
    text=re.sub(r"MRN-\d+","[MRN]",text,flags=re.I); return re.sub(r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b","[NAME]",text)
def compare_historical_reports(reports: list[dict]):
    if len(reports)<2: return "Not enough reports for historical comparison."
    prev,latest=reports[-2],reports[-1]; latest_l=latest["text"].lower(); improved=["decrease","decreased","improved","resolution","near-complete resolution","trace residual"]; worsening=["increase","increased","worsened","new focal"]
    score=sum(t in latest_l for t in improved)-sum(t in latest_l for t in worsening); trend="improved" if score>0 else "worsened" if score<0 else "appears stable/indeterminate"
    return f"Latest study ({latest['date']}) compared with {prev['date']}: findings {trend}. Latest report: {latest['text']}"
def explain_to_patient(comparison: str):
    if "improved" in comparison: return "The newer chest X-ray shows that the previously seen changes are getting better, with less fluid or shadowing than before. Please review the result with your clinician, who can interpret it together with your symptoms and other tests."
    return "The newer chest X-ray does not show a clear improvement from the available text alone. Please review it with your clinician, who can interpret it together with your symptoms and other tests."
