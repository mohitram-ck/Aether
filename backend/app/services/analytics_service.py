import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.transaction import Transaction
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")


async def get_transaction_timeseries(db: AsyncSession, hours: int = 24) -> pd.DataFrame:
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(
            func.date_trunc("minute", Transaction.created_at).label("minute"),
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total_amount")
        )
        .where(Transaction.created_at >= since)
        .group_by("minute")
        .order_by("minute")
    )
    rows = result.fetchall()
    if not rows:
        return pd.DataFrame(columns=["minute", "count", "total_amount"])
    return pd.DataFrame(rows, columns=["minute", "count", "total_amount"])


def forecast_load(series: pd.Series, steps: int = 10) -> list:
    if len(series) < 5:
        return [float(series.mean()) if len(series) > 0 else 0.0] * steps
    try:
        model = ARIMA(series, order=(2, 1, 2))
        fitted = model.fit()
        forecast = fitted.forecast(steps=steps)
        return [round(max(0, f), 2) for f in forecast.tolist()]
    except Exception:
        return [float(series.mean())] * steps


def detect_velocity_fraud(series: pd.Series, threshold: float = 3.0) -> dict:
    if len(series) < 3:
        return {"is_anomaly": False, "reason": "Insufficient data"}
    mean = series.mean()
    std = series.std()
    if std == 0:
        return {"is_anomaly": False, "reason": "No variance in data"}
    latest = series.iloc[-1]
    z_score = (latest - mean) / std
    if z_score > threshold:
        return {
            "is_anomaly": True,
            "reason": f"Transaction velocity spike detected (z-score: {round(z_score, 2)})",
            "z_score": round(z_score, 2)
        }
    return {"is_anomaly": False, "z_score": round(z_score, 2)}


def detect_amount_anomaly(series: pd.Series, threshold: float = 3.0) -> dict:
    if len(series) < 3:
        return {"is_anomaly": False, "reason": "Insufficient data"}
    mean = series.mean()
    std = series.std()
    if std == 0:
        return {"is_anomaly": False, "reason": "No variance"}
    latest = series.iloc[-1]
    z_score = (latest - mean) / std
    if z_score > threshold:
        return {
            "is_anomaly": True,
            "reason": f"Unusual amount spike detected (z-score: {round(z_score, 2)})",
            "z_score": round(z_score, 2)
        }
    return {"is_anomaly": False, "z_score": round(z_score, 2)}


async def run_full_analysis(db: AsyncSession) -> dict:
    df = await get_transaction_timeseries(db)

    if df.empty:
        return {
            "status": "insufficient_data",
            "message": "Not enough transactions to analyze yet",
            "forecast": [],
            "velocity_anomaly": {"is_anomaly": False},
            "amount_anomaly": {"is_anomaly": False}
        }

    count_series = df["count"].astype(float)
    amount_series = df["total_amount"].astype(float)

    forecast = forecast_load(count_series, steps=10)
    velocity = detect_velocity_fraud(count_series)
    amount = detect_amount_anomaly(amount_series)

    overall_fraud_risk = velocity["is_anomaly"] or amount["is_anomaly"]

    return {
        "status": "ok",
        "data_points_analyzed": len(df),
        "forecast_next_10_minutes": forecast,
        "velocity_anomaly": velocity,
        "amount_anomaly": amount,
        "fraud_risk_detected": overall_fraud_risk,
        "analyzed_at": datetime.utcnow().isoformat()
    }