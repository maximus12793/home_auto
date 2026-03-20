from __future__ import annotations

import json
from collections.abc import Callable, Iterable

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from maintenance_orchestrator.audit.log import AuditLog
from maintenance_orchestrator.models.domain import AuditEvent, MaintenanceRequest
from maintenance_orchestrator.store.memory import RequestStore

Base = declarative_base()


class DBRequest(Base):
    __tablename__ = "requests"
    correlation_id = Column(String, primary_key=True)
    portfolio_id = Column(String, index=True)
    data = Column(Text)


class DBAudit(Base):
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_correlation_id = Column(String, index=True)
    data = Column(Text)


class DatabaseRequestStore(RequestStore):
    def __init__(self, db_url: str | None = None) -> None:
        import os
        db_url = db_url or os.getenv("DB_URL", "sqlite:///maintenance.db")
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def put(self, req: MaintenanceRequest) -> MaintenanceRequest:
        with self.Session() as session:
            db_req = DBRequest(
                correlation_id=req.correlation_id,
                portfolio_id=req.portfolio_id,
                data=req.model_dump_json()
            )
            session.merge(db_req)
            session.commit()
        return req

    def get(self, correlation_id: str) -> MaintenanceRequest | None:
        with self.Session() as session:
            db_req = session.query(DBRequest).filter_by(correlation_id=correlation_id).first()
            if db_req:
                return MaintenanceRequest.model_validate_json(db_req.data)
        return None

    def list_portfolio(self, portfolio_id: str) -> list[MaintenanceRequest]:
        with self.Session() as session:
            db_reqs = session.query(DBRequest).filter_by(portfolio_id=portfolio_id).all()
            return [MaintenanceRequest.model_validate_json(r.data) for r in db_reqs]

    def update(
        self, correlation_id: str, mutator: Callable[[MaintenanceRequest], MaintenanceRequest]
    ) -> MaintenanceRequest | None:
        with self.Session() as session:
            db_req = session.query(DBRequest).filter_by(correlation_id=correlation_id).first()
            if not db_req:
                return None
            req = MaintenanceRequest.model_validate_json(db_req.data)
            updated = mutator(req)
            db_req.data = updated.model_dump_json()
            db_req.portfolio_id = updated.portfolio_id
            session.commit()
            return updated

    def all_ids(self) -> Iterable[str]:
        with self.Session() as session:
            return [r.correlation_id for r in session.query(DBRequest.correlation_id).all()]


class DatabaseAuditLog(AuditLog):
    def __init__(self, db_url: str | None = None) -> None:
        import os
        db_url = db_url or os.getenv("DB_URL", "sqlite:///maintenance.db")
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def append(self, event: AuditEvent) -> AuditEvent:
        with self.Session() as session:
            db_audit = DBAudit(
                request_correlation_id=event.request_correlation_id,
                data=event.model_dump_json()
            )
            session.add(db_audit)
            session.commit()
        return event

    def for_request(self, correlation_id: str) -> list[AuditEvent]:
        with self.Session() as session:
            db_audits = session.query(DBAudit).filter_by(request_correlation_id=correlation_id).all()
            return [AuditEvent.model_validate_json(a.data) for a in db_audits]
