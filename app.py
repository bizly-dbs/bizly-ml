import joblib
import numpy as np
import pandas as pd
from datetime import timedelta, datetime
from flask import Flask, jsonify, request, render_template
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
import json
import os
from keras.models import load_model

app = Flask(__name__)

model_path = 'analisis_kesehatan_bisnis/model.keras'
business_model = tf.keras.models.load_model(model_path)

with open('analisis_kesehatan_bisnis/tfjs_model/scaler_params.json', 'r') as f:
    scaler_params = json.load(f)

with open('analisis_kesehatan_bisnis/tfjs_model/label_classes.json', 'r') as f:
    label_classes = json.load(f)

def preprocess_input(data):
    """Preprocess input data for business health analysis"""
    input_tensor = tf.convert_to_tensor([data], dtype=tf.float32)
    
    data_min = tf.convert_to_tensor(scaler_params['data_min_'], dtype=tf.float32)
    data_range = tf.convert_to_tensor(scaler_params['data_range_'], dtype=tf.float32)
    
    return (input_tensor - data_min) / data_range

def analyze_business_health(data):
    """Analyze business health using the model"""
    try:
        preprocessed_data = preprocess_input(data)
        
        prediction = business_model.predict(preprocessed_data)
        predicted_class_index = np.argmax(prediction[0])
        
        return {
            'health_status': label_classes[predicted_class_index],
            'confidence': float(prediction[0][predicted_class_index])
        }
    except Exception as e:
        return {'error': str(e)}

model_path = 'forecasting/random_forest_model.pkl'
model = joblib.load(model_path)

def make_future_predictions(sales_data, n_days=30):
    """
    Make future predictions using the input sales data
    """
    print(f"\nMaking {n_days} days future predictions...")

    df = pd.DataFrame(sales_data)
    df['date'] = pd.to_datetime(df['date'])
    
    last_sales = df['total_sales'].mean()

    last_date = df['date'].max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(n_days)]

    predictions = []
    for i in range(n_days):
        trend = 1 + (i * 0.001)  
        seasonal = 1 + 0.1 * np.sin(2 * np.pi * i / 7) 
        noise = np.random.normal(1, 0.05) 

        pred = last_sales * trend * seasonal * noise
        predictions.append(max(0, pred))

    return predictions


@app.route('/')
def home():
    return 403

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        
        required_fields = ['pemasukan', 'pengeluaran', 'jumlah_transaksi', 'jumlah_hari_rugi']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        pemasukan = float(data['pemasukan'])
        pengeluaran = float(data['pengeluaran'])
        jumlah_transaksi = float(data['jumlah_transaksi'])
        jumlah_hari_rugi = float(data['jumlah_hari_rugi'])
        
        rasio_transaksi = jumlah_transaksi / (pengeluaran + 1)
        persen_pengeluaran = pengeluaran / (pemasukan + pengeluaran + 1e-9)
        
        input_data = [
            pemasukan,
            pengeluaran,
            jumlah_transaksi,
            jumlah_hari_rugi,
            rasio_transaksi,
            persen_pengeluaran
        ]
        
        result = analyze_business_health(input_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid input. Please provide a list of daily sales data."}), 400
    
    for item in data:
        if not isinstance(item, dict) or 'date' not in item or 'total_sales' not in item:
            return jsonify({"error": "Each item must contain 'date' and 'total_sales' fields."}), 400
    
    n_days = request.args.get('n_days', default=7, type=int)

    if n_days < 1 or n_days > 30:
        return jsonify({"error": "Invalid input. Please enter a number between 1 and 30 for the number of days."}), 400

    future_predictions = make_future_predictions(data, n_days)

    return jsonify(future_predictions)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=False)