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
    creator_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('users.id'), nullable=True)
    
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
