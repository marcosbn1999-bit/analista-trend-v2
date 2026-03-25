import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# 1. CONFIGURAÇÃO DE ELITE
st.set_page_config(page_title="Analista Trend Pro | IQ Style", layout="wide", initial_sidebar_state="expanded")

# Interface Dark Mode (Estilo IQ Option)
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #ffffff; }
    div.stMetric { background-color: #1c2127; padding: 15px; border-radius: 10px; border: 1px solid #2d343c; }
    [data-testid="stSidebar"] { background-color: #14181d; border-right: 1px solid #2d343c; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #2d343c; color: white; border: none; }
    .stButton>button:hover { background-color: #3e4751; border: 1px solid #00c853; }
    header {visibility: hidden;} footer {visibility: hidden;}
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
        st.warning("⚠️ Configure TELEGRAM_TOKEN e CHAT_ID nos Secrets.")

# --- SIDEBAR (SELETOR IQ OPTION) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2502/2502543.png", width=50)
    st.title("Trend Pro")
    
    st.markdown("### 💎 Ativos Rápidos")
    if 'ativo' not in st.session_state: st.session_state.ativo = "BTC-USD"
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("₿ BTC"): st.session_state.ativo = "BTC-USD"
        if st.button("🔷 ETH"): st.session_state.ativo = "ETH-USD"
    with col2:
        if st.button("☀️ SOL"): st.session_state.ativo = "SOL-USD"
        if st.button("💵 EUR/USD"): st.session_state.ativo = "EURUSD=X"

    st.divider()
    busca = st.text_input("🔍 Buscar Ativo", value=st.session_state.ativo).upper()
    if busca != st.session_state.ativo:
        st.session_state.ativo = busca
        st.rerun()

    timeframe = st.selectbox("⏱️ Intervalo", ["5m", "15m", "1h", "4h", "1d"], index=1)
    
    st.divider()
    if st.button("🔔 Testar Telegram"):
        enviar_telegram(f"✅ *Analista Trend Ativo*\nMonitorando: {st.session_state.ativo}")
        st.toast("Sinal enviado!")

# --- PROCESSAMENTO ---
@st.cache_data(ttl=60)
def obter_dados(ticker, interval):
    periodo = "5d" if "m" in interval else "max"
    df = yf.download(ticker, period=periodo, interval=interval)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

ativo = st.session_state.ativo
df = obter_dados(ativo, timeframe)

if not df.empty and len(df) > 50:
    # 3. INTELIGÊNCIA TÉCNICA
    df['RSI_14'] = ta.rsi(df['Close'], length=14)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['ATR_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    df['ADX_14'] = adx_df['ADX_14']
    
    df_clean = df.dropna()
    if not df_clean.empty:
        atual = df_clean.iloc[-1]
        preco, rsi, adx, sma50, atr = atual['Close'], atual['RSI_14'], atual['ADX_14'], atual['SMA_50'], atual['ATR_14']

        # 4. LÓGICA DE SINAL
        score = 0
        sinal, cor_sinal, detalhe = "AGUARDAR", "#546e7a", "Aguardando confluência..."

        if rsi < 35 and preco > sma50 and adx > 25:
            sinal, cor_sinal, detalhe, score = "COMPRA FORTE", "#00c853", "Tendência de Alta + RSI Baixo", 85
        elif rsi > 65 and preco < sma50 and adx > 25:
            sinal, cor_sinal, detalhe, score = "VENDA FORTE", "#ef5350", "Tendência de Baixa + RSI Alto", 85

        confiabilidade = min(score, 98) if sinal != "AGUARDAR" else 0

        # 5. DASHBOARD VISUAL
        st.markdown(f"""
            <div style="background-color: #1c2127; padding: 25px; border-radius: 15px; border-left: 10px solid {cor_sinal}; margin-bottom: 25px;">
                <div style="display: flex; justify-content: space-between;">
                    <div><h1 style="margin:0; color:white;">{sinal}</h1><p style="color:#aaa;">{detalhe}</p></div>
                    <div style="text-align: right;"><h2 style="margin:0; color:{cor_sinal};">{confiabilidade}%</h2><p style="color:#aaa; font-size:0.8em;">CONFIABILIDADE</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Gráfico Estilo IQ Option
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Preço"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#ff9800', width=2), name="Média 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], line=dict(color='#9c27b0', width=2), name="RSI"), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', 
                          xaxis_rangeslider_visible=False, height=700, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # 6. DISPARO TELEGRAM (Gatilho Ajustado)
        if sinal != "AGUARDAR" and confiabilidade >= 75:
            if st.session_state.get('last_alert') != sinal:
                tp = preco + (atr * 2.5) if "COMPRA" in sinal else preco - (atr * 2.5)
                sl = preco - (atr * 1.5) if "COMPRA" in sinal else preco + (atr * 1.5)
                msg = f"🎯 *SINAL PRO: {ativo}*\n\n🔥 *{sinal}*\n✅ Confiança: {confiabilidade}%\n💰 Preço: {preco:.2f}\n🛡️ Stop: {sl:.2f}\n📈 Alvo: {tp:.2f}"
                enviar_telegram(msg)
                st.session_state['last_alert'] = sinal
else:
    st.error("Dados insuficientes. Tente outro ativo ou aumente o tempo gráfico.")
