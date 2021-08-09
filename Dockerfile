FROM tiangolo/uvicorn-gunicorn:python3.8
COPY ./pd6-be /app
COPY .env logging.yaml .version* /app/
RUN pip install -r requirements.txt
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]