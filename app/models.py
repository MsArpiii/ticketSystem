from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(default='user')

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    severity: Mapped[str] = mapped_column(default='Low')
    status: Mapped[str] = mapped_column(default='Open')
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    creator_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('users.id'), nullable=True)
    attachment_filename: Mapped[Optional[str]] = mapped_column(nullable=True)
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    is_sla_breached: Mapped[bool] = mapped_column(default=False)
    
    creator = db.relationship('User', foreign_keys=[creator_id])
    assigned_user = db.relationship('User', foreign_keys=[assigned_to_id])

class TicketHistory(db.Model):
    __tablename__ = 'ticket_history'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(db.ForeignKey('tickets.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    action: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[str] = mapped_column(default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    ticket = db.relationship('Ticket', backref=db.backref('history', lazy=True))
    user = db.relationship('User')

class TicketAuditLog(db.Model):
    __tablename__ = 'ticket_audit_log'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(db.ForeignKey('tickets.id'), nullable=False)
    changed_by_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    old_status: Mapped[str] = mapped_column(nullable=False)
    new_status: Mapped[str] = mapped_column(nullable=False)
    action_note: Mapped[Optional[str]] = mapped_column(nullable=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)

    ticket = db.relationship('Ticket')
    changed_by = db.relationship('User')
