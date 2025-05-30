import os
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import logging

 # Load environment variables
load_dotenv()

# Initialize Flask app FIRST
app = Flask(__name__)

# CORS setup
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "https://comforting-syrniki-99725d.netlify.app",
    "https://4dac-2601-18f-687-72f0-5046-d41c-a640-b17f.ngrok-free.app"
])

# App config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-unsafe')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'parcel_delivery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB and migration AFTER app is ready
from database import db
db.init_app(app)
migrate = Migrate(app, db)

# Now import models (after db is bound to app)
from models import Customer, Courier, Parcel, TrackingUpdate

# Register blueprints
from parcels import parcels_bp
app.register_blueprint(parcels_bp)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Utility function
def generate_tracking_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

# Route: Setup demo data
@app.route('/setup/demo', methods=['POST'])
def setup_demo_data():
    db.create_all()

    if not Courier.query.first():
        couriers = [
            Courier(id='CR001', name='John Doe', email='john@example.com', phone='555-0100', vehicle='Van'),
            Courier(id='CR002', name='Jane Smith', email='jane@example.com', phone='555-0200', vehicle='Bike'),
        ]
        db.session.bulk_save_objects(couriers)

    if not Customer.query.first():
        customers = [
            Customer(name='Alice Johnson', email='alice@example.com', phone='555-1111', address='123 Apple St'),
            Customer(name='Bob Williams', email='bob@example.com', phone='555-2222', address='456 Banana Ave')
        ]
        db.session.add_all(customers)
        db.session.commit()

        for i in range(20):
            tracking_number = generate_tracking_number()
            sender = customers[i % len(customers)]
            recipient = customers[(i + 1) % len(customers)]
            parcel = Parcel(
                tracking_number=tracking_number,
                sender_id=sender.id,
                recipient_id=recipient.id,
                courier_id='CR001' if i % 2 == 0 else 'CR002',
                weight=1.5 + i,
                length=10 + i,
                width=5 + i,
                height=2 + i,
                service_type='Express',
                estimated_delivery=datetime.utcnow() + timedelta(days=3),
                description=f"Demo parcel {i + 1}",
                status='In Transit'
            )
            db.session.add(parcel)
            db.session.flush()

            updates = [
                TrackingUpdate(parcel_id=tracking_number, status='Dispatched', location='Warehouse A', description='Left the facility'),
                TrackingUpdate(parcel_id=tracking_number, status='In Transit', location='Distribution Center', description='On the way'),
            ]
            db.session.bulk_save_objects(updates)

        db.session.commit()

    return jsonify({'message': 'Demo data initialized'}), 200

@app.before_request
def auto_seed_demo():
    if not hasattr(app, 'demo_data_seeded'):
        with app.app_context():
            if not Parcel.query.first():
                setup_demo_data()
        app.demo_data_seeded = True


@app.route('/couriers', methods=['GET'])
def get_all_couriers():
    couriers = Courier.query.all()
    return jsonify([c.to_dict() for c in couriers]), 200


@app.route('/couriers/login', methods=['POST'])
def courier_login():
    data = request.json
    courier_id = data.get('courier_id')
    password = data.get('password')

    valid_credentials = {
        'CR001': 'john123',
        'CR002': 'jane123'
    }

    if valid_credentials.get(courier_id) == password:
        session['courier_id'] = courier_id
        return jsonify({'message': 'Login successful', 'courier_id': courier_id}), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/couriers/me', methods=['GET'])
def get_logged_in_courier():
    courier_id = session.get('courier_id')
    if not courier_id:
        return jsonify({'error': 'Not logged in'}), 401
    courier = Courier.query.get(courier_id)
    return jsonify(courier.to_dict()) if courier else jsonify({'error': 'Courier not found'}), 404


@app.route('/couriers/logout', methods=['POST'])
def courier_logout():
    session.pop('courier_id', None)
    return jsonify({'message': 'Logged out'}), 200

# Run the server
if __name__ == '__main__':
     app.run(debug=True)


     # Ensure these imports are available at the top or within the function
from flask.cli import with_appcontext

@app.cli.command("seed")
@with_appcontext
def seed():
    from models import Customer, Courier, Parcel, TrackingUpdate
    from database import db
    from datetime import datetime, timedelta
    import random
    import string

    db.drop_all()
    db.create_all()

    # Create demo customers
    alice = Customer(name="Alice Johnson", email="alice@example.com", phone="555-1234", address="123 Main St")
    bob = Customer(name="Bob Smith", email="bob@example.com", phone="555-5678", address="456 Oak Ave")
    db.session.add_all([alice, bob])

    # Create a courier
    courier = Courier(id="C123", name="John Courier", email="john@delivery.com", phone="555-9012", vehicle="Bike")
    db.session.add(courier)

    # Create a parcel
    tracking_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    parcel = Parcel(
        tracking_number=tracking_number,
        sender=alice,
        recipient=bob,
        courier=courier,
        weight=2.5,
        length=10.0,
        width=5.0,
        height=3.0,
        service_type="Express",
        estimated_delivery=datetime.utcnow() + timedelta(days=2),
        description="Books",
        status="In Transit"
    )
    db.session.add(parcel)

    # Add tracking update
    update = TrackingUpdate(
        parcel_id=tracking_number,
        status="Dispatched",
        location="Warehouse A",
        description="Parcel has been dispatched"
    )
    db.session.add(update)

    db.session.commit()
    print("Seeded demo data successfully.")