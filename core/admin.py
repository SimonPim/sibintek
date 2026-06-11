from django.contrib import admin
from .models import StatusZayavki, GruppaIspolnitelei, Ispolnitel, Servisy, Zayavki

@admin.register(StatusZayavki)
class StatusZayavkiAdmin(admin.ModelAdmin):
    list_display = ['id', 'status']
    search_fields = ['status']

@admin.register(GruppaIspolnitelei)
class GruppaIspolniteleiAdmin(admin.ModelAdmin):
    list_display = ['id', 'naimenovanie_gruppy']
    search_fields = ['naimenovanie_gruppy']

@admin.register(Ispolnitel)
class IspolnitelAdmin(admin.ModelAdmin):
    list_display = ['id', 'familia', 'user', 'gruppa', 'aktiven_ili_net']
    list_filter = ['gruppa', 'aktiven_ili_net']
    search_fields = ['familia', 'user__username']

@admin.register(Servisy)
class ServisyAdmin(admin.ModelAdmin):
    list_display = ['id', 'naimenovanie', 'adress']
    search_fields = ['naimenovanie', 'adress']

@admin.register(Zayavki)
class ZayavkiAdmin(admin.ModelAdmin):
    list_display = ['id', 'naimenovanie', 'servis', 'status', 'ispolnitel', 'data_sozdaniya_zayavki']
    list_filter = ['status', 'servis', 'ispolnitel__gruppa']
    search_fields = ['naimenovanie', 'opisanie_problem']
    date_hierarchy = 'data_sozdaniya_zayavki'