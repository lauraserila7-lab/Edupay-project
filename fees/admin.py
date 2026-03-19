from django.contrib import admin
from .models import Student, Class, Payment, FeeStructure, MpesaCallback


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'annual_fee']
    search_fields = ['name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'full_name', 'student_class', 'parent_phone', 'status']
    list_filter = ['status', 'student_class']
    search_fields = ['first_name', 'last_name', 'admission_number']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'method', 'status', 'mpesa_receipt', 'created_at']
    list_filter = ['method', 'status', 'term']
    search_fields = ['student__first_name', 'student__last_name', 'mpesa_receipt', 'reference']
    readonly_fields = ['mpesa_checkout_id', 'mpesa_receipt', 'created_at', 'updated_at']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['student_class', 'term', 'year', 'tuition', 'total']
    list_filter = ['term', 'year']


@admin.register(MpesaCallback)
class MpesaCallbackAdmin(admin.ModelAdmin):
    list_display = ['checkout_request_id', 'result_code', 'amount', 'mpesa_receipt', 'created_at']
    readonly_fields = ['raw_response', 'created_at']
