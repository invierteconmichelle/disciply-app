import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# Configuración de página
st.set_page_config(page_title="Disciply.io - MVP Prototype", page_icon="⚡", layout="wide")

# Estilo visual en Modo Oscuro (FinTech Look)
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #1E222D; padding: 15px; border-radius: 10px; border: 1px solid #2A2E39; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Disciply.io — Prototipo de Gobernanza & D-Score")
st.caption("Carga tu exportación de NinjaTrader para evaluar tu sesión diaria.")

DB_FILE = "disciply_sessions.csv"

# Limpieza profunda de montos P&L
def parse_pnl_value(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip().replace('$', '').replace(',', '')
    if val_str.startswith('(') and val_str.endswith(')'):
        val_str = '-' + val_str[1:-1]
    try:
        return float(val_str)
    except:
        return 0.0

# --- MÓDULO 1: CARGA DE DATOS DE NINJATRADER ---
st.subheader("1. Importar Sesión de NinjaTrader")
uploaded_file = st.file_uploader("Arrastra tu archivo CSV o TXT de NinjaTrader aquí", type=["csv", "txt"])

pnl_auto = 0.0
total_trades_auto = 0
win_rate_auto = 0.0
best_trade_auto = 0.0
worst_trade_auto = 0.0

if uploaded_file is not None:
    try:
        # Detectar automáticamente si el archivo usa comas, puntos y comas (;) o tabulaciones
        try:
            df_nt = pd.read_csv(uploaded_file, sep=None, engine='python')
        except:
            uploaded_file.seek(0)
            df_nt = pd.read_csv(uploaded_file, sep=';')
        
        # Búsqueda flexible de columna de P&L en NinjaTrader
        pnl_keywords = ['cum. net profit', 'profit', 'p&l', 'p/l', 'ganancia', 'beneficio', 'pnl', 'net', 'amount']
        profit_col = None
        
        for kw in pnl_keywords:
            for col in df_nt.columns:
                if kw in str(col).lower():
                    profit_col = col
                    break
            if profit_col:
                break
        
        if profit_col:
            df_nt['pnl_clean'] = df_nt[profit_col].apply(parse_pnl_value)
            
            pnl_auto = float(df_nt['pnl_clean'].sum())
            total_trades_auto = len(df_nt)
            winning_trades = len(df_nt[df_nt['pnl_clean'] > 0])
            win_rate_auto = (winning_trades / total_trades_auto * 100) if total_trades_auto > 0 else 0.0
            best_trade_auto = float(df_nt['pnl_clean'].max())
            worst_trade_auto = float(df_nt['pnl_clean'].min())
            
            st.success(f"✅ Archivo procesado con éxito ({total_trades_auto} trades detectados en columna '{profit_col}').")
        else:
            st.warning("⚠️ Selecciona manualmente la columna que contiene las ganancias/pérdidas:")
            selected_col = st.selectbox("Columna de P&L:", df_nt.columns)
            if selected_col:
                df_nt['pnl_clean'] = df_nt[selected_col].apply(parse_pnl_value)
                pnl_auto = float(df_nt['pnl_clean'].sum())
                total_trades_auto = len(df_nt)
                winning_trades = len(df_nt[df_nt['pnl_clean'] > 0])
                win_rate_auto = (winning_trades / total_trades_auto * 100) if total_trades_auto > 0 else 0.0
                best_trade_auto = float(df_nt['pnl_clean'].max())
                worst_trade_auto = float(df_nt['pnl_clean'].min())
    except Exception as e:
        st.error(f"Error al leer el archivo de NinjaTrader: {e}")

# Métrica Cuantitativa
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("P&L de la Sesión", f"${pnl_auto:,.2f}")
col2.metric("Total Trades", f"{total_trades_auto}")
col3.metric("Win Rate", f"{win_rate_auto:.1f}%")
col4.metric("Mejor Trade", f"${best_trade_auto:,.2f}")
col5.metric("Peor Trade", f"${worst_trade_auto:,.2f}")

st.divider()

# --- MÓDULO 2: RÚBRICA CUALITATIVA DEL D-SCORE ---
st.subheader("2. Evaluación Cualitativa (D-Score Engine)")
st.info("Califica cada pilar del 0 al 20 según la ejecución de tus reglas hoy.")

with st.form("d_score_form"):
    session_date = st.date_input("Fecha de la Sesión", date.today())
    setup_tag = st.text_input("Setup / Etiqueta Principal (ej. PRT, TaN, Breakout)", "PRT")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    p1 = col_p1.slider("Pilar 1: Gestión de Riesgo (¿Respetaste el Stop Loss/Lotaje?)", 0, 20, 20)
    p2 = col_p2.slider("Pilar 2: Ejecución del Plan (¿Entraste según reglas?)", 0, 20, 20)
    p3 = col_p3.slider("Pilar 3: Control Emocional (¿Cero Venganza/FOMO?)", 0, 20, 20)
    
    col_p4, col_p5 = st.columns(2)
    p4 = col_p4.slider("Pilar 4: Límite de Frecuencia (¿Respetaste máximo de trades?)", 0, 20, 20)
    p5 = col_p5.slider("Pilar 5: Bitácora & Notas (¿Documentaste el contexto?)", 0, 20, 20)
    
    notes = st.text_area("Notas / Observaciones de la Sesión", "")
    
    d_score_total = p1 + p2 + p3 + p4 + p5
    status = "PASS" if d_score_total >= 80 else "SIM-MODE"
    
    submit_button = st.form_submit_button("💾 Guardar Sesión en Disciply")

if submit_button:
    new_data = pd.DataFrame([{
        "Date": str(session_date),
        "PnL": pnl_auto,
        "Trades": total_trades_auto,
        "Setup": setup_tag,
        "D_Score": d_score_total,
        "Status": status,
        "P1_Risk": p1,
        "P2_Plan": p2,
        "P3_Emotions": p3,
        "P4_Freq": p4,
        "P5_Journal": p5,
        "Notes": notes
    }])
    
    if os.path.exists(DB_FILE):
        new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
    else:
        new_data.to_csv(DB_FILE, index=False)
        
    st.balloons()
    st.success(f"¡Sesión registrada! Tu D-Score de hoy es: {d_score_total}/100 | Estatus: {status}")

st.divider()

# --- MÓDULO 3: DASHBOARD HISTÓRICO Y ANÁLISIS ---
st.subheader("3. Dashboard General & Histórico de Disciplina")

if os.path.exists(DB_FILE):
    df_hist = pd.read_csv(DB_FILE)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sesiones Auditadas", len(df_hist))
    m2.metric("Promedio D-Score", f"{df_hist['D_Score'].mean():.1f} / 100")
    m3.metric("P&L Acumulado", f"${df_hist['PnL'].sum():,.2f}")
    m4.metric("Días en SIM-Mode", len(df_hist[df_hist['Status'] == 'SIM-MODE']))
    
    fig = px.bar(df_hist, x="Date", y="PnL", color="D_Score", 
                 title="Relación entre D-Score (Color) y Rendimiento Financiero (P&L)",
                 color_continuous_scale="RdYlGn", text="D_Score")
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### Histórico de Registros")
    st.dataframe(df_hist.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("Aún no has guardado ninguna sesión. Procesa tu primer archivo para comenzar a construir tu histórico.")
