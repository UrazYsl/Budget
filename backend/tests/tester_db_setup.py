import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()
from typing import Type
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
from models import Base, Category, Account

#similar to seed.py, but for the testing database
def setup_db(db: Session) -> None:
    items = {}
    items[Category] = ["Misc", "Food", "Transport", "Entertainment"]
    items[Account] = ["Checking", "Savings", "Credit Card", "Cash"]
    for model, item_list in items.items():
        for item in item_list:
            seed_items(db, model, item)
    db.commit()

def seed_items(db: Session, model: Type[Base], item: str) -> None:
    # Check if given item already exists
    existing = db.query(model).filter(model.name == item).first()
    if not existing:
        db.add(model(name=item)) 

def get_test_session():
    engine = create_engine(os.getenv("TEST_DATABASE_URL"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    setup_db(session)
    return session

if __name__ == "__main__":
    session = get_test_session()
    setup_db(session)