from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout, authenticate, login
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Zayavki, Servisy, StatusZayavki, Ispolnitel
import openpyxl
from openpyxl import Workbook
from datetime import datetime
import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def custom_login(request):
    """Кастомная страница входа"""
    if request.user.is_authenticated:
        return redirect('requests_list')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('requests_list')
        else:
            return render(request, 'core/login.html', {'error': True})
    return render(request, 'core/login.html', {'error': False})


def get_is_manager(user):
    """Вспомогательная функция для проверки роли менеджера"""
    return user.groups.filter(name='Менеджеры').exists()


@login_required(login_url='/login/')
def requests_list(request):
    """Главная страница - только НЕ архивные заявки"""
    queryset = Zayavki.objects.filter(is_archived=False).select_related(
        'status', 'ispolnitel', 'ispolnitel__user'
    ).all()

    # Фильтры
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(naimenovanie__icontains=search_query) |
            Q(opisanie_problem__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        queryset = queryset.filter(status_id=status_filter)

    executor_filter = request.GET.get('executor', '')
    if executor_filter:
        queryset = queryset.filter(ispolnitel_id=executor_filter)

    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)

    statusy = StatusZayavki.objects.all()
    ispolniteli = Ispolnitel.objects.filter(aktiven_ili_net=True)
    is_manager = get_is_manager(request.user)

    # Пагинация: 10 заявок на страницу
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'zayavki': page_obj,
        'statusy': statusy,
        'ispolniteli': ispolniteli,
        'search_query': search_query,
        'status_filter': status_filter,
        'executor_filter': executor_filter,
        'priority_filter': priority_filter,
        'is_manager': is_manager,
    }
    return render(request, 'core/requests_list.html', context)


@login_required(login_url='/login/')
def my_requests(request):
    """Личный кабинет - только свои НЕ архивные заявки"""
    try:
        profile = Ispolnitel.objects.get(user=request.user, aktiven_ili_net=True)
    except Ispolnitel.DoesNotExist:
        return render(request, 'core/my_requests.html', {
            'zayavki': [], 'profile': None, 'is_manager': False
        })

    queryset = Zayavki.objects.filter(
        ispolnitel=profile,
        is_archived=False
    ).select_related(
        'status', 'ispolnitel', 'ispolnitel__user'
    ).order_by('-data_sozdaniya_zayavki')

    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(naimenovanie__icontains=search_query) |
            Q(opisanie_problem__icontains=search_query)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        queryset = queryset.filter(status_id=status_filter)

    statusy = StatusZayavki.objects.all()
    is_manager = get_is_manager(request.user)

    # Пагинация
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'zayavki': page_obj,
        'profile': profile,
        'statusy': statusy,
        'search_query': search_query,
        'status_filter': status_filter,
        'is_manager': is_manager,
    }
    return render(request, 'core/my_requests.html', context)


@login_required(login_url='/login/')
def statistics_view(request):
    """Статистика - только для менеджеров"""
    is_manager = get_is_manager(request.user)
    
    if not is_manager and not request.user.is_superuser:
        messages.error(request, "Доступ к статистике имеют только менеджеры.")
        return redirect('requests_list')

    total = Zayavki.objects.filter(is_archived=False).count()
    new_count = Zayavki.objects.filter(is_archived=False, status__status="Новая").count()
    work_count = Zayavki.objects.filter(is_archived=False, status__status="В работе").count()
    done_count = Zayavki.objects.filter(is_archived=False, status__status="Выполнена").count()
    closed_count = Zayavki.objects.filter(is_archived=False, status__status="Закрыта").count()

    context = {
        'total': total,
        'new_count': new_count,
        'work_count': work_count,
        'done_count': done_count,
        'closed_count': closed_count,
        'is_manager': is_manager,
    }
    return render(request, 'core/stats.html', context)


@login_required(login_url='/login/')
def create_request(request):
    """Создание заявки - ТОЛЬКО ДЛЯ МЕНЕДЖЕРОВ И АДМИНОВ"""
    is_manager = get_is_manager(request.user)
    
    # ✅ Проверка прав - исполнитель не может создавать заявки
    if not (is_manager or request.user.is_superuser):
        messages.error(request, "Создавать заявки могут только менеджеры и администраторы.")
        return redirect('requests_list')

    if request.method == 'POST':
        Zayavki.objects.create(
            naimenovanie=request.POST.get('naimenovanie'),
            opisanie_problem=request.POST.get('opisanie_problem'),
            servis_text=request.POST.get('servis_text'),
            status_id=request.POST.get('status'),
            ispolnitel_id=request.POST.get('ispolnitel') or None,
            srok_zayavki=request.POST.get('srok_zayavki') or None,
            priority=request.POST.get('priority', 'medium'),
        )
        messages.success(request, "Заявка успешно создана!")
        return redirect('requests_list')

    context = {
        'statusy': StatusZayavki.objects.all(),
        'ispolniteli': Ispolnitel.objects.filter(aktiven_ili_net=True),
        'is_manager': is_manager,
    }
    return render(request, 'core/create_request.html', context)


@login_required(login_url='/login/')
def edit_request(request, id):
    """Редактирование заявки"""
    zayavka = get_object_or_404(Zayavki, id=id, is_archived=False)
    is_manager = get_is_manager(request.user)
    is_admin = request.user.is_superuser
    is_executor_assigned = (
        zayavka.ispolnitel and zayavka.ispolnitel.user == request.user
    )

    if not (is_manager or is_admin or is_executor_assigned):
        messages.error(request, "У вас нет прав на редактирование этой заявки.")
        return redirect('requests_list')

    if request.method == 'POST':
        zayavka.naimenovanie = request.POST.get('naimenovanie')
        zayavka.opisanie_problem = request.POST.get('opisanie_problem')
        zayavka.servis_text = request.POST.get('servis_text')
        zayavka.status_id = request.POST.get('status')
        zayavka.ispolnitel_id = request.POST.get('ispolnitel') or None
        zayavka.srok_zayavki = request.POST.get('srok_zayavki') or None
        zayavka.priority = request.POST.get('priority', 'medium')
        zayavka.save()
        messages.success(request, "Изменения сохранены.")
        return redirect('requests_list')

    context = {
        'zayavka': zayavka,
        'statusy': StatusZayavki.objects.all(),
        'ispolniteli': Ispolnitel.objects.filter(aktiven_ili_net=True),
        'is_manager': is_manager,
    }
    return render(request, 'core/edit_request.html', context)


@login_required(login_url='/login/')
def delete_request(request, id):
    """Мягкое удаление - перемещение в архив"""
    if not (get_is_manager(request.user) or request.user.is_superuser):
        messages.error(request, "У вас нет прав на удаление.")
        return redirect('requests_list')

    zayavka = get_object_or_404(Zayavki, id=id, is_archived=False)

    zayavka.is_archived = True
    zayavka.deleted_by = request.user.username
    zayavka.data_udaleniya = timezone.now()
    zayavka.save()

    messages.success(request, f"Заявка #{zayavka.id} перемещена в архив.")
    return redirect('requests_list')


@login_required(login_url='/login/')
def archive_list(request):
    """Просмотр архива - только для менеджеров и админов"""
    is_manager = get_is_manager(request.user)
    
    if not (is_manager or request.user.is_superuser):
        messages.error(request, "Доступ к архиву имеют только менеджеры и администраторы.")
        return redirect('requests_list')

    queryset = Zayavki.objects.filter(is_archived=True).select_related(
        'status', 'ispolnitel', 'ispolnitel__user'
    ).order_by('-data_udaleniya')

    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(naimenovanie__icontains=search_query) |
            Q(opisanie_problem__icontains=search_query)
        )

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'archive_items': page_obj,
        'search_query': search_query,
        'is_manager': is_manager,
    }
    return render(request, 'core/archive_list.html', context)


@login_required(login_url='/login/')
def restore_from_archive(request, id):
    """Восстановление заявки из архива"""
    if not (get_is_manager(request.user) or request.user.is_superuser):
        messages.error(request, "У вас нет прав на восстановление.")
        return redirect('archive_list')

    zayavka = get_object_or_404(Zayavki, id=id, is_archived=True)

    zayavka.is_archived = False
    zayavka.deleted_by = None
    zayavka.data_udaleniya = None
    zayavka.save()

    messages.success(request, f"Заявка #{zayavka.id} восстановлена из архива.")
    return redirect('archive_list')


@login_required(login_url='/login/')
def permanent_delete(request, id):
    """Полное удаление из архива (необратимо!)"""
    if not (get_is_manager(request.user) or request.user.is_superuser):
        messages.error(request, "У вас нет прав на удаление.")
        return redirect('archive_list')

    zayavka = get_object_or_404(Zayavki, id=id, is_archived=True)
    zayavka.delete()
    messages.success(request, "Заявка полностью удалена из системы.")
    return redirect('archive_list')


@login_required(login_url='/login/')
def export_to_excel(request):
    """Экспорт в Excel - только для менеджеров и админов"""
    if not (request.user.is_superuser or get_is_manager(request.user)):
        messages.error(request, "Экспорт доступен только менеджерам и администраторам.")
        return redirect('requests_list')

    queryset = Zayavki.objects.filter(is_archived=False).select_related(
        'status', 'ispolnitel', 'ispolnitel__user'
    ).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Заявки"
    ws.append([
        'ID', 'Название', 'Сервис/Оборудование', 'Статус', 'Приоритет',
        'Исполнитель', 'Дата создания', 'Описание'
    ])

    for z in queryset:
        priority_display = dict(Zayavki.PRIORITY_CHOICES).get(z.priority, z.priority)
        ws.append([
            z.id,
            z.naimenovanie,
            z.servis_text or '',
            z.status.status if z.status else '',
            priority_display,
            z.ispolnitel.familia if z.ispolnitel else '',
            z.data_sozdaniya_zayavki.strftime('%d.%m.%Y'),
            z.opisanie_problem,
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="zayavki_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    )
    wb.save(response)
    return response


@login_required(login_url='/login/')
def export_to_pdf(request, id):
    """Экспорт заявки в PDF"""
    zayavka = get_object_or_404(Zayavki, id=id, is_archived=False)

    font_path = os.path.join(os.path.dirname(__file__), 'arial.ttf')
    try:
        pdfmetrics.registerFont(TTFont('RusFont', font_path))
        font_name = 'RusFont'
    except Exception:
        font_name = 'Helvetica'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()

    style_company = ParagraphStyle(
        name='Company', parent=styles['Heading2'],
        fontName=font_name, fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=0, alignment=TA_CENTER
    )
    style_subtitle = ParagraphStyle(
        name='Subtitle', parent=styles['Normal'],
        fontName=font_name, fontSize=10,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=20, alignment=TA_CENTER
    )
    style_title = ParagraphStyle(
        name='DocTitle', parent=styles['Title'],
        fontName=font_name, fontSize=18,
        textColor=colors.HexColor('#111827'),
        alignment=TA_CENTER, spaceAfter=25, spaceBefore=10
    )
    style_label = ParagraphStyle(
        name='Label', parent=styles['Normal'],
        fontName=font_name, fontSize=10,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER
    )
    style_value = ParagraphStyle(
        name='Value', parent=styles['Normal'],
        fontName=font_name, fontSize=11,
        textColor=colors.HexColor('#111827'),
        leftIndent=5
    )
    style_section = ParagraphStyle(
        name='Section', parent=styles['Heading3'],
        fontName=font_name, fontSize=12,
        textColor=colors.HexColor('#111827'),
        spaceAfter=10, spaceBefore=15,
        borderWidth=1, borderColor=colors.HexColor('#FFD700'),
        borderPadding=5
    )
    style_desc = ParagraphStyle(
        name='Description', parent=styles['Normal'],
        fontName=font_name, fontSize=11, leading=15,
        backColor=colors.HexColor('#f9fafb'),
        borderPadding=10, borderColor=colors.HexColor('#e5e7eb'),
        borderWidth=1, textColor=colors.HexColor('#374151')
    )
    style_footer = ParagraphStyle(
        name='Footer', parent=styles['Normal'],
        fontName=font_name, fontSize=9,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER
    )

    priority_display = dict(Zayavki.PRIORITY_CHOICES).get(zayavka.priority, zayavka.priority)
    priority_color = {
        'high': '#dc2626',
        'medium': '#d97706',
        'low': '#059669'
    }.get(zayavka.priority, '#6b7280')

    style_priority = ParagraphStyle(
        name='Priority', parent=style_value,
        textColor=colors.HexColor(priority_color),
        fontName=font_name
    )

    story = []
    story.append(Paragraph("ООО ИК «СИБИНТЕК»", style_company))
    story.append(Paragraph("Система управления сервисными заявками", style_subtitle))
    story.append(Spacer(1*cm, 0.3*cm))

    line = Table([['-' * 80]], colWidths=[16*cm])
    line.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#FFD700'))]))
    story.append(line)
    story.append(Spacer(1*cm, 0.5*cm))

    story.append(Paragraph(f"КАРТОЧКА ЗАЯВКИ N{zayavka.id}", style_title))
    story.append(Paragraph("Основная информация", style_section))

    data = [
        [Paragraph("Название:", style_label), Paragraph(zayavka.naimenovanie, style_value)],
        [Paragraph("Статус:", style_label), Paragraph(
            zayavka.status.status if zayavka.status else 'Не задан', style_value
        )],
        [Paragraph("Приоритет:", style_label), Paragraph(priority_display, style_priority)],
        [Paragraph("Сервис/Оборудование:", style_label), Paragraph(
            zayavka.servis_text or 'Не указан', style_value
        )],
        [Paragraph("Исполнитель:", style_label), Paragraph(
            f"{zayavka.ispolnitel.familia} ({zayavka.ispolnitel.user.username})"
            if zayavka.ispolnitel else 'Не назначен',
            style_value
        )],
        [Paragraph("Дата создания:", style_label), Paragraph(
            zayavka.data_sozdaniya_zayavki.strftime('%d.%m.%Y %H:%M'), style_value
        )],
    ]
    if zayavka.srok_zayavki:
        data.append([
            Paragraph("Срок выполнения:", style_label),
            Paragraph(zayavka.srok_zayavki.strftime('%d.%m.%Y'), style_value)
        ])

    table = Table(data, colWidths=[4*cm, 11*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f9fafb')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    story.append(KeepTogether(table))

    story.append(Paragraph("Описание проблемы", style_section))
    story.append(Spacer(0.3*cm, 0.3*cm))
    story.append(Paragraph(zayavka.opisanie_problem or "Не указано", style_desc))

    story.append(Spacer(1*cm, 2*cm))
    story.append(Paragraph(
        "Исполнитель: ___________________ / Дата: _______________",
        style_footer
    ))

    story.append(Spacer(1*cm, 1*cm))
    footer_line = Table([['-' * 80]], colWidths=[16*cm])
    footer_line.setStyle(TableStyle([('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#e5e7eb'))]))
    story.append(footer_line)
    story.append(Spacer(0.3*cm, 0.3*cm))
    story.append(Paragraph(
        f"Документ сгенерирован автоматически {datetime.now().strftime('%d.%m.%Y %H:%M')} | ООО ИК «СИБИНТЕК»",
        style_footer
    ))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="zayavka_{zayavka.id}.pdf"'
    return response


def logout_view(request):
    """Выход из системы"""
    django_logout(request)
    return redirect('/')