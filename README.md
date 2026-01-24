# Inventory Optimization API

A production-ready REST API for demand forecasting and inventory optimization using time series analysis and statistical methods.

## Features

- **Demand Forecasting**: Uses Exponential Smoothing to predict future product demand
- **Safety Stock Calculation**: Calculates optimal safety stock levels based on service level targets
- **Cost Savings Analysis**: Estimates potential cost savings from optimized inventory management
- **REST API**: Easy-to-use API endpoints for integration with other systems

## Project Overview

This project uses historical sales data (Walmart dataset) to:
1. Forecast future demand using time series analysis
2. Calculate optimal safety stock levels to prevent stockouts
3. Estimate cost savings compared to traditional fixed-buffer approaches

## API Endpoints

### `GET /health`
Health check endpoint to verify service status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Inventory Optimization API",
  "version": "1.0.0"
}
```

### `POST /predict`
Get demand forecast and inventory recommendations.

**Request Body:**
```json
{
  "store_id": 1,
  "dept_id": 1,
  "forecast_periods": 12,
  "lead_time_days": 7,
  "service_level": 0.95
}
```

**Response:**
```json
{
  "forecast": {
    "forecast": [22000, 23000, ...],
    "lower_bound": [20000, 21000, ...],
    "upper_bound": [24000, 25000, ...]
  },
  "safety_stock": {
    "safety_stock": 5000,
    "reorder_point": 8000,
    "average_daily_demand": 3200,
    "service_level": 0.95
  },
  "cost_savings": {
    "current_safety_stock": 33000,
    "optimized_safety_stock": 25000,
    "reduction": 8000,
    "reduction_percentage": 24.2
  }
}
```

### `GET /stores`
Get list of available stores and departments in the dataset.

## Local Development

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Aarjav2434/Inventory-Optimization-2.git
cd Inventory-Optimization-2
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Deployment to Render

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Add deployment files"
git push origin main
```

### Step 2: Create Render Web Service
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: inventory-optimizer
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free (or your preferred tier)

### Step 3: Deploy
Render will automatically deploy your application. The API will be available at:
`https://your-service-name.onrender.com`

## Testing the API

### Using curl:
```bash
# Health check
curl https://your-service-name.onrender.com/health

# Get prediction
curl -X POST https://your-service-name.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{"store_id": 1, "dept_id": 1, "forecast_periods": 12}'
```

### Using Python:
```python
import requests

url = "https://your-service-name.onrender.com/predict"
payload = {
    "store_id": 1,
    "dept_id": 1,
    "forecast_periods": 12,
    "lead_time_days": 7,
    "service_level": 0.95
}

response = requests.post(url, json=payload)
print(response.json())
```

## Model Details

### Forecasting Method
- **Algorithm**: Exponential Smoothing (Holt-Winters)
- **Seasonality**: Additive (52-week yearly pattern)
- **Trend**: Additive

### Safety Stock Calculation
- **Formula**: Z × σ × √L
  - Z = Z-score for target service level
  - σ = Standard deviation of demand
  - L = Lead time

### Service Level
- Default: 95% (configurable)
- Represents the probability of not having a stockout

## Project Structure

```
inventory-optimizer/
├── app.py                          # Flask API application
├── model.py                        # Inventory optimization model
├── requirements.txt                # Python dependencies
├── Procfile                        # Render deployment config
├── Train.csv                       # Training data
├── Inventory Optimization.ipynb    # Original analysis notebook
└── README.md                       # This file
```

## License

MIT License

## Author

Aarjav Patel
