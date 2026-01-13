import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Control Wateqe", layout="wide")

# --- GESTIÓN DE ESTADO (MEMORIA) ---
if 'diario' not in st.session_state:
    st.session_state.diario = pd.DataFrame(columns=[
        'Fecha', 'Mes_Ref', 'Z_Total', 'Tarjeta', 
        'Efectivo_Teorico', 'Efectivo_Real', 'Descuadre_Caja', 
        'Personal_Dia'
    ])

if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=['Fecha', 'Mes_Ref', 'Categoria', 'Importe'])

if 'fijos' not in st.session_state:
    st.session_state.fijos = pd.DataFrame(columns=['Mes_Ref', 'Concepto', 'Importe'])

if 'categorias_stock' not in st.session_state:
    st.session_state.categorias_stock = ["Bebida Alcohol", "Refrescos", "Hielo", "Fruta/Varios"]

if 'categorias_fijos' not in st.session_state:
    st.session_state.categorias_fijos = ["Alquiler", "Luz", "Agua", "Gestoría", "Internet"]

def get_month_str(date_obj):
    return date_obj.strftime("%Y-%m")

# --- SIDEBAR: INTRODUCCIÓN DE DATOS ---
st.sidebar.title("🎮 Panel de Control")

# --- CARGA MASIVA ---
with st.sidebar.expander("📂 Importar Histórico (Excel/CSV)", expanded=False):
    uploaded_file = st.file_uploader("Sube el archivo CSV", type=['csv'])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)
            df_upload['Fecha'] = pd.to_datetime(df_upload['Fecha'])
            if st.button("Cargar Datos"):
                st.session_state.stock = pd.concat([st.session_state.stock, df_upload], ignore_index=True)
                st.success(f"¡Cargadas {len(df_upload)} líneas!")
        except Exception as e:
            st.error(f"Error: {e}")

# SECCIÓN 1: CATEGORÍAS
with st.sidebar.expander("➕ Añadir Categoría", expanded=False):
    tipo_cat = st.radio("Tipo:", ["Proveedor/Stock", "Gasto Fijo"])
    nueva_cat = st.text_input("Nombre:")
    if st.button("Crear"):
        if nueva_cat:
            if tipo_cat == "Proveedor/Stock":
                if nueva_cat not in st.session_state.categorias_stock:
                    st.session_state.categorias_stock.append(nueva_cat)
            else:
                if nueva_cat not in st.session_state.categorias_fijos:
                    st.session_state.categorias_fijos.append(nueva_cat)
            st.success("Añadido")

# SECCIÓN 2: GASTOS FIJOS
with st.sidebar.expander("1. Gastos Fijos (Alquiler/Luz)", expanded=False):
    mes_gasto = st.date_input("Mes", key="fijo_date")
    cat_fijo = st.selectbox("Concepto", st.session_state.categorias_fijos)
    imp_fijo = st.number_input("Importe (€)", min_value=0.0, step=50.0, key="fijo_imp")
    if st.button("Guardar Fijo"):
        mes_str = get_month_str(mes_gasto)
        duplicado = st.session_state.fijos[(st.session_state.fijos['Mes_Ref'] == mes_str) & (st.session_state.fijos['Concepto'] == cat_fijo)]
        if not duplicado.empty:
            st.error("⛔ Ya existe este gasto este mes.")
        else:
            nuevo = {'Mes_Ref': mes_str, 'Concepto': cat_fijo, 'Importe': imp_fijo}
            st.session_state.fijos = pd.concat([st.session_state.fijos, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("Guardado.")

# SECCIÓN 3: COMPRA STOCK MANUAL
with st.sidebar.expander("2. Compra Manual Stock", expanded=False):
    fecha_stock = st.date_input("Fecha", key="stock_date")
    cat_stock = st.selectbox("Producto", st.session_state.categorias_stock)
    imp_stock = st.number_input("Importe (€)", min_value=0.0, step=10.0, key="stock_imp")
    if st.button("Registrar Compra"):
        mes_str = get_month_str(fecha_stock)
        nuevo = {'Fecha': pd.to_datetime(fecha_stock), 'Mes_Ref': mes_str, 'Categoria': cat_stock, 'Importe': imp_stock}
        st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([nuevo])], ignore_index=True)
        st.success("Registrado.")

# SECCIÓN 4: CIERRE DIARIO
with st.sidebar.expander("3. Cierre Diario", expanded=True):
    fecha_dia = st.date_input("Fecha Apertura", key="dia_date")
    z_dia = st.number_input("Z Total", min_value=0.0, step=50.0)
    tarjeta = st.number_input("Tarjeta", min_value=0.0, step=50.0)
    efectivo_real = st.number_input("Efectivo Cajón", min_value=0.0, step=50.0)
    personal = st.number_input("Nóminas Hoy", min_value=0.0, step=10.0)
    if st.button("Cerrar Día"):
        if not st.session_state.diario.empty and pd.to_datetime(fecha_dia) in st.session_state.diario['Fecha'].values:
             st.error("⛔ Día ya registrado.")
        else:
            mes_str = get_month_str(fecha_dia)
            teorico = z_dia - tarjeta
            descuadre = efectivo_real - teorico
            nuevo = {
                'Fecha': pd.to_datetime(fecha_dia), 'Mes_Ref': mes_str,
                'Z_Total': z_dia, 'Tarjeta': tarjeta,
                'Efectivo_Teorico': teorico, 'Efectivo_Real': efectivo_real,
                'Descuadre_Caja': descuadre, 'Personal_Dia': personal
            }
            st.session_state.diario = pd.concat([st.session_state.diario, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("Día Registrado.")

# --- DASHBOARD ---
st.title("🍹 Control de Cuentas Pub Wateqe")

# CREAMOS LAS PESTAÑAS
tab_mes, tab_anual = st.tabs(["📅 Análisis Mensual", "📈 Resumen ANUAL"])

# ==========================================
# PESTAÑA 1: VISIÓN MENSUAL (Lo de antes)
# ==========================================
with tab_mes:
    todos_meses = set(st.session_state.diario['Mes_Ref'].unique()) | set(st.session_state.stock['Mes_Ref'].unique()) | set(st.session_state.fijos['Mes_Ref'].unique())
    lista_meses = sorted(list(todos_meses))

    if lista_meses:
        mes_sel = st.selectbox("Seleccionar Mes", lista_meses, index=len(lista_meses)-1)
        
        # Filtrado
        df_d = st.session_state.diario[st.session_state.diario['Mes_Ref'] == mes_sel].copy()
        df_s = st.session_state.stock[st.session_state.stock['Mes_Ref'] == mes_sel].copy()
        df_f = st.session_state.fijos[st.session_state.fijos['Mes_Ref'] == mes_sel].copy()
        
        # Cálculos
        ventas_totales = df_d['Z_Total'].sum()
        personal_total = df_d['Personal_Dia'].sum()
        stock_total = df_s['Importe'].sum()
        fijos_total = df_f['Importe'].sum()
        beneficio = ventas_totales - (personal_total + stock_total + fijos_total)
        
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas Mes", f"{ventas_totales:.0f}€")
        c2.metric("Beneficio Neto", f"{beneficio:.0f}€", delta_color="normal")
        c3.metric("Descuadre Caja", f"{df_d['Descuadre_Caja'].sum():.0f}€")
        
        ratio_stock = (stock_total / ventas_totales * 100) if ventas_totales > 0 else 0
        c4.metric("% Coste Stock", f"{ratio_stock:.1f}%", delta_color="inverse")

        st.markdown("---")
        
        # Gráficos Mes
        col_izq, col_der = st.columns(2)
        with col_izq:
            if not df_s.empty:
                st.subheader("📦 Compras del Mes")
                st.plotly_chart(px.pie(df_s, values='Importe', names='Categoria', hole=0.4), use_container_width=True)
            else: st.info("Sin compras este mes.")

        with col_der:
            st.subheader("📊 Gastos vs Ingresos")
            dat = pd.DataFrame({'Tipo': ['Personal', 'Stock', 'Fijos'], '€': [personal_total, stock_total, fijos_total]})
            st.plotly_chart(px.bar(dat, x='Tipo', y='€', color='Tipo'), use_container_width=True)

        if not df_d.empty:
            st.subheader("📅 Detalle Diario")
            st.dataframe(df_d[['Fecha', 'Z_Total', 'Descuadre_Caja', 'Personal_Dia']].style.format("{:.2f}€"))
    else:
        st.info("Introduce datos para ver el análisis mensual.")

# ==========================================
# PESTAÑA 2: VISIÓN ANUAL (NUEVO)
# ==========================================
with tab_anual:
    if lista_meses:
        st.header("🌍 Visión Global del Año")
        
        # 1. PREPARACIÓN DE DATOS ANUALES
        # Agrupamos todo por MES para poder compararlos
        
        # Ventas y Personal por Mes
        resumen_diario = st.session_state.diario.groupby('Mes_Ref')[['Z_Total', 'Personal_Dia', 'Descuadre_Caja']].sum().reset_index()
        
        # Stock por Mes
        resumen_stock = st.session_state.stock.groupby('Mes_Ref')['Importe'].sum().reset_index().rename(columns={'Importe': 'Gasto_Stock'})
        
        # Fijos por Mes
        resumen_fijos = st.session_state.fijos.groupby('Mes_Ref')['Importe'].sum().reset_index().rename(columns={'Importe': 'Gasto_Fijos'})
        
        # Juntamos todo en una sola tabla maestra (df_anual)
        df_anual = pd.DataFrame({'Mes_Ref': lista_meses})
        df_anual = df_anual.merge(resumen_diario, on='Mes_Ref', how='left').fillna(0)
        df_anual = df_anual.merge(resumen_stock, on='Mes_Ref', how='left').fillna(0)
        df_anual = df_anual.merge(resumen_fijos, on='Mes_Ref', how='left').fillna(0)
        
        # Calculamos Beneficio Mensual
        df_anual['Gastos_Totales'] = df_anual['Personal_Dia'] + df_anual['Gasto_Stock'] + df_anual['Gasto_Fijos']
        df_anual['Beneficio'] = df_anual['Z_Total'] - df_anual['Gastos_Totales']
        df_anual['%_Stock'] = (df_anual['Gasto_Stock'] / df_anual['Z_Total'] * 100).fillna(0)

        # 2. KPIs GLOBALES (TOTAL AÑO)
        col1, col2, col3, col4 = st.columns(4)
        
        total_venta_ano = df_anual['Z_Total'].sum()
        total_beneficio_ano = df_anual['Beneficio'].sum()
        total_descuadre_ano = df_anual['Descuadre_Caja'].sum()
        ratio_stock_ano = (df_anual['Gasto_Stock'].sum() / total_venta_ano * 100) if total_venta_ano > 0 else 0
        
        col1.metric("Ventas Totales (Año)", f"{total_venta_ano:,.0f}€")
        col2.metric("Beneficio Total (Año)", f"{total_beneficio_ano:,.0f}€", delta_color="normal")
        col3.metric("Descuadre Acumulado", f"{total_descuadre_ano:.2f}€")
        col4.metric("% Stock Medio Anual", f"{ratio_stock_ano:.1f}%")
        
        st.markdown("---")
        
        # 3. GRÁFICOS DE EVOLUCIÓN
        
        c_chart1, c_chart2 = st.columns(2)
        
        # Gráfico A: Evolución Ingresos vs Gastos
        with c_chart1:
            st.subheader("📈 Evolución: Ingresos vs Gastos")
            fig_evo = go.Figure()
            # Barra de Ventas
            fig_evo.add_trace(go.Bar(x=df_anual['Mes_Ref'], y=df_anual['Z_Total'], name='Ventas', marker_color='green'))
            # Barra de Gastos
            fig_evo.add_trace(go.Bar(x=df_anual['Mes_Ref'], y=df_anual['Gastos_Totales'], name='Gastos Totales', marker_color='red'))
            
            fig_evo.update_layout(barmode='group')
            st.plotly_chart(fig_evo, use_container_width=True)
            
        # Gráfico B: Evolución del Beneficio
        with c_chart2:
            st.subheader("💰 Tendencia del Beneficio")
            fig_ben = px.line(df_anual, x='Mes_Ref', y='Beneficio', markers=True, title="¿Cuánto ganamos cada mes?")
            fig_ben.add_hline(y=0, line_dash="dash", line_color="grey") # Línea de cero
            st.plotly_chart(fig_ben, use_container_width=True)

        # 4. TABLA RESUMEN ANUAL
        with st.expander("Ver Tabla Resumen por Meses"):
            st.dataframe(df_anual.style.format({
                'Z_Total': "{:.2f}€", 
                'Personal_Dia': "{:.2f}€",
                'Gasto_Stock': "{:.2f}€",
                'Gasto_Fijos': "{:.2f}€",
                'Gastos_Totales': "{:.2f}€",
                'Beneficio': "{:.2f}€",
                '%_Stock': "{:.1f}%"
            }))
            
    else:
        st.info("Aún no hay datos suficientes para mostrar el resumen anual.")
