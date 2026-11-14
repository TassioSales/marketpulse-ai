import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
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
            
            # 1. Medias Moveis
            df["sma_7"] = df["value"].rolling(window=7, min_periods=1).mean()
            df["sma_21"] = df["value"].rolling(window=21, min_periods=1).mean()
            df["sma_50"] = df["value"].rolling(window=50, min_periods=1).mean()
            df["pct_change"] = df["value"].pct_change() * 100
            
            # 2. Bandas de Bollinger (20 periodos, 2 desvios padrao)
            rolling_mean_20 = df["value"].rolling(window=20, min_periods=5).mean()
            rolling_std_20 = df["value"].rolling(window=20, min_periods=5).std().fillna(0)
            df["upper_band"] = rolling_mean_20 + (2 * rolling_std_20)
            df["lower_band"] = rolling_mean_20 - (2 * rolling_std_20)
            df["is_anomaly"] = (df["value"] > df["upper_band"]) | (df["value"] < df["lower_band"])
            
            # 3. RSI (Relative Strength Index - 14 periodos)
            delta = df["value"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = gain / (loss.replace(0, np.nan))
            df["rsi"] = 100 - (100 / (1 + rs))
            df["rsi"] = df["rsi"].fillna(50)
            
            # 4. MACD (12, 26, 9)
            exp1 = df["value"].ewm(span=12, adjust=False).mean()
            exp2 = df["value"].ewm(span=26, adjust=False).mean()
            df["macd"] = exp1 - exp2
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
            df["macd_hist"] = df["macd"] - df["macd_signal"]

            self.dataframes[key] = df

    def get_summary_metrics(self):
        """Retorna indicadores-chave avançados para os cards executivos."""
        summary = {}
        for key, df in self.dataframes.items():
            if df.empty:
                continue
            sinfo = self.raw_data["series"][key]
            latest_val = float(df["value"].iloc[-1])
            prev_val = float(df["value"].iloc[-2]) if len(df) > 1 else latest_val
            daily_change = ((latest_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0.0
            
            idx_30 = max(0, len(df) - 30)
            val_30 = float(df["value"].iloc[idx_30])
            change_30d = ((latest_val - val_30) / val_30) * 100 if val_30 != 0 else 0.0
            
            recent_pct = df["pct_change"].dropna().tail(30)
            volatility = float(recent_pct.std()) if not recent_pct.empty else 0.0
            
            rsi_val = float(df["rsi"].iloc[-1])
            if rsi_val > 70:
                rsi_status = "Sobrecomprado (Alerta de Correção)"
            elif rsi_val < 30:
                rsi_status = "Sobrevendido (Oportunidade de Entrada)"
            else:
                rsi_status = "Neutro / Equilibrado"

            # Suporte e Resistencia
            recent_high = float(df["value"].tail(60).max())
            recent_low = float(df["value"].tail(60).min())

            summary[key] = {
                "name": sinfo["name"],
                "unit": sinfo["unit"],
                "category": sinfo["category"],
                "icon": sinfo.get("icon", "📌"),
                "current_value": round(latest_val, 4),
                "daily_change_pct": round(daily_change, 2),
                "change_30d_pct": round(change_30d, 2),
                "min_year": round(float(df["value"].min()), 4),
                "max_year": round(float(df["value"].max()), 4),
                "support_60d": round(recent_low, 4),
                "resistance_60d": round(recent_high, 4),
                "volatility_30d": round(volatility, 2),
                "rsi": round(rsi_val, 1),
                "rsi_status": rsi_status,
                "last_date": df["date"].iloc[-1].strftime("%d/%m/%Y")
            }
        return summary

    def generate_advanced_chart(self, key: str):
        """Gera um grafico profissional de terminal financeiro de 2 paineis (Preço + RSI)."""
        if key not in self.dataframes or self.dataframes[key].empty:
            return None
        
        df = self.dataframes[key]
        sinfo = self.raw_data["series"][key]
        
        # Subplots: Painel 1 (Preco e Medias) 75% da altura; Painel 2 (RSI) 25%
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            row_heights=[0.72, 0.28]
        )
        
        # 1. Banda de Bollinger
        if len(df) > 15:
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["upper_band"],
                mode="lines", line=dict(width=0),
                showlegend=False, hoverinfo="skip"
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["lower_band"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor="rgba(16, 185, 129, 0.08)",
                name="Banda de Bollinger (2σ)", hoverinfo="skip"
            ), row=1, col=1)
            
            # Médias Móveis
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["sma_7"],
                mode="lines", name="SMA 7d",
                line=dict(color="#38bdf8", width=1.5)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["sma_21"],
                mode="lines", name="SMA 21d",
                line=dict(color="#f59e0b", width=1.5, dash="dot")
            ), row=1, col=1)

        # 2. Linha Principal de Valor
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["value"],
            mode="lines+markers" if len(df) < 30 else "lines",
            name=sinfo["name"],
            line=dict(color="#10b981", width=2.5),
            marker=dict(size=5, color="#10b981")
        ), row=1, col=1)

        # 3. Marcadores de Anomalias Estatísticas
        anomalies = df[df["is_anomaly"]]
        if not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies["date"], y=anomalies["value"],
                mode="markers", name="Anomalia Extrema (2σ)",
                marker=dict(color="#ef4444", size=8, symbol="diamond-open", line=dict(width=2, color="#ef4444"))
            ), row=1, col=1)

        # 4. Projeção Monte Carlo / Cone de Tendência (próximos 15 dias)
        if len(df) > 20:
            last_date = df["date"].iloc[-1]
            last_val = df["value"].iloc[-1]
            future_dates = [last_date + timedelta(days=i) for i in range(1, 16)]
            std_recent = df["pct_change"].tail(20).std() / 100 * last_val
            
            proj_upper = [last_val + (std_recent * np.sqrt(i) * 1.5) for i in range(1, 16)]
            proj_lower = [max(0.1, last_val - (std_recent * np.sqrt(i) * 1.5)) for i in range(1, 16)]
            
            fig.add_trace(go.Scatter(
                x=[last_date] + future_dates,
                y=[last_val] + proj_upper,
                mode="lines", line=dict(color="rgba(168, 85, 247, 0.4)", width=1, dash="dash"),
                showlegend=False, hoverinfo="skip"
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=[last_date] + future_dates,
                y=[last_val] + proj_lower,
                mode="lines", line=dict(color="rgba(168, 85, 247, 0.4)", width=1, dash="dash"),
                fill="tonexty", fillcolor="rgba(168, 85, 247, 0.12)",
                name="Projeção Estocástica 15d"
            ), row=1, col=1)

        # 5. Painel Inferior: RSI (14)
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["rsi"],
            mode="lines", name="RSI (14)",
            line=dict(color="#a855f7", width=1.5)
        ), row=2, col=1)

        # Linhas de sobrecompra (70) e sobrevenda (30) no RSI
        fig.add_hline(y=70, line=dict(color="#ef4444", width=1, dash="dot"), row=2, col=1)
        fig.add_hline(y=30, line=dict(color="#10b981", width=1, dash="dot"), row=2, col=1)
        fig.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.02)", line_width=0, row=2, col=1)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13, 17, 23, 0.95)",
            margin=dict(l=45, r=20, t=35, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11)
            ),
            hovermode="x unified"
        )
        
        fig.update_yaxes(title_text=sinfo["unit"], gridcolor="#21262d", row=1, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], gridcolor="#21262d", row=2, col=1)
        fig.update_xaxes(gridcolor="#21262d")

        return fig.to_json()

    def get_correlation_matrix(self):
        """Calcula matriz de correlacao cruzada de Pearson entre todas as series."""
        combined = pd.DataFrame()
        for key, df in self.dataframes.items():
            if not df.empty and len(df) > 10:
                s = df.set_index("date")["value"]
                combined[self.raw_data["series"][key]["name"].split(" (")[0]] = s
        
        combined = combined.dropna()
        if combined.empty:
            return {}
        
        corr = combined.corr().round(2)
        return {
            "columns": list(corr.columns),
            "values": corr.values.tolist()
        }

if __name__ == "__main__":
    engine = MarketAnalyticsEngine()
    print("Métricas:")
    print(list(engine.get_summary_metrics().keys()))
    print("Correlação:")
    print(engine.get_correlation_matrix())
