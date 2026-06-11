import os
import django
from datetime import datetime, timedelta
import random

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import StatusZayavki, Servisy, Ispolnitel, Zayavki

print("⏳ Подготовка данных...")

# 1. Статусы
status_names = ["Новая", "В работе", "Выполнена", "Закрыта"]
statuses = {}
for name in status_names:
    obj, _ = StatusZayavki.objects.get_or_create(status=name)
    statuses[name] = obj

# 2. Сервис
service, _ = Servisy.objects.get_or_create(naimenovanie="Главный офис", adress="ул. Ленина, 1")

# 3. Петров
try:
    user_petrov = User.objects.get(username='petrov')
except User.DoesNotExist:
    user_petrov = User.objects.create_user(username='petrov', password='12345')
executor_petrov, _ = Ispolnitel.objects.get_or_create(
    user=user_petrov, defaults={'familia': 'Петров Иван', 'aktiven_ili_net': True}
)

# 4. Сидоров
try:
    user_sid = User.objects.get(username='sidorov')
except User.DoesNotExist:
    user_sid = User.objects.create_user(username='sidorov', password='12345')
executor_sid, _ = Ispolnitel.objects.get_or_create(
    user=user_sid, defaults={'familia': 'Сидоров Алексей', 'aktiven_ili_net': True}
)

# 5. Шаблоны
templates_petrov = [
    ("Принтер в бухгалтерии", "Не печатает документы, выдаёт ошибку Paper Jam."),
    ("Интернет на 3 этаже", "Отсутствует подключение к корпоративной сети Wi-Fi."),
    ("Тормозит 1С", "При выгрузке отчётов программа зависает на 10+ минут."),
    ("Замена картриджа", "Закончился тонер в МФУ отдела продаж."),
    ("Установка ПО", "Требуется установка Adobe Acrobat Pro для дизайнеров."),
    ("Настройка Outlook", "Не приходит корпоративная почта на новый ноутбук."),
    ("Ремонт сервера", "Сервер №2 перегревается, требуется замена термопасты."),
    ("Обновление антивируса", "Базы не обновляются, лицензия истекла."),
    ("Замена монитора", "Мерцает экран, требуется замена матрицы."),
    ("Настройка сетевого диска", "Нет доступа к папке \\server\\docs."),
    ("Ошибка в CRM", "Не сохраняются контрагенты, ошибка 500."),
    ("Профилактика ПК", "Плановая чистка от пыли и обновление драйверов.")
]

templates_sidorov = [
    ("Настройка нового рабочего места", "Подключить два монитора, мышь и клавиатуру для нового сотрудника."),
    ("Сброс пароля Active Directory", "Заблокирована учётная запись manager_04."),
    ("Замена SSD диска", "Жёсткий диск в ПК директора вышел из строя, требуется срочная замена."),
    ("Проблема с телефоном IP", "IP-телефон в переговорной №3 не регистрируется в АТС."),
    ("Настройка VPN", "Требуется доступ к удалённому серверу для работы из дома."),
    ("Замена мыши и клавиатуры", "Износился кабель мыши, клавиатура не пробивает пробел.")
]

priorities = ['high', 'medium', 'low']
now = datetime.now()
created_count = 0

# Создаём 12 заявок для Петрова
for i, status_name in enumerate(status_names):
    for j in range(3):
        idx = i * 3 + j
        if idx < len(templates_petrov):
            title, desc = templates_petrov[idx]
            status_obj = statuses[status_name]

            if status_name == "Новая":
                created = now - timedelta(hours=random.randint(1, 24))
                deadline = (now + timedelta(days=random.randint(2, 5))).date()
            elif status_name == "В работе":
                created = now - timedelta(days=random.randint(1, 3))
                deadline = (now + timedelta(days=random.randint(1, 4))).date()
            elif status_name == "Выполнена":
                created = now - timedelta(days=random.randint(5, 15))
                deadline = (now - timedelta(days=random.randint(1, 3))).date()
            else:
                created = now - timedelta(days=random.randint(10, 30))
                deadline = (now - timedelta(days=random.randint(5, 10))).date()

            z = Zayavki(
                naimenovanie=title,
                servis=service,
                status=status_obj,
                ispolnitel=executor_petrov,
                srok_zayavki=deadline,
                opisanie_problem=desc,
                priority=random.choice(priorities)
            )
            z.data_sozdaniya_zayavki = created
            z.save()
            created_count += 1

# Создаём 6 заявок для Сидорова
sidorov_status_seq = ["Новая", "Новая", "В работе", "В работе", "Выполнена", "Закрыта"]
for i, (title, desc) in enumerate(templates_sidorov):
    status_name = sidorov_status_seq[i]
    status_obj = statuses[status_name]

    if status_name == "Новая":
        created = now - timedelta(hours=random.randint(2, 48))
        deadline = (now + timedelta(days=random.randint(3, 7))).date()
    elif status_name == "В работе":
        created = now - timedelta(days=random.randint(2, 5))
        deadline = (now + timedelta(days=random.randint(1, 5))).date()
    elif status_name == "Выполнена":
        created = now - timedelta(days=random.randint(4, 10))
        deadline = (now - timedelta(days=random.randint(1, 2))).date()
    else:
        created = now - timedelta(days=random.randint(8, 20))
        deadline = (now - timedelta(days=random.randint(3, 7))).date()

    z = Zayavki(
        naimenovanie=title,
        servis=service,
        status=status_obj,
        ispolnitel=executor_sid,
        srok_zayavki=deadline,
        opisanie_problem=desc,
        priority=random.choice(priorities)
    )
    z.data_sozdaniya_zayavki = created
    z.save()
    created_count += 1

print(f"\n🎉 ГОТОВО! Создано {created_count} заявок.")
print("✅ Петров: 12 заявок (по 3 на каждый статус)")
print("✅ Сидоров: 6 заявок (разные статусы)")
print("🔍 Теперь закрой это окно и обнови сайт (F5)")