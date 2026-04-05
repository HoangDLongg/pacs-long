# PACS++ — Luu Trang Thai Phien Lam Viec
# Luu luc: 2026-03-28 | Trang thai: Tat may — chuan bi Sprint 1

## DA HOAN THANH (Sprint 0)
- Docker Compose: PostgreSQL 16 + pgvector + Orthanc 24.5.3
- FastAPI Backend: Port 8000, tat ca API hoat dong
- Database: 5 users, 30 BN, 44 ca chup (seed_data.py)
- LLM: Ollama (qwen2.5-coder:7b) - local, khong can API key
- Tai lieu: 8 file docs/ + PACS_MASTER_DOCUMENT.md

## KHOI DONG LAI MAY — Thu tu:
  1. docker compose up -d
  2. ollama serve  (terminal rieng)
  3. cd backend && .\venv\Scripts\activate && python main.py

## KE HOACH SPRINT 1 — Tung buoc 1:

  [Giai doan 1 - Setup]
  Buoc 1: npx create-vite@latest frontend-react -- --template react
  Buoc 2: Cai react-router-dom, proxy /api -> :8000
  Buoc 3: Copy 4 file CSS vao src/styles/

  [Giai doan 2 - UI tinh]
  Buoc 4: UC01 - Giao dien Login (chua goi API)
  Buoc 5: App Shell - Sidebar + Topbar (layout tinh)

  [Giai doan 3 - Tung Use Case]
  Buoc 6 : UC01  - Ket noi API dang nhap that
  Buoc 7 : UC03  - Worklist: hien thi danh sach
  Buoc 8 : UC05  - Worklist: stat cards
  Buoc 9 : UC04  - Worklist: bo loc
  Buoc 10: UC07  - Viewer: xem thong tin + Orthanc iframe
  Buoc 11: UC10  - Report: xem bao cao (readonly)
  Buoc 12: UC08  - Report: tao bao cao moi
  Buoc 13: UC09  - Report: cap nhat bao cao
  Buoc 14: UC06  - Upload DICOM
  Buoc 15: UC12  - Search: tu khoa
  Buoc 16: UC13  - Search: Dense (BGE-M3)
  Buoc 17: UC14  - Search: Hybrid
  Buoc 18: UC15  - Search: NL2SQL hoi dap
  Buoc 19: UC11  - Xuat PDF
  Buoc 20: UC16/17 - Admin page

## KHI QUAY LAI - Noi voi AI:
  "bat dau buoc 1"  -> Setup Vite project
  "bat dau buoc 4"  -> Code Login UI tinh
  "cho file DICOM"  -> Huong dan lay file .dcm test

## QUYET DINH DA CHOT:
  - Frontend: Vite (KHONG dung CDN Babel - da that bai)
  - Routing: React Router v6
  - CSS: Vanilla CSS - 4 file rieng
  - LLM: Ollama local, Gemini fallback
  - Style: 1 use case = 1 lan code

## TAI KHOAN TEST:
  admin     / admin123  (Quan tri)
  dr.nam    / doctor123 (Bac si)
  tech.hung / tech123   (KTV)
