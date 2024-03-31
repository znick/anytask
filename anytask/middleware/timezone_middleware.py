from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.user.is_authenticated:
            tz = request.session.get('django_timezone',
                                     default=request.user.profile.time_zone) or settings.TIME_ZONE
            timezone.activate(tz)
        else:
            timezone.deactivate()
