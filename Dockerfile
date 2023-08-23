FROM tiangolo/uvicorn-gunicorn:python3.10

# Prometheus
# Environment variable is in lower case due to implementation of prometheus-fastapi-instrumentator.
# Can change back to upper case if there is a new fixed version
ENV prometheus_multiproc_dir=/tmp_multiproc
ENV PRE_START_PATH=/app/prestart.sh

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
