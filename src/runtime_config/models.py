from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression, func

from runtime_config.enums.settings import ValueType
from runtime_config.enums.token import TokenType
from runtime_config.enums.user import UserRole

Base = declarative_base()
metadata = Base.metadata  # type: ignore[attr-defined]


class Setting(Base):  # type: ignore[valid-type, misc]
    __tablename__ = 'setting'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    value = Column(Text)
    value_type = Column(Enum(ValueType), nullable=False)
    is_disabled = Column(Boolean, server_default=expression.false(), nullable=False)
    service_name_id = Column(Integer, ForeignKey('service_name.id'), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey('user.id'))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint('name', 'service_name_id', name='unique_setting_name_per_service'),)


class ServiceName(Base):  # type: ignore[valid-type, misc]
    __tablename__ = 'service_name'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    is_archived = Column(Boolean, server_default=expression.false(), nullable=False)


class SettingHistory(Base):  # type: ignore[valid-type, misc]
    __tablename__ = 'setting_history'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    value = Column(Text)
    value_type = Column(Enum(ValueType), nullable=False)
    is_disabled = Column(Boolean, nullable=False)
    service_name_id = Column(Integer, ForeignKey('service_name.id'), nullable=False)
    updated_at = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, server_default=expression.false(), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey('user.id'))
    deleted_by_user_id = Column(Integer, ForeignKey('user.id'))


class User(Base):  # type: ignore[valid-type, misc]
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    full_name = Column(Text)
    email = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, server_default=expression.false(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    is_archived = Column(Boolean, server_default=expression.false(), nullable=False)


class Token(Base):  # type: ignore[valid-type, misc]
    __tablename__ = 'token'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    token = Column(Text, nullable=False, unique=True)
    type = Column(Enum(TokenType), nullable=False)
