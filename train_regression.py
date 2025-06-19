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

# Pastikan timestamp valid
df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
df = df.dropna(subset=["timestamp"])

# Ambil 2000 data terakhir dan urutkan
df = df.sort_values("timestamp").tail(2000).copy()

# Dapatkan tanggal awal bulan dan tanggal saat ini
current_date = datetime.now()
first_day_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

# Filter data dari tanggal 1 bulan ini hingga sekarang untuk training
train_data = df[(df["timestamp"] >= first_day_of_month) & (df["timestamp"] <= current_date)].copy()

# Jika data terlalu sedikit, gunakan semua
if len(train_data) < 100:
    train_data = df.copy()
    print(f"Data dari tanggal 1 hingga sekarang terlalu sedikit ({len(train_data)} baris), menggunakan semua data")
else:
    print(f"Menggunakan {len(train_data)} data dari {first_day_of_month.strftime('%Y-%m-%d')} hingga {current_date.strftime('%Y-%m-%d %H:%M:%S')}")

# Feature engineering
train_data["hour"] = train_data["timestamp"].dt.hour
train_data["day_of_week"] = train_data["timestamp"].dt.dayofweek
train_data["sin_hour"] = np.sin(2 * np.pi * train_data["hour"] / 24)
train_data["cos_hour"] = np.cos(2 * np.pi * train_data["hour"] / 24)

# Siapkan fitur dan target
features = ["sin_hour", "cos_hour", "day_of_week"]
X = train_data[features]
y_suhu = train_data["suhu"]
y_kelembapan = train_data["kelembapan"]
y_mq135 = train_data["mq135"]

# Split data
X_train, X_val, y_suhu_train, y_suhu_val = train_test_split(X, y_suhu, test_size=0.2, random_state=42)
_, _, y_kelembapan_train, y_kelembapan_val = train_test_split(X, y_kelembapan, test_size=0.2, random_state=42)
_, _, y_mq135_train, y_mq135_val = train_test_split(X, y_mq135, test_size=0.2, random_state=42)

# Model training
model_suhu = LinearRegression().fit(X_train, y_suhu_train)
model_kelembapan = LinearRegression().fit(X_train, y_kelembapan_train)
model_mq135 = LinearRegression().fit(X_train, y_mq135_train)

# Forecast dari tanggal 1 sampai 7 hari ke depan dari sekarang (per jam)
forecast = []
start_time = first_day_of_month
end_time = current_date + timedelta(days=7)

num_hours = int((end_time - start_time).total_seconds() / 3600)

for i in range(num_hours):
    forecast_time = start_time + timedelta(hours=i)
    hour = forecast_time.hour
    day_of_week = forecast_time.weekday()
    sin_hour = np.sin(2 * np.pi * hour / 24)
    cos_hour = np.cos(2 * np.pi * hour / 24)

    features_input = pd.DataFrame({
        "sin_hour": [sin_hour],
        "cos_hour": [cos_hour],
        "day_of_week": [day_of_week]
    })

    pred_suhu = model_suhu.predict(features_input)[0]
    pred_kelembapan = model_kelembapan.predict(features_input)[0]
    pred_mq135 = model_mq135.predict(features_input)[0]

    forecast.append({
        "timestamp": forecast_time.strftime("%Y-%m-%d %H:%M:%S"),
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
        "trained_on_data_from": first_day_of_month.strftime("%Y-%m-%d"),
        "trained_on_data_to": current_date.strftime("%Y-%m-%d %H:%M:%S"),
        "forecast_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_points_used": len(train_data)
    },
    "forecast": forecast
}

output_path = "forecast_result.json"
with open(output_path, "w") as f:
    json.dump(output, f, indent=4)

print(f"Hasil forecasting disimpan di '{output_path}'")
print(f"Prediksi dari {start_time.strftime('%Y-%m-%d %H:%M:%S')} hingga {end_time.strftime('%Y-%m-%d %H:%M:%S')}")


#Evaluasi model
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
# Suhu
y_actual_suhu = y_suhu_val
y_pred_suhu = model_suhu.predict(X_val)

mae_suhu = mean_absolute_error(y_actual_suhu, y_pred_suhu)
rmse_suhu = np.sqrt(mean_squared_error(y_actual_suhu, y_pred_suhu))
r2_suhu = r2_score(y_actual_suhu, y_pred_suhu)

print("=== Evaluasi Suhu ===")
print(f"MAE  : {mae_suhu:.2f}")
print(f"RMSE : {rmse_suhu:.2f}")
print(f"R²   : {r2_suhu:.2f}")

# Kelembapan
y_actual_kelembapan = y_kelembapan_val
y_pred_kelembapan = model_kelembapan.predict(X_val)

print("\n=== Evaluasi Kelembapan ===")
print(f"MAE  : {mean_absolute_error(y_actual_kelembapan, y_pred_kelembapan):.2f}")
print(f"RMSE : {np.sqrt(mean_squared_error(y_actual_kelembapan, y_pred_kelembapan)):.2f}")
print(f"R²   : {r2_score(y_actual_kelembapan, y_pred_kelembapan):.2f}")

# MQ135
y_actual_mq135 = y_mq135_val
y_pred_mq135 = model_mq135.predict(X_val)

print("\n=== Evaluasi MQ135 ===")
print(f"MAE  : {mean_absolute_error(y_actual_mq135, y_pred_mq135):.2f}")
print(f"RMSE : {np.sqrt(mean_squared_error(y_actual_mq135, y_pred_mq135)):.2f}")
print(f"R²   : {r2_score(y_actual_mq135, y_pred_mq135):.2f}")
