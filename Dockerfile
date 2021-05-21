FROM python:alpine
COPY . /app
CMD pip install -r requirements.txt
CMD python bot.py
