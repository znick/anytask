from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import logging

logger = logging.getLogger('django.request')


@csrf_exempt
@require_POST
def webhook(token):
    logger.info('anytelegram webhook stub: token=%s', token)
