# coding: utf-8
from datetime import timedelta

import django.utils.timezone
from django.db import migrations, models

# Legacy File rows migrated under the OLD algorithm (file already
# 'S3/'-prefixed) have no real "uploaded at" timestamp recorded anywhere.
# Backfill a synthetic sentinel safely in the past: default T1 is 210 days,
# default T2 is T1+8 days, plus a 30-day safety margin in case those
# defaults get tuned later. Kept as a literal constant (not read from live
# settings) so this migration stays deterministic regardless of future
# settings changes.
LEGACY_S3_SENTINEL_DELTA = timedelta(days=210 + 8 + 30)  # 248 days


def backfill_create_time(apps, schema_editor):
    File = apps.get_model('issues', 'File')
    db_alias = schema_editor.connection.alias
    rows = []
    for f in File.objects.using(db_alias).select_related('event').iterator():
        if f.event_id is not None:
            f.create_time = f.event.timestamp
            rows.append(f)
    File.objects.using(db_alias).bulk_update(rows, ['create_time'], batch_size=500)


def backfill_s3_uploaded_at(apps, schema_editor):
    File = apps.get_model('issues', 'File')
    db_alias = schema_editor.connection.alias
    sentinel = django.utils.timezone.now() - LEGACY_S3_SENTINEL_DELTA
    File.objects.using(db_alias).filter(file__startswith='S3/').update(s3_uploaded_at=sentinel)


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0011_auto_20251026_2354'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='file',
            name='update_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='file',
            name='s3_uploaded_at',
            field=models.DateTimeField(blank=True, db_index=True, default=None, null=True),
        ),
        migrations.RunPython(backfill_create_time, migrations.RunPython.noop),
        migrations.RunPython(backfill_s3_uploaded_at, migrations.RunPython.noop),
    ]
