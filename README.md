# 🎓 EduPay — School Fee Management System

A Django web application that solves the problem of manual, cash-based school fee management in Kenyan schools. EduPay enables digital fee collection including **M-Pesa STK Push** payments, full student management, and real-time fee tracking.

---

## 🔴 Problem Being Solved

Many private and community schools in Kenya manage fee payments manually — cash, handwritten receipts, and Excel sheets. This leads to:
- Lost or forged payment records
- No real-time fee balance tracking for parents or admin
- Difficult fee follow-up and defaulter identification
- No digital payment option, requiring parents to physically visit school

## ✅ Solution

EduPay provides:
- A centralised digital fee management dashboard
- M-Pesa STK Push (parents pay from their phone without visiting school)
- Real-time fee balance and defaulter reports
- Full CRUD for Students, Classes, Payments, and Fee Structures

---

## ✅ Checkpoints

| Checkpoint | Status | Details |
|---|---|---|
| CRUD Operations | ✅ | Students, Classes, Payments, Fee Structures — full Create/Read/Update/Delete |
| M-Pesa Integration | ✅ | Safaricom Daraja API — STK Push + Callback handler |
| Good UI | ✅ | Bootstrap 5, sidebar layout, charts, responsive |
| Real Problem | ✅ | Fee management chaos in Kenyan schools |

---

## 🏗️ Project Structure

```
edupay/
├── edupay/                  # Django project config
│   ├── settings.py          # All settings including M-Pesa config
│   ├── urls.py
│   └── wsgi.py
├── fees/                    # Main app
│   ├── models.py            # Student, Class, Payment, FeeStructure, MpesaCallback
│   ├── views.py             # All CRUD + M-Pesa views
│   ├── forms.py             # All Django forms
│   ├── mpesa.py             # Daraja API helper (token, STK push, callback)
│   ├── urls.py              # All URL patterns
│   ├── admin.py             # Django admin registrations
│   └── templates/fees/      # All HTML templates
│       ├── dashboard.html
│       ├── student_list.html
│       ├── student_detail.html
│       ├── student_form.html
│       ├── payment_list.html
│       ├── payment_form.html
│       ├── mpesa_pay.html
│       ├── class_list.html
│       ├── class_form.html
│       ├── fee_structure_list.html
│       ├── fee_structure_form.html
│       ├── defaulters.html
│       └── confirm_delete.html
├── templates/
│   ├── base.html            # Sidebar layout base
│   └── login.html           # Login page
├── requirements.txt
└── manage.py
```

---

## 🚀 Setup & Installation

### 1. Clone / Extract the project
```bash
cd edupay
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create admin user
```bash
python manage.py createsuperuser
```

### 6. Run the development server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000** — Login with your superuser credentials.

---

## 📱 M-Pesa Integration Setup

EduPay uses the **Safaricom Daraja API** for M-Pesa STK Push (Lipa Na M-Pesa Online).

### Step 1: Get Daraja API credentials
1. Go to [https://developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. Create an account and log in
3. Go to **My Apps** → Create a new app
4. Enable **Lipa Na M-Pesa Sandbox**
5. Copy your **Consumer Key** and **Consumer Secret**

### Step 2: Configure settings.py
```python
# edupay/settings.py

MPESA_ENVIRONMENT = 'sandbox'           # 'sandbox' or 'production'
MPESA_CONSUMER_KEY = 'your-key-here'
MPESA_CONSUMER_SECRET = 'your-secret-here'
MPESA_SHORTCODE = '174379'              # Sandbox test shortcode
MPESA_PASSKEY = 'your-passkey-here'    # From Daraja portal (Lipa Na M-Pesa tab)
MPESA_CALLBACK_URL = 'https://yourdomain.com/mpesa/callback/'
```

### Step 3: Expose callback URL (for testing)
Use **ngrok** to expose your local server:
```bash
ngrok http 8000
```
Then set `MPESA_CALLBACK_URL` to: `https://YOUR-NGROK-URL.ngrok.io/mpesa/callback/`

### Sandbox Test Credentials
- Shortcode: `174379`
- Test Phone: Any format `0712345678`
- In sandbox, no real money is deducted

### How STK Push Works
1. Admin enters student, phone number, and amount on `/mpesa/pay/`
2. EduPay calls Daraja API → Safaricom sends STK Pop-up to parent's phone
3. Parent enters M-Pesa PIN
4. Safaricom sends callback to `/mpesa/callback/`
5. EduPay updates the payment record to `completed` automatically

---

## 📋 Key URLs

| URL | Description |
|---|---|
| `/` | Dashboard |
| `/students/` | Student list |
| `/students/add/` | Add student |
| `/students/<id>/` | Student profile + payment history |
| `/payments/` | All payments |
| `/payments/add/` | Record manual payment |
| `/mpesa/pay/` | M-Pesa STK Push |
| `/mpesa/callback/` | Daraja callback (POST, csrf-exempt) |
| `/classes/` | Class management |
| `/fee-structure/` | Fee structure per class/term |
| `/reports/defaulters/` | Fee defaulters report |
| `/admin/` | Django admin panel |
| `/login/` | Login page |

---

## 🛠️ Tech Stack

- **Backend**: Django 4.2 (Python)
- **Database**: SQLite (dev) — easily switch to PostgreSQL
- **Frontend**: Bootstrap 5 + Bootstrap Icons + Chart.js
- **Fonts**: Plus Jakarta Sans (Google Fonts)
- **Payments**: Safaricom Daraja API (M-Pesa STK Push)
- **Auth**: Django built-in authentication

---

## 🔒 Going to Production

1. Change `DEBUG = False` and set a real `SECRET_KEY`
2. Switch to PostgreSQL
3. Set `MPESA_ENVIRONMENT = 'production'`
4. Use real Daraja production credentials
5. Set a real `MPESA_CALLBACK_URL` (must be HTTPS)
6. Run `python manage.py collectstatic`

---

*Built with Django · EduPay © 2024*
# Edupay-project
