.PHONY: install train predict api dashboard test

install:
	pip install -r requirements.txt
	pip install -e .

train:
	python scripts/train.py --symbol BTC-USD --period 2y --models all

predict:
	python scripts/predict.py --symbol BTC-USD --steps 7

api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

test:
	python tests/test_fetcher.py
	python tests/test_features.py
	python tests/test_models.py

docker-build:
	docker build -t crypto-prediction .

docker-run:
	docker run -p 8000:8000 -p 8501:8501 crypto-prediction
