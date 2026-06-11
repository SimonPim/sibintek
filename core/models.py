from django.db import models
from django.contrib.auth.models import User


class GruppaIspolnitelei(models.Model):
    naimenovanie_gruppy = models.CharField(max_length=255, verbose_name="Название группы")

    def __str__(self):
        return self.naimenovanie_gruppy

    class Meta:
        verbose_name = "Группа исполнителей"
        verbose_name_plural = "Группы исполнителей"


class Ispolnitel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    familia = models.CharField(max_length=255, verbose_name="Фамилия Имя")
    gruppa = models.ForeignKey(GruppaIspolnitelei, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Группа")
    aktiven_ili_net = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return self.familia

    class Meta:
        verbose_name = "Исполнитель"
        verbose_name_plural = "Исполнители"


class Servisy(models.Model):
    naimenovanie = models.CharField(max_length=255, verbose_name="Название сервиса")
    adress = models.CharField(max_length=255, verbose_name="Адрес", blank=True, null=True)

    def __str__(self):
        return self.naimenovanie

    class Meta:
        verbose_name = "Сервис"
        verbose_name_plural = "Сервисы"


class StatusZayavki(models.Model):
    status = models.CharField(max_length=50, verbose_name="Статус")

    def __str__(self):
        return self.status

    class Meta:
        verbose_name = "Статус заявки"
        verbose_name_plural = "Статусы заявок"


class Zayavki(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'Высокий'),
        ('medium', 'Средний'),
        ('low', 'Низкий')
    ]

    naimenovanie = models.CharField(max_length=255, verbose_name="Название заявки")
    servis_text = models.CharField(max_length=255, verbose_name="Сервис/Оборудование", blank=True, null=True)
    servis = models.ForeignKey(Servisy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сервис (старое)")
    status = models.ForeignKey(StatusZayavki, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Статус")
    ispolnitel = models.ForeignKey(Ispolnitel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Исполнитель")
    data_sozdaniya_zayavki = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    srok_zayavki = models.DateField(null=True, blank=True, verbose_name="Срок выполнения")
    opisanie_problem = models.TextField(verbose_name="Описание проблемы")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Приоритет"
    )

    # Поля для архива (мягкое удаление)
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")
    deleted_by = models.CharField(max_length=255, verbose_name="Удалил", blank=True, null=True)
    data_udaleniya = models.DateTimeField(verbose_name="Дата удаления", blank=True, null=True)

    def __str__(self):
        return self.naimenovanie

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-data_sozdaniya_zayavki']