run:
	uvicorn api.main:app --reload

test:
	pytest

lint:
	black api tests
