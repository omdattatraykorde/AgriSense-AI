from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os
from datetime import datetime

app = Flask(__name__)

# =========================================
# LOAD CROP MODEL FILES
# =========================================
crop_model = joblib.load("xgboost_model.pkl")
crop_encoder = joblib.load("label_encoder.pkl")
crop_columns = joblib.load("columns.pkl")

# =========================================
# LOAD FERTILIZER MODEL FILES
# =========================================
fert_model = joblib.load("fert_model.pkl")
fert_encoder = joblib.load("fert_encoder.pkl")
fert_crop_encoder = joblib.load("crop_encoder.pkl")
fert_columns = joblib.load("fert_columns.pkl")  # IMPORTANT (rename while saving)

# =========================================
# HOME ROUTE
# =========================================
@app.route('/')
def home():
    return "Crop + Fertilizer API Running ✅"

# =========================================
# HEALTH ROUTE
# =========================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "working": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# =========================================
# CROP PREDICTION
# =========================================
@app.route('/predict-crop', methods=['POST'])
def predict_crop():
    try:
        data = request.json

        input_df = pd.DataFrame([data])
        input_df = pd.get_dummies(input_df)
        input_df = input_df.reindex(columns=crop_columns, fill_value=0)

        prediction = crop_model.predict(input_df)
        crop = crop_encoder.inverse_transform(prediction)[0]

        return jsonify({
            "recommended_crop": crop
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================
# FERTILIZER PREDICTION
# =========================================
@app.route('/predict-fertilizer', methods=['POST'])
def predict_fertilizer():
    try:
        data = request.json

        input_df = pd.DataFrame([data])

        # Normalize input
        input_df['crop'] = input_df['crop'].str.strip().str.capitalize()
        input_df['district_name'] = input_df['district_name'].str.strip().str.lower()
        input_df['soil_color'] = input_df['soil_color'].str.strip().str.lower()

        # Validate crop
        if input_df['crop'][0] not in fert_crop_encoder.classes_:
            return jsonify({
                "error": f"Invalid crop value. Allowed: {list(fert_crop_encoder.classes_)}"
            }), 400

        # Encode crop
        input_df['crop'] = fert_crop_encoder.transform(input_df['crop'])

        # One-hot encoding
        input_df = pd.get_dummies(input_df)

        # Match columns
        input_df = input_df.reindex(columns=fert_columns, fill_value=0)

        # Predict
        prediction = fert_model.predict(input_df)
        fertilizer = fert_encoder.inverse_transform(prediction)[0]

        return jsonify({
            "recommended_fertilizer": fertilizer
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================
# RUN APP
# =========================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)