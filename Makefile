.PHONY: install data pipeline api test docker

install:
	pip install -r requirements.txt

data:
	python scripts/generate_data.py --scale 2 --output data/raw

pipeline:
	python pipelines/lakehouse_pipeline.py --raw data/raw --lake data/lakehouse --warehouse data/warehouse

api:
	uvicorn backend.app.main:app --reload --port 8000

test:
	pytest backend/tests

docker:
	docker compose up --build
