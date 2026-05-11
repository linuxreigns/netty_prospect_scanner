from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)  # queued|running|retry|done|error

    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=2)

    discovered_count: Mapped[int] = mapped_column(Integer, default=0)
    scanned_count: Mapped[int] = mapped_column(Integer, default=0)
    saved_count: Mapped[int] = mapped_column(Integer, default=0)
    hot_count: Mapped[int] = mapped_column(Integer, default=0)

    phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prospect_id: Mapped[int | None] = mapped_column(
        ForeignKey("prospects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pipeline_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("pipeline_jobs.job_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rubro: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    provincia: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    ok: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    classification: Mapped[str] = mapped_column(String(20), default="LOW", index=True)

    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposal_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    prospect: Mapped["Prospect | None"] = relationship("Prospect", lazy="joined")
    pipeline_job: Mapped["PipelineJob | None"] = relationship("PipelineJob", lazy="joined")

    traces: Mapped[list["AgentTrace"]] = relationship(
        "AgentTrace",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="traces")


class CommercialQueueAuditEvent(Base):
    __tablename__ = "commercial_queue_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    queue_item_id: Mapped[str] = mapped_column(
        ForeignKey("commercial_queue_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # create|approve|reject|bulk_approve|bulk_reject
    actor: Mapped[str] = mapped_column(String(120), nullable=False, default="system")
    previous_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)


class CommercialQueueItem(Base):
    __tablename__ = "commercial_queue_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # email|whatsapp
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id", ondelete="CASCADE"), index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending|approved|rejected|sent
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    prospect: Mapped["Prospect"] = relationship("Prospect", lazy="joined")
    audit_events: Mapped[list["CommercialQueueAuditEvent"]] = relationship(
        "CommercialQueueAuditEvent",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class Prospect(Base):
    __tablename__ = "prospects"
    __table_args__ = (UniqueConstraint("domain", name="uq_prospect_domain"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rubro: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    provincia: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Estado técnico
    http_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    ssl_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    cms: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    ecommerce_platform: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    frontend_stack: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    has_chatbot: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    chatbot_vendor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    has_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    has_contact_form: Mapped[bool] = mapped_column(Boolean, default=False)
    has_email: Mapped[bool] = mapped_column(Boolean, default=False)
    has_phone: Mapped[bool] = mapped_column(Boolean, default=False)
    has_facebook: Mapped[bool] = mapped_column(Boolean, default=False)
    has_instagram: Mapped[bool] = mapped_column(Boolean, default=False)
    has_contact_page: Mapped[bool] = mapped_column(Boolean, default=False)
    has_products_or_cart: Mapped[bool] = mapped_column(Boolean, default=False)
    looks_outdated: Mapped[bool] = mapped_column(Boolean, default=False)
    has_clear_cta: Mapped[bool] = mapped_column(Boolean, default=False)

    netty_fit_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    fit_classification: Mapped[str] = mapped_column(String(20), default="Bajo", index=True)
    score_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
