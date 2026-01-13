import streamlit as st
import pandas as pd
import plotly.express as px

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

# --- NUEVA FUNCIÓN: CARGA MASIVA ---
with st.sidebar.expander("📂 Importar Histórico (Excel/CSV)", expanded=False):
    st.info("Sube aquí el archivo que te generaré con los datos del PDF.")
    uploaded_file = st.file_uploader("Elige el archivo CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Leemos el CSV
            df_upload = pd.read_csv(uploaded_file)
            
            # Convertimos fecha a datetime
            df_upload['Fecha'] = pd.to_datetime(df_upload['Fecha'])
            
            # Botón de confirmación
            if st.button("Cargar Datos del Archivo"):
                st.session_state.stock = pd.concat([st.session_state.stock, df_upload], ignore_index=True)
                st.success(f"¡Cargadas {len(df_upload)} facturas correctamente!")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

# SECCIÓN 1: CONFIGURACIÓN DE CATEGORÍAS
with st.sidebar.expander("➕ Añadir Nueva Categoría", expanded=False):
    tipo_cat = st.radio("Tipo:", ["Proveedor/Stock", "Gasto Fijo"])
    nueva_cat = st.text_input("Nombre:")
    if st.button("Crear"):
        if nueva_cat:
            if tipo_cat == "Proveedor/Stock":
                if nueva_cat not in st.session_state.categorias_stock:
                    st.session_state.categorias_stock.append(nueva_cat)
                    st.success("Añadido")
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
            st.error(f"⛔ Ya existe {cat_fijo} en {mes_str}.")
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
             st.error(f"⛔ El día {fecha_dia} ya existe.")
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

todos_meses = set(st.session_state.diario['Mes_Ref'].unique()) | set(st.session_state.stock['Mes_Ref'].unique()) | set(st.session_state.fijos['Mes_Ref'].unique())
lista_meses = sorted(list(todos_meses))

if lista_meses:
    mes_sel = st.selectbox("Mes a Analizar", lista_meses, index=len(lista_meses)-1)
    
    df_d = st.session_state.diario[st.session_state.diario['Mes_Ref'] == mes_sel].copy()
    df_s = st.session_state.stock[st.session_state.stock['Mes_Ref'] == mes_sel].copy()
    df_f = st.session_state.fijos[st.session_state.fijos['Mes_Ref'] == mes_sel].copy()
    
    ventas_totales = df_d['Z_Total'].sum()
    personal_total = df_d['Personal_Dia'].sum()
    stock_total = df_s['Importe'].sum()
    fijos_total = df_f['Importe'].sum()
    
    beneficio = ventas_totales - (personal_total + stock_total + fijos_total)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas", f"{ventas_totales:.0f}€")
    c2.metric("Beneficio", f"{beneficio:.0f}€", delta_color="normal")
    c3.metric("Descuadre Caja", f"{df_d['Descuadre_Caja'].sum():.0f}€")
    
    ratio_stock = (stock_total / ventas_totales * 100) if ventas_totales > 0 else 0
    c4.metric("% Coste Stock", f"{ratio_stock:.1f}%")
    if ratio_stock > 35: c4.error("⚠️ Alto")
    else: c4.success("✅ OK")

    st.markdown("---")
    
    col_izq, col_der = st.columns([1, 1])
    with col_izq:
        st.subheader("📦 Compras")
        if not df_s.empty:
            fig_pie = px.pie(df_s, values='Importe', names='Categoria', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            with st.expander("Ver detalle facturas"):
                st.dataframe(df_s, hide_index=True)
        else: st.info("Sin compras.")

    with col_der:
        st.subheader("📊 Gastos vs Ingresos")
        dat = pd.DataFrame({'Tipo': ['Personal', 'Stock', 'Fijos'], '€': [personal_total, stock_total, fijos_total]})
        st.plotly_chart(px.bar(dat, x='Tipo', y='€', color='Tipo'), use_container_width=True)

    st.subheader("📅 Operativa Diaria")
    if not df_d.empty:
        st.dataframe(df_d[['Fecha', 'Z_Total', 'Descuadre_Caja', 'Personal_Dia']].style.format("{:.2f}€"))
else:
    st.info("👋 Sube el CSV del proveedor o añade datos manuales.")
