import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

st.set_page_config(page_title="Disciply.io | Mentor Dashboard", page_icon="⚡", layout="wide")

# CSS para estilo FinTech y Tablas limpias
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background-color: #0b0f19; font-family: 'Inter', sans-serif; color: #e2e8f0; }
    h1, h2, h3 { color: #f8fafc; font-weight: 600; }
    h1 { background: -webkit-linear-gradient(45deg, #4ade80, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;}
    div[data-testid="stMetricValue"] { color: #ffffff; font-size: 2rem; font-weight: 800; }
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Disciply.io — Mentor Dashboard")
st.markdown("Plataforma de gobernanza y seguimiento de disciplina para estudiantes.")

DB_FILE = "disciply_sessions.csv"

# Datos simulados de estudiantes (para que el Dashboard no se vea vacío)
STUDENTS = ["Carlos R.", "María F.", "Javier T.", "Ana Gómez", "Pedro H.", "TÚ (Admin)"]

def parse_pnl_value(val):
    if pd.isna(val): return 0.0
    val_str = str(val).strip().replace('$', '').replace(' ', '')
    if ',' in val_str and '.' not in val_str: val_str = val_str.replace(',', '.')
    elif ',' in val_str and '.' in val_str: val_str = val_str.replace(',', '')
    if val_str.startswith('(') and val_str.endswith(')'): val_str = '-' + val_str[1:-1]
    try: return float(val_str)
    except: return 0.0

# --- SISTEMA DE PESTAÑAS (TABS) ---
tab1, tab2 = st.tabs(["🎓 Estado de Estudiantes (Admin)", "➕ Auditar Sesión a Estudiante"])

# ==========================================
# TAB 1: DASHBOARD DE MENTORA (ESTUDIANTES)
# ==========================================
with tab1:
    st.subheader("Vista General de la Comunidad")
    
    # 1. Leer la base de datos real (si existe)
    if os.path.exists(DB_FILE):
        df_real = pd.read_csv(DB_FILE)
    else:
        df_real = pd.DataFrame(columns=["Student", "Date", "PnL", "Trades", "D_Score", "Status"])

    # 2. Inyectar datos dummy para visualización (Mockup)
    dummy_data = pd.DataFrame([
        {"Student": "Carlos R.", "Date": "2026-08-19", "PnL": 450.00, "Trades": 2, "D_Score": 95, "Status": "PASS"},
        {"Student": "María F.", "Date": "2026-08-19", "PnL": -150.00, "Trades": 1, "D_Score": 100, "Status": "PASS"},
        {"Student": "Javier T.", "Date": "2026-08-19", "PnL": -850.00, "Trades": 8, "D_Score": 45, "Status": "SIM-MODE"},
        {"Student": "Ana Gómez", "Date": "2026-08-19", "PnL": 120.00, "Trades": 3, "D_Score": 85, "Status": "PASS"}
    ])
    
    # Unir datos simulados con los datos reales que vayas subiendo
    df_dashboard = pd.concat([dummy_data, df_real], ignore_index=True) if not df_real.empty else dummy_data
    
    # Métricas Globales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estudiantes Activos", len(df_dashboard['Student'].unique()))
    c2.metric("Promedio Global D-Score", f"{df_dashboard['D_Score'].mean():.0f}/100")
    c3.metric("En Simulación (Castigados)", len(df_dashboard[df_dashboard['Status'] == 'SIM-MODE']))
    c4.metric("P&L Total Comunidad", f"${df_dashboard['PnL'].sum():,.2f}")
    
    st.markdown("---")
    
    # Columnas para Gráfico y Tabla
    col_chart, col_table = st.columns([1.5, 2])
    
    with col_chart:
        st.markdown("#### Riesgo vs Disciplina")
        fig = px.scatter(df_dashboard, x="D_Score", y="PnL", color="Status", 
                         hover_name="Student", size_max=60, template="plotly_dark",
                         color_discrete_map={"PASS": "#4ade80", "SIM-MODE": "#ef4444"})
        fig.add_vline(x=80, line_dash="dash", line_color="gray", annotation_text="Límite Sim-Mode")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("#### Últimas Sesiones Auditadas")
        
        # Función para dar color al estatus en la tabla
        def color_status(val):
            color = '#4ade80' if val == 'PASS' else '#ef4444'
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(
            df_dashboard[['Student', 'Date', 'PnL', 'D_Score', 'Status']].sort_values(by="Date", ascending=False),
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# TAB 2: AUDITORÍA (LO QUE YA CONSTRUIMOS)
# ==========================================
with tab2:
    st.subheader("Auditar Sesión de NinjaTrader")
    
    # AHORA ELIGES A QUIÉN LE ASIGNAS EL ARCHIVO
    selected_student = st.selectbox("👤 Asignar esta sesión al estudiante:", STUDENTS)
    
    uploaded_file = st.file_uploader("Sube el CSV de NinjaTrader", type=["csv", "txt"])

    pnl_auto, total_trades_auto, win_rate_auto = 0.0, 0, 0.0

    if uploaded_file is not None:
        try:
            try: df_nt = pd.read_csv(uploaded_file, sep=None, engine='python')
            except:
                uploaded_file.seek(0)
                df_nt = pd.read_csv(uploaded_file, sep=';')
            
            profit_col = 'Profit' if 'Profit' in df_nt.columns else None
            if not profit_col:
                for col in df_nt.columns:
                    if 'profit' in str(col).lower() and 'cum' not in str(col).lower():
                        profit_col = col; break

            if profit_col:
                df_nt['pnl_clean'] = df_nt[profit_col].apply(parse_pnl_value)
                group_cols = [c for c in ['Entry time', 'Exit time', 'Instrument'] if c in df_nt.columns]
                trades_df = df_nt.groupby(group_cols, as_index=False)['pnl_clean'].sum() if group_cols else df_nt[['pnl_clean']]

                pnl_auto = float(trades_df['pnl_clean'].sum())
                total_trades_auto = len(trades_df)
                st.success(f"✅ Archivo procesado. Trades consolidados: {total_trades_auto}")
        except Exception as e:
            st.error(f"Error al leer: {e}")

    # Formulario del D-Score
    with st.form("d_score_form"):
        st.markdown(f"**Evaluando a:** {selected_student}")
        col_p1, col_p2, col_p3 = st.columns(3)
        p1 = col_p1.radio("🛡️ Gestión de Riesgo", [1, 2, 3, 4, 5], index=4, horizontal=True)
        p2 = col_p2.radio("🎯 Ejecución (Plan)", [1, 2, 3, 4, 5], index=4, horizontal=True)
        p3 = col_p3.radio("🧘 Control Emocional", [1, 2, 3, 4, 5], index=4, horizontal=True)
        
        col_p4, col_p5 = st.columns([1, 2])
        p4 = col_p4.radio("⏱️ Overtrading", [1, 2, 3, 4, 5], index=4, horizontal=True)
        notes = col_p5.text_input("📝 Notas del Mentor", "")
        
        d_score_total = (p1 + p2 + p3 + p4) * 5 
        status = "PASS" if d_score_total >= 80 else "SIM-MODE"
        
        submit_button = st.form_submit_button("Guardar Evaluación en Base de Datos")

    if submit_button:
        new_data = pd.DataFrame([{
            "Student": selected_student,  # AHORA SE GUARDA EL NOMBRE DEL ESTUDIANTE
            "Date": str(date.today()),
            "PnL": pnl_auto,
            "Trades": total_trades_auto,
            "D_Score": d_score_total,
            "Status": status,
            "Notes": notes
        }])
        
        if os.path.exists(DB_FILE):
            new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
        else:
            new_data.to_csv(DB_FILE, index=False)
            
        st.success(f"Registro guardado para {selected_student}. Revisa la pestaña 'Estado de Estudiantes'.")
