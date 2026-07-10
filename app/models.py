"""Pydantic response models for the FastAPI application."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool


class ReadyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str


class StatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    headline: str | None = None
    continued_use_note: str | None = None
    update_note: str | None = None
    verification_note: str | None = None
    current_as_of: str | None = None


class FAQResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    category: str | None = None
    question: str | None = None
    answer_short: str | None = None
    answer_long: str | None = None
    source_urls: str | None = None


class TimelineResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    event_date: str | None = None
    title: str | None = None
    event_type: str | None = None
    summary: str | None = None
    consumer_impact: str | None = None
    source_url: str | None = None
    source_title: str | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    severity: str | None = None
    title: str | None = None
    body: str | None = None
    cta_label: str | None = None
    cta_url: str | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_key: str | None = None
    title: str | None = None
    url: str | None = None
    publication_date: str | None = None
    source_type: str | None = None
    summary: str | None = None


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    table_name: str | None = None
    row_id: int | None = None
    title: str | None = None
    snippet: str | None = None
