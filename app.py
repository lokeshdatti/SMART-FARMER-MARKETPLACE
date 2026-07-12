import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from decimal import Decimal
from datetime import datetime
from functools import wraps

# Import local modules
from config import Config
from models import db, Farmer, Customer, Product, Order, OrderItem, Payment, Review
import prediction_engine
import recommender

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Create tables in sqlite if running in dev without seeding
with app.app_context():
    db.create_all()

# --- Role Authentication Decorator ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            
            # Verify user exists in database
            user_id = session['user_id']
            user_role = session['user_role']
            if user_role == 'farmer':
                user = Farmer.query.get(user_id)
            else:
                user = Customer.query.get(user_id)
                
            if not user:
                session.clear()
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('login', next=request.url))
                
            if role and user_role != role:
                flash(f'Access denied. This page is reserved for {role}s.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Context Processor for Global Variables ---
@app.context_processor
def inject_global_vars():
    # Inject current user information into all templates
    current_user = None
    cart_count = 0
    
    if 'user_id' in session:
        user_id = session['user_id']
        role = session['user_role']
        if role == 'farmer':
            current_user = Farmer.query.get(user_id)
        elif role == 'customer':
            current_user = Customer.query.get(user_id)
            
        if not current_user:
            session.clear()
            
    # Inject cart count
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    
    return dict(current_user=current_user, current_role=session.get('user_role'), cart_count=cart_count)

# --- Mock Email Sending Utility ---
def send_order_confirmation_email(order, customer, order_items):
    """
    Simulates sending an email notification for order confirmation.
    Writes the email contents to a local log file (emails.log) and print/console,
    and attempts SMTP delivery if SMTP server is configured in .env.
    """
    subject = f"Order Confirmation #ORD-{order.id} - Smart Farmer Marketplace"
    
    # Render HTML content manually for the log
    items_html = ""
    for item in order_items:
        items_html += f"<li>{item['product'].name} - {item['quantity']} {item['product'].unit} @ Rs. {item['price']} = Rs. {item['quantity'] * item['price']}</li>"
        
    email_body = f"""
    <html>
    <head><style>body {{ font-family: sans-serif; padding: 20px; }} .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; }}</style></head>
    <body>
        <div class="card">
            <h2>Thank you for your order, {customer.name}!</h2>
            <p>Your order <strong>#ORD-{order.id}</strong> has been successfully placed. We have notified the farmers to prepare your fresh vegetables.</p>
            <h3>Order Details:</h3>
            <ul>
                {items_html}
            </ul>
            <p><strong>Total Amount:</strong> Rs. {order.total_amount}</p>
            <p><strong>Shipping Address:</strong> {order.shipping_address}</p>
            <p><strong>Status:</strong> {order.status} (Paid via {order.payment.payment_method if order.payment else 'Pending'})</p>
            <p>Eliminating middlemen, ensuring fair prices! Thank you for buying direct from farmers.</p>
        </div>
    </body>
    </html>
    """
    
    log_entry = f"========================================\n" \
                f"TIMESTAMP: {datetime.utcnow().isoformat()}\n" \
                f"TO: {customer.email}\n" \
                f"SUBJECT: {subject}\n" \
                f"CONTENT:\n{email_body}\n" \
                f"========================================\n"
                
    # Write to local file
    try:
        log_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emails.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        print(f"[MOCK EMAIL] Saved order confirmation to {log_path}")
    except Exception as e:
        print(f"Error logging mock email: {e}")
        
    # Attempt actual SMTP if config is present
    if app.config.get('MAIL_SERVER') and app.config.get('MAIL_USERNAME'):
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
            msg['To'] = customer.email
            
            part = MIMEText(email_body, 'html')
            msg.attach(part)
            
            server = smtplib.SMTP(app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT'))
            if app.config.get('MAIL_USE_TLS'):
                server.starttls()
            server.login(app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD'))
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
            server.quit()
            print("[EMAIL] SMTP Order Confirmation email sent successfully!")
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send email via SMTP: {e}")

# --- WEB CONTROLLER ROUTES ---

@app.route('/')
def index():
    # Homepage: featured products (top 4 available) and agricultural partners
    featured_products = Product.query.filter_by(status='Available').order_by(Product.created_at.desc()).limit(4).all()
    farmers = Farmer.query.order_by(Farmer.joined_at.desc()).limit(3).all()
    return render_template('index.html', featured_products=featured_products, farmers=farmers)

# --- Authentication Pages ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user_id = session['user_id']
        role = session['user_role']
        if role == 'farmer':
            user = Farmer.query.get(user_id)
        else:
            user = Customer.query.get(user_id)
        if user:
            return redirect(url_for('index'))
        else:
            session.clear()
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') # 'farmer' or 'customer'
        
        if role == 'farmer':
            user = Farmer.query.filter_by(email=email).first()
        else:
            user = Customer.query.filter_by(email=email).first()
            
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_role'] = role
            # Clear previous cart if farmer logs in
            if role == 'farmer':
                session.pop('cart', None)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or (url_for('farmer_dashboard') if role == 'farmer' else url_for('index')))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        role = request.form.get('role') # 'farmer' or 'customer'
        
        # Check if email already exists
        existing_email = False
        if role == 'farmer':
            existing_email = Farmer.query.filter_by(email=email).first() is not None
        else:
            existing_email = Customer.query.filter_by(email=email).first() is not None
            
        if existing_email:
            flash('Email address already registered.', 'danger')
            return render_template('register.html')
            
        if role == 'farmer':
            region = request.form.get('region', '')
            user = Farmer(name=name, email=email, phone=phone, address=address, region=region)
        else:
            user = Customer(name=name, email=email, phone=phone, address=address)
            
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(f'Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# --- Catalog / Directory ---
@app.route('/products')
def products():
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'newest')
    
    query = Product.query.filter_by(status='Available')
    
    if search_query:
        query = query.filter(Product.name.like(f"%{search_query}%") | Product.description.like(f"%{search_query}%"))
    if category:
        query = query.filter(Product.category == category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
        
    # Sort
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name_asc':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())
        
    product_list = query.all()
    
    # Fetch unique categories for filters
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('products.html', products=product_list, categories=categories, 
                           selected_category=category, search_query=search_query, 
                           min_price=min_price, max_price=max_price, sort_by=sort_by)

# --- Product Details, AI Prediction & Reviews ---
@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Review submission handling
    if request.method == 'POST':
        if 'user_id' not in session or session.get('user_role') != 'customer':
            flash('Only logged-in customers can submit reviews.', 'warning')
            return redirect(url_for('login'))
            
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '')
        customer_id = session['user_id']
        
        # Check if customer has already reviewed this product
        existing_review = Review.query.filter_by(product_id=product.id, customer_id=customer_id).first()
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.created_at = datetime.utcnow()
            flash('Your review has been updated.', 'success')
        else:
            new_review = Review(product_id=product.id, customer_id=customer_id, rating=rating, comment=comment)
            db.session.add(new_review)
            flash('Review submitted successfully!', 'success')
            
        db.session.commit()
        return redirect(url_for('product_detail', product_id=product.id))
        
    # Get current seasonality predictions for Chart.js graphing
    demand_level = request.args.get('demand', 'Medium')
    supply_level = request.args.get('supply', 'Medium')
    
    # Get the 12-month projected trend
    trend_data = prediction_engine.get_12_month_prediction_trend(product.category, demand_level, supply_level)
    
    # Current month prediction
    current_month = datetime.now().month
    current_prediction = prediction_engine.predict_price(product.category, current_month, demand_level, supply_level)
    
    return render_template('product_detail.html', product=product, trend_data=trend_data, 
                           current_prediction=current_prediction, selected_demand=demand_level, 
                           selected_supply=supply_level, current_month=current_month)

# --- Shopping Cart & Checkout ---
@app.route('/cart')
@login_required(role='customer')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    subtotal = Decimal('0.00')
    
    for prod_id, qty in cart.items():
        product = Product.query.get(int(prod_id))
        if product:
            qty_decimal = Decimal(str(qty))
            total_price = product.price * qty_decimal
            subtotal += total_price
            cart_items.append({
                'product': product,
                'quantity': qty,
                'total_price': total_price
            })
            
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required(role='customer')
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty = request.form.get('quantity', type=float, default=1.0)
    
    if qty <= 0:
        flash('Quantity must be greater than zero.', 'warning')
        return redirect(request.referrer or url_for('products'))
        
    if product.quantity < Decimal(str(qty)):
        flash(f'Cannot add {qty} {product.unit}. Only {product.quantity} {product.unit} available in stock.', 'danger')
        return redirect(request.referrer or url_for('products'))
        
    cart = session.get('cart', {})
    product_key = str(product_id)
    
    if product_key in cart:
        new_qty = cart[product_key] + qty
        if product.quantity < Decimal(str(new_qty)):
            flash(f'Cannot add items. Total in cart exceeds available stock.', 'danger')
            return redirect(request.referrer or url_for('products'))
        cart[product_key] = new_qty
    else:
        cart[product_key] = qty
        
    session['cart'] = cart
    session.modified = True
    flash(f'{product.name} added to cart.', 'success')
    return redirect(url_for('view_cart'))

@app.route('/cart/update/<int:product_id>', methods=['POST'])
@login_required(role='customer')
def update_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty = request.form.get('quantity', type=float)
    cart = session.get('cart', {})
    product_key = str(product_id)
    
    if product_key in cart:
        if qty is None or qty <= 0:
            del cart[product_key]
            flash(f'{product.name} removed from cart.', 'info')
        elif product.quantity < Decimal(str(qty)):
            flash(f'Only {product.quantity} {product.unit} available. Cannot set to {qty}.', 'danger')
        else:
            cart[product_key] = qty
            flash('Cart updated successfully.', 'success')
            
        session['cart'] = cart
        session.modified = True
        
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:product_id>')
@login_required(role='customer')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_key = str(product_id)
    if product_key in cart:
        del cart[product_key]
        session['cart'] = cart
        session.modified = True
        flash('Item removed from cart.', 'info')
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
@login_required(role='customer')
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('products'))
        
    customer = Customer.query.get(session['user_id'])
    shipping_address = request.form.get('shipping_address') or customer.address
    payment_method = request.form.get('payment_method', 'Cash on Delivery')
    
    if not shipping_address:
        flash('Please provide a shipping address.', 'warning')
        return redirect(url_for('view_cart'))
        
    # Verify stock and calculate total
    order_items_to_create = []
    total_amount = Decimal('0.00')
    
    for prod_id, qty in cart.items():
        product = Product.query.get(int(prod_id))
        if not product or product.status != 'Available':
            flash(f'One of the products in your cart ({product.name if product else "Unknown"}) is no longer available.', 'danger')
            return redirect(url_for('view_cart'))
            
        qty_decimal = Decimal(str(qty))
        if product.quantity < qty_decimal:
            flash(f'Not enough stock for {product.name}. Available: {product.quantity} {product.unit}.', 'danger')
            return redirect(url_for('view_cart'))
            
        item_total = product.price * qty_decimal
        total_amount += item_total
        order_items_to_create.append({
            'product': product,
            'quantity': qty_decimal,
            'price': product.price
        })
        
    # Create the Order
    order = Order(
        customer_id=customer.id,
        total_amount=total_amount,
        shipping_address=shipping_address,
        status='Paid' if payment_method != 'Cash on Delivery' else 'Pending',
        created_at=datetime.utcnow()
    )
    db.session.add(order)
    db.session.commit() # Save to get Order ID
    
    # Save Order Items and deduct product stock
    for item in order_items_to_create:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product'].id,
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
        
        # Deduct Stock
        item['product'].quantity -= item['quantity']
        if item['product'].quantity <= 0:
            item['product'].status = 'Out of Stock'
            
    # Process Payment
    txn_id = f"TXN-{order.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    payment = Payment(
        order_id=order.id,
        payment_method=payment_method,
        transaction_id=txn_id if payment_method != 'Cash on Delivery' else None,
        amount=total_amount,
        status='Success' if payment_method != 'Cash on Delivery' else 'Pending',
        created_at=datetime.utcnow()
    )
    db.session.add(payment)
    db.session.commit()
    
    # Send order confirmation email notification
    send_order_confirmation_email(order, customer, order_items_to_create)
    
    # Clear cart
    session.pop('cart', None)
    
    flash(f'Order placed successfully! Transaction ID: {txn_id if payment_method != "Cash on Delivery" else "COD"}', 'success')
    return redirect(url_for('customer_dashboard'))

# --- Customer Dashboard ---
@app.route('/customer/dashboard')
@login_required(role='customer')
def customer_dashboard():
    customer = Customer.query.get(session['user_id'])
    
    # Query customer's order history
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()
    
    # Generate personalized recommendations
    recommendations = recommender.get_recommendations(customer_id=customer.id, limit=4)
    
    return render_template('customer_dashboard.html', customer=customer, orders=orders, recommendations=recommendations)

# --- Farmer Dashboard (CRUD Operations) ---
@app.route('/farmer/dashboard')
@login_required(role='farmer')
def farmer_dashboard():
    farmer = Farmer.query.get(session['user_id'])
    products = Product.query.filter_by(farmer_id=farmer.id).order_by(Product.created_at.desc()).all()
    
    # Calculate statistics
    total_products = len(products)
    total_sales = Decimal('0.00')
    total_orders_count = 0
    
    # Find all sales of this farmer's products
    sales_query = db.session.query(OrderItem, Order)\
        .join(Order, OrderItem.order_id == Order.id)\
        .join(Product, OrderItem.product_id == Product.id)\
        .filter(Product.farmer_id == farmer.id).all()
        
    unique_orders = set()
    for item, order in sales_query:
        total_sales += item.price * item.quantity
        unique_orders.add(order.id)
        
    total_orders_count = len(unique_orders)
    
    return render_template('farmer_dashboard.html', farmer=farmer, products=products, 
                           total_products=total_products, total_sales=total_sales, 
                           total_orders_count=total_orders_count)

@app.route('/farmer/product/add', methods=['POST'])
@login_required(role='farmer')
def farmer_add_product():
    name = request.form.get('name')
    category = request.form.get('category')
    description = request.form.get('description')
    price = request.form.get('price', type=float)
    quantity = request.form.get('quantity', type=float)
    unit = request.form.get('unit', 'kg')
    image_url = request.form.get('image_url')
    
    if not name or not category or price is None or quantity is None:
        flash('Please fill out all required fields.', 'danger')
        return redirect(url_for('farmer_dashboard'))
        
    # Unsplash fallback images by category for clean UI
    if not image_url or not image_url.strip():
        fallbacks = {
            'Leafy Greens': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=500',
            'Root Vegetables': 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=500',
            'Cruciferous': 'https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=500',
            'Alliums': 'https://images.unsplash.com/photo-1620574387735-3624d75b2dbc?w=500',
            'Nightshades': 'https://images.unsplash.com/photo-1595855759920-86582396756a?w=500',
            'Cucurbits': 'https://images.unsplash.com/photo-1604977042946-1eecc30f269e?w=500'
        }
        image_url = fallbacks.get(category, 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500')
        
    product = Product(
        farmer_id=session['user_id'],
        name=name,
        category=category,
        description=description,
        price=price,
        quantity=quantity,
        unit=unit,
        image_url=image_url,
        status='Available' if quantity > 0 else 'Out of Stock'
    )
    
    db.session.add(product)
    db.session.commit()
    
    flash(f'Product "{name}" added successfully!', 'success')
    return redirect(url_for('farmer_dashboard'))

@app.route('/farmer/product/update/<int:product_id>', methods=['POST'])
@login_required(role='farmer')
def farmer_update_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Security check: Ensure product belongs to logged-in farmer
    if product.farmer_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('farmer_dashboard'))
        
    product.name = request.form.get('name')
    product.category = request.form.get('category')
    product.description = request.form.get('description')
    product.price = Decimal(request.form.get('price', '0.00'))
    product.quantity = Decimal(request.form.get('quantity', '0.00'))
    product.unit = request.form.get('unit', 'kg')
    
    img = request.form.get('image_url')
    if img and img.strip():
        product.image_url = img
        
    product.status = 'Available' if product.quantity > 0 else 'Out of Stock'
    
    db.session.commit()
    flash(f'Product "{product.name}" updated successfully!', 'success')
    return redirect(url_for('farmer_dashboard'))

@app.route('/farmer/product/delete/<int:product_id>', methods=['POST'])
@login_required(role='farmer')
def farmer_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Security check
    if product.farmer_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('farmer_dashboard'))
        
    name = product.name
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product "{name}" deleted successfully.', 'warning')
    return redirect(url_for('farmer_dashboard'))

# --- Contact Support Page ---
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # In a real app, this sends a mail to support
        # We will log it locally
        log_entry = f"========================================\n" \
                    f"SUPPORT INQUIRY: {datetime.utcnow().isoformat()}\n" \
                    f"FROM: {name} ({email})\n" \
                    f"SUBJECT: {subject}\n" \
                    f"MESSAGE:\n{message}\n" \
                    f"========================================\n"
        try:
            log_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'support_tickets.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging support inquiry: {e}")
            
        flash('Thank you for contacting us! Our support team will get back to you shortly.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

# --- API Endpoints ---
@app.route('/api/price-predict')
def api_price_predict():
    category = request.args.get('category')
    demand = request.args.get('demand', 'Medium')
    supply = request.args.get('supply', 'Medium')
    
    if not category:
        return jsonify({'error': 'category parameter is required'}), 400
        
    trend = prediction_engine.get_12_month_prediction_trend(category, demand, supply)
    return jsonify({
        'category': category,
        'demand': demand,
        'supply': supply,
        'trend': trend
    })

if __name__ == '__main__':
    app.run(debug=True)
