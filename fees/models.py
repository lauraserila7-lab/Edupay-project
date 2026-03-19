from django.db import models
from django.utils import timezone


class Class(models.Model):
    name = models.CharField(max_length=50)          # e.g. "Form 1", "Grade 6"
    level = models.CharField(max_length=50, blank=True)
    annual_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['name']

    def __str__(self):
        return self.name


class Student(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('graduated', 'Graduated')]

    admission_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    parent_name = models.CharField(max_length=200)
    parent_phone = models.CharField(max_length=15)  # Used for M-Pesa STK Push
    parent_email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    date_enrolled = models.DateField(default=timezone.now)
    photo = models.ImageField(upload_to='students/', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments.filter(status='completed'))

    @property
    def balance(self):
        if self.student_class:
            return self.student_class.annual_fee - self.total_paid
        return 0

    @property
    def is_defaulter(self):
        return self.balance > 0


class FeeStructure(models.Model):
    TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3'), ('annual', 'Annual')]

    student_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='fee_structures')
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    year = models.PositiveIntegerField(default=timezone.now().year)
    tuition = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activity_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ['student_class', 'term', 'year']

    def __str__(self):
        return f"{self.student_class} - {self.get_term_display()} {self.year}"

    @property
    def total(self):
        return self.tuition + self.activity_fee + self.exam_fee + self.other_fee


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    ]
    TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3'), ('annual', 'Annual')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='mpesa')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    term = models.CharField(max_length=10, choices=TERM_CHOICES, default='1')
    year = models.PositiveIntegerField(default=timezone.now().year)
    reference = models.CharField(max_length=100, blank=True)          # Receipt / M-Pesa ref
    mpesa_checkout_id = models.CharField(max_length=100, blank=True)  # STK push checkout ID
    mpesa_receipt = models.CharField(max_length=50, blank=True)       # Final M-Pesa receipt
    phone_number = models.CharField(max_length=15, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - KES {self.amount} ({self.get_status_display()})"


class MpesaCallback(models.Model):
    """Stores raw M-Pesa callback data for auditing."""
    checkout_request_id = models.CharField(max_length=100, blank=True)
    result_code = models.IntegerField(null=True)
    result_desc = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    raw_response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Callback {self.checkout_request_id} - Code {self.result_code}"
