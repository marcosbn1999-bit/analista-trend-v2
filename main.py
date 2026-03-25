import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# 1. CONFIGURAÇÃO DE ELITE
st.set_page_config(page_title="Analista Trend Pro | High Win", layout="wide", initial_sidebar_state="expanded")

# CSS Customizado (SaaS Design)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stPlotlyChart { background-color: #ffffff; border-radius: 12px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    footer {visibility: hidden;} header {visibility: hidden;}
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
        st.warning("⚠️ Verifique TELEGRAM_TOKEN e CHAT_ID nos Secrets.")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Analista Trend Pro")
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
    # Correção para Multi-Index do yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df = obter_dados(ativo, timeframe)

if not df.empty and len(df) > 50:
    # 3. INTELIGÊNCIA TÉCNICA (Cálculo Seguro)
    # Forçamos a criação das colunas para evitar KeyError
    df['RSI_14'] = ta.rsi(df['Close'], length=14)
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['ATR_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    
    # ADX e Bandas (Retornam DataFrames, extraímos o necessário)
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    df['ADX_14'] = adx_df['ADX_14']
    
    bbands = ta.bbands(df['Close'], length=20, std=2)
    df['BBL_20'] = bbands.iloc[:, 0] # Banda Inferior
    df['BBU_20'] = bbands.iloc[:, 2] # Banda Superior
    
    # Limpeza de valores nulos para o cálculo do 'atual'
    df_clean = df.dropna()
    
    if not df_clean.empty:
        atual = df_clean.iloc[-1]
        preco = atual['Close']
        rsi = atual['RSI_14']
        adx = atual['ADX_14']
        sma50 = atual['SMA_50']
        atr = atual['ATR_14']

        # 4. LÓGICA DE CONFIABILIDADE
        score = 0
        sinal = "AGUARDAR"
        cor_sinal = "#546e7a"
        detalhe = "Mercado sem tendência clara"

        if rsi < 35 and preco > sma50 and adx > 25:
            sinal = "COMPRA FORTE"; cor_sinal = "#00c853"
            detalhe = "Exaustão de Venda + Tendência de Alta"; score = 85
        elif rsi > 65 and preco < sma50 and adx > 25:
            sinal = "VENDA FORTE"; cor_sinal = "#d50000"
            detalhe = "Exaustão de Compra + Tendência de Baixa"; score = 85

        confiabilidade = min(score + (10 if adx > 40 else 0), 98) if sinal != "AGUARDAR" else 0

        # 5. DASHBOARD VISUAL
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 25px; border-radius: 15px; border-left: 10px solid {cor_sinal}; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 25px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div><h1 style="margin:0;">{sinal}</h1><p style="margin:0; color:#666;">{detalhe}</p></div>
                    <div style="text-align: right;"><h2 style="margin:0; color:{cor_sinal};">{confiabilidade}%</h2><p style="margin:0; font-size:0.8em;">CONFIABILIDADE</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Gráfico
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Preço"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#ff9800', width=1.5), name="Tendência (SMA 50)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], line=dict(color='#9c27b0', width=2), name="RSI"), row=2, col=1)
        fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=600, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # 6. DISPARO TELEGRAM
        if sinal != "AGUARDAR" and confiabilidade >= 75:
            if st.session_state.get('last_alert') != sinal:
                tp = preco + (atr * 2) if "COMPRA" in sinal else preco - (atr * 2)
                sl = preco - (atr * 1.5) if "COMPRA" in sinal else preco + (atr * 1.5)
                msg = f"🎯 *SINAL PRO*\nAtivo: {ativo}\nAção: {sinal}\n🔥 Confiança: {confiabilidade}%\n💰 Entrada: {preco:.2f}\n🛡️ Stop: {sl:.2f}\n✅ Alvo: {tp:.2f}"
                enviar_telegram(msg)
                st.session_state['last_alert'] = sinal
else:
    st.error("Dados insuficientes para análise. Tente um ativo com mais liquidez ou aumente o tempo gráfico.")
