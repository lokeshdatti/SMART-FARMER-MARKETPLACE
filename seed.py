import os
from app import app
from models import db, Farmer, Customer, Product, Review, Order, OrderItem, Payment
from datetime import datetime, timedelta

def seed_database():
    print("Seeding database...")
    
    # 1. Recreate tables
    db.drop_all()
    db.create_all()
    
    # 2. Add Farmers
    farmers_data = [
        {
            'name': 'Ramesh Kumar',
            'email': 'ramesh@farmer.com',
            'phone': '9876543210',
            'address': 'Farmhouse 12, Green Valley, Punjab',
            'region': 'North India (Punjab)',
            'password': 'password123'
        },
        {
            'name': 'Suresh Patel',
            'email': 'suresh@farmer.com',
            'phone': '9876543211',
            'address': 'Organic Fields, Anand, Gujarat',
            'region': 'West India (Gujarat)',
            'password': 'password123'
        },
        {
            'name': 'Anil Sharma',
            'email': 'anil@farmer.com',
            'phone': '9876543212',
            'address': 'Hills view farms, Shimla, Himachal Pradesh',
            'region': 'Himalayan Foothills (Shimla)',
            'password': 'password123'
        }
    ]
    
    farmers = []
    for f_info in farmers_data:
        farmer = Farmer(
            name=f_info['name'],
            email=f_info['email'],
            phone=f_info['phone'],
            address=f_info['address'],
            region=f_info['region']
        )
        farmer.set_password(f_info['password'])
        db.session.add(farmer)
        farmers.append(farmer)
    
    db.session.commit()
    print(f"Added {len(farmers)} Farmers.")
    
    # 3. Add Customers
    customers_data = [
        {
            'name': 'Lokesh Kumar',
            'email': 'lokesh@consumer.com',
            'phone': '8765432100',
            'address': 'Flat 402, Sunshine Apartments, Sector 15, Noida, UP',
            'password': 'password123'
        },
        {
            'name': 'Vamsi Krishna',
            'email': 'vamsi@consumer.com',
            'phone': '8765432101',
            'address': 'Villa 9, Palm Meadows, Whitefield, Bangalore, Karnataka',
            'password': 'password123'
        },
        {
            'name': 'Priya Singh',
            'email': 'priya@consumer.com',
            'phone': '8765432102',
            'address': 'House 88, Civil Lines, Jaipur, Rajasthan',
            'password': 'password123'
        }
    ]
    
    customers = []
    for c_info in customers_data:
        customer = Customer(
            name=c_info['name'],
            email=c_info['email'],
            phone=c_info['phone'],
            address=c_info['address']
        )
        customer.set_password(c_info['password'])
        db.session.add(customer)
        customers.append(customer)
        
    db.session.commit()
    print(f"Added {len(customers)} Customers.")
    
    # 4. Add Products
    products_data = []
    
    products = []
    for p_info in products_data:
        prod = Product(
            farmer_id=p_info['farmer_id'],
            name=p_info['name'],
            category=p_info['category'],
            description=p_info['description'],
            price=p_info['price'],
            quantity=p_info['quantity'],
            unit=p_info['unit'],
            image_url=p_info['image_url'],
            status='Available'
        )
        db.session.add(prod)
        products.append(prod)
        
    db.session.commit()
    print(f"Added {len(products)} Products.")
    
    # 5. Add Reviews
    reviews_data = []
    
    for r_info in reviews_data:
        review = Review(
            product_id=products[r_info['product_idx']].id,
            customer_id=customers[r_info['customer_idx']].id,
            rating=r_info['rating'],
            comment=r_info['comment']
        )
        db.session.add(review)
        
    db.session.commit()
    print("Added Reviews.")
    
    # 6. Add a mock past order (None)
    print("Zero products seeded. Ready for user additions.")

if __name__ == '__main__':
    with app.app_context():
        seed_database()
