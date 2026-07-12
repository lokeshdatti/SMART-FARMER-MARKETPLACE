import os
# Configure database path for testing before importing app to avoid overwriting production database
base_dir = os.path.abspath(os.path.dirname(__file__))
test_db_path = os.path.join(base_dir, 'test_marketplace.db')
os.environ['DATABASE_URL'] = f'sqlite:///{test_db_path}'

import unittest
from app import app, db
from models import Farmer, Customer, Product, Order, Review, Payment
import prediction_engine
import recommender

class SmartFarmerMarketplaceTests(unittest.TestCase):
    
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.db_path = test_db_path
        
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            self.seed_test_data()
            
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def seed_test_data(self):
        # Create a test Farmer
        farmer = Farmer(name="Test Farmer", email="test@farmer.com", region="Punjab")
        farmer.set_password("password")
        db.session.add(farmer)
        
        # Create a test Customer
        customer = Customer(name="Test Customer", email="test@customer.com", address="Noida")
        customer.set_password("password")
        db.session.add(customer)
        db.session.commit()
        
        # Create a test Product
        product = Product(
            farmer_id=farmer.id,
            name="Organic Spinach",
            category="Leafy Greens",
            price=30.00,
            quantity=10.0,
            unit="kg",
            status="Available"
        )
        db.session.add(product)
        db.session.commit()
        
        # Create a Review
        review = Review(product_id=product.id, customer_id=customer.id, rating=5, comment="Great!")
        db.session.add(review)
        db.session.commit()

    # --- Test Cases ---

    def test_database_models(self):
        """Test database retrieval works and relations are set up correctly"""
        with app.app_context():
            farmer = Farmer.query.filter_by(email="test@farmer.com").first()
            self.assertIsNotNone(farmer)
            self.assertEqual(len(farmer.products), 1)
            self.assertEqual(farmer.products[0].name, "Organic Spinach")
            
            customer = Customer.query.filter_by(email="test@customer.com").first()
            self.assertIsNotNone(customer)
            self.assertEqual(len(customer.reviews), 1)
            self.assertEqual(customer.reviews[0].rating, 5)

    def test_homepage_routing(self):
        """Test that the homepage loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart Farmer', response.data)
        self.assertIn(b'Organic Spinach', response.data)

    def test_products_directory_routing(self):
        """Test that the vegetable catalog directory page loads successfully"""
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Organic Spinach', response.data)

    def test_price_prediction_engine(self):
        """Test the custom AI price prediction algorithm output"""
        pred = prediction_engine.predict_price('Leafy Greens', 1, 'Medium', 'Medium')
        self.assertIn('predicted_price', pred)
        self.assertGreater(pred['predicted_price'], 10.0)
        
        trend = prediction_engine.get_12_month_prediction_trend('Leafy Greens', 'High', 'Low')
        self.assertEqual(len(trend), 12)
        self.assertEqual(trend[0]['month_name'], 'Jan')

    def test_price_prediction_api(self):
        """Test that the prediction JSON API endpoint functions correctly"""
        response = self.client.get('/api/price-predict?category=Leafy+Greens&demand=High&supply=Low')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['category'], 'Leafy Greens')
        self.assertEqual(len(data['trend']), 12)

    def test_recommendation_system(self):
        """Test that the customer recommendation module outputs appropriate listings"""
        with app.app_context():
            recs = recommender.get_recommendations(limit=1)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0].name, "Organic Spinach")

if __name__ == '__main__':
    unittest.main()
