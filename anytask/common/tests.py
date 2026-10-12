# coding: utf-8
from datetime import timedelta

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from common.s3_rollout import effective_t1, effective_t2, ready_to_delete_local, should_serve_from_s3
from storage import S3OverlayStorage


class S3RolloutTest(SimpleTestCase):
    def setUp(self):
        self.now = timezone.now()

    def test_effective_t1_default_delta(self):
        uploaded_at = self.now
        self.assertEqual(effective_t1(uploaded_at), uploaded_at + timedelta(days=210))

    def test_effective_t1_absolute_override_wins(self):
        override = self.now - timedelta(days=1)
        with override_settings(AWS_S3_SERVE_AT=override):
            self.assertEqual(effective_t1(self.now), override)
            self.assertEqual(effective_t1(self.now - timedelta(days=1000)), override)

    def test_effective_t2_relative_to_effective_t1_default(self):
        uploaded_at = self.now
        self.assertEqual(effective_t2(uploaded_at), uploaded_at + timedelta(days=210 + 8))

    def test_effective_t2_tracks_t1_absolute_override(self):
        t1_override = self.now - timedelta(days=100)
        with override_settings(AWS_S3_SERVE_AT=t1_override):
            self.assertEqual(effective_t2(self.now), t1_override + timedelta(days=8))

    def test_effective_t2_absolute_override_independent(self):
        t2_override = self.now - timedelta(days=1)
        with override_settings(AWS_S3_DELETE_LOCAL_AT=t2_override):
            # T1 is still relative-default, but T2 is forced regardless.
            self.assertEqual(effective_t2(self.now), t2_override)

    def test_should_serve_from_s3_none_is_false(self):
        self.assertFalse(should_serve_from_s3(None))

    def test_should_serve_from_s3_before_and_after_t1(self):
        before_t1 = self.now - timedelta(days=209)
        after_t1 = self.now - timedelta(days=211)
        self.assertFalse(should_serve_from_s3(before_t1, now=self.now))
        self.assertTrue(should_serve_from_s3(after_t1, now=self.now))

    def test_ready_to_delete_local_requires_past_t2(self):
        past_t1_not_t2 = self.now - timedelta(days=211)
        past_t2 = self.now - timedelta(days=219)
        self.assertFalse(ready_to_delete_local(past_t1_not_t2, now=self.now))
        self.assertTrue(ready_to_delete_local(past_t2, now=self.now))

    def test_ready_to_delete_local_none_is_false(self):
        self.assertFalse(ready_to_delete_local(None))

    def test_ready_to_delete_local_blocked_without_t1_even_with_t2_override(self):
        t2_override = self.now - timedelta(days=1)
        with override_settings(AWS_S3_DELETE_LOCAL_AT=t2_override):
            # uploaded "now" -> default T1 (210 days) hasn't happened yet,
            # so deletion must stay blocked even though T2 itself is overridden
            # to be in the past.
            self.assertFalse(ready_to_delete_local(self.now, now=self.now))

    def test_round_trip_append_s3_prefix_is_s3_stored(self):
        name = 'files/abc/x.py'
        s3_name = S3OverlayStorage.append_s3_prefix(name)
        self.assertFalse(S3OverlayStorage.is_s3_stored(name))
        self.assertTrue(S3OverlayStorage.is_s3_stored(s3_name))
