# Crypto Prediction - Makefile
.PHONY: install train predict api dashboard check test serve frontend

install:            ## install python dependencies into .venv
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

serve:              ## web dashboard + REST API on :8000 (default app)
	.venv/bin/python run.py serve

api:                ## REST API on :8000
	.venv/bin/python run.py serve

dashboard:          ## Streamlit dashboard on :8501
	.venv/bin/python run.py dashboard

check:              ## self-diagnostic: deps, data, models, prediction
	.venv/bin/python run.py check --offline

predict:            ## predict BTC-USD for the next 7 days
	.venv/bin/python run.py predict --symbol BTC-USD

train:              ## (re)train all bundled models on fresh data
	.venv/bin/python scripts/pretrain.py

test:               ## run the test suite (~1 min; needs: pip install -e .[dev])
	.venv/bin/python -m pytest tests -q

frontend:           ## rebuild the React web dashboard (needs node/npm)
	cd frontend && npm install && npm run build

docker-build:       ## build the docker image
	docker build -t crypto-prediction .

docker-run:         ## run the docker image
	docker run -p 8000:8000 -p 8501:8501 crypto-prediction
