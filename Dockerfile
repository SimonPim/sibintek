FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём папку для базы данных (постоянное хранилище)
RUN mkdir -p /data

# Запускаем сервер
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
