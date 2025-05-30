from flask import Blueprint, jsonify, request
from models import db, Parcel, Customer, Courier, TrackingUpdate
from datetime import datetime, timedelta
import random
import string

parcels_bp = Blueprint('parcels', __name__)

def generate_tracking_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

@parcels_bp.route('/parcels/track/<string:tracking_number>', methods=['GET'])
def track_parcel(tracking_number):
    parcel = Parcel.query.filter_by(tracking_number=tracking_number).first()
    if parcel is None:
        return jsonify({'error': 'Parcel not found'}), 404
    return jsonify(parcel.to_dict())


@parcels_bp.route('/parcels', methods=['GET'])
def get_all_parcels():
    parcels = Parcel.query.all()
    return jsonify([parcel.to_dict() for parcel in parcels]), 200


@parcels_bp.route('/parcels', methods=['POST'])
def create_parcel():
    try:
        data = request.json
        print("Received data:", data)
        tracking_number = generate_tracking_number()

        # Create sender and recipient
        sender = Customer(
            name=data['sender']['name'],
            email=data['sender']['email'],
            phone=data['sender']['phone'],
            address=data['sender']['address']
        )
        recipient = Customer(
            name=data['recipient']['name'],
            email=data['recipient']['email'],
            phone=data['recipient']['phone'],
            address=data['recipient']['address']
        )
        db.session.add(sender)
        db.session.add(recipient)
        db.session.flush()  # Needed to get their IDs

        # Auto-assign a random available courier
        courier = Courier.query.order_by(db.func.random()).first()
        if not courier:
            return jsonify({'error': 'No couriers available'}), 500

        # Create the parcel
        parcel = Parcel(
            tracking_number=tracking_number,
            sender_id=sender.id,
            recipient_id=recipient.id,
            courier_id=courier.id,
            weight=data.get('weight', 1.0),
            length=data.get('length', 10),
            width=data.get('width', 5),
            height=data.get('height', 2),
            service_type=data.get('service_type', 'Standard'),
            estimated_delivery=datetime.utcnow() + timedelta(days=random.randint(2, 7)),
            description=data.get('description', 'Demo parcel'),
            status='Created'
        )
        db.session.add(parcel)
        db.session.flush()

        # Add initial tracking update
        update = TrackingUpdate(
            parcel_id=parcel.id,
            status='Created',
            location='System',
            timestamp=datetime.utcnow(),
            description='Parcel created and assigned to courier: ' + courier.name
        )
        db.session.add(update)
        db.session.commit()

        return jsonify(parcel.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        print("Parcel creation failed:", str(e))
        return jsonify({'error': 'Parcel creation failed', 'details': str(e)}), 500
    
 
@parcels_bp.route('/parcels/<tracking_number>/status', methods=['PUT'])
def update_parcel_status(tracking_number):
    parcel = Parcel.query.filter_by(tracking_number=tracking_number).first()
    if not parcel:
        return jsonify({'error': 'Parcel not found'}), 404

    data = request.json
    parcel.status = data['status']

    update = TrackingUpdate(
        parcel_id=parcel.id,
        status=data['status'],
        location=data.get('location', 'Unknown'),
        timestamp=datetime.utcnow(),
        description=data.get('description', '')
    )
    db.session.add(update)
    db.session.commit()

    return jsonify({'message': 'Status updated'}), 200