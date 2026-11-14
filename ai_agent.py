import json
import os
from datetime import datetime
from analytics_engine import MarketAnalyticsEngine

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

class MarketPulseAIAgent:
    def __init__(self, engine: MarketAnalyticsEngine):
        self.engine = engine
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def generate_executive_report(self) -> dict:
        """Gera um relatorio analitico sintetizado e estruturado com inteligencia economica."""
        metrics = self.engine.get_summary_metrics()
        now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        dolar = metrics.get("dolar", {})
        ipca = metrics.get("ipca", {})
        selic = metrics.get("selic", {})
        agro = metrics.get("ic_br_agro", {})
        comm = metrics.get("ic_br_geral", {})

        # Diagnostico Macro
        dolar_val = dolar.get("current_value", 0.0)
        dolar_30d = dolar.get("change_30d_pct", 0.0)
        selic_val = selic.get("current_value", 0.0)
        ipca_val = ipca.get("current_value", 0.0)
        agro_30d = agro.get("change_30d_pct", 0.0)

        # Classificacao de cenario
        if dolar_30d > 4.0:
            dolar_status = "Pressionado em Alta (Desvalorização Cambial)"
            dolar_impact = "Aumento nos custos de insumos importados, fertilizantes e eletrônicos; benefício direto para exportadores de grãos e carnes."
        elif dolar_30d < -3.0:
            dolar_status = "Em Arrefecimento (Valorização do Real)"
            dolar_impact = "Alívio na inflação de atacado, barateando fretes e matérias-primas importadas."
        else:
            dolar_status = "Estável em Faixa Lateral"
            dolar_impact = "Previsibilidade para planejamento de compras e estoques de médio prazo."

        # Analise Agro
        if agro_30d > 5.0:
            agro_trend = "Forte Demanda e Preços Aquecidos (+{:.1f}%)".format(agro_30d)
            agro_advice = "Excelente momento para produtores capitalizarem margens. Criadores intensivos (aves, suínos e pequenos animais) devem travar custos de ração/farelo."
        else:
            agro_trend = "Preços Equilibrados (+{:.1f}%)".format(agro_30d)
            agro_advice = "Manter gestão rigorosa de custos e buscar agregação de valor local."

        markdown_content = f"""# 📊 Relatório Executivo de Inteligência Econômica & Mercado
*Gerado por **MarketPulse AI Engine** em {now_str}*

---

## 🧭 1. Resumo Executivo (Macro & Cenário)
O cenário econômico consolidado pelo **MarketPulse AI** reflete um ambiente de política monetária restritiva, com a **Taxa Selic mantida em {selic_val:.2f}% a.a.** e inflação mensal (IPCA) em **{ipca_val:.2f}%**. O mercado cambial opera com o Dólar a **R$ {dolar_val:.4f}** ({dolar_status}, com variação de {dolar_30d:+.2f}% em 30 dias).

Paralelamente, o **Índice de Commodities Agropecuárias (IC-Br)** registra variação de **{agro_30d:+.2f}%**, apontando firmeza na demanda por grãos e proteínas no mercado interno e externo.

---

## 📈 2. Painel Consolidado de Indicadores Chave

| Indicador | Categoria | Valor Atual | Variação 30d | Mín. Ano | Máx. Ano |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dólar Comercial** | Câmbio | R$ {dolar_val:.4f} | `{dolar_30d:+.2f}%` | R$ {dolar.get('min_year', 0):.4f} | R$ {dolar.get('max_year', 0):.4f} |
| **Meta Selic** | Juros | {selic_val:.2f}% a.a. | `{selic.get('change_30d_pct', 0):+.2f}%` | {selic.get('min_year', 0):.2f}% | {selic.get('max_year', 0):.2f}% |
| **IPCA Mensal** | Inflação | {ipca_val:.2f}% | `{ipca.get('change_30d_pct', 0):+.2f}%` | {ipca.get('min_year', 0):.2f}% | {ipca.get('max_year', 0):.2f}% |
| **IC-Br Commodities** | Geral | {comm.get('current_value', 0):,.0f} pts | `{comm.get('change_30d_pct', 0):+.2f}%` | {comm.get('min_year', 0):,.0f} | {comm.get('max_year', 0):,.0f} |
| **IC-Br Agropecuária** | Agro/Alimentos | {agro.get('current_value', 0):,.0f} pts | `{agro_30d:+.2f}%` | {agro.get('min_year', 0):,.0f} | {agro.get('max_year', 0):,.0f} |

---

## 🔍 3. Análise Setorial e Impacto Local

### 🌐 Câmbio & Importações
* **Status:** {dolar_status}
* **Impacto Operacional:** {dolar_impact}

### 🌾 Agronegócio, Nutrição Animal e Pequenos Negócios
* **Tendência:** {agro_trend}
* **Diagnóstico:** {agro_advice}
* **Oportunidade de Ouro:** Setores com baixo custo de insumos locais (como criação de organismos e rações alternativas, tenébrios, insumos orgânicos e feiras diretas ao consumidor) capturam margens líquidas superiores a 60% por não dependerem de maquinário importado dolarizado.

---

## ⚠️ 4. Matriz de Riscos & Recomendações Estratégicas

### 🔴 Riscos a Monitorar:
1. **Custo do Crédito:** Com Selic em {selic_val:.2f}%, o custo de capital de giro é elevado. Evitar endividamento bancário de curto prazo para expansão física.
2. **Repasse de Preços:** O varejo de consumo final demonstra elasticidade reduzida; aumentos agressivos de preço tendem a reduzir o volume de vendas.

### 🟢 Recomendações Táticas:
* **Para Pequenos Negócios & Produtores:** Priorizar vendas em canais digitais próprios (WhatsApp, Mercado Livre, Shopee) eliminando intermediários e intermediando entregas locais.
* **Gestão de Caixa:** Aproveitar rendimentos de 100% do CDI em reservas líquidas (garantindo retorno real confortável acima da inflação).
* **Eficiência Operacional:** Automatizar processos de prospecção e controle com IA para operar com equipe enxuta.

---
*Relatório gerado autonomamente pela engine MarketPulse AI — Dados oficiais Banco Central do Brasil (SGS).*
"""

        report_file = os.path.join(REPORTS_DIR, "latest_briefing.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return {
            "timestamp": now_str,
            "markdown": markdown_content,
            "dolar_status": dolar_status,
            "agro_trend": agro_trend,
            "metrics": metrics
        }

if __name__ == "__main__":
    engine = MarketAnalyticsEngine()
    agent = MarketPulseAIAgent(engine)
    report = agent.generate_executive_report()
    print("Relatório gerado com sucesso!")
    print(report["markdown"][:400] + "...")
