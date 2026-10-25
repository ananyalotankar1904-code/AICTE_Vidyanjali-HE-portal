import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.application import Application, WorkflowHistory

DATASET_PATH = r"C:\Users\DELL\Downloads\Dataset_2_Synthetic_Applications_25.xlsx"


def load_dataset_records():
    """Extract records from Dataset 2 xlsx via standard library."""
    if not os.path.exists(DATASET_PATH):
        print(f"Dataset file not found at {DATASET_PATH}")
        return []

    with zipfile.ZipFile(DATASET_PATH) as z:
        tree = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        rows = tree.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row")
        header = ["".join(c.itertext()) for c in rows[0].findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c")]
        data = []
        for r in rows[1:]:
            cells = ["".join(c.itertext()) for c in r.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c")]
            if len(cells) >= len(header):
                data.append(dict(zip(header, cells)))
        return data


def seed_database():
    """Seeds the SQLite database with the 25 synthetic prototype applications."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        existing_count = db.query(Application).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} applications. Skipping seed.")
            return

        records = load_dataset_records()
        print(f"Loading {len(records)} applications into database...")

        for row in records:
            app = Application(
                application_id=row["application_id"],
                institution_id=row["institution_id"],
                application_type=row["application_type"],
                current_stage=row["current_stage"],
                application_status=row["application_status"],
                submitted_date=row["submitted_date"],
                stage_entered_date=row["stage_entered_date"],
                due_date=row["due_date"],
                assigned_role=row["assigned_role"],
                deficiency_flag=row["deficiency_flag"],
                last_updated=row["last_updated"],
                data_type=row["data_type"],
                deadline_condition=row["deadline_condition"],
                reference_date=row["reference_date"],
                demo_notes=row["demo_notes"],
                academic_year="2026-2027",
            )
            db.add(app)

            # Add initial audit history record
            history = WorkflowHistory(
                application_id=row["application_id"],
                from_stage="NONE",
                to_stage=row["current_stage"],
                from_status="NONE",
                to_status=row["application_status"],
                action="SEED_IMPORT",
                actor_id="system_seed",
                actor_role="System",
                timestamp=datetime.now(timezone.utc),
                remarks="Imported from synthetic prototype dataset",
            )
            db.add(history)

        db.commit()
        print("Database seeded successfully with 25 prototype applications!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
