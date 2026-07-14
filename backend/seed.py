"""Run once after the DB is up to create a couple of demo HCPs.
Usage: python seed.py
"""
from app.database import SessionLocal, Base, engine
from app.models import HCP

Base.metadata.create_all(bind=engine)

DEMO_HCPS = [
    {"name": "Dr. Sarah Chen", "specialty": "Cardiology", "territory": "North Zone", "hospital": "City General Hospital", "email": "s.chen@citygeneral.example"},
    {"name": "Dr. Raj Malhotra", "specialty": "Oncology", "territory": "West Zone", "hospital": "St. Mary's Medical Center", "email": "r.malhotra@stmarys.example"},
    {"name": "Dr. Emily Osei", "specialty": "Endocrinology", "territory": "East Zone", "hospital": "Lakeside Clinic", "email": "e.osei@lakeside.example"},
]

def run():
    db = SessionLocal()
    try:
        for h in DEMO_HCPS:
            exists = db.query(HCP).filter(HCP.name == h["name"]).first()
            if not exists:
                db.add(HCP(**h))
        db.commit()
        print("Seeded demo HCPs.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
