from python:3.13-slim

env PYTHONPATH=/app:/usr/local/lib/python3.13/site-packages

workdir /app

copy requirements.txt /app/
run pip install -r requirements.txt

copy kontxt*.whl /app/
run pip install ./kontxt-*.whl

cmd ["python", "-m", "kontxt.services.api"]