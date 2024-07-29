.PHONY: setup start stop test clean reinstall init_db

PORT = 8000

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

start:
	@echo "Checking if port $(PORT) is in use..."
	@lsof -i :$(PORT) || true
	@if lsof -i :$(PORT) > /dev/null; then \
		echo "Port $(PORT) is in use. Attempting to free it..."; \
		lsof -ti :$(PORT) | xargs kill -9; \
		sleep 1; \
	fi
	@echo "Starting the server..."
	. venv/bin/activate && python3 run.py

stop:
	@echo "Stopping the server..."
	@pkill -f "python3 run.py" || echo "No running server found."
	@echo "Ensuring port $(PORT) is free..."
	@lsof -ti :$(PORT) | xargs kill -9 || true

test:
	. venv/bin/activate && pytest

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf venv

reinstall: clean setup install

init_db:
	. venv/bin/activate && python3 init_db.py