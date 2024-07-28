.PHONY: setup start test clean install reinstall init_db

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

start:
	. venv/bin/activate && python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

stop:
	pgrep -f "uvicorn server.main:app" | xargs kill -9
	# lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

test:
	. venv/bin/activate && pytest

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf venv

reinstall: clean setup install

init_db:
	. venv/bin/activate && python3 init_db.py