import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# Configuración de página
st.set_page_config(page_title="Disciply.io - MVP Prototype", page_icon="⚡", layout="wide")

# Estilo visual en Modo Oscuro
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #1E222D; padding: 15px; border-radius: 10px; border: 1px solid #2A2E39; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Disciply.io — Prototipo de Gobernanza & D-Score")
st.caption("Carga tu exportación de NinjaTrader para evaluar tu sesión diaria.")

DB_FILE = "disciply_sessions.csv"

# Limpieza de valores numéricos de P&L
def parse_pnl_value(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip().replace('$', '').replace(' ', '')
    if ',' in val_str and '.' not in val_str:
        val_str = val_str.replace(',', '.')
    elif ',' in val_str and '.' in val_str:
        val_str = val_str.replace(',', '')
    if val_str.startswith('(') and val_str.endswith(')'):
        val_str = '-' + val_str[1:-1]
    try:
        return float(val_str)
    except:
        return 0.0

# --- MÓDULO 1: CARGA DE DATOS ---
st.subheader("1. Importar Sesión de NinjaTrader")
uploaded_file = st.file_uploader("Arrastra tu archivo CSV o TXT de NinjaTrader aquí", type=["csv", "txt"])

pnl_auto = 0.0
total_trades_auto = 0
win_rate_auto = 0.0
best_trade_auto = 0.0
worst_trade_auto = 0.0

if uploaded_file is not None:
    try:
        try:
            df_nt = pd.read_csv(uploaded_file, sep=None, engine='python')
        except:
            uploaded_file.seek(0)
            df_nt = pd.read_csv(uploaded_file, sep=';')
        
        profit_col = 'Profit' if 'Profit' in df_nt.columns else None
        if not profit_col:
            for col in df_nt.columns:
                if 'profit' in str(col).lower() and 'cum' not in str(col).lower():
                    profit_col = col
                    break

        if profit_col:
            df_nt['pnl_clean'] = df_nt[profit_col].apply(parse_pnl_value)
            group_cols = [c for c in ['Entry time', 'Exit time', 'Instrument'] if c in df_nt.columns]
            
            if group_cols:
                trades_df = df_nt.groupby(group_cols, as_index=False)['pnl_clean'].sum()
            else:
                trades_df = df_nt[['pnl_clean']]

            pnl_auto = float(trades_df['pnl_clean'].sum())
            total_trades_auto = len(trades_df)
            winning_trades = len(trades_df[trades_df['pnl_clean'] > 0])
            win_rate_auto = (winning_trades / total_trades_auto * 100) if total_trades_auto > 0 else 0.0
            best_trade_auto = float(trades_df['pnl_clean'].max())
            worst_trade_auto = float(trades_df['pnl_clean'].min())
            
            st.success(f"✅ Archivo procesado con éxito: {total_trades_auto} trade(s) detectado(s).")
        else:
            st.error("⚠️ No se pudo encontrar la columna de ganancias.")
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("P&L de la Sesión", f"${pnl_auto:,.2f}")
col2.metric("Total Trades", f"{total_trades_auto}")
col3.metric("Win Rate", f"{win_rate_auto:.1f}%")
col4.metric("Mejor Trade", f"${best_trade_auto:,.2f}")
col5.metric("Peor Trade", f"${worst_trade_auto:,.2f}")

st.divider()

# --- MÓDULO 2: EVALUACIÓN POR ESTRELLAS ---
st.subheader("2. Evaluación Cualitativa (D-Score Engine)")
st.info("Califica del 1 al 5 cada pilar (1 = Pésimo | 5 = Perfecto).")

with st.form("d_score_form"):
    session_date = st.date_input("Fecha de la Sesión", date.today())
    setup_tag = st.text_input("Setup Principal (ej. PRT, TaN)", "PRT")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    p1 = col_p1.radio("1. Gestión de Riesgo (Lotes/Stop Loss)", [1, 2, 3, 4, 5], index=4, horizontal=True)
    p2 = col_p2.radio("2. Ejecución (Respeto al Setup)", [1, 2, 3, 4, 5], index=4, horizontal=True)
    p3 = col_p3.radio("3. Emociones (Cero FOMO/Venganza)", [1, 2, 3, 4, 5], index=4, horizontal=True)
    
    col_p4, col_p5 = st.columns(2)
    p4 = col_p4.radio("4. Frecuencia (Límite de Trades)", [1, 2, 3, 4, 5], index=4, horizontal=True)
    p5 = col_p5.radio("5. Auditoría (Llenado de Bitácora)", [1, 2, 3, 4, 5], index=4, horizontal=True)
    
    notes = st.text_area("Notas Breves", "")
    
    # Conversión matemática: (25 puntos máximos) * 4 = 100
    d_score_total = (p1 + p2 + p3 + p4 + p5) * 4
    status = "PASS" if d_score_total >= 80 else "SIM-MODE"
    
    submit_button = st.form_submit_button("💾 Guardar Sesión")

if submit_button:
    new_data = pd.DataFrame([{
        "Date": str(session_date),
        "PnL": pnl_auto,
        "Trades": total_trades_auto,
        "Setup": setup_tag,
        "D_Score": d_score_total,
        "Status": status,
        "Notes": notes
    }])
    
    if os.path.exists(DB_FILE):
        new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
    else:
        new_data.to_csv(DB_FILE, index=False)
        
    st.balloons()
    st.success(f"¡Sesión registrada! Tu D-Score de hoy es: {d_score_total}/100 | Estatus: {status}")

st.divider()

# --- MÓDULO 3: HISTÓRICO ---
st.subheader("3. Dashboard General & Histórico")

if os.path.exists(DB_FILE):
    df_hist = pd.read_csv(DB_FILE)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sesiones Auditadas", len(df_hist))
    m2.metric("Promedio D-Score", f"{df_hist['D_Score'].mean():.1f} / 100")
    m3.metric("P&L Acumulado", f"${df_hist['PnL'].sum():,.2f}")
    m4.metric("Días en SIM-Mode", len(df_hist[df_hist['Status'] == 'SIM-MODE']))
    
    fig = px.bar(df_hist, x="Date", y="PnL", color="D_Score", 
                 title="Rendimiento Financiero (P&L) vs Disciplina (Color)",
                 color_continuous_scale="RdYlGn", text="D_Score")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df_hist.sort_values(by="Date", ascending=False), use_container_width=True)
