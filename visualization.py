import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import json

# Load forecast data
with open("forecast_result.json", "r") as f:
    data = json.load(f)["forecast"]

# Convert to DataFrame
df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date

# Initialize Dash app
app = Dash(__name__)
app.title = "Dashboard Forecasting"

# Layout
app.layout = html.Div([
    html.H2("Dashboard Forecasting Suhu, Kelembapan & Kualitas Udara", style={"textAlign": "center"}),

    html.Label("Pilih Tanggal:"),
    dcc.Dropdown(
        id="date-selector",
        options=[{"label": str(d), "value": str(d)} for d in sorted(df["date"].unique())],
        value=str(df["date"].min()),
        clearable=False,
        style={"width": "300px", "marginBottom": "20px"}
    ),

    dcc.Graph(id="forecast-graph", style={"height": "600px"}),

    html.Div("Data berasal dari file forecast_result.json", id="footer", style={"textAlign": "center", "marginTop": "30px", "color": "#666"})
])

# Callback untuk memperbarui grafik berdasarkan tanggal
@app.callback(
    Output("forecast-graph", "figure"),
    Input("date-selector", "value")
)
def update_graph(selected_date):
    dff = df[df["date"] == pd.to_datetime(selected_date).date()]

    fig = go.Figure()

    # Garis suhu
    fig.add_trace(go.Scatter(
        x=dff["timestamp"],
        y=dff["suhu"],
        mode="lines+markers",
        name="Suhu (°C)",
        line=dict(color="orange"),
        hovertemplate=(
            "<b>Waktu:</b> %{x}<br>"
            "<b>Suhu:</b> %{y:.1f} °C<br>"
            "<b>Kelembapan:</b> %{customdata[0]:.1f} %<br>"
            "<b>MQ135:</b> %{customdata[1]}<br>"
            "<b>Label Suhu-Kelembapan:</b> %{customdata[2]}<br>"
            "<b>Label Udara:</b> %{customdata[3]}<extra></extra>"
        ),
        customdata=dff[["kelembapan", "mq135", "label_suhu_kelembapan", "label_kualitas_udara"]]
    ))

    # Garis kelembapan
    fig.add_trace(go.Scatter(
        x=dff["timestamp"],
        y=dff["kelembapan"],
        mode="lines+markers",
        name="Kelembapan (%)",
        line=dict(color="blue"),
        hoverinfo="skip"
    ))

    # Garis MQ135
    fig.add_trace(go.Scatter(
        x=dff["timestamp"],
        y=dff["mq135"],
        mode="lines+markers",
        name="MQ135",
        line=dict(color="green"),
        yaxis="y2",
        hoverinfo="skip"
    ))

    fig.update_layout(
        title=f"Forecast untuk {selected_date}",
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

# Jalankan aplikasi
if __name__ == "__main__":
    app.run(debug=True)
