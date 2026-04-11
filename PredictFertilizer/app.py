from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os
from datetime import datetime

app = Flask(__name__)

# -------------------------------
# LOAD MODEL FILES
# -------------------------------
model = joblib.load("fert_model.pkl")
fert_encoder = joblib.load("fert_encoder.pkl")
crop_encoder = joblib.load("crop_encoder.pkl")
columns = joblib.load("columns.pkl")

# -------------------------------
# HOME ROUTE
# -------------------------------
@app.route('/')
def home():
    return "Fertilizer API Running ✅"

# -------------------------------
# HEALTH ROUTE
# -------------------------------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "working": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# -------------------------------
# PREDICT ROUTE
# -------------------------------
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json

        # Convert input to dataframe
        input_df = pd.DataFrame([data])

        # -------------------------------
        # FIX 1: Normalize text inputs
        # -------------------------------
        input_df['crop'] = input_df['crop'].str.strip().str.capitalize()
        input_df['district_name'] = input_df['district_name'].str.strip().str.lower()
        input_df['soil_color'] = input_df['soil_color'].str.strip().str.lower()

        # -------------------------------
        # FIX 2: Encode crop safely
        # -------------------------------
        if input_df['crop'][0] not in crop_encoder.classes_:
            return jsonify({
                "error": f"Invalid crop value. Allowed: {list(crop_encoder.classes_)}"
            }), 400

        input_df['crop'] = crop_encoder.transform(input_df['crop'])

        # -------------------------------
        # FIX 3: One-hot encoding
        # -------------------------------
        input_df = pd.get_dummies(input_df)

        # -------------------------------
        # FIX 4: Match training columns
        # -------------------------------
        input_df = input_df.reindex(columns=columns, fill_value=0)

        # -------------------------------
        # PREDICT
        # -------------------------------
        prediction = model.predict(input_df)

        fertilizer = fert_encoder.inverse_transform(prediction)[0]

        return jsonify({
            "recommended_fertilizer": fertilizer
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# -------------------------------
# RUN APP (RENDER COMPATIBLE)
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)