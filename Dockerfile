FROM python:3.12-slim

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./llm ./llm
COPY ./migrations ./migrations
COPY ./webhooks ./webhooks
#COPY ./tests ./tests
COPY ./op_migrations.py .
COPY ./surrealdb_migrations.py .
COPY ./settings.py .
#COPY ./logger.py .
COPY ./templates ./templates
COPY ./app.py .
COPY ./dashboard.py .
COPY ./tasks.py .

EXPOSE 5000

RUN pip install gunicorn

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
