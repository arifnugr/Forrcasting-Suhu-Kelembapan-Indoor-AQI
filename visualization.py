import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import json

# --- Load Data Asli ---
raw_df = pd.read_csv("sensor_data.csv", parse_dates=["timestamp"])
raw_df = raw_df.sort_values("timestamp")
raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"])
raw_df["date"] = raw_df["timestamp"].dt.date

# Ambil data mulai tanggal 1 bulan ini
first_day = pd.Timestamp.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
raw_df = raw_df[raw_df["timestamp"] >= first_day]

# --- Load Data Prediksi ---
with open("forecast_result.json", "r") as f:
    forecast = json.load(f)["forecast"]

forecast_df = pd.DataFrame(forecast)
forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"])
forecast_df["date"] = forecast_df["timestamp"].dt.date

# Gabungkan semua tanggal unik dari data asli dan prediksi
all_dates = sorted(set(raw_df["date"].unique()).union(set(forecast_df["date"].unique())))

# --- Inisialisasi Dash App ---
app = Dash(__name__)
app.title = "Dashboard Forecasting"

# --- Layout ---
app.layout = html.Div([
    html.H2("Dashboard Forecasting Suhu, Kelembapan & Kualitas Udara", style={"textAlign": "center"}),

    html.Label("Pilih Tanggal:"),
    dcc.Dropdown(
        id="date-selector",
        options=[{"label": str(d), "value": str(d)} for d in all_dates],
        value=str(min(all_dates)),
        clearable=False,
        style={"width": "300px", "marginBottom": "20px"}
    ),

    dcc.Graph(id="forecast-graph", style={"height": "600px"}),

    html.Div("Data asli dari sensor_data.csv, prediksi dari forecast_result.json", 
             id="footer", style={"textAlign": "center", "marginTop": "30px", "color": "#666"})
])

# --- Callback ---
@app.callback(
    Output("forecast-graph", "figure"),
    Input("date-selector", "value")
)
def update_graph(selected_date):
    selected_date = pd.to_datetime(selected_date).date()

    # Filter data
    df_actual = raw_df[raw_df["date"] == selected_date]
    df_pred = forecast_df[forecast_df["date"] == selected_date]

    fig = go.Figure()

    # --- SUHU ---
    # Data asli (putus-putus)
    fig.add_trace(go.Scatter(
        x=df_actual["timestamp"],
        y=df_actual["suhu"],
        mode="lines+markers",
        name="Suhu Asli (°C)",
        line=dict(color="orange", dash="dot"),
        hovertemplate="<b>Waktu:</b> %{x}<br><b>Suhu Asli:</b> %{y:.1f} °C<extra></extra>"
    ))
    # Data prediksi
    fig.add_trace(go.Scatter(
        x=df_pred["timestamp"],
        y=df_pred["suhu"],
        mode="lines+markers",
        name="Suhu Prediksi (°C)",
        line=dict(color="orange", dash="solid"),
        hovertemplate="<b>Waktu:</b> %{x}<br><b>Suhu Prediksi:</b> %{y:.1f} °C<br><b>Kelembapan:</b> %{customdata[0]:.1f} %<br><b>MQ135:</b> %{customdata[1]}<br><b>Label:</b> %{customdata[2]}<br><b>Udara:</b> %{customdata[3]}<extra></extra>",
        customdata=df_pred[["kelembapan", "mq135", "label_suhu_kelembapan", "label_kualitas_udara"]]
    ))

    # --- KELEMBAPAN ---
    fig.add_trace(go.Scatter(
        x=df_actual["timestamp"],
        y=df_actual["kelembapan"],
        mode="lines+markers",
        name="Kelembapan Asli (%)",
        line=dict(color="blue", dash="dot"),
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=df_pred["timestamp"],
        y=df_pred["kelembapan"],
        mode="lines+markers",
        name="Kelembapan Prediksi (%)",
        line=dict(color="blue", dash="solid"),
        hoverinfo="skip"
    ))

    # --- MQ135 (Y-Axis ke-2) ---
    fig.add_trace(go.Scatter(
        x=df_actual["timestamp"],
        y=df_actual["mq135"],
        mode="lines+markers",
        name="MQ135 Asli",
        line=dict(color="green", dash="dot"),
        yaxis="y2",
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=df_pred["timestamp"],
        y=df_pred["mq135"],
        mode="lines+markers",
        name="MQ135 Prediksi",
        line=dict(color="green", dash="solid"),
        yaxis="y2",
        hoverinfo="skip"
    ))

    # --- Layout ---
    fig.update_layout(
        title=f"Data & Prediksi untuk {selected_date}",
        xaxis_title="Waktu",
        yaxis_title="Suhu / Kelembapan",
        yaxis2=dict(
            title="MQ135",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white"
    )

    return fig

# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
