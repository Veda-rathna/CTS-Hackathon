"""SQLAlchemy ORM models for Synthea synthetic healthcare dataset."""
from __future__ import annotations

from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    Numeric,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class SyntheaPatient(Base):
    """Synthea synthetic patient model."""

    __tablename__ = "synthea_patients"

    id = Column(String(64), primary_key=True, index=True)
    birthdate = Column(Date, nullable=True)
    deathdate = Column(Date, nullable=True)
    ssn = Column(String(32), nullable=True)
    drivers = Column(String(32), nullable=True)
    passport = Column(String(32), nullable=True)
    prefix = Column(String(16), nullable=True)
    first = Column(String(64), nullable=True)
    last = Column(String(64), nullable=True)
    suffix = Column(String(16), nullable=True)
    maiden = Column(String(64), nullable=True)
    marital = Column(String(16), nullable=True)
    race = Column(String(32), nullable=True)
    ethnicity = Column(String(32), nullable=True)
    gender = Column(String(8), nullable=True)
    birthplace = Column(String(128), nullable=True)
    address = Column(String(128), nullable=True)
    city = Column(String(64), nullable=True)
    state = Column(String(32), nullable=True)
    zip = Column(String(16), nullable=True)
    lat = Column(Numeric(10, 6), nullable=True)
    lon = Column(Numeric(10, 6), nullable=True)
    healthcare_expenses = Column(Numeric(12, 2), nullable=True)
    healthcare_coverage = Column(Numeric(12, 2), nullable=True)

    # Relationships
    encounters = relationship("SyntheaEncounter", back_populates="patient", cascade="all, delete-orphan")
    conditions = relationship("SyntheaCondition", back_populates="patient", cascade="all, delete-orphan")
    procedures = relationship("SyntheaProcedure", back_populates="patient", cascade="all, delete-orphan")
    observations = relationship("SyntheaObservation", back_populates="patient", cascade="all, delete-orphan")


class SyntheaEncounter(Base):
    """Synthea encounter record."""

    __tablename__ = "synthea_encounters"

    id = Column(String(64), primary_key=True, index=True)
    start_date = Column(DateTime, nullable=True)
    stop_date = Column(DateTime, nullable=True)
    patient_id = Column(String(64), ForeignKey("synthea_patients.id"), nullable=False, index=True)
    organization_id = Column(String(64), nullable=True)
    provider_id = Column(String(64), nullable=True)
    payer_id = Column(String(64), nullable=True)
    encounterclass = Column(String(64), nullable=True)
    code = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)
    base_encounter_cost = Column(Numeric(12, 2), nullable=True)
    total_claim_cost = Column(Numeric(12, 2), nullable=True)
    payer_coverage = Column(Numeric(12, 2), nullable=True)
    reasoncode = Column(String(64), nullable=True)
    reasondescription = Column(Text, nullable=True)

    patient = relationship("SyntheaPatient", back_populates="encounters")


class SyntheaCondition(Base):
    """Synthea diagnosed condition record (ICD-10 / SNOMED)."""

    __tablename__ = "synthea_conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(Date, nullable=True)
    stop_date = Column(Date, nullable=True)
    patient_id = Column(String(64), ForeignKey("synthea_patients.id"), nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    code = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)

    patient = relationship("SyntheaPatient", back_populates="conditions")


class SyntheaProcedure(Base):
    """Synthea medical procedure record (HCPCS / CPT / SNOMED)."""

    __tablename__ = "synthea_procedures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(DateTime, nullable=True)
    stop_date = Column(DateTime, nullable=True)
    patient_id = Column(String(64), ForeignKey("synthea_patients.id"), nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    code = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)
    base_cost = Column(Numeric(12, 2), nullable=True)
    reasoncode = Column(String(64), nullable=True)
    reasondescription = Column(Text, nullable=True)

    patient = relationship("SyntheaPatient", back_populates="procedures")


class SyntheaObservation(Base):
    """Synthea clinical observation / lab measurement."""

    __tablename__ = "synthea_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=True)
    patient_id = Column(String(64), ForeignKey("synthea_patients.id"), nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    category = Column(String(64), nullable=True)
    code = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)
    value = Column(Text, nullable=True)
    units = Column(String(32), nullable=True)
    type = Column(String(32), nullable=True)

    patient = relationship("SyntheaPatient", back_populates="observations")


class SyntheaPARequest(Base):
    """Pre-built Prior Authorization Request generated from Synthea patient records."""

    __tablename__ = "synthea_pa_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pa_request_id = Column(String(64), unique=True, index=True)
    patient_id = Column(String(64), nullable=False)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(8), nullable=True)
    patient_state = Column(String(32), nullable=True)
    procedure_code = Column(String(64), nullable=False, index=True)
    procedure_description = Column(Text, nullable=True)
    diagnosis_code = Column(String(64), nullable=True, index=True)
    diagnosis_description = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    review_type = Column(String(32), default="NON_URGENT")
