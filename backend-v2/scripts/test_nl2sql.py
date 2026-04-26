"""Quick test for NL2SQL"""
import requests

BASE = "http://localhost:8000"

# Login
r = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("Token OK\n")

questions = [
    "Bao nhiêu ca CT?",
    "Ca nào chưa đọc?",
    "Thống kê theo modality",
    "Tổn thương phổi dạng nốt đơn độc",
]

for q in questions:
    print(f"Q: {q}")
    r = requests.post(f"{BASE}/api/search/ask", json={"question": q}, headers=headers)
    data = r.json()
    print(f"  Intent: {data['intent']} | Source: {data.get('source', '-')}")
    if data.get('sql'):
        print(f"  SQL: {data['sql'][:80]}...")
    print(f"  Answer: {data['answer']}")
    if data.get('data'):
        print(f"  Data: {data['data'][:2]}")
    if data.get('rag_results'):
        print(f"  RAG: {len(data['rag_results'])} results")
    print()

print("[DONE]")
