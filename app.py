"""
Inventory Optimization API
Flask REST API for demand forecasting and inventory optimization
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from model import InventoryOptimizer

app = Flask(__name__)
CORS(app)

# Configuration
DATA_FILE = 'Train.csv'


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Inventory Optimization API',
        'version': '1.0.0'
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict demand and calculate inventory recommendations
    
    Expected JSON payload:
    {
        "store_id": 1,
        "dept_id": 1,
        "forecast_periods": 12,
        "lead_time_days": 7,
        "service_level": 0.95
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required parameters
        store_id = data.get('store_id', 1)
        dept_id = data.get('dept_id', 1)
        forecast_periods = data.get('forecast_periods', 12)
        lead_time_days = data.get('lead_time_days', 7)
        service_level = data.get('service_level', 0.95)
        
        # Validate data file exists
        if not os.path.exists(DATA_FILE):
            return jsonify({
                'error': 'Training data file not found',
                'message': 'Please ensure Train.csv is available'
            }), 404
        
        # Load data
        df = pd.read_csv(DATA_FILE)
        
        # Initialize optimizer
        optimizer = InventoryOptimizer(service_level=service_level)
        
        # Prepare data
        ts_data = optimizer.prepare_data(df, store_id=store_id, dept_id=dept_id)
        
        if len(ts_data) == 0:
            return jsonify({
                'error': 'No data found',
                'message': f'No data available for Store {store_id}, Department {dept_id}'
            }), 404
        
        # Get recommendations
        recommendations = optimizer.get_recommendations(
            ts_data,
            forecast_periods=forecast_periods,
            lead_time_days=lead_time_days
        )
        
        # Add request parameters to response
        recommendations['parameters'] = {
            'store_id': store_id,
            'dept_id': dept_id,
            'forecast_periods': forecast_periods,
            'lead_time_days': lead_time_days,
            'service_level': service_level
        }
        
        return jsonify(recommendations)
        
    except ValueError as e:
        return jsonify({
            'error': 'Validation error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/stores', methods=['GET'])
def get_stores():
    """Get list of available stores and departments"""
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify({
                'error': 'Training data file not found'
            }), 404
        
        df = pd.read_csv(DATA_FILE)
        
        stores = df['Store'].unique().tolist()
        departments = df['Dept'].unique().tolist()
        
        # Get store-department combinations
        combinations = df.groupby(['Store', 'Dept']).size().reset_index(name='records')
        
        return jsonify({
            'stores': sorted(stores),
            'departments': sorted(departments),
            'combinations': combinations.to_dict('records'),
            'total_records': len(df)
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'service': 'Inventory Optimization API',
        'version': '1.0.0',
        'endpoints': {
            '/health': {
                'method': 'GET',
                'description': 'Health check endpoint'
            },
            '/predict': {
                'method': 'POST',
                'description': 'Get demand forecast and inventory recommendations',
                'parameters': {
                    'store_id': 'Store ID (default: 1)',
                    'dept_id': 'Department ID (default: 1)',
                    'forecast_periods': 'Number of periods to forecast (default: 12)',
                    'lead_time_days': 'Lead time in days (default: 7)',
                    'service_level': 'Target service level (default: 0.95)'
                }
            },
            '/stores': {
                'method': 'GET',
                'description': 'Get list of available stores and departments'
            }
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
