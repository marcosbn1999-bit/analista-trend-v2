import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# 1. CONFIGURAÇÃO DE ELITE (Layout Wide e Design SaaS)
st.set_page_config(page_title="Analista Trend Pro | High Win", layout="wide", initial_sidebar_state="expanded")

# CSS Customizado para visual "Enxuto" e Profissional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stPlotlyChart { background-color: #ffffff; border-radius: 12px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE NOTIFICAÇÕES (Telegram)
def enviar_telegram(mensagem):
    try:
        token = st.secrets["8429949960:AAE7wSVGQLUC2AcSVJZ-epy22ygKOtirPe0"]
        chat_id = st.secrets["8520189654"]
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={mensagem}&parse_mode=Markdown"
        requests.get(url, timeout=10)
    except:
        st.warning("⚠️ Configure o TELEGRAM_TOKEN e CHAT_ID nos Secrets para receber sinais.")

# --- SIDEBAR (Painel de Controle) ---
with st.sidebar:
    st.title("⚡ Analista Trend Pro")
    st.caption("Versão 2.0 - High Win Strategy")
    ativo = st.text_input("Símbolo do Ativo", value="BTC-USD").upper()
    timeframe = st.selectbox("Tempo Gráfico", ["5m", "15m", "1h", "4h", "1d"], index=1)
    
    st.divider()
    if st.button("🔔 Testar Conexão Telegram"):
        enviar_telegram(f"✅ *Analista Trend Pro Online!*\nMonitorando: {ativo}")
        st.toast("Sinal de teste enviado!")

# --- PROCESSAMENTO DE DADOS ---
@st.cache_data(ttl=60)
def obter_dados(ticker, interval):
    periodo = "5d" if "m" in interval else "max"
    df = yf.download(ticker, period=periodo, interval=interval)
    return df

df = obter_dados(ativo, timeframe)

if not df.empty:
    # 3. INTELIGÊNCIA TÉCNICA (Indicadores de Confluência)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns] # Limpeza yfinance
    df.ta.rsi(length=14, append=True)
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.adx(length=14, append=True)
    df.ta.atr(length=14, append=True)
    
    # Valores do Último Fechamento
    atual = df.iloc[-1]
    preco = atual['Close']
    rsi = atual['RSI_14']
    adx = atual['ADX_14']
    sma50 = atual['SMA_50']
    atr = atual['ATR_14']

    # 4. CÁLCULO DE CONFIABILIDADE E SINAL
    score = 0
    sinal = "AGUARDAR"
    detalhe = "Mercado em consolidação ou sem força"
    cor_sinal = "#546e7a" # Cinza

    # Lógica de Compra Forte
    if rsi < 35 and preco > sma50 and adx > 25:
        sinal = "COMPRA FORTE"
        cor_sinal = "#00c853"
        detalhe = "Exaustão de Venda + Tendência de Alta Confirmada"
        score = 70 + (10 if adx > 40 else 5) + (15 if preco > sma50 else 0)
    
    # Lógica de Venda Forte
    elif rsi > 65 and preco < sma50 and adx > 25:
        sinal = "VENDA FORTE"
        cor_sinal = "#d50000"
        detalhe = "Exaustão de Compra + Tendência de Baixa Confirmada"
        score = 70 + (10 if adx > 40 else 5) + (15 if preco < sma50 else 0)

    confiabilidade = min(score, 98) if sinal != "AGUARDAR" else 0

    # 5. DASHBOARD VISUAL (Interface SaaS)
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.title(f"📊 Dashboard: {ativo}")
    with col_t2:
        st.write("") # Alinhamento
        if st.button("🔄 Atualizar"): st.rerun()

    # Box Principal de Sinal
    st.markdown(f"""
        <div style="background-color: #ffffff; padding: 25px; border-radius: 15px; border-left: 10px solid {cor_sinal}; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 25px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin:0; color: #1e1e1e; font-size: 2.5em;">{sinal}</h1>
                    <p style="margin:0; color: #666; font-size: 1.2em;">{detalhe}</p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin:0; color: {cor_sinal}; font-size: 3em;">{confiabilidade}%</h2>
                    <p style="margin:0; color: #666; font-size: 0.9em; font-weight: bold;">CONFIABILIDADE MATEMÁTICA</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Métricas de Suporte
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Preço", f"{preco:.2f}", f"{((preco/df['Close'].iloc[-2])-1)*100:.2f}%")
    m2.metric("RSI (IFR)", f"{rsi:.1f}", "Sobrevenda" if rsi < 30 else "Sobrecompra" if rsi > 70 else "Neutro")
    m3.metric("Força (ADX)", f"{adx:.1f}", "Tendência Forte" if adx > 25 else "Fraca")
    m4.metric("Volatilidade (ATR)", f"{atr:.2f}", "Alta" if atr > df['ATR_14'].mean() else "Baixa")

    # 6. GRÁFICO INTERATIVO PROFISSIONAL
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # Candlesticks e Médias
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Preço"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#2196f3', width=1.5), name="Média 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#ff9800', width=1.5), name="Média 50"), row=1, col=1)
    
    # RSI no Subplot 2
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], line=dict(color='#9c27b0', width=2), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=700, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # 7. GESTÃO DE RISCO E DISPARO TELEGRAM
    if sinal != "AGUARDAR" and confiabilidade >= 75:
        # Cálculo de TP e SL usando ATR
        tp = preco + (atr * 2) if "COMPRA" in sinal else preco - (atr * 2)
        sl = preco - (atr * 1.5) if "COMPRA" in sinal else preco + (atr * 1.5)
        
        if st.session_state.get('last_alert') != sinal:
            msg = (
                f"🎯 *SINAL DE ALTA PRECISÃO*\n\n"
                f"Ativo: #{ativo}\n"
                f"Ação: *{sinal}*\n"
                f"🔥 Confiança: {confiabilidade}%\n"
                f"────────────────\n"
                f"💰 Entrada: {preco:.2f}\n"
                f"🛡️ Stop Loss: {sl:.2f}\n"
                f"✅ Take Profit: {tp:.2f}\n"
                f"────────────────\n"
                f"📊 ADX: {adx:.0f} | RSI: {rsi:.0f}"
            )
            enviar_telegram(msg)
            st.session_state['last_alert'] = sinal
else:
    st.warning("Aguardando dados do mercado... Verifique o símbolo do ativo.")
