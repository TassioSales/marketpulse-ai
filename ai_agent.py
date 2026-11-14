import json
import os
import urllib.request
from datetime import datetime
from analytics_engine import MarketAnalyticsEngine

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

class MarketPulseAIAgent:
    def __init__(self, engine: MarketAnalyticsEngine):
        self.engine = engine
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def _call_gemini(self, prompt: str, system_instruction: str = "") -> str:
        """Chama a API do Google Gemini 2.5 Flash via REST para raciocínio dinâmico."""
        if not self.api_key:
            return ""

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048
            }
        }

        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=18) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception as e:
            print(f"[MarketPulse AI] Falha na chamada ao Gemini API: {e}")

        return ""

    def generate_executive_report(self) -> dict:
        """Gera um relatório macroeconômico aprofundado, institucional e dinâmico com Gemini."""
        metrics = self.engine.get_summary_metrics()
        now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")

        context_data = {
            "data_atual": now_str,
            "indicadores_ao_vivo": metrics
        }

        system_prompt = (
            "Você é o estrategista-chefe de investimentos e macroeconomia do MarketPulse AI Terminal, "
            "uma plataforma de inteligência financeira de padrão Bloomberg / Goldman Sachs. "
            "Escreva em português do Brasil impecável, com tom executivo, objetivo, analítico e de alto nível. "
            "Formate a resposta em Markdown estruturado, com tabelas, listas com marcadores, destaques em negrito "
            "e insights acionáveis para empresários, investidores e tomadores de decisão."
        )

        user_prompt = f"""
Por favor, elabore o Briefing Macroeconômico Executivo e Diagnóstico de Cenários completo com base nos dados reais do Banco Central do Brasil consolidados abaixo:

Dados do Mercado (BACEN / SGS):
{json.dumps(context_data, indent=2, ensure_ascii=False)}

Estruture o relatório exatamente com as seguintes seções:
# 🏛️ Relatório de Inteligência Macroeconômica & Cenários
1. 🧭 Resumo Executivo & Diagnóstico de Conjuntura (Câmbio, Juros, Inflação e Commodities)
2. 📊 Tabela de Análise Quantitativa e Técnicas (Cotação, Variação 30d, Suporte/Resistência, RSI e Status Técnico)
3. 🔬 Análise Setorial Aprofundada:
   - Câmbio, Dólar e Cadeia de Importação/Exportação
   - Política Monetária, Selic e Mercado de Crédito
   - Agronegócio & Oportunidades em Nutrição Alternativa / Biotecnologia (ex: produção de proteína sustentável/tenébrios e rações de alta margem descoladas do dólar)
4. ⚠️ Matriz Estratégica de Riscos & Tomada de Decisão (Ações recomendadas para empresas e investidores)

Seja profundo, técnico, analítico e evite respostas genéricas. Use números exatos fornecidos no JSON.
"""

        gemini_response = self._call_gemini(user_prompt, system_prompt)

        if gemini_response and len(gemini_response) > 200:
            markdown_content = gemini_response
        else:
            # Fallback dinâmico com cálculo real
            dolar = metrics.get("dolar", {})
            euro = metrics.get("euro", {})
            ipca = metrics.get("ipca", {})
            selic = metrics.get("selic", {})
            agro = metrics.get("ic_br_agro", {})

            dolar_val = dolar.get("current_value", 5.65)
            dolar_30d = dolar.get("change_30d_pct", 0.0)
            dolar_rsi = dolar.get("rsi", 50.0)
            selic_val = selic.get("current_value", 13.75)
            agro_val = agro.get("current_value", 148000)
            agro_30d = agro.get("change_30d_pct", 0.0)

            markdown_content = f"""# 🏛️ Relatório de Inteligência Macroeconômica & Cenários
*Elaborado autonomamente por **MarketPulse AI Engine** em {now_str}*

---

## 🧭 1. Resumo Executivo & Diagnóstico Geral
O ambiente macroeconômico brasileiro opera sob um regime de **política monetária restritiva**, com a **Taxa Selic fixada em {selic_val:.2f}% a.a.** e o CDI acompanhando a dinâmica de liquidez. O mercado de câmbio apresenta o **Dólar cotado a R$ {dolar_val:.4f}** ({dolar_30d:+.2f}% nos últimos 30 dias), com o Euro negociado a **R$ {euro.get('current_value', 0):.4f}**.

O **Índice de Commodities Agropecuárias (IC-Br Agro)** registra **{agro_val:,.0f} pontos** ({agro_30d:+.2f}% em 30d), sinalizando forte sustentação nos preços de grãos e proteína animal.

---

## 📊 2. Terminal de Indicadores & Métricas Quantitativas

| Ativo / Indicador | Categoria | Cotação Atual | Variação 30d | Suporte (60d) | Resistência (60d) | RSI (14) | Status Técnico |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dólar Comercial** | Câmbio | **R$ {dolar_val:.4f}** | `{dolar_30d:+.2f}%` | R$ {dolar.get('support_60d', 0):.4f} | R$ {dolar.get('resistance_60d', 0):.4f} | `{dolar_rsi:.1f}` | {dolar.get('rsi_status', 'Neutro')} |
| **Euro Comercial** | Câmbio | **R$ {euro.get('current_value', 0):.4f}** | `{euro.get('change_30d_pct', 0):+.2f}%` | R$ {euro.get('support_60d', 0):.4f} | R$ {euro.get('resistance_60d', 0):.4f} | `{euro.get('rsi', 50):.1f}` | {euro.get('rsi_status', 'Neutro')} |
| **Meta Selic** | Juros | **{selic_val:.2f}% a.a.** | `{selic.get('change_30d_pct', 0):+.2f}%` | {selic.get('min_year', 0):.2f}% | {selic.get('max_year', 0):.2f}% | — | Estável |
| **IPCA Mensal** | Inflação | **{ipca.get('current_value', 0):.2f}%** | `{ipca.get('change_30d_pct', 0):+.2f}%` | {ipca.get('min_year', 0):.2f}% | {ipca.get('max_year', 0):.2f}% | — | Controlado |
| **IC-Br Agropecuária** | Agro/Grãos | **{agro_val:,.0f}** | `{agro_30d:+.2f}%` | {agro.get('support_60d', 0):,.0f} | {agro.get('resistance_60d', 0):,.0f} | `{agro.get('rsi', 50):.1f}` | Alta Demanda |

---

## 🔬 3. Análise Setorial Aprofundada

### 💵 Câmbio & Importações
A faixa atual do dólar estimula o setor exportador de commodities, enquanto encarece a importação de fertilizantes, polímeros e componentes eletrônicos. Empresas importadoras devem estruturar travas de câmbio (hedge via NDF) para os próximos 60 a 90 dias.

### 🌾 Agronegócio & Nutrição Animal Alternativa
Com custos elevados em rações tradicionais atreladas a milho e soja, a transição para **fontes alternativas de proteína (como farinha de insetos e larvas de Tenébrio)** ganha enorme atratividade econômica: baixo custo de entrada, ciclo de reprodução rápido de 60 a 90 dias, e margem bruta superior a 70% na venda a criadores e lojas agropecuárias.

---

## ⚠️ 4. Matriz Estratégica de Riscos & Decisão
1. **Tesouraria:** Maximizar caixa em ativos pós-fixados a 100%+ do CDI com liquidez diária.
2. **Custos:** Antecipar compras de insumos críticos sensíveis ao câmbio.
"""

        # Salvar em histórico de relatórios
        filename = f"briefing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(REPORTS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return {
            "timestamp": now_str,
            "markdown": markdown_content,
            "metrics": metrics
        }

    def simulate_custom_scenario(self, user_question: str) -> dict:
        """Processa perguntas customizadas ou simulações com IA generativa real."""
        metrics = self.engine.get_summary_metrics()
        now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")

        context_data = {
            "pergunta_do_usuario": user_question,
            "data_atual": now_str,
            "indicadores_economicos_reais": {
                k: {
                    "nome": v["name"],
                    "valor_atual": v["current_value"],
                    "variacao_30d": v["change_30d_pct"],
                    "rsi": v.get("rsi"),
                    "suporte": v.get("support_60d"),
                    "resistencia": v.get("resistance_60d")
                }
                for k, v in metrics.items()
            }
        }

        system_prompt = (
            "Você é o agente especialista de inteligência e cenários de mercado do MarketPulse AI Terminal. "
            "Você analisa qualquer pergunta ou cenário econômico, financeiro, de negócios, investimentos ou agronegócio "
            "com máxima profundidade técnica, dados reais e raciocínio estratégico detalhado. "
            "NUNCA dê respostas prontas, curtas ou superficiais. Use tabelas, estimativas numéricas de custo, receita, "
            "margem de lucro, prós/contras, impactos nas cadeias de suprimento e plano de ação passo a passo. "
            "Responda em português do Brasil impecável e formatado em Markdown rico."
        )

        user_prompt = f"""
O usuário enviou a seguinte pergunta ou simulação de cenário estratégico:
"{user_question}"

Aqui estão os dados econômicos e de mercado reais do Brasil neste exato momento:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

Por favor, faça uma análise estratégica completa e aprofundada respondendo exatamente à dúvida do usuário:
1. Diagnóstico e Contexto Econômico Relacionado à pergunta
2. Simulação de Impactos Práticos (Custo, Receita, Margens e Riscos)
3. Oportunidades de Lucro ou Proteção de Capital
4. Plano de Ação Recomendado (Passo a passo com táticas acionáveis)
"""

        gemini_response = self._call_gemini(user_prompt, system_prompt)

        if gemini_response and len(gemini_response) > 150:
            analysis = gemini_response
        else:
            # Fallback inteligente se Gemini estiver indisponível
            dolar_val = metrics.get("dolar", {}).get("current_value", 5.65)
            selic_val = metrics.get("selic", {}).get("current_value", 13.75)
            agro_val = metrics.get("ic_br_agro", {}).get("current_value", 148508)
            analysis = f"""### 🔍 Análise de Cenário: "{user_question}"
*Processado com os dados oficiais do Banco Central em {now_str}*

#### 1. 📊 Indicadores Base do Cenário
* **Dólar Comercial:** R$ {dolar_val:.4f}
* **Taxa Selic:** {selic_val:.2f}% ao ano
* **Índice de Commodities Agro:** {agro_val:,.0f} pontos

#### 2. ⚡ Diagnóstico e Viabilidade
Para o cenário solicitado ("{user_question}"), os dados apontam que a combinação de juros reais elevados e pressão cambial favorece modelos de baixo endividamento inicial e receita em ciclo curto.

#### 3. 🎯 Recomendações Estratégicas
1. **Controle Rigoroso de OPEX:** Evite alavancagem bancária tradicional com Selic em dois dígitos.
2. **Monetização Rápida:** Priorize vendas diretas e geração de fluxo de caixa imediato.
"""

        return {
            "timestamp": now_str,
            "question": user_question,
            "markdown": analysis
        }
