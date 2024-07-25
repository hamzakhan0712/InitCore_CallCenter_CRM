from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView

urlpatterns = [
    
    path('', views.dashboard, name='dashboard'), 
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('monitor/', views.monitor_users, name='monitor_users'),
    path('get_recent_breaks/', views.get_recent_breaks, name='get_recent_breaks'),
    path('break_state/<int:user_id>/', views.break_state, name='break_state'),
    path('settings/', views.settings_view, name='settings'),
    path('other_administrative_settings/', views.other_administrative_settings, name='other_administrative_settings'),
    path('delete_break/<int:breaktype_id>/', views.delete_break, name='delete_break'),
    path('delete_package/<int:package_id>/', views.delete_package, name='delete_package'),
    path('delete_sub_disposition/<int:sub_disposition_id>/', views.delete_sub_disposition, name='delete_sub_disposition'),
    path('delete_payment_method/<int:payment_method_id>/', views.delete_payment_method, name='delete_payment_method'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        html_email_template_name='registration/password_reset_email.html',
        success_url='/password_reset/done/'
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),


    path('create/', views.create_user, name='create_user'),
    path('create-team/', views.create_team, name='create_team'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add-agent-to-team/<int:team_id>/', views.add_agent_to_team, name='add_agent_to_team'),
    path('staff/<int:team_id>/remove-agent/<int:agent_id>/', views.remove_agent_from_team, name='remove_agent_from_team'),
    path('staff/edit/<int:team_id>/', views.edit_team, name='edit_team'),
    path('staff/delete/<int:team_id>/', views.delete_team, name='delete_team'),
    path('staff/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('staff/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('update-user-status/<int:user_id>/', views.update_user_status, name='update_user_status'),
    path('staff/<int:pk>/password/', auth_views.PasswordChangeView.as_view(), name='password_change'),

    path('leads/', views.lead_list, name='lead_list'),
    path('leads/lead_mapping/', views.lead_mapping, name='lead_mapping'),
    path('lead/<int:lead_id>/history/', views.lead_history, name='lead_history'),
    path('leads/export/', views.export_leads, name='export_leads'),
    path('leads/add/', views.create_lead, name='create_lead'), 
    path('leads/edit/<int:lead_id>/', views.edit_lead, name='edit_lead'),
    path('leads/delete/<int:lead_id>/', views.delete_lead, name='delete_lead'),
    path('assign_leads_to_team/', views.assign_leads_to_team, name='assign_leads_to_team'),
    path('lead-transfers/', views.lead_transfers, name='lead_transfers'),
    path('delete-lead-transfer/<int:lead_id>/', views.delete_lead_transfer, name='delete_lead_transfer'),
    path('download-excel-report/', views.download_excel_report, name='download_excel_report'),
    path('dispose_lead/', views.dispose_lead, name='dispose_lead'),

    
    path('paid-customers/', views.paid_customers, name='paid_customers'),
    path('verify-customer/', views.verify_customer, name='verify_customer'),
    path('create_or_update_company/', views.create_or_update_company, name='create_or_update_company'),
    path('paid-customers/create/', views.create_paid_customer, name='create_paid_customer'),
    path('paid-customers/edit/<int:customerId>/', views.edit_paid_customer, name='edit_paid_customer'),
    path('paid-customers/delete/<int:customerId>/', views.delete_paid_customer, name='delete_paid_customer'),
    path('paid-customers/export/', views.export_paid_customers, name='export_paid_customers'),
    path('autocomplete-leads/', views.autocomplete_leads, name='autocomplete_leads'),

    path('complaints/', views.complaints_list, name='complaints_list'),
    path('complaints/create/', views.create_complaint, name='create_complaint'),
    path('complaints/edit/<int:complaint_id>/', views.edit_complaint, name='edit_complaint'),
    path('complaints/delete/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
    
    path('attendance/', views.attendance, name='attendance'),
    path('export_attendance/', views.export_attendance, name='export_attendance'),
    path('update-regulation-reason/<int:attendance_id>/', views.update_regulation_reason, name='update_regulation_reason'),

    path('sales/', views.sales, name='sales'),
    path('agent-sales-history/<int:agent_id>/', views.agent_sales_history, name='agent_sales_history'),
    path('export-sales/', views.export_sales, name='export_sales'),

    path('analytics/', views.analytics, name='analytics'),
    path('reports/', views.reports, name='reports'),
    path('api/leads/', views.get_leads_by_sub_disposition, name='get_leads_by_sub_disposition'),
    path('reports/export-lead-report/', views.export_lead_report, name='export-lead-report'),
]

from . import routing
urlpatterns += routing.websocket_urlpatterns