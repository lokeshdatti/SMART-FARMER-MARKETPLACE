import os
from app import app
from models import db, Customer, Farmer

def restore_user():
    print("Restoring user DATTI LOKESH...")
    
    email = "lokeshdatti9@gmail.com"
    name = "DATTI LOKESH"
    password_hash = "scrypt:32768:8:1$8P5Ivm8MOJWCc7ZP$22c7baade36053a342c354cac51f28f574ce15b10e2b04a26e4631bd5999638b2744f221f34a22db564a45bd9707973fef203440eb9cdf0af9be1be0379a0d4a"
    phone = "+91- 9059158378"
    address = "gavarapalem, anakapalle"
    
    # 1. Restore as Customer
    existing_customer = Customer.query.filter_by(email=email).first()
    if not existing_customer:
        customer = Customer(
            name=name,
            email=email,
            password_hash=password_hash,
            phone=phone,
            address=address
        )
        db.session.add(customer)
        print("Customer account restored successfully.")
    else:
        print("Customer account already exists.")
        
    # 2. Restore as Farmer
    existing_farmer = Farmer.query.filter_by(email=email).first()
    if not existing_farmer:
        farmer = Farmer(
            name=name,
            email=email,
            password_hash=password_hash,
            phone=phone,
            address=address,
            region="Anakapalle"
        )
        db.session.add(farmer)
        print("Farmer account restored successfully.")
    else:
        print("Farmer account already exists.")
        
    db.session.commit()
    print("Restore completed successfully!")

if __name__ == '__main__':
    with app.app_context():
        restore_user()
