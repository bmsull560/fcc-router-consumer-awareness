"""Tests for typed site-data models."""

from __future__ import annotations

import unittest
from datetime import date

from scripts.models import (
    FAQ,
    Alert,
    Claim,
    ConditionalApproval,
    ConsumerStatus,
    PrimarySource,
    TimelineEvent,
    Waiver,
)


class TestModels(unittest.TestCase):
    def test_consumer_status_defaults(self) -> None:
        status = ConsumerStatus.from_dict({})
        self.assertEqual(status.headline, '')
        self.assertEqual(status.current_as_of, date.fromisoformat('2026-07-09'))

    def test_consumer_status_parses_date(self) -> None:
        status = ConsumerStatus.from_dict({'current_as_of': '2026-12-25'})
        self.assertEqual(status.current_as_of, date.fromisoformat('2026-12-25'))

    def test_consumer_status_falls_back_on_bad_date(self) -> None:
        status = ConsumerStatus.from_dict({'current_as_of': 'not-a-date'})
        self.assertEqual(status.current_as_of, date.fromisoformat('2026-07-09'))

    def test_alert_defaults(self) -> None:
        alert = Alert.from_dict({})
        self.assertEqual(alert.severity, 'notice')
        self.assertIsNone(alert.cta_url)
        self.assertIsNone(alert.cta_label)

    def test_alert_parses(self) -> None:
        alert = Alert.from_dict(
            {
                'severity': 'warning',
                'title': 'Title',
                'body': 'Body',
                'cta_label': 'Read',
                'cta_url': 'https://example.com/',
            }
        )
        self.assertEqual(alert.severity, 'warning')
        self.assertEqual(alert.cta_url, 'https://example.com/')
        self.assertEqual(alert.cta_label, 'Read')

    def test_faq_parses(self) -> None:
        faq = FAQ.from_dict(
            {
                'category': 'Basics',
                'question': 'Q?',
                'answer_short': 'A short',
                'answer_long': 'A long',
                'source_urls': 'https://a | https://b',
            }
        )
        self.assertEqual(faq.category, 'Basics')
        self.assertEqual(faq.source_urls, 'https://a | https://b')

    def test_timeline_event_parses(self) -> None:
        event = TimelineEvent.from_dict(
            {
                'event_date': '2026-07-09',
                'event_type': 'rulemaking',
                'title': 'Title',
                'summary': 'Summary',
                'consumer_impact': 'Impact',
                'source_url': 'https://example.com/',
                'source_title': 'Source',
            }
        )
        self.assertEqual(event.event_date, '2026-07-09')
        self.assertEqual(event.source_url, 'https://example.com/')

    def test_waiver_open_ended_default(self) -> None:
        waiver = Waiver.from_dict(
            {
                'waiver_type': 'SW',
                'party': 'Party',
                'equipment_scope': 'Routers',
                'source_url': 'https://example.com/',
            }
        )
        self.assertEqual(waiver.effective_end_date, 'open-ended')
        self.assertEqual(waiver.effective_start_date, '')

    def test_conditional_approval_open_ended_default(self) -> None:
        approval = ConditionalApproval.from_dict(
            {
                'producer': 'Producer',
                'brand_or_product_family': 'Family',
                'device_description': 'Device',
                'source_url': 'https://example.com/',
            }
        )
        self.assertEqual(approval.approval_end_date, 'open-ended')

    def test_claim_parses(self) -> None:
        claim = Claim.from_dict(
            {
                'claim': 'All routers are banned',
                'verdict': 'false',
                'explanation': 'No',
                'consumer_guidance': 'Check',
            }
        )
        self.assertEqual(claim.verdict, 'false')

    def test_primary_source_optional_date(self) -> None:
        source = PrimarySource.from_dict(
            {'title': 'Title', 'url': 'https://example.com/', 'source_type': 'PDF'}
        )
        self.assertIsNone(source.publication_date)
        self.assertEqual(source.summary, '')

    def test_primary_source_with_date(self) -> None:
        source = PrimarySource.from_dict(
            {
                'title': 'Title',
                'url': 'https://example.com/',
                'source_type': 'PDF',
                'publication_date': '2026-07-09',
                'summary': 'Summary',
            }
        )
        self.assertEqual(source.publication_date, '2026-07-09')


if __name__ == '__main__':
    raise SystemExit(unittest.main())
