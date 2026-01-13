import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Auditoría Pub V2", layout="wide")

st.title("🕵️ Herramienta de Auditoría Avanzada - Pub")
st.markdown("---")

# --- BARRA LATERAL: CONFIGURACIÓN Y DATOS ---
st.sidebar.title("⚙️ Configuración")

# 1. Configuración de Gastos Fijos Mensuales
with st.sidebar.expander("1. Gastos Fijos Mensuales", expanded=True):
    st.caption("Introduce los gastos totales del mes para prorratearlos.")
    alquiler_mes = st.number_input("Alquiler Mensual", value=0.0, step=100.0)
    personal_fijo_mes = st.number_input("Nóminas/Personal Fijo Mes", value=0.0, step=100.0)
    otros_fijos_mes = st.number_input("Luz/Agua/Seguros Mes", value=0.0, step=50.0)
    
    dias_apertura = st.number_input("¿Cuántos días abres al mes?", value=20, min_value=1, max_value=31)
    
    # Cálculo del coste fijo diario
    total_fijos_mes = alquiler_mes + personal_fijo_mes + otros_fijos_mes
    coste_fijo_diario = total_fijos_mes / dias_apertura
    
    st.info(f"Coste Fijo por día de apertura: **{coste_fijo_diario:.2f}€**")

# 2. Introducción de Datos Diarios
st.sidebar.header("📝 Datos del Día (Diario)")
with st.sidebar.form(key='daily_form'):
    fecha = st.date_input("Fecha")
    
    st.subheader("💰 La Caja (Z)")
    col_a, col_b = st.columns(2)
    z_total = col_a.number_input("Total Venta (Z)", min_value=0.0, format="%.2f")
    tarjeta = col_b.number_input("Total Tarjeta", min_value=0.0, format="%.2f")
    efectivo_real = st.number_input("Efectivo RECONTADO (Cajón)", min_value=0.0, format="%.2f")
    
    st.subheader("📦 Compras / Variable")
    stock_bebida = st.number_input("Compra de Stock (Bebida) HOY", min_value=0.0, format="%.2f", help="Si hoy compraste para toda la semana, ponlo aquí.")
    personal_extra = st.number_input("Personal Extra/Variable (Hoy)", min_value=0.0, format="%.2f")
    
    submit_button = st.form_submit_button(label='Registrar Día')

# --- LÓGICA DE DATOS ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'Fecha', 'Z_Total', 'Tarjeta', 'Efectivo_Teorico', 
        'Efectivo_Real', 'Descuadre_Caja', 
        'Compra_Stock', 'Personal_Extra', 'Fijo_Diario_Imputado', 
        'Beneficio_Estimado'
    ])

if submit_button:
    # Cálculos
    efectivo_teorico = z_total - tarjeta
    descuadre = efectivo_real - efectivo_teorico
    
    # Beneficio = Ventas - (Compras Stock + Extras + Parte proporcional del fijo)
    # NOTA: Aunque el stock sea para la semana, en flujo de caja sale hoy. 
    # Pero en el análisis gráfico veremos el acumulado.
    beneficio_dia = z_total - (stock_bebida + personal_extra + coste_fijo_diario)
    
    new_row = {
        'Fecha': pd.to_datetime(fecha),
        'Z_Total': z_total,
        'Tarjeta': tarjeta,
        'Efectivo_Teorico': efectivo_teorico,
        'Efectivo_Real': efectivo_real,
        'Descuadre_Caja': descuadre,
        'Compra_Stock': stock_bebida,
        'Personal_Extra': personal_extra,
        'Fijo_Diario_Imputado': coste_fijo_diario,
        'Beneficio_Estimado': beneficio_dia
    }
    
    new_df = pd.DataFrame([new_row])
    st.session_state.data = pd.concat([st.session_state.data, new_df], ignore_index=True)
    st.success(f"Día {fecha} registrado. Coste fijo imputado: {coste_fijo_diario:.2f}€")

# --- DASHBOARD ---
if not st.session_state.data.empty:
    df = st.session_state.data.sort_values(by='Fecha')
    
    # KPIs GLOBALES (Lo importante para la reunión)
    st.header("📊 Visión Global del Periodo Analizado")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Descuadre ACUMULADO (¿Falta dinero en total?)
    sum_descuadre = df['Descuadre_Caja'].sum()
    col1.metric("Descuadre Caja Acumulado", f"{sum_descuadre:.2f}€", delta_color="normal")
    if sum_descuadre < -20:
        col1.error("🚨 FALTA EFECTIVO")
    
    # 2. Ratio de Bebida ACUMULADO (La clave para el stock semanal)
    total_ventas = df['Z_Total'].sum()
    total_compras_stock = df['Compra_Stock'].sum()
    
    if total_ventas > 0:
        ratio_stock_real = (total_compras_stock / total_ventas) * 100
    else:
        ratio_stock_real = 0
        
    col2.metric("Ratio Coste Bebida (Global)", f"{ratio_stock_real:.1f}%")
    if ratio_stock_real > 35:
        col2.warning("⚠️ OJO: Ratio alto (>35%)")
    elif ratio_stock_real < 20:
        col2.success("✅ Ratio excelente")
        
    # 3. Beneficio Neto Estimado
    total_beneficio = df['Beneficio_Estimado'].sum()
    col3.metric("Beneficio Neto (Estimado)", f"{total_beneficio:.2f}€")

    # 4. Proyección Ventas Mes (Si seguimos así)
    dias_registrados = len(df)
    if dias_registrados > 0:
        proyeccion = (total_ventas / dias_registrados) * dias_apertura
        col4.metric("Proyección Ventas Mes", f"{proyeccion:.0f}€")

    st.markdown("---")

    # GRÁFICOS DE ANÁLISIS
    c1, c2 = st.columns(2)
    
    # Gráfico 1: Ventas vs Compras ACUMULADAS
    # Este gráfico soluciona tu problema: verás si la línea de ventas se separa de la de compras
    with c1:
        st.subheader("📈 Ventas vs. Compras (Acumulado)")
        df['Venta_Acumulada'] = df['Z_Total'].cumsum()
        df['Stock_Acumulado'] = df['Compra_Stock'].cumsum()
        
        fig_ac = go.Figure()
        fig_ac.add_trace(go.Scatter(x=df['Fecha'], y=df['Venta_Acumulada'], mode='lines+markers', name='Ventas Acumuladas', line=dict(color='green', width=3)))
        fig_ac.add_trace(go.Scatter(x=df['Fecha'], y=df['Stock_Acumulado'], mode='lines+markers', name='Gasto Bebida Acumulado', line=dict(color='red')))
        fig_ac.update_layout(title="Si la línea roja toca la verde, pierdes dinero.")
        st.plotly_chart(fig_ac, use_container_width=True)
        st.caption("*Este gráfico suaviza los picos de compra de stock semanal.*")

    # Gráfico 2: Desglose de Gastos Diarios (Incluyendo el fijo prorrateado)
    with c2:
        st.subheader("🍰 Estructura de Costes Diaria")
        # Preparamos datos para barra apilada
        fig_bar = px.bar(df, x='Fecha', y=['Compra_Stock', 'Personal_Extra', 'Fijo_Diario_Imputado', 'Beneficio_Estimado'],
                         title="¿A dónde va el dinero cada día?",
                         labels={'value': 'Euros', 'variable': 'Concepto'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # TABLA DE DATOS
    with st.expander("Ver Tabla de Datos Detallada"):
        st.dataframe(df.style.format("{:.2f}€", subset=['Z_Total', 'Efectivo_Real', 'Descuadre_Caja', 'Beneficio_Estimado']))

else:
    st.info("👈 Introduce primero la Configuración Mensual y luego registra el primer día.")
