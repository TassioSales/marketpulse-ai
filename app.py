from flask import Flask, render_template_string, jsonify, request
import json
import os
from analytics_engine import MarketAnalyticsEngine
from ai_agent import MarketPulseAIAgent

app = Flask(__name__)
engine = MarketAnalyticsEngine()
agent = MarketPulseAIAgent(engine)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MarketPulse AI — Plataforma de Inteligência Econômica & Dados</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow { box-shadow: 0 0 25px -5px rgba(16, 185, 129, 0.25); }
    </style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen">
    <!-- Header -->
    <header class="border-b border-gray-800/80 bg-gray-900/60 sticky top-0 z-40 backdrop-blur-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-black text-gray-950 shadow-lg shadow-emerald-500/20">
                    MP
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight flex items-center gap-2">
                        MarketPulse <span class="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">AI</span>
                        <span class="text-[10px] uppercase tracking-wider font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">v1.0 Live</span>
                    </h1>
                    <p class="text-xs text-gray-400">Inteligência de Dados Macroeconômicos & Análise Preditiva</p>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <button onclick="refreshData()" class="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    Atualizar Dados
                </button>
                <button onclick="generateReport()" class="px-4 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-gray-950 shadow-md shadow-emerald-500/20 transition flex items-center gap-2 glow">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    Gerar Briefing Executivo com IA
                </button>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        <!-- KPI Cards Grid -->
        <section id="kpi-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <!-- Renderizado via JS -->
        </section>

        <!-- Main Chart Section -->
        <section class="glass rounded-2xl p-6 space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
                <div>
                    <h2 class="text-base font-semibold text-gray-100 flex items-center gap-2">
                        📈 Série Histórica Interativa & Projeção Estatística
                    </h2>
                    <p class="text-xs text-gray-400">Canal estatístico de volatilidade (Bollinger) e médias móveis</p>
                </div>
                <div class="flex flex-wrap gap-1.5" id="chart-selectors">
                    <button onclick="loadChart('dolar')" class="chart-tab active px-3 py-1 text-xs rounded-lg font-medium transition bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Dólar (USD)</button>
                    <button onclick="loadChart('selic')" class="chart-tab px-3 py-1 text-xs rounded-lg font-medium transition bg-gray-800 text-gray-400 border border-gray-700/60 hover:text-gray-200">Selic (% a.a.)</button>
                    <button onclick="loadChart('ipca')" class="chart-tab px-3 py-1 text-xs rounded-lg font-medium transition bg-gray-800 text-gray-400 border border-gray-700/60 hover:text-gray-200">IPCA Mensal</button>
                    <button onclick="loadChart('ic_br_agro')" class="chart-tab px-3 py-1 text-xs rounded-lg font-medium transition bg-gray-800 text-gray-400 border border-gray-700/60 hover:text-gray-200">Commodities Agro</button>
                    <button onclick="loadChart('ic_br_geral')" class="chart-tab px-3 py-1 text-xs rounded-lg font-medium transition bg-gray-800 text-gray-400 border border-gray-700/60 hover:text-gray-200">IC-Br Geral</button>
                </div>
            </div>
            
            <!-- Plotly Container -->
            <div id="plotly-container" class="w-full h-[420px]">
                <div class="h-full flex items-center justify-center text-gray-500 text-sm">Carregando dados da série...</div>
            </div>
        </section>

        <!-- Executive AI Report Modal / Card -->
        <section id="report-section" class="glass rounded-2xl p-6 space-y-4 hidden">
            <div class="flex items-center justify-between pb-3 border-b border-gray-800">
                <div class="flex items-center gap-2.5">
                    <span class="w-3 h-3 rounded-full bg-emerald-400 animate-ping"></span>
                    <h3 class="text-base font-semibold text-gray-100">Síntese Estratégica do Agente de IA</h3>
                </div>
                <button onclick="document.getElementById('report-section').classList.add('hidden')" class="text-gray-400 hover:text-gray-200 text-sm">Fechar ✕</button>
            </div>
            <div id="report-content" class="prose prose-invert max-w-none text-sm leading-relaxed text-gray-300">
                <!-- Conteudo Markdown renderizado aqui -->
            </div>
        </section>
    </main>

    <footer class="border-t border-gray-800/80 py-6 text-center text-xs text-gray-500">
        MarketPulse AI • Desenvolvido por <span class="text-emerald-400 font-medium">Tássio Sales</span> • Dados Oficiais do Banco Central do Brasil (SGS)
    </footer>

    <script>
        let currentSeries = 'dolar';

        async function fetchMetrics() {
            const res = await fetch('/api/metrics');
            const data = await res.json();
            renderKPIs(data);
        }

        function renderKPIs(metrics) {
            const container = document.getElementById('kpi-grid');
            container.innerHTML = '';
            for (const [key, item] of Object.entries(metrics)) {
                const isPositive = item.change_30d_pct >= 0;
                const changeColor = isPositive ? 'text-emerald-400' : 'text-rose-400';
                const sign = isPositive ? '+' : '';
                
                const card = document.createElement('div');
                card.className = 'glass rounded-xl p-4 space-y-2 hover:border-gray-700 transition cursor-pointer';
                card.onclick = () => loadChart(key);
                card.innerHTML = `
                    <div class="flex items-center justify-between text-[11px] font-medium text-gray-400">
                        <span>${item.category}</span>
                        <span class="${changeColor} font-semibold">${sign}${item.change_30d_pct}% (30d)</span>
                    </div>
                    <div class="text-xl font-bold text-gray-100 tracking-tight">
                        ${item.current_value.toLocaleString('pt-BR')} <span class="text-xs font-normal text-gray-400">${item.unit}</span>
                    </div>
                    <div class="text-xs text-gray-300 font-medium truncate">${item.name}</div>
                    <div class="pt-1.5 flex justify-between text-[10px] text-gray-500 border-t border-gray-800/60">
                        <span>Min: ${item.min_year}</span>
                        <span>Max: ${item.max_year}</span>
                    </div>
                `;
                container.appendChild(card);
            }
        }

        async function loadChart(key) {
            currentSeries = key;
            document.querySelectorAll('.chart-tab').forEach(b => {
                b.className = 'chart-tab px-3 py-1 text-xs rounded-lg font-medium transition bg-gray-800 text-gray-400 border border-gray-700/60 hover:text-gray-200';
            });
            event.target.className = 'chart-tab active px-3 py-1 text-xs rounded-lg font-medium transition bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';

            const res = await fetch(`/api/chart/${key}`);
            const chartData = await res.json();
            Plotly.newPlot('plotly-container', chartData.data, chartData.layout, { responsive: true, displayModeBar: false });
        }

        async function generateReport() {
            const section = document.getElementById('report-section');
            const content = document.getElementById('report-content');
            section.classList.remove('hidden');
            content.innerHTML = '<div class="py-8 text-center text-gray-400">Gerando análise preditiva e recomendações executivas com IA...</div>';
            
            const res = await fetch('/api/generate-report');
            const data = await res.json();
            content.innerHTML = marked.parse(data.markdown);
            section.scrollIntoView({ behavior: 'smooth' });
        }

        async function refreshData() {
            await fetch('/api/refresh', { method: 'POST' });
            await fetchMetrics();
            await loadChart(currentSeries);
        }

        // Init
        fetchMetrics();
        loadChart('dolar');
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/metrics")
def get_metrics():
    return jsonify(engine.get_summary_metrics())

@app.route("/api/chart/<key>")
def get_chart(key):
    chart_json = engine.generate_plotly_chart(key)
    if chart_json:
        return jsonify(json.loads(chart_json))
    return jsonify({"error": "Série não encontrada"}), 404

@app.route("/api/generate-report")
def generate_report():
    report = agent.generate_executive_report()
    return jsonify(report)

@app.route("/api/refresh", methods=["POST"])
def refresh_cache():
    global engine, agent
    from data_collector import update_all_market_data
    update_all_market_data(force=True)
    engine = MarketAnalyticsEngine()
    agent = MarketPulseAIAgent(engine)
    return jsonify({"status": "updated"})

if __name__ == "__main__":
    print("MarketPulse AI rodando em http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
