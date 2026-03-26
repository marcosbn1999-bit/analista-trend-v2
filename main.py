import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. SETUP DE INTERFACE & AUTO-REFRESH
st.set_page_config(page_title="Analista Pro | Intelligence", layout="wide")
st_autorefresh(interval=60 * 1000, key="datarefresh")

# Inicializa o Histórico na Sessão (para não apagar ao atualizar)
if 'historico' not in st.session_state:
    st.session_state.historico = []

st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e6edf3; }
    .status-card { background: #1c2127; padding: 15px; border-radius: 12px; border: 1px solid #30363d; text-align: center; }
    .historico-card { background: #161b22; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 4px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE INTELIGÊNCIA (ALTA PROBABILIDADE - VERSÃO BLINDADA)
def processar_inteligencia(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if df.empty or len(df) < 50:
            return None, 0, "ERRO DADOS"
            
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        
        # Indicadores com tratamento de erro
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        # Cálculo seguro do ADX
        adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        if adx_df is not None and not adx_df.empty:
            df['ADX'] = adx_df['ADX_14']
        else:
            df['ADX'] = 0 # Valor neutro caso falhe
        
        # Remove NaNs apenas para pegar o último valor válido
        df_valid = df.dropna(subset=['RSI', 'SMA_200'])
        if df_valid.empty:
            return df, 0, "AGUARDAR"
            
        ultimo = df_valid.iloc[-1]
        score = 0
        status = "AGUARDAR"
        
        # Filtros de Elite
        trend_up = ultimo['Close'] > ultimo['SMA_200']
        strong_move = ultimo['ADX'] > 25
        
        if trend_up and ultimo['RSI'] < 38 and strong_move:
            score = 88; status = "COMPRA"
        elif not trend_up and ultimo['RSI'] > 62 and strong_move:
            score = 88; status = "VENDA"
        elif strong_move:
            score = 60; status = "MONITORAR"
        else:
            score = 35; status = "NEUTRO"
            
        return df, score, status
    except Exception as e:
        return None, 0, "ERRO"

# --- SIDEBAR: GESTÃO DE RISCO ---
with st.sidebar:
    st.title("🛡️ Gestão de Risco")
    banca = st.number_input("Banca ($)", value=1000.0, step=100.0)
    risco_perc = st.slider("Risco por Trade (%)", 0.5, 5.0, 1.0)
    valor_risco = banca * (risco_perc / 100)
    st.divider()
    
    st.subheader("📜 Últimos Alertas")
    if not st.session_state.historico:
        st.write("Aguardando sinais...")
    for item in st.session_state.historico[::-1][:8]: # Mostra os últimos 8
        cor_h = "#00c853" if item['dir'] == "COMPRA" else "#ff5252"
        st.markdown(f"""
            <div class='historico-card'>
                <span style='color:{cor_h}; font-weight:bold;'>{item['dir']}</span> | {item['ativo']}<br>
                <span style='font-size:0.7em; color:#8b949e;'>{item['hora']}</span>
            </div>
        """, unsafe_allow_html=True)

# --- CONTEÚDO PRINCIPAL ---
st.title("🎯 Analista Pro | Intelligence")
ATIVOS = ["BTC-USD", "ETH-USD", "SOL-USD", "EURUSD=X", "XAUUSD=X", "NVDA", "AAPL"]

# Scanner de Topo
cols = st.columns(len(ATIVOS))
for i, t in enumerate(ATIVOS):
    _, sc, stt = processar_inteligencia(t)
    
    # Adiciona ao histórico se for um sinal forte e novo
    if sc >= 80:
        agora = datetime.now().strftime('%H:%M')
        if not any(h['ativo'] == t and h['hora'] == agora for h in st.session_state.historico):
            st.session_state.historico.append({'ativo': t, 'dir': stt, 'hora': agora})

    with cols[i]:
        cor = "#00c853" if stt == "COMPRA" else "#ff5252" if stt == "VENDA" else "#8b949e"
        st.markdown(f"<div class='status-card'><p style='font-size:0.7em;color:#8b949e;margin:0;'>{t}</p><h3 style='color:{cor};margin:0;'>{sc}%</h3><p style='font-size:0.6em;color:{cor};margin:0;'>{stt}</p></div>", unsafe_allow_html=True)

st.divider()

# Detalhes do Ativo
selecionado = st.selectbox("Raio-X do Ativo:", ATIVOS)
df_d, sc_d, stt_d = processar_inteligencia(selecionado)
atual = df_d.iloc[-1]

c1, c2 = st.columns([2, 1])

with c1:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_d.index, open=df_d['Open'], high=df_d['High'], low=df_d['Low'], close=df_d['Close'], name="Preço"))
    fig.add_trace(go.Scatter(x=df_d.index, y=df_d['SMA_200'], line=dict(color='#ff9800', width=2), name="Média 200"))
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    cor_st = "#00c853" if stt_d == "COMPRA" else "#ff5252" if stt_d == "VENDA" else "#8b949e"
    st.markdown(f"<div style='background:#1c2127; padding:20px; border-radius:10px; border-left:8px solid {cor_st};'><h2 style='margin:0;color:{cor_st};'>{stt_d}</h2><p style='margin:0;'>Confiança: {sc_d}%</p></div>", unsafe_allow_html=True)
    
    st.divider()
    if sc_d >= 60:
        atr = atual['ATR']
        dist_stop = atr * 1.5
        stop = atual['Close'] - dist_stop if stt_d == "COMPRA" else atual['Close'] + dist_stop
        alvo = atual['Close'] + (atr * 3) if stt_d == "COMPRA" else atual['Close'] - (atr * 3)
        lote = valor_risco / dist_stop
        
        st.write(f"🛑 **Stop Loss:** {stop:.2f}")
        st.write(f"🎯 **Take Profit:** {alvo:.2f}")
        st.success(f"📟 **TAMANHO DO LOTE:** {lote:.4f}")
    else:
        st.info("Aguardando confluência de indicadores.")

st.divider()
st.caption(f"Terminal Analista Pro Intelligence • Versão 4.0 • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
