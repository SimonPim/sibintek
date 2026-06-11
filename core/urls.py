from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.requests_list, name='requests_list'),
    path('my/', views.my_requests, name='my_requests'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('create/', views.create_request, name='create_request'),
    path('edit/<int:id>/', views.edit_request, name='edit_request'),
    path('delete/<int:id>/', views.delete_request, name='delete_request'),
    path('archive/', views.archive_list, name='archive_list'),
    path('archive/restore/<int:id>/', views.restore_from_archive, name='restore_from_archive'),
    path('archive/delete/<int:id>/', views.permanent_delete, name='permanent_delete'),
    path('export/', views.export_to_excel, name='export_to_excel'),
    path('pdf/<int:id>/', views.export_to_pdf, name='export_to_pdf'),
]