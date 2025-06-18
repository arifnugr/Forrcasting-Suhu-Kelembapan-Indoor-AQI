import paho.mqtt.client as mqtt
import json
import csv
import os

csv_file = "sensor_data.csv"

# Fungsi untuk menentukan label kombinasi suhu & kelembapan
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

# Fungsi untuk menentukan kualitas udara
def label_kualitas_udara(mq):
    if mq <= 500:
        return "sangat baik"
    elif mq <= 650:
        return "baik"
    elif mq <= 800:
        return "cukup buruk"
    elif mq <= 1300:
        return "buruk"
    else:
        return "berbahaya"

# Baca ID terakhir dari file jika ada
def get_last_id():
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            reader = list(csv.reader(f))
            if len(reader) > 1:
                try:
                    return int(reader[-1][0]) + 1
                except:
                    return 1
    return 1

data_id = get_last_id()

# Jika file belum ada, buat dengan header
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "timestamp", "suhu", "kelembapan", "label_suhu_kelembapan", "mq135", "label_kualitas_udara"])

# Callback saat konek ke broker
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke broker, kode:", rc)
    client.subscribe("esp32/sensor")

# Callback saat pesan diterima
def on_message(client, userdata, msg):
    global data_id
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)

        suhu = float(data['suhu'])
        kelembapan = float(data['kelembaban'])
        mq135 = int(data['mq135'])

        label_iklim = label_suhu_kelembapan(suhu, kelembapan)
        label_udara = label_kualitas_udara(mq135)

        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([data_id, data['waktu'], suhu, kelembapan, label_iklim, mq135, label_udara])

        print(f"[{data['waktu']}] ID {data_id} | Suhu: {suhu}°C, Kelembapan: {kelembapan}%, MQ135: {mq135} → {label_iklim}, {label_udara}")
        data_id += 1

    except Exception as e:
        print("Gagal parsing atau menulis data:", e)

# Inisialisasi client MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("broker.hivemq.com", 1883, 60)
client.loop_forever()
