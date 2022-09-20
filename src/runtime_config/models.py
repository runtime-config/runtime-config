from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression

from runtime_config.enums.settings import ValueType

Base = declarative_base()
metadata = Base.metadata  # type: ignore


class Setting(Base):  # type: ignore
    __tablename__ = 'setting'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    value = Column(Text)
    value_type = Column(Enum(ValueType), nullable=False)
    disable = Column(Boolean, server_default=expression.false(), nullable=False)
    service_name = Column(Text, nullable=False)
    created_by_db_user = Column(Text)
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (UniqueConstraint('name', 'service_name', name='unique_setting_name_per_service'),)


class SettingHistory(Base):  # type: ignore
    __tablename__ = 'setting_history'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    value = Column(Text)
    value_type = Column(Enum(ValueType), nullable=False)
    disable = Column(Boolean, nullable=False)
    service_name = Column(Text, nullable=False)
    created_by_db_user = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, server_default=expression.false(), nullable=False)
    deleted_by_db_user = Column(Text)
