import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json
import os

from data_collector import update_all_market_data

class MarketAnalyticsEngine:
    def __init__(self):
        self.raw_data = update_all_market_data()
        self.dataframes = {}
        self._build_dataframes()

    def _build_dataframes(self):
        for key, sinfo in self.raw_data.get("series", {}).items():
            records = sinfo.get("data", [])
            if not records:
                continue
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
            df = df.sort_values("date").reset_index(drop=True)
            
            # Calculo de medias moveis e volatilidade
            df["sma_7"] = df["value"].rolling(window=7, min_periods=1).mean()
            df["sma_30"] = df["value"].rolling(window=30, min_periods=1).mean()
            df["pct_change"] = df["value"].pct_change() * 100
            
            # Anomalias: desvio de mais de 2 sigmas da media movel de 30 dias
            rolling_std = df["value"].rolling(window=30, min_periods=5).std().fillna(0)
            df["upper_band"] = df["sma_30"] + (2 * rolling_std)
            df["lower_band"] = df["sma_30"] - (2 * rolling_std)
            df["is_anomaly"] = (df["value"] > df["upper_band"]) | (df["value"] < df["lower_band"])
            
            self.dataframes[key] = df

    def get_summary_metrics(self):
        """Retorna indicadores-chave consolidados para o dashboard executivo."""
        summary = {}
        for key, df in self.dataframes.items():
            if df.empty:
                continue
            sinfo = self.raw_data["series"][key]
            latest_val = float(df["value"].iloc[-1])
            prev_val = float(df["value"].iloc[-2]) if len(df) > 1 else latest_val
            daily_change = ((latest_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0.0
            
            # Variacao em 30 dias
            idx_30 = max(0, len(df) - 30)
            val_30 = float(df["value"].iloc[idx_30])
            change_30d = ((latest_val - val_30) / val_30) * 100 if val_30 != 0 else 0.0
            
            # Volatilidade (desvio padrao percentual dos ultimos 30 dias)
            recent_pct = df["pct_change"].dropna().tail(30)
            volatility = float(recent_pct.std()) if not recent_pct.empty else 0.0
            
            summary[key] = {
                "name": sinfo["name"],
                "unit": sinfo["unit"],
                "category": sinfo["category"],
                "current_value": round(latest_val, 4),
                "daily_change_pct": round(daily_change, 2),
                "change_30d_pct": round(change_30d, 2),
                "min_year": round(float(df["value"].min()), 4),
                "max_year": round(float(df["value"].max()), 4),
                "volatility_30d": round(volatility, 2),
                "last_date": df["date"].iloc[-1].strftime("%d/%m/%Y")
            }
        return summary

    def generate_plotly_chart(self, key: str):
        """Gera um grafico Plotly interativo de alta definicao em formato JSON."""
        if key not in self.dataframes or self.dataframes[key].empty:
            return None
        
        df = self.dataframes[key]
        sinfo = self.raw_data["series"][key]
        
        fig = go.Figure()
        
        # Banda superior e inferior (Bollinger / Incerteza)
        if len(df) > 15:
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["upper_band"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                name="Teto Estatístico"
            ))
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["lower_band"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(16, 185, 129, 0.08)",
                showlegend=False,
                name="Canal de Volatilidade"
            ))
            
            # Linha da Media Movel 30d
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["sma_30"],
                mode="lines",
                name="Média Móvel (30d)",
                line=dict(color="#f59e0b", width=1.5, dash="dot")
            ))
        
        # Linha Principal de Valores
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="lines+markers" if len(df) < 30 else "lines",
            name=sinfo["name"],
            line=dict(color="#10b981", width=2.5),
            marker=dict(size=6, color="#10b981")
        ))
        
        # Marcadores de anomalia
        anomalies = df[df["is_anomaly"]]
        if not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies["date"],
                y=anomalies["value"],
                mode="markers",
                name="Anomalia Estatística",
                marker=dict(color="#ef4444", size=9, symbol="diamond")
            ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17, 24, 39, 0.8)",
            margin=dict(l=40, r=20, t=30, b=40),
            xaxis=dict(
                gridcolor="#374151",
                showgrid=True,
                zeroline=False
            ),
            yaxis=dict(
                gridcolor="#374151",
                showgrid=True,
                zeroline=False,
                title=sinfo["unit"]
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified"
        )
        
        return fig.to_json()

if __name__ == "__main__":
    engine = MarketAnalyticsEngine()
    metrics = engine.get_summary_metrics()
    print("Resumo de Métricas Estatísticas:")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
