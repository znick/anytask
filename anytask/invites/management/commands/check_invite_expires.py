#!/usr/bin/python
from django.core.management.base import BaseCommand, CommandError
import datetime
from django.db.models import Q
from django.conf import settings

from invites.models import Invite

class Command(BaseCommand):
    help = 'Invite clenup'

    def handle(self, *args, **options):
        invite_expired_date = datetime.datetime.now() - datetime.timedelta(days=settings.INVITE_EXPIRED_DAYS)
        invites_to_delete = []
        for invite in Invite.objects.filter(invited_user=None).filter(added_time__lt = invite_expired_date):
            print invite
            invites_to_delete.append(invite)

        for invite in invites_to_delete:
            invite.delete()
