from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os

app = Flask(__name__)

# Load files
model = joblib.load("xgboost_model.pkl")
le = joblib.load("label_encoder.pkl")
columns = joblib.load("columns.pkl")

@app.route('/')
def home():
    return "API Running ✅"

from datetime import datetime

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "working": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    input_df = pd.DataFrame([data])
    input_df = pd.get_dummies(input_df)
    input_df = input_df.reindex(columns=columns, fill_value=0)

    prediction = model.predict(input_df)
    crop = le.inverse_transform(prediction)[0]

    return jsonify({"recommended_crop": crop})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
