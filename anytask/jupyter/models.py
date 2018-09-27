import logging

from django.utils.text import slugify
from django.conf import settings

from django.db.models.signals import post_save, post_delete
from anytask.tasks.models import Task

from .client import get_or_create_assignment, delete_assignment

logger = logging.getLogger(__name__)


def get_assignment_name(instance):
    return '{}-{}'.format(instance.pk, slugify(instance.short_title))


def create_nbgrader_assignment(sender, instance, created, **kwargs):
    logger.info('create nbgrader assignment for task: %s', instance)

    if not created or not instance.type == Task.TYPE_IPYNB:
        return

    assignment = get_or_create_assignment(name=instance.nb_assignment_name)
    logger.debug('ASSIGNMENT: %r', assignment)
    logger.info('nbgrader assignment "%s" has been created: task_id=%d', instance.nb_assignment_name, instance.pk)


def delete_nbgrader_assignment(sender, instance, **kwargs):
    logger.info('delete nbgrader assignment for task: %s', instance)

    if not instance.type == Task.TYPE_IPYNB:
        return

    info = delete_assignment(name=instance.nb_assignment_name)
    logger.debug('DELETED: %r', info)


if not getattr(settings, 'JUPYTER_NBGRADER_DISABLED', False):
    post_save.connect(create_nbgrader_assignment, sender=Task)
    post_delete.connect(delete_nbgrader_assignment, sender=Task)
