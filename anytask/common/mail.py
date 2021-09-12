import logging
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_mass_mail_html(messages):
    num_sent = 0
    for message in messages:
        subject, plain_text, html, from_email, emails = message
        try:
            num_sent += send_mail(subject=subject, message=plain_text, from_email=from_email, recipient_list=emails,
                                  html_message=html)
        except Exception:
            logging.exception("Exception while sending mail to '%s' : ", emails)

    return num_sent
