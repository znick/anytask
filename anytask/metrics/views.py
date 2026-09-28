# -*- coding: utf-8 -*-

import os
from datetime import timedelta

from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest, multiprocess
from prometheus_client.core import GaugeMetricFamily

from anycontest.models import ContestSubmission

# (label, older than, newer than)
SUBMISSION_AGES = (
    ('lt_30m', None, timedelta(minutes=30)),
    ('30m_1d', timedelta(minutes=30), timedelta(days=1)),
    ('1d_7d', timedelta(days=1), timedelta(days=7)),
    ('gt_7d', timedelta(days=7), None),
)

NO_SEND_ERROR = Q(send_error__isnull=True) | Q(send_error='')
NO_RUN_ID = Q(run_id__isnull=True) | Q(run_id='')

SUBMISSION_STATES = (
    # sent to Contest, check_contest polls these for a verdict
    ('waiting', NO_SEND_ERROR & ~NO_RUN_ID),
    # Contest rejected the submission, it will never get a verdict
    ('send_error', ~NO_SEND_ERROR),
    # not sent to Contest (yet)
    ('not_sent', NO_SEND_ERROR & NO_RUN_ID),
)


class ContestSubmissionsCollector(object):
    """Computed from the DB on every scrape, so it's the same whichever uwsgi worker serves /metrics."""

    def collect(self):
        now = timezone.now()
        counts = {}
        for state, state_q in SUBMISSION_STATES:
            for age, older_than, newer_than in SUBMISSION_AGES:
                q = state_q
                if older_than is not None:
                    q &= Q(create_time__lte=now - older_than)
                if newer_than is not None:
                    q &= Q(create_time__gt=now - newer_than)
                counts[(state, age)] = Count('id', filter=q)

        values = ContestSubmission.objects.filter(got_verdict=False).aggregate(
            **{'{}__{}'.format(*key): count for key, count in counts.items()})

        metric = GaugeMetricFamily('anytask_contest_submissions_without_verdict',
                                   'Contest submissions without a verdict, by state and age.',
                                   labels=['state', 'age'])
        for state, age in counts:
            metric.add_metric([state, age], values['{}__{}'.format(state, age)])
        yield metric


# auto_describe=False: don't query the DB at registration (import) time
db_registry = CollectorRegistry(auto_describe=False)
db_registry.register(ContestSubmissionsCollector())


@require_GET
def metrics(request):
    # uwsgi runs several worker processes: in multiprocess mode prometheus_client keeps each worker's
    # values in PROMETHEUS_MULTIPROC_DIR and sums them up here, otherwise only this process's are seen
    if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        registry = REGISTRY
    return HttpResponse(generate_latest(registry) + generate_latest(db_registry), content_type=CONTENT_TYPE_LATEST)
