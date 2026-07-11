"""Validated dataclasses for site-data JSON payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


def _require_str(data: dict[str, object], key: str) -> str:
    """Return a required string value, or '' if missing/null."""
    value = data.get(key)
    return '' if value is None else str(value)


def _optional_str(data: dict[str, object], key: str) -> str | None:
    """Return an optional string value, or None if missing/null."""
    value = data.get(key)
    if value is None:
        return None
    result = str(value)
    return result if result else None


@dataclass(frozen=True, slots=True)
class ConsumerStatus:
    """Single-row homepage status panel."""

    headline: str
    continued_use_note: str
    update_note: str
    verification_note: str
    current_as_of: date

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ConsumerStatus:
        """Build a ConsumerStatus from exported JSON, supplying safe defaults."""
        current_as_of_raw = data.get('current_as_of', '2026-07-09')
        try:
            current_as_of = date.fromisoformat(str(current_as_of_raw))
        except (TypeError, ValueError):
            current_as_of = date.fromisoformat('2026-07-09')
        return cls(
            headline=_require_str(data, 'headline'),
            continued_use_note=_require_str(data, 'continued_use_note'),
            update_note=_require_str(data, 'update_note'),
            verification_note=_require_str(data, 'verification_note'),
            current_as_of=current_as_of,
        )


@dataclass(frozen=True, slots=True)
class Alert:
    """Site banner/warning."""

    severity: str
    title: str
    body: str
    cta_label: str | None
    cta_url: str | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Alert:
        return cls(
            severity=_require_str(data, 'severity') or 'notice',
            title=_require_str(data, 'title'),
            body=_require_str(data, 'body'),
            cta_label=_optional_str(data, 'cta_label'),
            cta_url=_optional_str(data, 'cta_url'),
        )


@dataclass(frozen=True, slots=True)
class FAQ:
    """Public FAQ entry."""

    category: str
    question: str
    answer_short: str
    answer_long: str
    source_urls: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> FAQ:
        return cls(
            category=_require_str(data, 'category'),
            question=_require_str(data, 'question'),
            answer_short=_require_str(data, 'answer_short'),
            answer_long=_require_str(data, 'answer_long'),
            source_urls=_require_str(data, 'source_urls'),
        )


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """Regulatory timeline event."""

    event_date: str
    event_type: str
    title: str
    summary: str
    consumer_impact: str
    source_url: str
    source_title: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TimelineEvent:
        return cls(
            event_date=_require_str(data, 'event_date'),
            event_type=_require_str(data, 'event_type'),
            title=_require_str(data, 'title'),
            summary=_require_str(data, 'summary'),
            consumer_impact=_require_str(data, 'consumer_impact'),
            source_url=_require_str(data, 'source_url'),
            source_title=_require_str(data, 'source_title'),
        )


@dataclass(frozen=True, slots=True)
class Waiver:
    """Active/proposed waiver record."""

    waiver_type: str
    party: str
    equipment_scope: str
    effective_start_date: str
    effective_end_date: str
    source_url: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Waiver:
        return cls(
            waiver_type=_require_str(data, 'waiver_type'),
            party=_require_str(data, 'party'),
            equipment_scope=_require_str(data, 'equipment_scope'),
            effective_start_date=_require_str(data, 'effective_start_date'),
            effective_end_date=_optional_str(data, 'effective_end_date') or 'open-ended',
            source_url=_require_str(data, 'source_url'),
        )


@dataclass(frozen=True, slots=True)
class ConditionalApproval:
    """Time-limited Conditional Approval."""

    producer: str
    brand_or_product_family: str
    device_description: str
    approval_start_date: str
    approval_end_date: str
    source_url: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ConditionalApproval:
        return cls(
            producer=_require_str(data, 'producer'),
            brand_or_product_family=_require_str(data, 'brand_or_product_family'),
            device_description=_require_str(data, 'device_description'),
            approval_start_date=_require_str(data, 'approval_start_date'),
            approval_end_date=_optional_str(data, 'approval_end_date') or 'open-ended',
            source_url=_require_str(data, 'source_url'),
        )


@dataclass(frozen=True, slots=True)
class Claim:
    """Myth-check or claim-verdict entry."""

    claim: str
    verdict: str
    explanation: str
    consumer_guidance: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Claim:
        return cls(
            claim=_require_str(data, 'claim'),
            verdict=_require_str(data, 'verdict'),
            explanation=_require_str(data, 'explanation'),
            consumer_guidance=_require_str(data, 'consumer_guidance'),
        )


@dataclass(frozen=True, slots=True)
class PrimarySource:
    """Primary FCC source document reference."""

    title: str
    url: str
    source_type: str
    publication_date: str | None
    summary: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PrimarySource:
        return cls(
            title=_require_str(data, 'title'),
            url=_require_str(data, 'url'),
            source_type=_require_str(data, 'source_type'),
            publication_date=_optional_str(data, 'publication_date'),
            summary=_require_str(data, 'summary'),
        )
