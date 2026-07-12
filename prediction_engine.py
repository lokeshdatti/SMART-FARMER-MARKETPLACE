import math
import random

# Base configurations for vegetable categories
CATEGORY_PROFILES = {
    'Leafy Greens': {'base_price': 40.0, 'seasonality_peak_month': 1, 'amplitude': 0.15},       # Peak winter
    'Cruciferous': {'base_price': 45.0, 'seasonality_peak_month': 12, 'amplitude': 0.20},      # Mid winter
    'Nightshades': {'base_price': 50.0, 'seasonality_peak_month': 9, 'amplitude': 0.25},       # Late monsoon/autumn
    'Root Vegetables': {'base_price': 30.0, 'seasonality_peak_month': 11, 'amplitude': 0.10},  # Late autumn
    'Gourds & Pumpkins': {'base_price': 35.0, 'seasonality_peak_month': 6, 'amplitude': 0.18}, # Mid summer
    'Beans & Pods': {'base_price': 55.0, 'seasonality_peak_month': 11, 'amplitude': 0.12},      # Late autumn
    'Fruits & Cucumbers': {'base_price': 60.0, 'seasonality_peak_month': 5, 'amplitude': 0.20}, # Peak summer
}


DEMAND_MULTIPLIERS = {
    'Low': -0.15,
    'Medium': 0.0,
    'High': 0.25
}

SUPPLY_MULTIPLIERS = {
    'Low': 0.30,      # Scarcity drives prices up
    'Medium': 0.0,
    'High': -0.20     # Abundance drops prices
}

def predict_price(category, month, demand_level='Medium', supply_level='Medium', seed_value=None):
    """
    Predicts the price of a vegetable category for a specific month (1-12)
    using seasonality patterns, demand, and supply indicators.
    """
    if category not in CATEGORY_PROFILES:
        category = 'Leafy Greens' # Default fallback
        
    profile = CATEGORY_PROFILES[category]
    base_price = profile['base_price']
    peak = profile['seasonality_peak_month']
    amplitude = profile['amplitude']
    
    # Calculate seasonality factor based on month: cosine wave peaking at peak_month
    # cos(2 * pi * (month - peak) / 12)
    seasonality_factor = amplitude * math.cos(2 * math.pi * (month - peak) / 12)
    
    # Supply and Demand factors
    demand_factor = DEMAND_MULTIPLIERS.get(demand_level, 0.0)
    supply_factor = SUPPLY_MULTIPLIERS.get(supply_level, 0.0)
    
    # Base calculation formula
    # P_pred = P_base * (1 + seasonality + demand + supply)
    multiplier = 1.0 + seasonality_factor + demand_factor + supply_factor
    predicted = base_price * multiplier
    
    # Apply a tiny deterministic pseudo-random fluctuation based on category/month/demand/supply
    if seed_value is None:
        # Generate a seed value based on inputs for consistency
        seed_value = hash(f"{category}-{month}-{demand_level}-{supply_level}") % 1000
    
    random.seed(seed_value)
    noise = random.uniform(-0.02, 0.02) # +/- 2% market volatility noise
    predicted = predicted * (1.0 + noise)
    
    # Clean output values
    predicted_val = max(10.0, round(predicted, 2)) # Ensure price never drops below 10
    
    return {
        'category': category,
        'predicted_price': predicted_val,
        'base_price': base_price,
        'seasonality_effect': round(seasonality_factor * 100, 1), # as percentage
        'demand_effect': round(demand_factor * 100, 1),
        'supply_effect': round(supply_factor * 100, 1),
        'total_multiplier': round(multiplier, 2)
    }

def get_12_month_prediction_trend(category, demand_level='Medium', supply_level='Medium'):
    """
    Returns a list of predicted prices for all 12 months for UI graphing.
    """
    trend = []
    # Seed value to keep the random fluctuations stable for the graph
    graph_seed = hash(f"{category}-graph-seed") % 1000
    
    for month in range(1, 13):
        pred = predict_price(category, month, demand_level, supply_level, seed_value=graph_seed + month)
        trend.append({
            'month_num': month,
            'month_name': [
                'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
            ][month - 1],
            'price': pred['predicted_price']
        })
    return trend
