from mailjet_rest import Client
from src.config import MAILJET_API_KEY, MAILJET_FROM_EMAIL, MAILJET_SECRET_KEY


def send_mail(
    subject: str,
    text: str,
    to_send_to: list[str],
    to_send_from: str = MAILJET_FROM_EMAIL,
) -> None:
    mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version='v3.1')
    data = {
        'Messages': [
            {
                'From': {'Email': to_send_from, 'Name': 'Me'},
                'To': [{'Email': mail, 'Name': 'You'} for mail in to_send_to],
                'Subject': subject,
                'TextPart': text,
            }
        ]
    }
    result = mailjet.send.create(data=data)
    if result.status_code == 200:
        print('Mail sent successfully')
    else:
        print(result.status_code)
        print(result.json())
