from models import Product, Order, OrderItem, Review, db
from sqlalchemy import func

def get_recommendations(customer_id=None, limit=4):
    """
    Generate vegetable recommendations for a customer.
    - If customer_id is provided and they have order history:
        1. Find their most purchased categories (Content-Based)
        2. Recommend top products in those categories that they haven't purchased
        3. Recommend popular products bought by other customers (Collaborative filtering)
    - If new customer or not logged in:
        Recommend top rated available products (Popularity-Based)
    """
    # 1. Fallback: Popularity-based recommendations (No customer or no history)
    def get_global_popular(count):
        # Subquery to calculate average ratings
        avg_ratings = db.session.query(
            Review.product_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.product_id).subquery()
        
        # Query products joined with their average ratings
        popular_products = db.session.query(Product, func.coalesce(avg_ratings.c.avg_rating, 0.0).label('rating'))\
            .outerjoin(avg_ratings, Product.id == avg_ratings.c.product_id)\
            .filter(Product.status == 'Available', Product.quantity > 0)\
            .order_by(db.desc('rating'), Product.created_at.desc())\
            .limit(count)\
            .all()
            
        return [p[0] for p in popular_products]

    if not customer_id:
        return get_global_popular(limit)
        
    try:
        # Get customer's purchase history: find all product ids purchased by this customer
        purchased_items = db.session.query(OrderItem.product_id, Product.category)\
            .join(Order, OrderItem.order_id == Order.id)\
            .join(Product, OrderItem.product_id == Product.id)\
            .filter(Order.customer_id == customer_id)\
            .all()
            
        if not purchased_items:
            # New customer with no history, return global popular items
            return get_global_popular(limit)
            
        # Analyze favorite categories from history
        purchased_product_ids = {item.product_id for item in purchased_items}
        category_counts = {}
        for item in purchased_items:
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
            
        # Find the customer's top category
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        top_category = top_categories[0][0] if top_categories else None
        
        recommended_products = []
        
        # Phase 1: Recommend available products in their favorite category (Content-based)
        # Exclude already purchased products first, if possible
        if top_category:
            content_rec = Product.query.filter(
                Product.category == top_category,
                Product.status == 'Available',
                Product.quantity > 0,
                ~Product.id.in_(purchased_product_ids)
            ).order_by(Product.price.asc()).limit(limit // 2).all()
            
            recommended_products.extend(content_rec)
            
        # Phase 2: Collaborative/Popular items (items bought by other customers, excluding their own)
        needed = limit - len(recommended_products)
        if needed > 0:
            # Query top selling products overall
            popular_other = db.session.query(Product, func.count(OrderItem.id).label('sales_count'))\
                .join(OrderItem, OrderItem.product_id == Product.id)\
                .filter(
                    Product.status == 'Available',
                    Product.quantity > 0,
                    ~Product.id.in_(purchased_product_ids)
                )\
                .group_by(Product.id)\
                .order_by(db.desc('sales_count'))\
                .limit(needed)\
                .all()
                
            collab_rec = [p[0] for p in popular_other]
            recommended_products.extend(collab_rec)
            
        # Fill any remaining slots with global popular products
        if len(recommended_products) < limit:
            remaining = limit - len(recommended_products)
            existing_ids = {p.id for p in recommended_products}
            globals_rec = [
                p for p in get_global_popular(limit * 2) 
                if p.id not in existing_ids and p.id not in purchased_product_ids
            ][:remaining]
            recommended_products.extend(globals_rec)
            
        # Final fallback: if still empty or too short, relax the exclusion of already purchased products
        if len(recommended_products) < limit:
            existing_ids = {p.id for p in recommended_products}
            fallback_rec = Product.query.filter(
                Product.status == 'Available',
                Product.quantity > 0,
                ~Product.id.in_(existing_ids)
            ).limit(limit - len(recommended_products)).all()
            recommended_products.extend(fallback_rec)
            
        return recommended_products[:limit]
        
    except Exception as e:
        # If any query fails (e.g. database setup issues during tests), return empty or global popular
        print(f"Recommendation Engine Error: {e}")
        return Product.query.filter(Product.status == 'Available').limit(limit).all()
