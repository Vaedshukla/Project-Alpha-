PY=python

start:
	uvicorn app.main:app --reload

migrate:
	alembic upgrade head

revision:
	alembic revision -m "update"

seed:
	$(PY) scripts/seed.py

test:
	pytest -q

