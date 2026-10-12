# coding: utf-8
"""Pure logic for the issues.File S3 rollout.

T1 - from this point on, anytask serves the S3 link for a file instead of
     the local one (see issues.models.File.get_url).
T2 - from this point on, the s3migrate_issue_attachments management command
     may flip File.file.name to the S3 path and delete the local copy.

No I/O, no model imports - kept deliberately pure so it's cheap to unit test.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone


def effective_t1(uploaded_at):
    """:param uploaded_at: aware datetime - File.s3_uploaded_at (caller
        must ensure it is not None).
    :return: aware datetime - the absolute AWS_S3_SERVE_AT override if set,
        else uploaded_at + AWS_S3_SERVE_DELAY_DAYS.
    """
    override = getattr(settings, 'AWS_S3_SERVE_AT', None)
    if override is not None:
        return override
    delay_days = getattr(settings, 'AWS_S3_SERVE_DELAY_DAYS', 210)
    return uploaded_at + timedelta(days=delay_days)


def effective_t2(uploaded_at):
    """:return: aware datetime - the absolute AWS_S3_DELETE_LOCAL_AT
        override if set, else effective_t1(uploaded_at) +
        AWS_S3_DELETE_LOCAL_DELAY_DAYS. Deliberately computed from the
        *effective* T1 (so a T1 absolute override also shifts the
        relative-default T2), not from uploaded_at directly.
    """
    override = getattr(settings, 'AWS_S3_DELETE_LOCAL_AT', None)
    if override is not None:
        return override
    delay_days = getattr(settings, 'AWS_S3_DELETE_LOCAL_DELAY_DAYS', 8)
    return effective_t1(uploaded_at) + timedelta(days=delay_days)


def should_serve_from_s3(uploaded_at, now=None):
    """:param uploaded_at: File.s3_uploaded_at value, may be None.
    :param now: aware datetime, defaults to timezone.now(); exposed only so
        callers (tests) can simulate elapsed time without mocking
        timezone.now() globally.
    """
    if uploaded_at is None:
        return False
    now = now if now is not None else timezone.now()
    return now >= effective_t1(uploaded_at)


def ready_to_delete_local(uploaded_at, now=None):
    """Defensive invariant: never ready to delete the local copy unless
    should_serve_from_s3 is independently already True for this file, even
    though T2 >= T1 by construction in sane configurations.
    """
    if uploaded_at is None:
        return False
    now = now if now is not None else timezone.now()
    return should_serve_from_s3(uploaded_at, now=now) and now >= effective_t2(uploaded_at)
