from django import forms
from .models import Student, Class, Payment, FeeStructure


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'admission_number', 'first_name', 'last_name', 'gender',
            'date_of_birth', 'student_class', 'parent_name',
            'parent_phone', 'parent_email', 'status', 'date_enrolled', 'photo',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_enrolled': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ADM-2024-001'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'student_class': forms.Select(attrs={'class': 'form-select'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0712345678'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'level', 'annual_fee']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Form 1'}),
            'level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Secondary'}),
            'annual_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'method', 'term', 'year', 'reference', 'notes', 'phone_number']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0712345678'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MpesaPaymentForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Student'
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0712345678'}),
        label='M-Pesa Phone Number'
    )
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
        label='Amount (KES)'
    )
    term = forms.ChoiceField(
        choices=Payment.TERM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Term'
    )

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip().replace('+', '').replace(' ', '')
        if phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        if not phone.startswith('254') or len(phone) != 12:
            raise forms.ValidationError('Enter a valid Kenyan phone number e.g. 0712345678')
        return phone


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['student_class', 'term', 'year', 'tuition', 'activity_fee', 'exam_fee', 'other_fee', 'description']
        widgets = {
            'student_class': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'tuition': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'activity_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'exam_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'other_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
