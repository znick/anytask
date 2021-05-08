from mail.base import BaseRenderer, BaseSender

import logging


logger = logging.getLogger('anytelegram')


class TelegramRenderer(BaseRenderer):
    def render_notification(self, user_profile, unread_messages):
        return 'Rendered notifications stub'

    def render_fulltext(self, message, recipients):
        return 'Rendered fulltext stub'


class TelegramSender(BaseSender):
    def mass_send(self, prepared_messages):
        logger.info('TelegramSender.mass_send stub:', prepared_messages)
        return 0
