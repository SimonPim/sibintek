FROM python:3.13-slim

WORKDIR /app

# Установка системных пакетов
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn psycopg2-binary

# Копируем весь проект
COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput

# Переменные
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

EXPOSE 8000

# Запуск
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
