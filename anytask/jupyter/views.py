import logging

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from unidecode import unidecode

from api.views import login_required_basic_auth
from issues.models import Issue, Event, File
from issues.model_issue_field import IssueField
from tasks.models import Task

from users.models import UserProfile


logger = logging.getLogger('django.request')


@csrf_exempt
@login_required_basic_auth
@require_http_methods(['POST'])
def update_jupyter_task(request):
    user = request.user

    assignment_id = request.POST.get('name')
    student_id = request.POST.get('student')
    score = float(request.POST.get('score', 0))
    max_score = float(request.POST.get('max_score', 0))
    # timestamp = request.POST.get('timestamp')
    logger.debug('REQUEST: %r', request.POST)

    if not student_id or not assignment_id:
        return HttpResponseBadRequest()

    try:
        profile = UserProfile.objects.get(ya_passport_login=student_id)
    except UserProfile.DoesNotExist:
        return HttpResponseNotFound('No student found')

    try:
        task = Task.objects.get(type=Task.TYPE_IPYNB, nb_assignment_name=assignment_id)
    except Task.DoesNotExist:
        return HttpResponseNotFound('No task found')

    issue, created = Issue.objects.get_or_create(task=task, student=profile.user)
    issue.set_status_accepted(user)

    if score >= 0:
        if max_score > 0 and max_score >= score:
            score = float(score) / float(max_score) * task.score_max

        try:
            issue.set_byname('mark', round(score, 2))
        except ValueError:
            return HttpResponseBadRequest('Wrong score: {}'.format(score))

    if request.FILES:
        logger.debug('FILES: %r', request.FILES)
        try:
            field = IssueField.objects.get(name='file')
        except IssueField.DoesNotExist:
            return HttpResponseNotFound('No issue field')

        event = Event.objects.create(issue_id=issue.id, author=user, field=field)

        for obj in request.FILES.getlist('files'):
            obj.name = unidecode(obj.name)
            File.objects.create(file=obj, event=event)

    return HttpResponse(status=200)
