import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración
st.set_page_config(page_title="Auditoría Pub V3 - Dinámica", layout="wide")

# --- INICIALIZACIÓN DE DATOS ---
if 'diario' not in st.session_state:
    st.session_state.diario = pd.DataFrame(columns=[
        'Fecha', 'Mes_Ref', 'Z_Total', 'Tarjeta', 
        'Efectivo_Teorico', 'Efectivo_Real', 'Descuadre_Caja', 
        'Gasto_Personal_Dia', 'Compra_Stock_Dia'
    ])

if 'fijos' not in st.session_state:
    st.session_state.fijos = pd.DataFrame(columns=['Mes_Ref', 'Concepto', 'Importe'])

# Función auxiliar para formato mes (YYYY-MM)
def get_month_str(date_obj):
    return date_obj.strftime("%Y-%m")

# --- SIDEBAR: INTRODUCCIÓN DE DATOS ---
st.sidebar.title("📝 Panel de Control")

# 1. GASTOS FIJOS (FACTURAS)
with st.sidebar.expander("1. Añadir Factura / Gasto Fijo", expanded=False):
    st.caption("Luz, Agua, Alquiler, Seguros...")
    mes_gasto = st.date_input("Mes al que pertenece la factura", key="date_gasto")
    concepto = st.selectbox("Tipo de Gasto", ["Alquiler", "Luz", "Agua", "Gestoría", "Internet", "Otros"])
    importe_fijo = st.number_input("Importe Factura (€)", min_value=0.0, step=10.0, key="imp_gasto")
    
    if st.button("Guardar Gasto Fijo"):
        mes_str = get_month_str(mes_gasto)
        new_gasto = {'Mes_Ref': mes_str, 'Concepto': concepto, 'Importe': importe_fijo}
        st.session_state.fijos = pd.concat([st.session_state.fijos, pd.DataFrame([new_gasto])], ignore_index=True)
        st.success(f"Gasto de {concepto} añadido a {mes_str}")

# 2. OPERATIVA DIARIA
with st.sidebar.expander("2. Añadir Día de Apertura", expanded=True):
    st.caption("Datos del cierre de cada noche")
    fecha_dia = st.date_input("Fecha de Apertura", key="date_dia")
    
    st.markdown("**Ingresos y Caja**")
    z_dia = st.number_input("Total Z (Ventas)", min_value=0.0, step=50.0)
    tarjeta_dia = st.number_input("Total Tarjeta", min_value=0.0, step=50.0)
    efectivo_real_dia = st.number_input("Efectivo RECONTADO (Cajón)", min_value=0.0, step=50.0)
    
    st.markdown("**Gastos del Día**")
    personal_dia = st.number_input("Pago Personal (Hoy)", min_value=0.0, step=10.0)
    stock_dia = st.number_input("Compra Bebida/Hielo (Hoy)", min_value=0.0, step=10.0)
    
    if st.button("Guardar Día"):
        mes_str = get_month_str(fecha_dia)
        teorico = z_dia - tarjeta_dia
        descuadre = efectivo_real_dia - teorico
        
        new_dia = {
            'Fecha': pd.to_datetime(fecha_dia),
            'Mes_Ref': mes_str,
            'Z_Total': z_dia,
            'Tarjeta': tarjeta_dia,
            'Efectivo_Teorico': teorico,
            'Efectivo_Real': efectivo_real_dia,
            'Descuadre_Caja': descuadre,
            'Gasto_Personal_Dia': personal_dia,
            'Compra_Stock_Dia': stock_dia
        }
        st.session_state.diario = pd.concat([st.session_state.diario, pd.DataFrame([new_dia])], ignore_index=True)
        st.success(f"Día {fecha_dia} registrado correctamente.")

# --- LÓGICA DE ANÁLISIS ---
st.title("🕵️ Auditoría Financiera y Fraude")

# Selector de Mes para analizar
if not st.session_state.diario.empty:
    lista_meses = st.session_state.diario['Mes_Ref'].unique()
    mes_seleccionado = st.selectbox("Selecciona el Mes a Analizar", lista_meses)
    
    # FILTRAR DATOS POR MES
    df_d = st.session_state.diario[st.session_state.diario['Mes_Ref'] == mes_seleccionado].copy()
    df_f = st.session_state.fijos[st.session_state.fijos['Mes_Ref'] == mes_seleccionado].copy()
    
    # CÁLCULOS DINÁMICOS
    # 1. Cuántos días se abrió este mes
    dias_abiertos = len(df_d)
    
    # 2. Total Gastos Fijos del Mes
    total_fijos_mes = df_f['Importe'].sum()
    
    # 3. Ratio diario (La clave de tu petición)
    if dias_abiertos > 0:
        coste_fijo_por_dia_abierto = total_fijos_mes / dias_abiertos
    else:
        coste_fijo_por_dia_abierto = 0
        
    # 4. Aplicar gastos al dataframe diario para ver beneficio real
    df_d['Fijo_Asignado'] = coste_fijo_por_dia_abierto
    df_d['Beneficio_Neto'] = df_d['Z_Total'] - (df_d['Gasto_Personal_Dia'] + df_d['Compra_Stock_Dia'] + df_d['Fijo_Asignado'])

    # --- MOSTRAR RESULTADOS ---
    
    # ALARMAS DE FRAUDE
    st.subheader("🚨 Detección de Anomalías")
    c1, c2, c3 = st.columns(3)
    
    total_descuadre = df_d['Descuadre_Caja'].sum()
    c1.metric("Descuadre Caja (Total Mes)", f"{total_descuadre:.2f} €")
    if total_descuadre < -10:
        c1.error("FALTA DINERO EN CAJA")
        
    total_ventas = df_d['Z_Total'].sum()
    total_stock = df_d['Compra_Stock_Dia'].sum()
    ratio_bebida = (total_stock / total_ventas * 100) if total_ventas > 0 else 0
    
    c2.metric("% Coste Bebida (Real)", f"{ratio_bebida:.1f} %")
    if ratio_bebida > 35:
        c2.warning("ALTO CONSUMO STOCK")
        
    beneficio_total = df_d['Beneficio_Neto'].sum()
    c3.metric("Beneficio Neto Real (Tras Gastos)", f"{beneficio_total:.2f} €")

    st.markdown("---")
    
    # VISUALIZACIÓN DE GASTOS
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("### 📉 Resumen de Costes")
        st.info(f"Días abiertos este mes: **{dias_abiertos}**")
        st.info(f"Total Facturas Fijas: **{total_fijos_mes:.2f}€**")
        st.warning(f"Cada vez que abres, cuesta de fijos: **{coste_fijo_por_dia_abierto:.2f}€**")
        
        # Tabla de facturas fijas
        if not df_f.empty:
            st.write("Listado de Facturas:")
            st.dataframe(df_f[['Concepto', 'Importe']], hide_index=True)

    with col_right:
        st.markdown("### 📊 Evolución Diaria (Realidad)")
        # Gráfico de barras apiladas
        fig = px.bar(df_d, x='Fecha', 
                     y=['Compra_Stock_Dia', 'Gasto_Personal_Dia', 'Fijo_Asignado', 'Beneficio_Neto'],
                     title="Composición de cada día (Ingresos vs Gastos)",
                     labels={'value': 'Euros', 'variable': 'Concepto'})
        st.plotly_chart(fig, use_container_width=True)

    # TABLA DETALLADA FINAL
    st.subheader("📋 Detalle Día a Día")
    st.dataframe(df_d[['Fecha', 'Z_Total', 'Descuadre_Caja', 'Gasto_Personal_Dia', 'Fijo_Asignado', 'Beneficio_Neto']].style.format("{:.2f}€"))

else:
    st.info("👈 Empieza añadiendo días de apertura en el menú de la izquierda.")
