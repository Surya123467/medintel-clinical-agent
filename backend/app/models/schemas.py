from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: str
    password: str

class AgentRequest(BaseModel):
    mrn: str
    message: str

class Source(BaseModel):
    filename: str
    page: int
    score: float = 0

class AgentResponse(BaseModel):
    answer: str
    clinician_summary: str | None = None
    patient_explanation: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    disclaimer: str
