from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings


class BCCEmailBackend(EmailBackend):
    def _send(self, email_message):
        bcc_email = getattr(settings, 'EMAIL_DEFAULT_BCC')
        if bcc_email and not email_message.bcc:
            email_message.bcc = [bcc_email]

        super(BCCEmailBackend, self)._send(email_message)
