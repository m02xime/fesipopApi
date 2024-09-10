from . import app, db
from .models import Festival
from datetime import date

def create_tables():
    with app.app_context():
        db.create_all()
        print("Tables created successfully.")

def add_initial_data():
    with app.app_context():
        festival1 = Festival(name='Festival de la Musique', location='Paris', date=date(2023, 6, 21))
        festival2 = Festival(name='Festival de la Bière', location='Munich', date=date(2023, 9, 15))
        db.session.add(festival1)
        db.session.add(festival2)
        db.session.commit()
        print("Initial data added successfully.")

if __name__ == '__main__':
    create_tables()
    add_initial_data()
