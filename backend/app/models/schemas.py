from pydantic import BaseModel
class LoginRequest(BaseModel):
    email: str
    password: str
class AgentRequest(BaseModel):
    mrn: str
    message: str
class AgentResponse(BaseModel):
    answer: str
    clinician_summary: str | None = None
    patient_explanation: str | None = None
    tools_used: list[str] = []
    disclaimer: str
