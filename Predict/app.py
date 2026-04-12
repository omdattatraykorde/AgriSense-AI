from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os
from datetime import datetime

app = Flask(__name__)

# -------------------------------
# LOAD ALL MODELS
# -------------------------------

# Crop
crop_model = joblib.load("xgboost_model.pkl")
crop_encoder = joblib.load("label_encoder.pkl")
crop_columns = joblib.load("columns.pkl")

# Fertilizer
fert_model = joblib.load("fert_model.pkl")
fert_encoder = joblib.load("fert_encoder.pkl")
fert_crop_encoder = joblib.load("crop_encoder.pkl")
fert_columns = joblib.load("fert_columns.pkl")

# Irrigation
irr_model = joblib.load("irrigation_model.pkl")
irr_columns = joblib.load("irrigation_columns.pkl")

# -------------------------------
# HOME
# -------------------------------
@app.route('/')
def home():
    return "Smart Agriculture API Running ✅"

# -------------------------------
# HEALTH
# -------------------------------
@app.route('/health')
def health():
    return jsonify({
        "working": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# -------------------------------
# CROP PREDICTION
# -------------------------------
@app.route('/predict-crop', methods=['POST'])
def predict_crop():
    try:
        data = request.json
        df = pd.DataFrame([data])
        df.columns = df.columns.str.lower()

        df = pd.get_dummies(df)
        df = df.reindex(columns=crop_columns, fill_value=0)

        pred = crop_model.predict(df)
        crop = crop_encoder.inverse_transform(pred)[0]

        return jsonify({"recommended_crop": crop})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# FERTILIZER PREDICTION
# -------------------------------
@app.route('/predict-fertilizer', methods=['POST'])
def predict_fertilizer():
    try:
        data = request.json
        df = pd.DataFrame([data])
        df.columns = df.columns.str.lower()

        # Fix text
        df['crop'] = df['crop'].str.capitalize()
        df['district_name'] = df['district_name'].str.lower()
        df['soil_color'] = df['soil_color'].str.lower()

        # Encode crop safely
        if df['crop'][0] not in fert_crop_encoder.classes_:
            return jsonify({
                "error": f"Invalid crop. Allowed: {list(fert_crop_encoder.classes_)}"
            }), 400

        df['crop'] = fert_crop_encoder.transform(df['crop'])

        df = pd.get_dummies(df)
        df = df.reindex(columns=fert_columns, fill_value=0)

        pred = fert_model.predict(df)
        fert = fert_encoder.inverse_transform(pred)[0]

        return jsonify({"recommended_fertilizer": fert})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# IRRIGATION PREDICTION
# -------------------------------
@app.route('/predict-irrigation', methods=['POST'])
def predict_irrigation():
    try:
        data = request.json
        df = pd.DataFrame([data])
        df.columns = df.columns.str.lower()

        # Clean text
        df['district_name'] = df['district_name'].str.capitalize()
        df['soil_color'] = df['soil_color'].str.title()
        df['crop'] = df['crop'].str.capitalize()

        df = pd.get_dummies(df)
        df = df.reindex(columns=irr_columns, fill_value=0)

        pred = irr_model.predict(df)[0]

        return jsonify({"irrigation_needed": int(pred)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)