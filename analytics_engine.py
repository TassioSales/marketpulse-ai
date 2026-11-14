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
            
            # Variação percentual diária/periódica
            df["pct_change"] = df["value"].pct_change() * 100
            
            # 1. Médias Móveis (apenas se houver dados suficientes)
            if len(df) >= 7:
                df["sma_7"] = df["value"].rolling(window=7, min_periods=1).mean()
            else:
                df["sma_7"] = np.nan

            if len(df) >= 21:
                df["sma_21"] = df["value"].rolling(window=21, min_periods=1).mean()
                df["sma_50"] = df["value"].rolling(window=50, min_periods=1).mean()
            else:
                df["sma_21"] = np.nan
                df["sma_50"] = np.nan
            
            # 2. Bandas de Bollinger (20 períodos, 2 desvios padrão)
            if len(df) >= 20:
                rolling_mean_20 = df["value"].rolling(window=20, min_periods=5).mean()
                rolling_std_20 = df["value"].rolling(window=20, min_periods=5).std().fillna(0)
                df["upper_band"] = rolling_mean_20 + (2 * rolling_std_20)
                df["lower_band"] = rolling_mean_20 - (2 * rolling_std_20)
                df["is_anomaly"] = (df["value"] > df["upper_band"]) | (df["value"] < df["lower_band"])
            else:
                df["upper_band"] = np.nan
                df["lower_band"] = np.nan
                df["is_anomaly"] = False
            
            # 3. RSI (Relative Strength Index)
            if len(df) >= 14:
                delta = df["value"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
                rs = gain / (loss.replace(0, np.nan))
                df["rsi"] = 100 - (100 / (1 + rs))
                df["rsi"] = df["rsi"].fillna(50)
            elif len(df) >= 3:
                # RSI rápido para dados mensais de menor amostragem
                delta = df["value"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=3, min_periods=1).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=3, min_periods=1).mean()
                rs = gain / (loss.replace(0, np.nan))
                df["rsi"] = 100 - (100 / (1 + rs))
                df["rsi"] = df["rsi"].fillna(50)
            else:
                df["rsi"] = 50.0

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
            
            idx_30 = max(0, len(df) - min(30, len(df)))
            val_30 = float(df["value"].iloc[idx_30])
            change_30d = ((latest_val - val_30) / val_30) * 100 if val_30 != 0 else 0.0
            
            recent_pct = df["pct_change"].dropna().tail(30)
            volatility = float(recent_pct.std()) if not recent_pct.empty else 0.0
            
            rsi_val = float(df["rsi"].iloc[-1])
            if rsi_val > 70:
                rsi_status = "Sobrecomprado (Alerta de Realização)"
            elif rsi_val < 30:
                rsi_status = "Sobrevendido (Oportunidade)"
            else:
                rsi_status = "Neutro / Equilibrado"

            # Suporte e Resistência dos últimos 60 registros
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
        """Gera um gráfico profissional com visual moderno Bloomberg/TradingView sem glitches."""
        if key not in self.dataframes or self.dataframes[key].empty:
            return None
        
        df = self.dataframes[key]
        sinfo = self.raw_data["series"][key]
        is_monthly = len(df) <= 15

        if is_monthly:
            # Gráfico de Painel Único para séries mensais (IPCA, IC-Br Agro, etc)
            fig = go.Figure()

            # Barras ou Linha de Alta Definição com marcadores
            fig.add_trace(go.Bar(
                x=df["date"],
                y=df["value"],
                name=sinfo["name"],
                marker=dict(
                    color=df["pct_change"].apply(lambda v: "#10b981" if v >= 0 else "#f43f5e"),
                    line=dict(color="#21262d", width=1)
                ),
                hovertemplate="<b>Data:</b> %{x|%B/%Y}<br><b>Valor:</b> %{y:,.4f} " + sinfo["unit"] + "<extra></extra>"
            ))

            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["value"],
                mode="lines+markers",
                name="Tendência",
                line=dict(color="#38bdf8", width=2),
                marker=dict(size=8, color="#38bdf8", symbol="circle")
            ))

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13, 17, 23, 0.95)",
                margin=dict(l=55, r=25, t=30, b=35),
                hoverlabel=dict(
                    bgcolor="#161b22",
                    bordercolor="#30363d",
                    font=dict(color="#f0f6fc", size=12, family="JetBrains Mono")
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=11, color="#8b949e")
                ),
                hovermode="x unified"
            )
            fig.update_yaxes(title_text=sinfo["unit"], gridcolor="#21262d", zerolinecolor="#30363d")
            fig.update_xaxes(
                gridcolor="#21262d",
                tickformat="%b/%Y",
                rangeselector=dict(
                    buttons=list([
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="Tudo")
                    ]),
                    bgcolor="#161b22",
                    activecolor="#10b981",
                    font=dict(color="#c9d1d9", size=11)
                )
            )
            return fig.to_json()

        # Para séries diárias (Dólar, Euro, Selic, CDI): Subplots 2 painéis
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.07,
            row_heights=[0.74, 0.26]
        )
        
        # 1. Bandas de Bollinger (área sombreada elegante)
        if len(df) >= 20 and not df["upper_band"].isna().all():
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["upper_band"],
                mode="lines", line=dict(width=0),
                showlegend=False, hoverinfo="skip"
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["lower_band"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor="rgba(16, 185, 129, 0.07)",
                name="Bollinger (2σ)", hoverinfo="skip"
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

        # 2. Linha Principal de Cotação com Preenchimento Suave
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["value"],
            mode="lines",
            name=sinfo["name"].split(" (")[0],
            line=dict(color="#10b981", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.04)",
            hovertemplate="<b>%{x|%d/%m/%Y}:</b> %{y:,.4f} " + sinfo["unit"] + "<extra></extra>"
        ), row=1, col=1)

        # 3. Marcadores de Anomalias Reais (Apenas se houver pontos estatisticamente fora do canal)
        if "is_anomaly" in df:
            anomalies = df[df["is_anomaly"]]
            if not anomalies.empty and len(anomalies) <= 15:
                fig.add_trace(go.Scatter(
                    x=anomalies["date"], y=anomalies["value"],
                    mode="markers", name="Anomalia (2σ)",
                    marker=dict(color="#ef4444", size=7, symbol="diamond", line=dict(width=1, color="#ffffff"))
                ), row=1, col=1)

        # 4. Painel Inferior: RSI (14)
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["rsi"],
            mode="lines", name="RSI (14)",
            line=dict(color="#a855f7", width=1.8),
            hovertemplate="<b>RSI:</b> %{y:.1f}<extra></extra>"
        ), row=2, col=1)

        # Linhas de sobrecompra (70) e sobrevenda (30) no RSI
        fig.add_hline(y=70, line=dict(color="rgba(239, 68, 68, 0.6)", width=1, dash="dot"), row=2, col=1)
        fig.add_hline(y=30, line=dict(color="rgba(16, 185, 129, 0.6)", width=1, dash="dot"), row=2, col=1)
        fig.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.02)", line_width=0, row=2, col=1)

        # Customização Avançada de Layout Dark Mode
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13, 17, 23, 0.95)",
            margin=dict(l=55, r=25, t=30, b=35),
            hoverlabel=dict(
                bgcolor="#161b22",
                bordercolor="#30363d",
                font=dict(color="#f0f6fc", size=12, family="JetBrains Mono")
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11, color="#8b949e")
            ),
            hovermode="x unified"
        )
        
        fig.update_yaxes(title_text=sinfo["unit"], gridcolor="#21262d", zerolinecolor="#30363d", row=1, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], gridcolor="#21262d", zerolinecolor="#30363d", row=2, col=1)
        
        # Range Selector para zoom instantâneo (1M, 3M, 6M, 1A, Tudo)
        fig.update_xaxes(
            gridcolor="#21262d",
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(step="all", label="Tudo")
                ]),
                bgcolor="#161b22",
                activecolor="#10b981",
                font=dict(color="#c9d1d9", size=11)
            ),
            row=1, col=1
        )
        fig.update_xaxes(gridcolor="#21262d", row=2, col=1)

        return fig.to_json()

    def get_correlation_matrix(self):
        """Calcula matriz de correlação cruzada de Pearson entre todas as séries."""
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
    print("Chart JSON OK:", len(engine.generate_advanced_chart("dolar")) > 500)
