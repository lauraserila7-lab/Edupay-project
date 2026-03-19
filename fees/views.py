import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import Student, Class, Payment, FeeStructure, MpesaCallback
from .forms import StudentForm, ClassForm, PaymentForm, MpesaPaymentForm, FeeStructureForm
from .mpesa import stk_push, process_mpesa_callback

logger = logging.getLogger(__name__)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    total_students = Student.objects.filter(status='active').count()
    total_collected = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_classes = Class.objects.count()
    defaulters = Student.objects.filter(status='active')
    defaulter_count = sum(1 for s in defaulters if s.is_defaulter)

    recent_payments = Payment.objects.filter(status='completed').select_related('student')[:8]
    recent_students = Student.objects.select_related('student_class').order_by('-date_enrolled')[:5]

    # Monthly collections (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month = timezone.now().month - i
        year = timezone.now().year
        if month <= 0:
            month += 12
            year -= 1
        total = Payment.objects.filter(
            status='completed',
            created_at__month=month,
            created_at__year=year
        ).aggregate(t=Sum('amount'))['t'] or 0
        monthly_data.append({'month': month, 'year': year, 'total': float(total)})

    context = {
        'total_students': total_students,
        'total_collected': total_collected,
        'total_classes': total_classes,
        'defaulter_count': defaulter_count,
        'recent_payments': recent_payments,
        'recent_students': recent_students,
        'monthly_data': json.dumps(monthly_data),
    }
    return render(request, 'fees/dashboard.html', context)


# ─── Students CRUD ────────────────────────────────────────────────────────────

@login_required
def student_list(request):
    query = request.GET.get('q', '')
    class_filter = request.GET.get('class', '')
    status_filter = request.GET.get('status', '')

    students = Student.objects.select_related('student_class')

    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query)
        )
    if class_filter:
        students = students.filter(student_class_id=class_filter)
    if status_filter:
        students = students.filter(status=status_filter)

    classes = Class.objects.all()
    return render(request, 'fees/student_list.html', {
        'students': students,
        'classes': classes,
        'query': query,
        'class_filter': class_filter,
        'status_filter': status_filter,
    })


@login_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.full_name} added successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentForm()
    return render(request, 'fees/student_form.html', {'form': form, 'title': 'Add Student'})


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    payments = student.payments.all()
    mpesa_form = MpesaPaymentForm(initial={
        'student': student,
        'phone_number': student.parent_phone,
    })
    return render(request, 'fees/student_detail.html', {
        'student': student,
        'payments': payments,
        'mpesa_form': mpesa_form,
    })


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'fees/student_form.html', {'form': form, 'title': 'Edit Student', 'student': student})


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Student {name} deleted.')
        return redirect('student_list')
    return render(request, 'fees/confirm_delete.html', {'object': student, 'type': 'Student'})


# ─── Classes CRUD ─────────────────────────────────────────────────────────────

@login_required
def class_list(request):
    classes = Class.objects.annotate(student_count=Count('students'))
    return render(request, 'fees/class_list.html', {'classes': classes})


@login_required
def class_create(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            c = form.save()
            messages.success(request, f'Class {c.name} created!')
            return redirect('class_list')
    else:
        form = ClassForm()
    return render(request, 'fees/class_form.html', {'form': form, 'title': 'Add Class'})


@login_required
def class_edit(request, pk):
    cls = get_object_or_404(Class, pk=pk)
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=cls)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class updated!')
            return redirect('class_list')
    else:
        form = ClassForm(instance=cls)
    return render(request, 'fees/class_form.html', {'form': form, 'title': 'Edit Class', 'object': cls})


@login_required
def class_delete(request, pk):
    cls = get_object_or_404(Class, pk=pk)
    if request.method == 'POST':
        cls.delete()
        messages.success(request, 'Class deleted.')
        return redirect('class_list')
    return render(request, 'fees/confirm_delete.html', {'object': cls, 'type': 'Class'})


# ─── Payments CRUD ────────────────────────────────────────────────────────────

@login_required
def payment_list(request):
    payments = Payment.objects.select_related('student').all()
    method = request.GET.get('method', '')
    status = request.GET.get('status', '')
    if method:
        payments = payments.filter(method=method)
    if status:
        payments = payments.filter(status=status)
    return render(request, 'fees/payment_list.html', {
        'payments': payments, 'method': method, 'status': status
    })


@login_required
def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = 'completed'
            payment.save()
            messages.success(request, f'Payment of KES {payment.amount} recorded!')
            return redirect('payment_list')
    else:
        form = PaymentForm()
    return render(request, 'fees/payment_form.html', {'form': form, 'title': 'Record Payment'})


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated!')
            return redirect('payment_list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'fees/payment_form.html', {'form': form, 'title': 'Edit Payment'})


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted.')
        return redirect('payment_list')
    return render(request, 'fees/confirm_delete.html', {'object': payment, 'type': 'Payment'})


# ─── M-Pesa STK Push ──────────────────────────────────────────────────────────

@login_required
def mpesa_pay(request):
    """Initiate STK Push payment from admin."""
    if request.method == 'POST':
        form = MpesaPaymentForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            phone = form.cleaned_data['phone_number']
            amount = form.cleaned_data['amount']
            term = form.cleaned_data['term']

            # Create pending payment record
            payment = Payment.objects.create(
                student=student,
                amount=amount,
                method='mpesa',
                status='pending',
                term=term,
                phone_number=phone,
            )

            # Initiate STK Push
            response = stk_push(
                phone_number=phone,
                amount=int(amount),
                account_reference=student.admission_number,
                transaction_desc=f'Fee {student.admission_number}'
            )

            if response.get('ResponseCode') == '0':
                checkout_id = response.get('CheckoutRequestID', '')
                payment.mpesa_checkout_id = checkout_id
                payment.save()
                messages.success(
                    request,
                    f'✅ STK Push sent to {phone}. Ask parent to enter M-Pesa PIN.'
                )
                return redirect('payment_list')
            else:
                payment.status = 'failed'
                payment.save()
                error_msg = response.get('errorMessage') or response.get('message', 'Unknown error')
                messages.error(request, f'❌ M-Pesa error: {error_msg}')
    else:
        form = MpesaPaymentForm()

    return render(request, 'fees/mpesa_pay.html', {'form': form})


@csrf_exempt
def mpesa_callback(request):
    """Endpoint Safaricom calls after payment. Must be public (no login_required)."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid JSON'})

        result = process_mpesa_callback(data)

        # Save raw callback
        MpesaCallback.objects.create(
            checkout_request_id=result.get('checkout_id', ''),
            result_code=result.get('result_code'),
            result_desc=result.get('message', ''),
            amount=result.get('amount'),
            mpesa_receipt=result.get('receipt', ''),
            phone=result.get('phone', ''),
            raw_response=data,
        )

        if result['success']:
            # Find and update matching pending payment
            try:
                payment = Payment.objects.get(mpesa_checkout_id=result['checkout_id'])
                payment.status = 'completed'
                payment.mpesa_receipt = result['receipt']
                payment.amount = result['amount']
                payment.save()
                logger.info(f"Payment {payment.id} completed via M-Pesa {result['receipt']}")
            except Payment.DoesNotExist:
                logger.warning(f"No payment found for checkout {result['checkout_id']}")

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})


# ─── Fee Structure ────────────────────────────────────────────────────────────

@login_required
def fee_structure_list(request):
    structures = FeeStructure.objects.select_related('student_class').all()
    return render(request, 'fees/fee_structure_list.html', {'structures': structures})


@login_required
def fee_structure_create(request):
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee structure saved!')
            return redirect('fee_structure_list')
    else:
        form = FeeStructureForm()
    return render(request, 'fees/fee_structure_form.html', {'form': form, 'title': 'Add Fee Structure'})


@login_required
def fee_structure_edit(request, pk):
    fs = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee structure updated!')
            return redirect('fee_structure_list')
    else:
        form = FeeStructureForm(instance=fs)
    return render(request, 'fees/fee_structure_form.html', {'form': form, 'title': 'Edit Fee Structure'})


@login_required
def fee_structure_delete(request, pk):
    fs = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        fs.delete()
        messages.success(request, 'Fee structure deleted.')
        return redirect('fee_structure_list')
    return render(request, 'fees/confirm_delete.html', {'object': fs, 'type': 'Fee Structure'})


# ─── Reports ──────────────────────────────────────────────────────────────────

@login_required
def defaulters_report(request):
    students = Student.objects.filter(status='active').select_related('student_class')
    defaulters = [s for s in students if s.is_defaulter]
    return render(request, 'fees/defaulters.html', {'defaulters': defaulters})
