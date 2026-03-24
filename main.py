import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import time
import requests
from datetime import datetime

# --- 1. CONFIGURAÇÕES TÉCNICAS (CONFIGURADO) ---
TOKEN = "8429949960:AAE7wSVGQLUC2AcSVJZ-epy22ygKOtirPe0"
CHAT_ID = "8520189654"
SENHA_PRIVADA = "123456" # <--- Você pode mudar essa senha aqui se quiser

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}"
    try: requests.get(url)
    except: pass

# --- 2. SEGURANÇA ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🛡️ Sentinela Privado")
        senha = st.text_input("Senha de Acesso:", type="password")
        if st.button("Entrar"):
            if senha == SENHA_PRIVADA:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Senha incorreta")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. MOTOR DE ANÁLISE ---
@st.cache_data(ttl=60)
def analisar_ativo(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if len(df) < 200: return None
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        df['EMA_21'] = ta.ema(df['Close'], length=21)
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        df['ADX'] = adx['ADX_14']
        df['RSI'] = ta.rsi(df['Close'], length=14)
        ultimo = df.iloc[-1]
        
        status = "AGUARDAR"
        cor = "info"
        # Lógica de Elite
        if ultimo['Close'] > ultimo['EMA_200'] and ultimo['ADX'] > 30 and 42 < ultimo['RSI'] < 59:
            status = "💎 SINAL DE ELITE"
            cor = "success"
        elif ultimo['Close'] < ultimo['EMA_21'] or ultimo['RSI'] > 75:
            status = "🛑 SAÍDA"
            cor = "error"

        return {"Ativo": ticker, "Preço": round(ultimo['Close'], 4), "Status": status, "ADX": round(ultimo['ADX'], 1), "cor": cor}
    except: return None

# --- 4. DASHBOARD ---
st.set_page_config(page_title="Sentinela IQ", layout="wide")
st.title("🛰️ Terminal de Alta Precisão")
st.write(f"Monitorando em Tempo Real: {datetime.now().strftime('%H:%M:%S')}")

monitorar = {
    "💱 Forex": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"],
    "₿ Cripto": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "💎 Commodities": ["GC=F", "SI=F", "CL=F"],
    "🏢 Ações": ["NVDA", "AAPL", "PETR4.SA", "VALE3.SA"]
}

for cat, ativos in monitorar.items():
    st.subheader(cat)
    cols = st.columns(len(ativos))
    for i, t in enumerate(ativos):
        res = analisar_ativo(t)
        if res:
            with cols[i]:
                st.metric(t, res['Preço'])
                if res['cor'] == "success":
                    st.success(res['Status'])
                    enviar_telegram(f"🚀 SINAL: {t}\nPreço: {res['Preço']}\nADX: {res['ADX']}")
                elif res['cor'] == "error": st.error(res['Status'])
                else: st.info(res['Status'])

time.sleep(60)
st.rerun()