import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Detector de Fraude - Pub", layout="wide")

st.title("🕵️ Herramienta de Auditoría y Control - Pub")
st.markdown("---")

# --- BARRA LATERAL: INTRODUCCIÓN DE DATOS ---
st.sidebar.header("📝 Introducir Datos del Día")

with st.sidebar.form(key='daily_form'):
    fecha = st.date_input("Fecha")
    
    st.subheader("💰 Ingresos (Cierre Z)")
    z_total = st.number_input("Total Venta (Z)", min_value=0.0, format="%.2f")
    tarjeta = st.number_input("Cobrado en Tarjeta", min_value=0.0, format="%.2f")
    efectivo_real = st.number_input("Efectivo Contado en Caja (Real)", min_value=0.0, format="%.2f")
    
    st.subheader("💸 Gastos / Compras")
    gasto_bebida = st.number_input("Compra de Bebida (Stock)", min_value=0.0, format="%.2f")
    gasto_personal = st.number_input("Personal", min_value=0.0, format="%.2f")
    gasto_alquiler = st.number_input("Alquiler/Fijos", min_value=0.0, format="%.2f")
    otros_gastos = st.number_input("Otros", min_value=0.0, format="%.2f")
    
    submit_button = st.form_submit_button(label='Añadir Registro')

# --- LÓGICA DE DATOS ---
# Inicializar el DataFrame en la sesión si no existe
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'Fecha', 'Z_Total', 'Tarjeta', 'Efectivo_Teorico', 
        'Efectivo_Real', 'Descuadre', 'Gasto_Bebida', 
        'Personal', 'Alquiler', 'Otros', 'Beneficio'
    ])

# Procesar el formulario
if submit_button:
    efectivo_teorico = z_total - tarjeta
    descuadre = efectivo_real - efectivo_teorico
    total_gastos = gasto_bebida + gasto_personal + gasto_alquiler + otros_gastos
    beneficio = z_total - total_gastos
    
    new_row = {
        'Fecha': fecha,
        'Z_Total': z_total,
        'Tarjeta': tarjeta,
        'Efectivo_Teorico': efectivo_teorico,
        'Efectivo_Real': efectivo_real,
        'Descuadre': descuadre,
        'Gasto_Bebida': gasto_bebida,
        'Personal': gasto_personal,
        'Alquiler': gasto_alquiler,
        'Otros': otros_gastos,
        'Beneficio': beneficio
    }
    
    # Convertir a DataFrame y concatenar
    new_df = pd.DataFrame([new_row])
    st.session_state.data = pd.concat([st.session_state.data, new_df], ignore_index=True)
    st.success(f"Datos del día {fecha} añadidos correctamente.")

# --- PANEL DE CONTROL (DASHBOARD) ---
if not st.session_state.data.empty:
    df = st.session_state.data
    
    # 1. ALARMAS DE FRAUDE (Lo más importante para tu reunión)
    st.header("🚨 Análisis de Fraude y Alertas")
    
    col1, col2, col3 = st.columns(3)
    
    # KPI 1: Descuadre de Caja Acumulado
    total_descuadre = df['Descuadre'].sum()
    color_descuadre = "inverse" if total_descuadre >= 0 else "normal"
    col1.metric("Descuadre Acumulado de Caja", f"{total_descuadre:.2f}€", 
                help="Si es negativo, falta dinero en caja comparado con la Z.")
    
    if total_descuadre < -10:
        col1.error("⚠️ FALTA DINERO: El efectivo contado es menor que lo que marca la máquina.")

    # KPI 2: Ratio de Coste de Bebida (Cost of Goods Sold)
    total_ventas = df['Z_Total'].sum()
    total_coste_bebida = df['Gasto_Bebida'].sum()
    
    if total_ventas > 0:
        ratio_coste = (total_coste_bebida / total_ventas) * 100
    else:
        ratio_coste = 0
        
    col2.metric("% Coste de Bebida", f"{ratio_coste:.1f}%")
    
    if ratio_coste > 35:
        col2.error("⚠️ ROBO DE STOCK: El coste de bebida es sospechosamente alto (>35%).")
    elif ratio_coste < 15 and total_coste_bebida > 0:
        col2.warning("❓ RARO: El coste es muy bajo. ¿Están metiendo bebida de contrabando?")
    else:
        col2.success("✅ Ratio de bebida normal.")

    # KPI 3: Porcentaje de Efectivo
    total_tarjeta = df['Tarjeta'].sum()
    porcentaje_efectivo = ((total_ventas - total_tarjeta) / total_ventas) * 100 if total_ventas > 0 else 0
    col3.metric("% Ventas en Efectivo", f"{porcentaje_efectivo:.1f}%")
    
    if porcentaje_efectivo < 10:
        col3.warning("⚠️ Poco efectivo: ¿Están cobrando sin registrar?")

    st.markdown("---")

    # 2. TABLA DE DATOS DETALLADA
    st.subheader("📋 Registro Detallado")
    st.dataframe(df.style.format("{:.2f}€", subset=['Z_Total', 'Tarjeta', 'Efectivo_Teorico', 'Efectivo_Real', 'Descuadre', 'Gasto_Bebida', 'Beneficio']))

    # 3. GRÁFICOS VISUALES
    st.subheader("📊 Evolución Visual")
    
    c1, c2 = st.columns(2)
    
    # Gráfico Ingresos vs Gastos
    with c1:
        fig_bar = px.bar(df, x='Fecha', y=['Z_Total', 'Gasto_Bebida', 'Personal'], 
                         title="Ventas vs Costes Principales", barmode='group')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    # Gráfico Descuadres
    with c2:
        fig_line = px.line(df, x='Fecha', y='Descuadre', title="Evolución del Descuadre de Caja (Debe ser 0)", markers=True)
        fig_line.add_hline(y=0, line_dash="dash", line_color="green")
        st.plotly_chart(fig_line, use_container_width=True)

else:
    st.info("👈 Usa el panel de la izquierda para introducir los datos del primer día.")
