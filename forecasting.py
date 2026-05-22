import pandas as pd
import torch
from chronos import ChronosPipeline


DEFAULT_TARGET = "Global_active_power"
DEFAULT_MODEL = "amazon/chronos-t5-small"


def load_consumption_series(csv_path, target_col=DEFAULT_TARGET):
    df = pd.read_csv(csv_path)
    df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
    timestamps = pd.to_datetime(
        df["Date"] + " " + df["Time"],
        format="%d/%m/%y %H:%M:%S",
        errors="coerce",
    )
    df = df.assign(timestamp=timestamps).dropna(subset=["timestamp"])
    df = df.set_index("timestamp").sort_index()

    series = df[target_col].astype("float")
    series = series.resample("1h").mean()
    series = series.interpolate().ffill().bfill()
    return series


def analyze_series(series):
    missing_pct = float(series.isna().mean() * 100.0)
    return {
        "rows": int(series.shape[0]),
        "start": series.index.min().isoformat(),
        "end": series.index.max().isoformat(),
        "mean": float(series.mean()),
        "std": float(series.std()),
        "min": float(series.min()),
        "max": float(series.max()),
        "missing_pct": round(missing_pct, 4),
    }


def select_day_series(series, day_str):
    day = pd.to_datetime(day_str, errors="coerce")
    if pd.isna(day):
        return pd.Series(dtype="float")
    day_date = day.date()
    return series[series.index.date == day_date]


def load_forecasting_pipeline(model_id=DEFAULT_MODEL, device_map="cpu"):
    return ChronosPipeline.from_pretrained(
        model_id,
        device_map=device_map,
        dtype=torch.float32,
    )


def forecast_next_value(pipeline, history_values, prediction_length=1, context_length=24):
    history = history_values[-context_length:]
    if len(history) == 0:
        return 0.0

    context = torch.tensor(history, dtype=torch.float32)
    forecast = pipeline.predict(context, prediction_length)
    median = torch.quantile(forecast[0], 0.5, dim=0)
    return float(median[0].item())
