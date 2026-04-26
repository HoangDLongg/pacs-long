"""Quick test for search API"""
import requests

BASE = "http://localhost:8000"

# Login
r = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Token OK")

# UC12: Keyword search
print("\n=== UC12: Keyword Search ===")
r = requests.get(f"{BASE}/api/search/keyword", params={"q": "phổi"}, headers=headers)
data = r.json()
print(f"Total: {data['total']} results")
for x in data["results"][:3]:
    print(f"  #{x['report_id']}: {x['conclusion'][:80]}")

# UC13: Dense search
print("\n=== UC13: Dense Search ===")
r = requests.post(f"{BASE}/api/search", json={"query": "tổn thương phổi dạng mờ kính", "method": "dense", "top_k": 5}, headers=headers)
data = r.json()
print(f"Total: {data['total']} results")
for x in data["results"][:3]:
    print(f"  #{x['report_id']} (score={x['score']}): {x['conclusion'][:80]}")

# UC14: Hybrid search
print("\n=== UC14: Hybrid Search ===")
r = requests.post(f"{BASE}/api/search", json={"query": "bóng tim to kèm dịch màng phổi", "method": "hybrid", "top_k": 5}, headers=headers)
data = r.json()
print(f"Total: {data['total']} results")
for x in data["results"][:3]:
    print(f"  #{x['report_id']} (score={x['score']}): {x['conclusion'][:80]}")

print("\n[DONE] All search methods working!")
