from django.utils import timezone


class TimezoneMiddleware(object):

    def process_request(self, request):
        if request.user.is_authenticated():
            tz = request.session.get('django_timezone', default=request.user.get_profile().time_zone)
            timezone.activate(tz)
        else:
            timezone.deactivate()
