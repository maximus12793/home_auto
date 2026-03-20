from __future__ import annotations

import json

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from maintenance_orchestrator.models.domain import QuoteRecord

Base = declarative_base()


class DBQuote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_correlation_id = Column(String, index=True)
    vendor_id = Column(String, index=True)
    data = Column(Text)


class QuoteStore:
    def list_quotes(self, correlation_id: str) -> list[QuoteRecord]:
        raise NotImplementedError

    def add_quote(self, correlation_id: str, quote: QuoteRecord) -> QuoteRecord:
        raise NotImplementedError


class DatabaseQuoteStore(QuoteStore):
    def __init__(self, db_url: str | None = None) -> None:
        import os
        db_url = db_url or os.getenv("DB_URL", "sqlite:///maintenance.db")
        kwargs = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in db_url:
            from sqlalchemy.pool import StaticPool
            kwargs["poolclass"] = StaticPool
        self.engine = create_engine(db_url, **kwargs)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def list_quotes(self, correlation_id: str) -> list[QuoteRecord]:
        with self.Session() as session:
            db_quotes = session.query(DBQuote).filter_by(request_correlation_id=correlation_id).all()
            return [QuoteRecord.model_validate_json(q.data) for q in db_quotes]

    def add_quote(self, correlation_id: str, quote: QuoteRecord) -> QuoteRecord:
        with self.Session() as session:
            db_quote = DBQuote(
                request_correlation_id=correlation_id,
                vendor_id=quote.vendor_id,
                data=quote.model_dump_json(),
            )
            session.add(db_quote)
            session.commit()
        return quote
