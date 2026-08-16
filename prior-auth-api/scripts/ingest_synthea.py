"""Ingest and Process Synthea Synthetic Data into PostgreSQL Database.

Reads CSV files from 'synthea_sample_data_csv_latest', creates the ORM tables,
populates Patients, Encounters, Conditions, Procedures, and Observations,
and synthesizes a ready-to-query Prior Authorization Requests table (synthea_pa_requests).

Usage:
    python scripts/ingest_synthea.py
"""
from __future__ import annotations

import csv
from datetime import datetime, date
import os
import sys
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from app.models.base import Base
import app.models  # Registers all ORM models including Synthea
from app.models.synthea import (
    SyntheaPatient,
    SyntheaEncounter,
    SyntheaCondition,
    SyntheaProcedure,
    SyntheaObservation,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_synthea")

# Locate Synthea folder (support workspace root or relative path)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNTHEA_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), "synthea_sample_data_csv_latest")
if not os.path.exists(SYNTHEA_DIR):
    SYNTHEA_DIR = os.path.join(PROJECT_ROOT, "synthea_sample_data_csv_latest")

BATCH_SIZE = 1000


def parse_date(date_str: str | None) -> date | None:
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip()[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def parse_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str or not dt_str.strip():
        return None
    try:
        clean = dt_str.strip().rstrip("Z")
        if "T" in clean:
            return datetime.fromisoformat(clean)
        return datetime.strptime(clean[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.strptime(clean[:10], "%Y-%m-%d")
        except Exception:
            return None


def parse_float(val: str | None) -> float | None:
    if not val or not val.strip():
        return None
    try:
        return float(val.strip())
    except Exception:
        return None


def parse_int(val: str | None) -> int | None:
    if not val or not val.strip():
        return None
    try:
        return int(float(val.strip()))
    except Exception:
        return None


def ingest_patients(session: Session, filepath: str) -> int:
    logger.info("Ingesting patients from %s...", filepath)
    count = 0
    batch = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(
                SyntheaPatient(
                    id=row.get("Id", "").strip(),
                    birthdate=parse_date(row.get("BIRTHDATE")),
                    deathdate=parse_date(row.get("DEATHDATE")),
                    ssn=row.get("SSN"),
                    drivers=row.get("DRIVERS"),
                    passport=row.get("PASSPORT"),
                    prefix=row.get("PREFIX"),
                    first=row.get("FIRST"),
                    last=row.get("LAST"),
                    suffix=row.get("SUFFIX"),
                    maiden=row.get("MAIDEN"),
                    marital=row.get("MARITAL"),
                    race=row.get("RACE"),
                    ethnicity=row.get("ETHNICITY"),
                    gender=row.get("GENDER"),
                    birthplace=row.get("BIRTHPLACE"),
                    address=row.get("ADDRESS"),
                    city=row.get("CITY"),
                    state=row.get("STATE"),
                    zip=row.get("ZIP"),
                    lat=parse_float(row.get("LAT")),
                    lon=parse_float(row.get("LON")),
                    healthcare_expenses=parse_float(row.get("HEALTHCARE_EXPENSES")),
                    healthcare_coverage=parse_float(row.get("HEALTHCARE_COVERAGE")),
                )
            )
            if len(batch) >= BATCH_SIZE:
                session.add_all(batch)
                session.commit()
                count += len(batch)
                batch.clear()
        if batch:
            session.add_all(batch)
            session.commit()
            count += len(batch)
    logger.info("[OK] Inserted %d patients.", count)
    return count


def ingest_encounters(session: Session, filepath: str) -> int:
    logger.info("Ingesting encounters from %s...", filepath)
    count = 0
    batch = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(
                SyntheaEncounter(
                    id=row.get("Id", "").strip(),
                    start_date=parse_datetime(row.get("START")),
                    stop_date=parse_datetime(row.get("STOP")),
                    patient_id=row.get("PATIENT", "").strip(),
                    organization_id=row.get("ORGANIZATION"),
                    provider_id=row.get("PROVIDER"),
                    payer_id=row.get("PAYER"),
                    encounterclass=row.get("ENCOUNTERCLASS"),
                    code=row.get("CODE"),
                    description=row.get("DESCRIPTION"),
                    base_encounter_cost=parse_float(row.get("BASE_ENCOUNTER_COST")),
                    total_claim_cost=parse_float(row.get("TOTAL_CLAIM_COST")),
                    payer_coverage=parse_float(row.get("PAYER_COVERAGE")),
                    reasoncode=row.get("REASONCODE"),
                    reasondescription=row.get("REASONDESCRIPTION"),
                )
            )
            if len(batch) >= BATCH_SIZE:
                session.add_all(batch)
                session.commit()
                count += len(batch)
                batch.clear()
        if batch:
            session.add_all(batch)
            session.commit()
            count += len(batch)
    logger.info("[OK] Inserted %d encounters.", count)
    return count


def ingest_conditions(session: Session, filepath: str) -> int:
    logger.info("Ingesting conditions from %s...", filepath)
    count = 0
    batch = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(
                SyntheaCondition(
                    start_date=parse_date(row.get("START")),
                    stop_date=parse_date(row.get("STOP")),
                    patient_id=row.get("PATIENT", "").strip(),
                    encounter_id=row.get("ENCOUNTER"),
                    code=row.get("CODE"),
                    description=row.get("DESCRIPTION"),
                )
            )
            if len(batch) >= BATCH_SIZE:
                session.add_all(batch)
                session.commit()
                count += len(batch)
                batch.clear()
        if batch:
            session.add_all(batch)
            session.commit()
            count += len(batch)
    logger.info("[OK] Inserted %d conditions.", count)
    return count


def ingest_procedures(session: Session, filepath: str) -> int:
    logger.info("Ingesting procedures from %s...", filepath)
    count = 0
    batch = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(
                SyntheaProcedure(
                    start_date=parse_datetime(row.get("START")),
                    stop_date=parse_datetime(row.get("STOP")),
                    patient_id=row.get("PATIENT", "").strip(),
                    encounter_id=row.get("ENCOUNTER"),
                    code=row.get("CODE"),
                    description=row.get("DESCRIPTION"),
                    base_cost=parse_float(row.get("BASE_COST")),
                    reasoncode=row.get("REASONCODE"),
                    reasondescription=row.get("REASONDESCRIPTION"),
                )
            )
            if len(batch) >= BATCH_SIZE:
                session.add_all(batch)
                session.commit()
                count += len(batch)
                batch.clear()
        if batch:
            session.add_all(batch)
            session.commit()
            count += len(batch)
    logger.info("[OK] Inserted %d procedures.", count)
    return count


def ingest_observations(session: Session, filepath: str) -> int:
    logger.info("Ingesting observations from %s...", filepath)
    count = 0
    batch = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(
                SyntheaObservation(
                    date=parse_datetime(row.get("DATE")),
                    patient_id=row.get("PATIENT", "").strip(),
                    encounter_id=row.get("ENCOUNTER"),
                    category=row.get("CATEGORY"),
                    code=row.get("CODE"),
                    description=row.get("DESCRIPTION"),
                    value=row.get("VALUE"),
                    units=row.get("UNITS"),
                    type=row.get("TYPE"),
                )
            )
            if len(batch) >= BATCH_SIZE:
                session.add_all(batch)
                session.commit()
                count += len(batch)
                batch.clear()
        if batch:
            session.add_all(batch)
            session.commit()
            count += len(batch)
    logger.info("[OK] Inserted %d observations.", count)
    return count


def main():
    print("=" * 65)
    print("         SYNTHEA DATASET INGESTION & PROCESSING")
    print("=" * 65)
    print(f"Target Synthea directory: {SYNTHEA_DIR}")

    if not os.path.exists(SYNTHEA_DIR):
        logger.error("Synthea directory not found at: %s", SYNTHEA_DIR)
        sys.exit(1)

    print("\n[1/3] Creating Synthea database tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("      [OK] Created Synthea ORM tables.")

    print("\n[2/3] Processing CSV files and populating database...")
    with Session(engine) as session:
        # Clear existing Synthea data if re-running
        session.execute(text("TRUNCATE TABLE synthea_observations, synthea_procedures, synthea_conditions, synthea_encounters, synthea_patients CASCADE;"))
        session.commit()

        ingest_patients(session, os.path.join(SYNTHEA_DIR, "patients.csv"))
        ingest_encounters(session, os.path.join(SYNTHEA_DIR, "encounters.csv"))
        ingest_conditions(session, os.path.join(SYNTHEA_DIR, "conditions.csv"))
        ingest_procedures(session, os.path.join(SYNTHEA_DIR, "procedures.csv"))
        ingest_observations(session, os.path.join(SYNTHEA_DIR, "observations.csv"))

    print("\n" + "=" * 65)
    print("               SYNTHEA DATASET INGESTION COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()
