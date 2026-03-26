import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. SETUP DE SEGURANÇA & INTERFACE (SaaS STYLE)
st.set_page_config(page_title="Analista Pro | Intelligence", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
            html, body { font-family: 'Inter', sans-serif; background-color: #05070a; color: #f0f2f6; }
            .login-box { text-align: center; margin-top: 100px; padding: 40px; border-radius: 20px; background: #0d1117; border: 1px solid #1f2937; }
            </style>
            <div class="login-box">
                <h1 style='color:#3b82f6; font-weight:600;'>Analista Pro</h1>
                <p style='color:#9ca3af;'>Terminal Intelligence v5.1 • Private Access</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            senha = st.text_input("Chave de Acesso", type="password")
            if st.button("Entrar"):
                if senha == "1234": # <--- DEFINA SUA SENHA AQUI
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Chave Incorreta")
        return False
    return True

if not check_password():
    st.stop()

# 2. AUTO-REFRESH & ESTILIZAÇÃO
st_autorefresh(interval=60 * 1000, key="datarefresh")
if 'historico' not in st.session_state:
    st.session_state.historico = []

st.markdown("""
    <style>
    .stApp { background: #05070a; }
    .scanner-card { background: #0d1117; padding: 15px; border-radius: 12px; border: 1px solid #1f2937; text-align: center; }
    .signal-main { background: linear-gradient(145deg, #0d1117, #161b22); padding: 25px; border-radius: 16px; border: 1px solid #30363d; text-align: center; }
    .target-box { background: #111827; padding: 15px; border-radius: 10px; border-left: 4px solid #3b82f6; margin-top: 15px; }
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# 3. MOTOR DE INTELIGÊNCIA (CONFLUÊNCIA 88%)
def processar_inteligencia(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if df.empty or len(df) < 50: return None, 0, "ERRO"
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        df['ADX'] = adx_df['ADX_14'] if adx_df is not None else 0
        
        ultimo = df.dropna(subset=['RSI', 'SMA_200']).iloc[-1]
        score = 35; status = "NEUTRO"
        
        trend_up = ultimo['Close'] > ultimo['SMA_200']
        strong = ultimo['ADX'] > 25
        
        if trend_up and ultimo['RSI'] < 38 and strong: score = 88; status = "COMPRA"
        elif not trend_up and ultimo['RSI'] > 62 and strong: score = 88; status = "VENDA"
        elif strong: score = 60; status = "MONITORAR"
            
        return df, score, status
    except: return None, 0, "ERRO"

# --- SIDEBAR: GESTÃO DINÂMICA ---
with st.sidebar:
    st.markdown("<h2 style='font-size:1.1rem;'>CONFIGURAÇÃO DE RISCO</h2>", unsafe_allow_html=True)
    # Valor agora é editável sem trava de simulação
    banca = st.number_input("Sua Banca Total ($)", value=1000.0, step=100.0)
    risco_perc = st.slider("Risco por Operação (%)", 0.5, 5.0, 1.0)
    valor_risco = banca * (risco_perc / 100)
    
    st.markdown("---")
    st.markdown("<h3 style='font-size:0.9rem;'>ALERTAS ATIVOS</h3>", unsafe_allow_html=True)
    for h in st.session_state.historico[::-1][:6]:
        cor_h = "#10b981" if h['dir'] == "COMPRA" else "#ef4444"
        st.markdown(f"<p style='font-size:0.75rem; margin:0;'>{h['hora']} • <span style='color:{cor_h}'>{h['ativo']}</span></p>", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align: center; font-weight: 600;'>Analista Pro <span style='color:#3b82f6;'>Intelligence</span></h1>", unsafe_allow_html=True)

# --- SCANNER GRID ---
ATIVOS = ["BTC-USD", "ETH-USD", "SOL-USD", "EURUSD=X", "XAUUSD=X", "NVDA", "AAPL"]
cols = st.columns(len(ATIVOS))

for i, t in enumerate(ATIVOS):
    _, sc, stt = processar_inteligencia(t)
    if sc >= 80:
        agora = datetime.now().strftime('%H:%M')
        if not any(h['ativo'] == t and h['hora'] == agora for h in st.session_state.historico):
            st.session_state.historico.append({'ativo': t, 'dir': stt, 'hora': agora})
    with cols[i]:
        cor = "#10b981" if stt == "COMPRA" else "#ef4444" if stt == "VENDA" else "#9ca3af"
        st.markdown(f"<div class='scanner-card'><div style='font-size:0.7rem; color:#9ca3af;'>{t}</div><div style='font-size:1.4rem; font-weight:600; color:{cor};'>{sc}%</div></div>", unsafe_allow_html=True)

st.divider()

# --- ANÁLISE E RAIO-X ---
selecionado = st.selectbox("Selecione o Ativo para Análise:", ATIVOS, label_visibility="collapsed")
df_d, sc_d, stt_d = processar_inteligencia(selecionado)

if df_d is not None:
    c1, c2 = st.columns([2.5, 1])
    with c1:
        fig = go.Figure(data=[go.Candlestick(x=df_d.index, open=df_d['Open'], high=df_d['High'], low=df_d['Low'], close=df_d['Close'], name="Preço")])
        fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_200'], line=dict(color='#3b82f6', width=1.5), name="SMA 200"))
        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cor_st = "#10b981" if stt_d == "COMPRA" else "#ef4444" if stt_d == "VENDA" else "#9ca3af"
        st.markdown(f"<div class='signal-main'><div style='font-size:2.2rem; font-weight:600; color:{cor_st};'>{stt_d}</div><div style='font-size:1rem; color:#9ca3af;'>Probabilidade: {sc_d}%</div></div>", unsafe_allow_html=True)
        
        if sc_d >= 60:
            atr = df_d.iloc[-1]['ATR']
            preco = df_d.iloc[-1]['Close']
            dist = atr * 1.5
            lote = valor_risco / dist
            
            stop = preco - dist if stt_d == "COMPRA" else preco + dist
            p1 = preco + (dist * 1.0) if stt_d == "COMPRA" else preco - (dist * 1.0)
            p2 = preco + (dist * 2.5) if stt_d == "COMPRA" else preco - (dist * 2.5)

            st.markdown(f"""
                <div class="target-box">
                    <p style="margin:0; font-size:0.85rem;">Tamanho do Lote: <b>{lote:.4f}</b></p>
                    <p style="margin:8px 0; font-size:0.85rem; color:#ef4444;">🛑 Stop Loss: {stop:.2f}</p>
                    <p style="margin:8px 0; font-size:0.85rem; color:#10b981;">🎯 Parcial (50%): {p1:.2f}</p>
                    <p style="margin:8px 0; font-size:0.85rem; color:#3b82f6;">🚀 Alvo Final: {p2:.2f}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aguardando confluência para gerar ordens de entrada.")

st.markdown(f"<p style='text-align:center; color:#4b5563; font-size:0.7rem; margin-top:50px;'>Analista Pro Intelligence © 2026 • Private Terminal</p>", unsafe_allow_html=True)
