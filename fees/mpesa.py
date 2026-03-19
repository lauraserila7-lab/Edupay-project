"""
mpesa.py — Safaricom Daraja API helper for EduPay
Handles: OAuth token, STK Push (LipaNaMpesa), Callback processing
"""
import base64
import json
import logging
import requests
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


def get_mpesa_access_token():
    """Fetch OAuth token from Daraja API."""
    if settings.MPESA_ENVIRONMENT == 'production':
        base_url = 'https://api.safaricom.co.ke'
    else:
        base_url = 'https://sandbox.safaricom.co.ke'

    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode('utf-8')

    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Basic {encoded}"},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.RequestException as e:
        logger.error(f"M-Pesa token error: {e}")
        return None


def generate_password():
    """Generate base64 encoded password for STK push."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode('utf-8')
    return password, timestamp


def stk_push(phone_number, amount, account_reference, transaction_desc):
    """
    Initiate Lipa Na M-Pesa STK Push.

    Args:
        phone_number (str): Customer phone e.g. '2547XXXXXXXX'
        amount (int/float): Amount to charge
        account_reference (str): e.g. Student admission number
        transaction_desc (str): Short description

    Returns:
        dict: Daraja API response or error dict
    """
    if settings.MPESA_ENVIRONMENT == 'production':
        base_url = 'https://api.safaricom.co.ke'
    else:
        base_url = 'https://sandbox.safaricom.co.ke'

    token = get_mpesa_access_token()
    if not token:
        return {'error': True, 'message': 'Could not get M-Pesa access token'}

    password, timestamp = generate_password()

    # Normalize phone number to 2547XXXXXXXX format
    phone = str(phone_number).strip().replace('+', '')
    if phone.startswith('07') or phone.startswith('01'):
        phone = '254' + phone[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference[:12],
        "TransactionDesc": transaction_desc[:13],
    }

    url = f"{base_url}/mpesa/stkpush/v1/processrequest"
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30
        )
        data = response.json()
        logger.info(f"STK Push response: {data}")
        return data
    except requests.RequestException as e:
        logger.error(f"STK Push error: {e}")
        return {'error': True, 'message': str(e)}


def process_mpesa_callback(callback_data):
    """
    Parse and process the M-Pesa STK Push callback.

    Args:
        callback_data (dict): Raw JSON from Safaricom callback

    Returns:
        dict: Parsed result with keys: success, checkout_id, receipt, amount, phone
    """
    try:
        stk_callback = callback_data['Body']['stkCallback']
        result_code = stk_callback['ResultCode']
        result_desc = stk_callback['ResultDesc']
        checkout_id = stk_callback['CheckoutRequestID']

        if result_code != 0:
            return {
                'success': False,
                'checkout_id': checkout_id,
                'result_code': result_code,
                'message': result_desc,
            }

        # Extract metadata items
        items = stk_callback['CallbackMetadata']['Item']
        meta = {item['Name']: item.get('Value') for item in items}

        return {
            'success': True,
            'checkout_id': checkout_id,
            'receipt': meta.get('MpesaReceiptNumber', ''),
            'amount': meta.get('Amount', 0),
            'phone': str(meta.get('PhoneNumber', '')),
            'transaction_date': meta.get('TransactionDate', ''),
            'result_code': result_code,
            'message': result_desc,
        }
    except (KeyError, TypeError) as e:
        logger.error(f"Callback parse error: {e}")
        return {'success': False, 'message': f'Callback parse error: {e}'}
