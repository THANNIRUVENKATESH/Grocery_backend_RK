import requests
from django.conf import settings

def send_whatsapp_template(phone, params, template_key='register', callback_data='Template Message'):
    """
    Send a WhatsApp template message using Interakt.
    :param phone: str, phone number in format '919999999999'
    :param params: list, parameters for the template (e.g., [otp])
    :param template_key: str, key for the template in settings.INTERAKT_TEMPLATES
    :param callback_data: str, optional callback data for tracking
    :return: bool, True if sent successfully, False otherwise
    """
    template_id = settings.INTERAKT_TEMPLATES.get(template_key)
    headers = {
        'Authorization': f'Bearer {settings.INTERAKT_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "countryCode": phone[:2],
        "phoneNumber": phone[2:],
        "callbackData": callback_data,
        "type": "Template",
        "template": {
            "templateId": template_id,
            "params": params
        }
    }
    try:
        response = requests.post(settings.INTERAKT_URL, json=data, headers=headers)
        response.raise_for_status()
        print(f"WhatsApp message sent: {response.json()}")
        return True
    except Exception as e:
        print(f"Failed to send WhatsApp message via Interakt: {e}")
        return False 