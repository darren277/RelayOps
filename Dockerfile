FROM python:3.12-slim

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

WORKDIR /app

RUN pip install --upgrade pip

#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt

RUN pip install flask werkzeug
RUN pip install gunicorn
RUN pip install dotenv
RUN pip install celery
RUN pip install requests
RUN pip install sympy
RUN pip install dash
RUN pip install pandas

RUN pip install openai

RUN pip install pyopenproject

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


CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
