app:
	streamlit run app.py

.PHONY: backend
backend:
	uvicorn backend.main:app --reload