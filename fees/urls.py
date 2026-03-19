from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),

    # Classes
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.class_create, name='class_create'),
    path('classes/<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:pk>/delete/', views.class_delete, name='class_delete'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

    # M-Pesa
    path('mpesa/pay/', views.mpesa_pay, name='mpesa_pay'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),

    # Fee Structure
    path('fee-structure/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structure/add/', views.fee_structure_create, name='fee_structure_create'),
    path('fee-structure/<int:pk>/edit/', views.fee_structure_edit, name='fee_structure_edit'),
    path('fee-structure/<int:pk>/delete/', views.fee_structure_delete, name='fee_structure_delete'),

    # Reports
    path('reports/defaulters/', views.defaulters_report, name='defaulters_report'),
]
