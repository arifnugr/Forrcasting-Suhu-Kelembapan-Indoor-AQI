import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import json

# Fungsi label suhu dan kelembapan
def label_suhu_kelembapan(suhu, kelembapan):
    if kelembapan < 30:
        return "kering"
    elif kelembapan > 80:
        return "lembab"
    elif suhu < 20:
        return "terlalu dingin"
    elif suhu > 32:
        return "terlalu panas"
    elif 20 <= suhu <= 27 and 30 <= kelembapan <= 60:
        return "nyaman"
    elif 20 <= suhu <= 27 and 60 < kelembapan <= 80:
        return "nyaman-lembab"
    elif 27 < suhu <= 32 and 30 <= kelembapan <= 60:
        return "nyaman-panas"
    elif 27 < suhu <= 32 and 60 < kelembapan <= 80:
        return "gerah"
    else:
        return "tidak diketahui"

# Fungsi label kualitas udara
def label_kualitas_udara(mq135):
    if mq135 <= 650:
        return "sangat baik"
    elif mq135 <= 800:
        return "cukup buruk"
    elif mq135 <= 1300:
        return "buruk"
    else:
        return "berbahaya"

# Load data
csv_path = "sensor_data.csv"
df = pd.read_csv(csv_path, parse_dates=["timestamp"])

# Ambil 2000 data terakhir dan urutkan
df = df.sort_values("timestamp").tail(2000).copy()

# Feature engineering
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.dayofweek
df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)

# Siapkan fitur dan target
features = ["sin_hour", "cos_hour", "day_of_week"]
X = df[features]
y_suhu = df["suhu"]
y_kelembapan = df["kelembapan"]
y_mq135 = df["mq135"]

# Split data menjadi data latih dan validasi
X_train, X_val, y_suhu_train, y_suhu_val = train_test_split(X, y_suhu, test_size=0.2, random_state=42)
_, _, y_kelembapan_train, y_kelembapan_val = train_test_split(X, y_kelembapan, test_size=0.2, random_state=42)
_, _, y_mq135_train, y_mq135_val = train_test_split(X, y_mq135, test_size=0.2, random_state=42)

# Model training
model_suhu = LinearRegression().fit(X_train, y_suhu_train)
model_kelembapan = LinearRegression().fit(X_train, y_kelembapan_train)
model_mq135 = LinearRegression().fit(X_train, y_mq135_train)

# Forecast 7 hari ke depan dari sekarang (per jam)
forecast = []
start_time = datetime.now() + timedelta(minutes=10)

for i in range(24 * 7):
    current_time = start_time + timedelta(hours=i)
    hour = current_time.hour
    day_of_week = current_time.weekday()
    sin_hour = np.sin(2 * np.pi * hour / 24)
    cos_hour = np.cos(2 * np.pi * hour / 24)

    # Perhatikan penggunaan nama fitur yang konsisten
    features_input = pd.DataFrame({
        "sin_hour": [sin_hour],
        "cos_hour": [cos_hour],
        "day_of_week": [day_of_week]
    })

    pred_suhu = model_suhu.predict(features_input)[0]
    pred_kelembapan = model_kelembapan.predict(features_input)[0]
    pred_mq135 = model_mq135.predict(features_input)[0]

    forecast.append({
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "suhu": round(pred_suhu, 2),
        "kelembapan": round(pred_kelembapan, 2),
        "mq135": int(pred_mq135),
        "label_suhu_kelembapan": label_suhu_kelembapan(pred_suhu, pred_kelembapan),
        "label_kualitas_udara": label_kualitas_udara(pred_mq135)
    })

# Simpan hasil forecast
output = {
    "model_info": {
        "features": features,
        "trained_on_last_n": 2000,
        "train_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    "forecast": forecast
}

output_path = "forecast_result.json"
with open(output_path, "w") as f:
    json.dump(output, f, indent=4)

print(f"Hasil forecasting disimpan di '{output_path}'")
