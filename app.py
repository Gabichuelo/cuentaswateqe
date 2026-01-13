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
    st.session_state.categorias_stock = ["Bebida Alcohol", "Refrescos", "Hielo", "Fruta/Varios", "Proveedor Yus (Bebida)", "Devolución Envases", "Rappel / Devolución"]

if 'categorias_fijos' not in st.session_state:
    st.session_state.categorias_fijos = ["Alquiler", "Luz", "Agua", "Gestoría", "Internet"]

def get_month_str(date_obj):
    return date_obj.strftime("%Y-%m")

# --- SIDEBAR ---
st.sidebar.title("🎮 Panel de Control")

# CARGA MASIVA
with st.sidebar.expander("📂 Importar Histórico (Excel/CSV)", expanded=False):
    uploaded_file = st.file_uploader("Sube el archivo CSV", type=['csv'])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)
            df_upload['Fecha'] = pd.to_datetime(df_upload['Fecha'])
            if st.button("Cargar Datos"):
                st.session_state.stock = pd.concat([st.session_state.stock, df_upload], ignore_index=True)
                # Eliminar duplicados exactos
                st.session_state.stock = st.session_state.stock.drop_duplicates()
                st.success(f"¡Cargado! Total facturas en sistema: {len(st.session_state.stock)}")
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
            st.error("⛔ Ya existe este gasto.")
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

tab_mes, tab_anual = st.tabs(["📅 Análisis Mensual", "📈 Resumen ANUAL"])

# ================= PESTAÑA MENSUAL =================
with tab_mes:
    todos_meses = set(st.session_state.diario['Mes_Ref'].unique()) | set(st.session_state.stock['Mes_Ref'].unique()) | set(st.session_state.fijos['Mes_Ref'].unique())
    lista_meses = sorted(list(todos_meses))

    if lista_meses:
        mes_sel = st.selectbox("Seleccionar Mes", lista_meses, index=len(lista_meses)-1)
        
        # Filtros
        df_d = st.session_state.diario[st.session_state.diario['Mes_Ref'] == mes_sel].copy()
        df_s = st.session_state.stock[st.session_state.stock['Mes_Ref'] == mes_sel].copy()
        df_f = st.session_state.fijos[st.session_state.fijos['Mes_Ref'] == mes_sel].copy()
        
        # KPIs
        ventas_totales = df_d['Z_Total'].sum()
        stock_total = df_s['Importe'].sum()
        fijos_total = df_f['Importe'].sum()
        personal_total = df_d['Personal_Dia'].sum()
        beneficio = ventas_totales - (personal_total + stock_total + fijos_total)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas", f"{ventas_totales:,.0f}€")
        c2.metric("Gasto Stock (Real)", f"{stock_total:,.2f}€", delta_color="inverse")
        c3.metric("Beneficio", f"{beneficio:,.0f}€")
        
        ratio = (stock_total/ventas_totales*100) if ventas_totales > 0 else 0
        c4.metric("% Ratio Bebida", f"{ratio:.1f}%")

        st.markdown("---")
        
        # AQUÍ ESTÁ LO QUE PEDÍAS: TABLA DETALLADA DE FACTURAS
        col_izq, col_der = st.columns([1, 1])
        
        with col_izq:
            st.subheader(f"🧾 Facturas de {mes_sel}")
            if not df_s.empty:
                # Mostramos la tabla formateada
                st.dataframe(
                    df_s[['Fecha', 'Categoria', 'Importe']].style.format({"Importe": "{:.2f}€"}),
                    use_container_width=True,
                    height=300
                )
                st.caption(f"Total Facturas en lista: {len(df_s)}")
            else:
                st.info("No hay facturas este mes.")

        with col_der:
            st.subheader("📊 Distribución")
            if not df_s.empty:
                # Agrupamos por categoría para el gráfico
                df_pie = df_s.groupby('Categoria')['Importe'].sum().reset_index()
                st.plotly_chart(px.pie(df_pie, values='Importe', names='Categoria', hole=0.4), use_container_width=True)

        st.markdown("---")
        st.subheader("📅 Operativa Diaria")
        if not df_d.empty:
            st.dataframe(df_d[['Fecha', 'Z_Total', 'Descuadre_Caja', 'Personal_Dia']].style.format("{:.2f}€"), use_container_width=True)

    else:
        st.info("Carga datos primero.")

# ================= PESTAÑA ANUAL =================
with tab_anual:
    if lista_meses:
        st.header("🌍 Visión Global")
        
        # Agrupación Anual
        res_diario = st.session_state.diario.groupby('Mes_Ref')[['Z_Total', 'Personal_Dia', 'Descuadre_Caja']].sum().reset_index()
        res_stock = st.session_state.stock.groupby('Mes_Ref')['Importe'].sum().reset_index().rename(columns={'Importe': 'Gasto_Stock'})
        res_fijos = st.session_state.fijos.groupby('Mes_Ref')['Importe'].sum().reset_index().rename(columns={'Importe': 'Gasto_Fijos'})
        
        df_anual = pd.DataFrame({'Mes_Ref': lista_meses})
        df_anual = df_anual.merge(res_diario, on='Mes_Ref', how='left').fillna(0)
        df_anual = df_anual.merge(res_stock, on='Mes_Ref', how='left').fillna(0)
        df_anual = df_anual.merge(res_fijos, on='Mes_Ref', how='left').fillna(0)
        
        df_anual['Gastos_Tot'] = df_anual['Personal_Dia'] + df_anual['Gasto_Stock'] + df_anual['Gasto_Fijos']
        df_anual['Beneficio'] = df_anual['Z_Total'] - df_anual['Gastos_Tot']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Año", f"{df_anual['Z_Total'].sum():,.0f}€")
        c2.metric("Gasto Stock Año", f"{df_anual['Gasto_Stock'].sum():,.0f}€")
        c3.metric("Beneficio Neto Año", f"{df_anual['Beneficio'].sum():,.0f}€")
        
        st.subheader("Evolución Mensual")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_anual['Mes_Ref'], y=df_anual['Z_Total'], name='Ventas', marker_color='#2ecc71'))
        fig.add_trace(go.Bar(x=df_anual['Mes_Ref'], y=df_anual['Gasto_Stock'], name='Stock (Bebida)', marker_color='#e74c3c'))
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Ver Datos Anuales"):
            st.dataframe(df_anual)
