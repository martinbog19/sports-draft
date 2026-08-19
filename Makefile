app:
	streamlit run app.py

.PHONY: backend
backend:
	uvicorn backend.main:app --reload

.PHONY: frontend
frontend:
	cd frontend && npm run dev