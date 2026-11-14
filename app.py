from flask import Flask, render_template_string, jsonify, request, Response
import json
import os
import io
import csv
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
    <title>MarketPulse AI — Bloomberg-Grade Intelligence Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(13, 17, 23, 0.75); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.07); }
        .glass-card { background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-emerald { box-shadow: 0 0 30px -5px rgba(16, 185, 129, 0.3); }
        .glow-purple { box-shadow: 0 0 30px -5px rgba(168, 85, 247, 0.3); }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #30363d; }
    </style>
</head>
<body class="bg-[#090d13] text-gray-100 min-h-screen flex flex-col selection:bg-emerald-500/30 selection:text-emerald-300">

    <!-- Top Live Ticker Ribbon -->
    <div class="border-b border-gray-800/80 bg-[#0d1117]/90 px-4 py-2 overflow-x-auto whitespace-nowrap flex items-center gap-6 text-xs font-mono">
        <div class="flex items-center gap-2 text-emerald-400 font-semibold tracking-wide">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            LIVE BACEN FEED
        </div>
        <div id="ticker-items" class="flex items-center gap-6 text-gray-300">
            <!-- Ticker via JS -->
        </div>
    </div>

    <!-- Main Navigation Bar -->
    <header class="border-b border-gray-800 bg-[#0d1117]/80 sticky top-0 z-40 backdrop-blur-xl">
        <div class="max-w-[1600px] mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center space-x-3.5">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-400 to-cyan-500 flex items-center justify-center font-black text-gray-950 text-base shadow-lg shadow-emerald-500/20">
                    MP
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-extrabold tracking-tight">MarketPulse <span class="bg-gradient-to-r from-emerald-400 to-cyan-300 bg-clip-text text-transparent">AI</span></span>
                        <span class="text-[10px] uppercase tracking-wider font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full">Terminal v2.0 Pro</span>
                    </div>
                    <p class="text-[11px] text-gray-400 font-medium">Plataforma de Inteligência Preditiva, Modelagem Quantitativa & IA Estratégica</p>
                </div>
            </div>

            <!-- Tab Switches -->
            <nav class="flex items-center p-1 rounded-xl bg-gray-900/90 border border-gray-800">
                <button onclick="switchTab('terminal')" id="tab-btn-terminal" class="tab-btn active px-4 py-1.5 text-xs font-semibold rounded-lg transition bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    📈 Terminal Gráfico
                </button>
                <button onclick="switchTab('ai-warroom')" id="tab-btn-ai-warroom" class="tab-btn px-4 py-1.5 text-xs font-medium rounded-lg text-gray-400 hover:text-gray-200 transition">
                    🤖 AI War Room
                </button>
                <button onclick="switchTab('correlation')" id="tab-btn-correlation" class="tab-btn px-4 py-1.5 text-xs font-medium rounded-lg text-gray-400 hover:text-gray-200 transition">
                    🔬 Matriz de Correlação
                </button>
                <button onclick="switchTab('data-table')" id="tab-btn-data-table" class="tab-btn px-4 py-1.5 text-xs font-medium rounded-lg text-gray-400 hover:text-gray-200 transition">
                    📋 Dados Brutos
                </button>
            </nav>

            <!-- Actions -->
            <div class="flex items-center space-x-2.5">
                <button onclick="refreshData()" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800/80 hover:bg-gray-700 text-gray-300 border border-gray-700 transition flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    Sincronizar
                </button>
                <button onclick="triggerFullBriefing()" class="px-4 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-gray-950 shadow-lg shadow-emerald-500/20 transition flex items-center gap-2 glow-emerald">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    Gerar Briefing Executivo
                </button>
            </div>
        </div>
    </header>

    <!-- Main Workspace -->
    <main class="max-w-[1600px] w-full mx-auto px-4 sm:px-6 py-6 space-y-6 flex-1">

        <!-- Executive KPI Cards -->
        <section id="kpi-grid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
            <!-- Cards via JS -->
        </section>

        <!-- VIEW 1: TERMINAL GRÁFICO -->
        <section id="view-terminal" class="space-y-4">
            <div class="glass-card rounded-2xl p-5 space-y-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-gray-800">
                    <div class="space-y-0.5">
                        <h2 class="text-sm font-bold text-gray-100 flex items-center gap-2" id="chart-main-title">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                            Gráfico Avançado Multidimensional com Médias Móveis & Bandas de Bollinger (2σ)
                        </h2>
                        <p class="text-[11px] text-gray-400" id="chart-sub-title">Canal estatístico de volatilidade, médias (SMA 7/21) e subpainel RSI (14)</p>
                    </div>
                    
                    <!-- Asset Selectors -->
                    <div class="flex flex-wrap gap-1.5" id="asset-selectors">
                        <!-- Populated via JS -->
                    </div>
                </div>

                <!-- Plotly Chart Frame -->
                <div id="plotly-container" class="w-full h-[520px]">
                    <div class="h-full flex items-center justify-center text-gray-500 text-xs font-mono">
                        Carregando modelo estatístico...
                    </div>
                </div>

                <!-- Quick Stats Footer for Selected Asset -->
                <div id="asset-details-bar" class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 pt-3 border-t border-gray-800/80 text-xs font-mono">
                    <!-- Populated via JS -->
                </div>
            </div>
        </section>

        <!-- VIEW 2: AI WAR ROOM (SALA DE GUERRA & SIMULAÇÕES) -->
        <section id="view-ai-warroom" class="space-y-6 hidden">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Prompt & Scenarios Column -->
                <div class="glass-card rounded-2xl p-5 space-y-5 lg:col-span-1">
                    <div>
                        <h3 class="text-sm font-bold text-gray-100 flex items-center gap-2">
                            🤖 AI Analyst Copilot
                        </h3>
                        <p class="text-xs text-gray-400 mt-1">Faça perguntas estratégicas sobre o mercado brasileiro ou simule cenários de estresse.</p>
                    </div>

                    <!-- Scenario Quick Buttons -->
                    <div class="space-y-2">
                        <label class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Cenários Prontos para Simulação:</label>
                        <div class="flex flex-col gap-2">
                            <button onclick="askScenario('Simular impacto se o dólar disparar para a faixa de R$ 6,00 no agronegócio e fretes')" class="text-left px-3.5 py-2.5 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-xs text-gray-300 transition flex items-center justify-between">
                                <span>💵 Dólar a R$ 6,00 (Estresse Cambial)</span>
                                <span class="text-emerald-400">➔</span>
                            </button>
                            <button onclick="askScenario('Análise de viabilidade e margens para comercializar Tenébrios e farinha de insetos no cenário atual')" class="text-left px-3.5 py-2.5 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-xs text-gray-300 transition flex items-center justify-between">
                                <span>🐛 Mercado de Tenébrios & Alimento Vivo</span>
                                <span class="text-emerald-400">➔</span>
                            </button>
                            <button onclick="askScenario('Qual o impacto da Selic alta na demanda do varejo e na tomada de crédito para pequenas empresas?')" class="text-left px-3.5 py-2.5 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-xs text-gray-300 transition flex items-center justify-between">
                                <span>🏦 Impacto da Selic Alta no Varejo</span>
                                <span class="text-emerald-400">➔</span>
                            </button>
                            <button onclick="triggerFullBriefing()" class="text-left px-3.5 py-2.5 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-xs text-gray-300 transition flex items-center justify-between">
                                <span>📊 Briefing Macroeconômico Institucional</span>
                                <span class="text-emerald-400">➔</span>
                            </button>
                        </div>
                    </div>

                    <!-- Custom Prompt Input -->
                    <div class="space-y-2 pt-2 border-t border-gray-800">
                        <label class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Pergunta Customizada:</label>
                        <div class="flex gap-2">
                            <input id="custom-prompt-input" type="text" placeholder="Ex: Qual o melhor setor para investir hoje?" class="flex-1 bg-gray-950 border border-gray-800 rounded-xl px-3.5 py-2 text-xs text-gray-100 placeholder-gray-500 focus:outline-none focus:border-emerald-500">
                            <button onclick="submitCustomPrompt()" class="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-gray-950 rounded-xl font-bold text-xs transition">
                                Enviar
                            </button>
                        </div>
                    </div>
                </div>

                <!-- AI Output Display -->
                <div class="glass-card rounded-2xl p-6 lg:col-span-2 space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-800">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-sm">
                                ⚡
                            </div>
                            <div>
                                <h3 class="text-sm font-bold text-gray-100" id="report-title">Síntese Estratégica do Agente de IA</h3>
                                <p class="text-[11px] text-gray-400" id="report-timestamp">Aguardando solicitação...</p>
                            </div>
                        </div>

                        <!-- Audio Synthesis Button -->
                        <button onclick="speakReport()" id="btn-audio" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 transition flex items-center gap-1.5 glow-purple">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"/></svg>
                            Ouvir com Voz de IA
                        </button>
                    </div>

                    <div id="ai-output" class="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed text-gray-300 min-h-[350px]">
                        <div class="py-16 text-center text-gray-500">
                            Clique em um dos cenários ao lado ou no botão "Gerar Briefing Executivo" para visualizar a análise completa.
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- VIEW 3: MATRIZ DE CORRELAÇÃO -->
        <section id="view-correlation" class="space-y-4 hidden">
            <div class="glass-card rounded-2xl p-6 space-y-4">
                <div>
                    <h2 class="text-sm font-bold text-gray-100 flex items-center gap-2">
                        🔬 Matriz de Correlação Cruzada (Pearson Matrix)
                    </h2>
                    <p class="text-xs text-gray-400 mt-0.5">Mede a intensidade da relação entre Câmbio, Inflação, Juros e Commodities brasileiras.</p>
                </div>
                <div class="overflow-x-auto pt-2">
                    <table id="correlation-table" class="w-full text-xs font-mono text-left border-collapse">
                        <!-- Populated via JS -->
                    </table>
                </div>
            </div>
        </section>

        <!-- VIEW 4: TABELA DE DADOS BRUTOS -->
        <section id="view-data-table" class="space-y-4 hidden">
            <div class="glass-card rounded-2xl p-6 space-y-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-gray-800">
                    <div>
                        <h2 class="text-sm font-bold text-gray-100">📋 Inspetor de Dados Históricos</h2>
                        <p class="text-xs text-gray-400">Séries temporais auditáveis e download em formato estruturado.</p>
                    </div>
                    <div class="flex items-center gap-3">
                        <select id="table-series-select" onchange="renderRawTable()" class="bg-gray-900 border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-gray-200">
                            <!-- Populated via JS -->
                        </select>
                        <a id="btn-export-csv" href="/api/export-csv/dolar" download class="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 transition">
                            Exportar CSV
                        </a>
                    </div>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-xs font-mono text-left border-collapse">
                        <thead class="bg-gray-900 sticky top-0 border-b border-gray-800 text-gray-400">
                            <tr>
                                <th class="p-2.5">Data</th>
                                <th class="p-2.5">Valor Original</th>
                                <th class="p-2.5">Média Móvel (7d)</th>
                                <th class="p-2.5">Média Móvel (21d)</th>
                                <th class="p-2.5">Variação %</th>
                                <th class="p-2.5">RSI (14)</th>
                            </tr>
                        </thead>
                        <tbody id="raw-table-body" class="divide-y divide-gray-800/60 text-gray-300">
                            <!-- Populated via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-800/80 bg-[#0d1117] py-4 px-6 text-center text-xs text-gray-500 flex flex-wrap items-center justify-between gap-2">
        <div>MarketPulse AI Engine • Arquitetura por <span class="text-emerald-400 font-semibold">Tássio Sales</span></div>
        <div class="flex items-center gap-4 text-gray-400 text-[11px] font-mono">
            <span>BACEN SGS API: <strong class="text-emerald-400">CONNECTED</strong></span>
            <span>DATA SCIENCE: <strong class="text-cyan-400">PANDAS / NUMPY</strong></span>
            <span>MODEL: <strong class="text-purple-400">GENAI QUANT</strong></span>
        </div>
    </footer>

    <!-- Scripts -->
    <script>
        let currentSeries = 'dolar';
        let allMetrics = {};
        let currentRawData = {};
        let lastReportText = '';

        async function init() {
            await fetchMetrics();
            await loadChart(currentSeries);
            await loadCorrelation();
            populateAssetSelectors();
        }

        async function fetchMetrics() {
            const res = await fetch('/api/metrics');
            allMetrics = await res.json();
            renderTicker(allMetrics);
            renderKPIs(allMetrics);
        }

        function renderTicker(metrics) {
            const container = document.getElementById('ticker-items');
            container.innerHTML = '';
            for (const [key, item] of Object.entries(metrics)) {
                const isPos = item.change_30d_pct >= 0;
                const color = isPos ? 'text-emerald-400' : 'text-rose-400';
                const sign = isPos ? '+' : '';
                container.innerHTML += `
                    <span class="cursor-pointer hover:text-white" onclick="loadChart('${key}')">
                        <strong>${key.toUpperCase()}</strong>: ${item.current_value.toLocaleString('pt-BR')} 
                        <span class="${color}">(${sign}${item.change_30d_pct}%)</span>
                    </span>
                `;
            }
        }

        function renderKPIs(metrics) {
            const container = document.getElementById('kpi-grid');
            container.innerHTML = '';
            for (const [key, item] of Object.entries(metrics)) {
                const isPos = item.change_30d_pct >= 0;
                const changeColor = isPos ? 'text-emerald-400' : 'text-rose-400';
                const sign = isPos ? '+' : '';
                
                const card = document.createElement('div');
                card.className = `glass rounded-xl p-3.5 space-y-1.5 transition cursor-pointer hover:border-emerald-500/40 ${key === currentSeries ? 'border-emerald-500/50 bg-emerald-500/5' : ''}`;
                card.id = `card-${key}`;
                card.onclick = () => loadChart(key);
                card.innerHTML = `
                    <div class="flex items-center justify-between text-[11px] font-medium text-gray-400">
                        <span class="flex items-center gap-1">${item.icon} ${item.name.split(' ')[0]}</span>
                        <span class="${changeColor} font-mono font-bold">${sign}${item.change_30d_pct}%</span>
                    </div>
                    <div class="text-base font-extrabold text-gray-100 font-mono tracking-tight">
                        ${item.current_value.toLocaleString('pt-BR')} <span class="text-[10px] font-normal text-gray-400">${item.unit}</span>
                    </div>
                    <div class="flex items-center justify-between text-[10px] text-gray-400 font-mono pt-1 border-t border-gray-800">
                        <span>RSI: <strong class="${item.rsi > 70 ? 'text-rose-400' : item.rsi < 30 ? 'text-emerald-400' : 'text-purple-400'}">${item.rsi}</strong></span>
                        <span class="text-gray-500">30d</span>
                    </div>
                `;
                container.appendChild(card);
            }
        }

        function populateAssetSelectors() {
            const container = document.getElementById('asset-selectors');
            const selectDropdown = document.getElementById('table-series-select');
            container.innerHTML = '';
            selectDropdown.innerHTML = '';

            for (const [key, item] of Object.entries(allMetrics)) {
                const isPos = item.daily_change_pct >= 0;
                const changeColor = isPos ? 'text-emerald-400' : 'text-rose-400';
                const activeClass = key === currentSeries 
                    ? 'px-3 py-1.5 text-xs rounded-xl font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm' 
                    : 'px-3 py-1.5 text-xs rounded-xl font-medium bg-gray-900/90 text-gray-300 border border-gray-800 hover:border-gray-700 hover:text-white';
                
                container.innerHTML += `
                    <button onclick="loadChart('${key}')" id="btn-chart-${key}" class="chart-pill ${activeClass} flex items-center gap-2 transition">
                        <span>${item.icon} ${item.name.split(' (')[0]}</span>
                        <span class="font-mono font-bold text-white">${item.current_value.toLocaleString('pt-BR')}</span>
                        <span class="text-[10px] font-mono ${changeColor}">(${isPos ? '+' : ''}${item.daily_change_pct}%)</span>
                    </button>
                `;

                selectDropdown.innerHTML += `
                    <option value="${key}">${item.icon} ${item.name}</option>
                `;
            }
        }

        async function loadChart(key) {
            currentSeries = key;
            populateAssetSelectors();

            const item = allMetrics[key];
            if (item) {
                const isPos = item.daily_change_pct >= 0;
                const changeColor = isPos ? 'text-emerald-400' : 'text-rose-400';
                document.getElementById('chart-main-title').innerHTML = `
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                    <span class="text-white font-extrabold">${item.icon} ${item.name}</span>
                    <span class="font-mono font-bold text-emerald-300 ml-2">${item.current_value.toLocaleString('pt-BR')} ${item.unit}</span>
                    <span class="text-xs font-mono ${changeColor} ml-1.5 font-bold">(${isPos ? '+' : ''}${item.daily_change_pct}% hoje)</span>
                `;
                document.getElementById('chart-sub-title').innerHTML = `
                    Suporte 60d: <b class="text-gray-200">${item.support_60d}</b> · Resistência 60d: <b class="text-gray-200">${item.resistance_60d}</b> · Volatilidade 30d: <b class="text-amber-300">${item.volatility_30d}%</b> · RSI (14): <b class="text-purple-300">${item.rsi} (${item.rsi_status})</b> · Data: <b class="text-gray-300">${item.last_date}</b>
                `;
            }

            renderKPIs(allMetrics);

            const res = await fetch(`/api/chart/${key}`);
            const chartData = await res.json();
            Plotly.newPlot('plotly-container', chartData.data, chartData.layout, { responsive: true, displayModeBar: false });

            // Update bottom stats bar
            if (item) {
                document.getElementById('asset-details-bar').innerHTML = `
                    <div class="p-2.5 rounded-xl bg-gray-900/60 border border-gray-800">
                        <div class="text-gray-500 text-[10px] font-semibold">SUPORTE 60D</div>
                        <div class="text-emerald-400 font-bold text-sm">${item.support_60d} <span class="text-[10px] text-gray-500">${item.unit}</span></div>
                    </div>
                    <div class="p-2.5 rounded-xl bg-gray-900/60 border border-gray-800">
                        <div class="text-gray-500 text-[10px] font-semibold">RESISTÊNCIA 60D</div>
                        <div class="text-rose-400 font-bold text-sm">${item.resistance_60d} <span class="text-[10px] text-gray-500">${item.unit}</span></div>
                    </div>
                    <div class="p-2.5 rounded-xl bg-gray-900/60 border border-gray-800">
                        <div class="text-gray-500 text-[10px] font-semibold">MÍNIMO ANUAL</div>
                        <div class="text-gray-200 font-bold text-sm">${item.min_year}</div>
                    </div>
                    <div class="p-2.5 rounded-xl bg-gray-900/60 border border-gray-800">
                        <div class="text-gray-500 text-[10px] font-semibold">MÁXIMO ANUAL</div>
                        <div class="text-gray-200 font-bold text-sm">${item.max_year}</div>
                    </div>
                    <div class="p-2.5 rounded-xl bg-gray-900/60 border border-gray-800">
                        <div class="text-gray-500 text-[10px] font-semibold">VOLATILIDADE (30d)</div>
                        <div class="text-amber-400 font-bold text-sm">${item.volatility_30d}%</div>
                    </div>
                    <div class="p-2.5 rounded-xl bg-gray-900/60 border border-gray-800">
                        <div class="text-gray-500 text-[10px] font-semibold">STATUS RSI</div>
                        <div class="text-purple-400 font-bold truncate text-sm">${item.rsi_status}</div>
                    </div>
                `;
            }

            document.getElementById('btn-export-csv').href = `/api/export-csv/${key}`;
            renderRawTable();
        }

        async function loadCorrelation() {
            const res = await fetch('/api/correlation');
            const data = await res.json();
            const table = document.getElementById('correlation-table');
            if (!data.columns) return;

            let html = '<thead class="bg-gray-900 border-b border-gray-800 text-gray-400"><tr><th class="p-2.5">Ativo</th>';
            data.columns.forEach(c => html += `<th class="p-2.5 text-center">${c}</th>`);
            html += '</tr></thead><tbody class="divide-y divide-gray-800/60">';

            data.values.forEach((row, i) => {
                html += `<tr><td class="p-2.5 font-bold text-gray-200 bg-gray-900/40">${data.columns[i]}</td>`;
                row.forEach(val => {
                    let color = 'text-gray-400';
                    let bg = '';
                    if (val >= 0.7) { color = 'text-emerald-300 font-bold'; bg = 'bg-emerald-500/10'; }
                    else if (val <= -0.5) { color = 'text-rose-300 font-bold'; bg = 'bg-rose-500/10'; }
                    html += `<td class="p-2.5 text-center ${color} ${bg}">${val.toFixed(2)}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody>';
            table.innerHTML = html;
        }

        async function renderRawTable() {
            const key = document.getElementById('table-series-select').value || currentSeries;
            const res = await fetch(`/api/series-table/${key}`);
            const data = await res.json();
            const tbody = document.getElementById('raw-table-body');
            tbody.innerHTML = '';

            data.slice(-50).reverse().forEach(row => {
                const isPos = row.pct_change >= 0;
                const color = isPos ? 'text-emerald-400' : 'text-rose-400';
                tbody.innerHTML += `
                    <tr class="hover:bg-gray-900/60 transition">
                        <td class="p-2.5 font-semibold text-gray-200">${row.date}</td>
                        <td class="p-2.5 font-bold text-white">${row.value.toLocaleString('pt-BR')}</td>
                        <td class="p-2.5 text-gray-400">${row.sma_7 ? row.sma_7.toFixed(4) : '-'}</td>
                        <td class="p-2.5 text-gray-400">${row.sma_21 ? row.sma_21.toFixed(4) : '-'}</td>
                        <td class="p-2.5 ${color}">${row.pct_change ? row.pct_change.toFixed(2) + '%' : '-'}</td>
                        <td class="p-2.5 text-purple-400">${row.rsi ? row.rsi.toFixed(1) : '-'}</td>
                    </tr>
                `;
            });
        }

        function switchTab(tab) {
            ['terminal', 'ai-warroom', 'correlation', 'data-table'].forEach(t => {
                document.getElementById(`view-${t}`).classList.add('hidden');
                document.getElementById(`tab-btn-${t}`).className = 'tab-btn px-4 py-1.5 text-xs font-medium rounded-lg text-gray-400 hover:text-gray-200 transition';
            });
            document.getElementById(`view-${tab}`).classList.remove('hidden');
            document.getElementById(`tab-btn-${tab}`).className = 'tab-btn active px-4 py-1.5 text-xs font-semibold rounded-lg transition bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';

            if (tab === 'terminal') {
                setTimeout(() => Plotly.Plots.resize('plotly-container'), 50);
            }
        }

        async function triggerFullBriefing() {
            switchTab('ai-warroom');
            const out = document.getElementById('ai-output');
            out.innerHTML = '<div class="py-16 text-center text-emerald-400 font-mono animate-pulse">⚙️ Sintetizando indicadores macroeconômicos, curvas de juros e cenários com IA...</div>';
            
            const res = await fetch('/api/generate-report');
            const data = await res.json();
            lastReportText = data.markdown;
            out.innerHTML = marked.parse(data.markdown);
            document.getElementById('report-timestamp').innerText = `Gerado em ${data.timestamp}`;
            document.getElementById('report-title').innerText = 'Relatório de Inteligência Macroeconômica & Cenários';
        }

        async function askScenario(question) {
            switchTab('ai-warroom');
            const out = document.getElementById('ai-output');
            out.innerHTML = `<div class="py-16 text-center text-emerald-400 font-mono animate-pulse">🧠 Analisando impacto do cenário: "${question}"...</div>`;

            const res = await fetch('/api/simulate-scenario', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const data = await res.json();
            lastReportText = data.markdown;
            out.innerHTML = marked.parse(data.markdown);
            document.getElementById('report-timestamp').innerText = `Simulação executada em ${data.timestamp}`;
            document.getElementById('report-title').innerText = `Simulação: ${question.slice(0, 45)}...`;
        }

        function submitCustomPrompt() {
            const val = document.getElementById('custom-prompt-input').value.trim();
            if (val) {
                askScenario(val);
                document.getElementById('custom-prompt-input').value = '';
            }
        }

        function speakReport() {
            if (!('speechSynthesis' in window)) {
                alert('Seu navegador não suporta síntese de voz.');
                return;
            }
            window.speechSynthesis.cancel();
            
            // Extrai texto limpo sem markdown
            const cleanText = lastReportText
                .replace(/[*#`_~\[\]\(\)]/g, '')
                .replace(/\|/g, ' ')
                .slice(0, 800);

            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = 'pt-BR';
            utterance.rate = 1.05;
            window.speechSynthesis.speak(utterance);
        }

        async function refreshData() {
            await fetch('/api/refresh', { method: 'POST' });
            await fetchMetrics();
            await loadChart(currentSeries);
            await loadCorrelation();
        }

        // Initialize on load
        window.onload = init;
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
    chart_json = engine.generate_advanced_chart(key)
    if chart_json:
        return jsonify(json.loads(chart_json))
    return jsonify({"error": "Série não encontrada"}), 404

@app.route("/api/correlation")
def get_correlation():
    return jsonify(engine.get_correlation_matrix())

@app.route("/api/series-table/<key>")
def get_series_table(key):
    if key in engine.dataframes:
        df = engine.dataframes[key]
        records = df.copy()
        records["date"] = records["date"].dt.strftime("%d/%m/%Y")
        return jsonify(records.to_dict(orient="records"))
    return jsonify([])

@app.route("/api/export-csv/<key>")
def export_csv(key):
    if key in engine.dataframes:
        df = engine.dataframes[key]
        si = io.StringIO()
        df.to_csv(si, index=False, sep=";")
        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=marketpulse_{key}.csv"}
        )
    return "Not found", 404

@app.route("/api/generate-report")
def generate_report():
    report = agent.generate_executive_report()
    return jsonify(report)

@app.route("/api/simulate-scenario", methods=["POST"])
def simulate_scenario():
    data = request.get_json() or {}
    q = data.get("question", "")
    res = agent.simulate_custom_scenario(q)
    return jsonify(res)

@app.route("/api/refresh", methods=["POST"])
def refresh_cache():
    global engine, agent
    from data_collector import update_all_market_data
    update_all_market_data(force=True)
    engine = MarketAnalyticsEngine()
    agent = MarketPulseAIAgent(engine)
    return jsonify({"status": "updated"})

if __name__ == "__main__":
    print("MarketPulse AI Pro Terminal rodando em http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
