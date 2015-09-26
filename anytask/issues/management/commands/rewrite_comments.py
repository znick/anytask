# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.mail import send_mass_mail
from django.contrib.sites.models import Site
from django.conf import settings

from issues.models import Event

import re

class Command(BaseCommand):
    help = "Send notifications via email"

    option_list = BaseCommand.option_list
    def handle(self, **options):

    option_list = BaseCommand.option_list + (
        make_option('--pattern',
            action='store',
            dest='pattern',
            default=None,
            help='pattern'),
        make_option('--replace',
            action='store',
            dest='replace',
            default=None,
            help='replace'),
        make_option('--dry_run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='dry_run'),
        )

        pattern = options['pattern']
        replace = options['replace']
        dry_run = options['dry_run']

        if not pattern:
            raise Exception("--pattern is required!")

        if not replace:
            raise Exception("--replace is required!")

        for event in Event.objects.all():
            print "======= {0} =========".format(event.id)
            print event.value
            print "-----------------------"
            event.value = re.sub(pattern, replace, event.value)
            print event.value
            print "======================="
            if not dry_run:
                event.save()

