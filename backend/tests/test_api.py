from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def token():
    r=client.post('/auth/login',json={'email':'doctor@medintel.demo','password':'doctor123'}); assert r.status_code==200; return r.json()['access_token']
def test_health(): assert client.get('/health').json()['status']=='ok'
def test_login_rejects_bad_password(): assert client.post('/auth/login',json={'email':'doctor@medintel.demo','password':'x'}).status_code==401
def test_agent_historical_comparison():
    t=token(); r=client.post('/agent',headers={'Authorization':f'Bearer {t}'},json={'mrn':'MRN-1023','message':'Compare latest with previous'}); assert r.status_code==200; data=r.json(); assert 'improved' in data['clinician_summary'].lower(); assert 'compare_historical_reports' in data['tools_used']
