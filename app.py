import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Control Wateqe", layout="wide")

# --- GESTIÓN DE ESTADO (MEMORIA) ---
# Inicializamos las tablas si no existen
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

# Lista de categorías por defecto (se pueden añadir más)
if 'categorias_stock' not in st.session_state:
    st.session_state.categorias_stock = ["Bebida Alcohol", "Refrescos", "Hielo", "Fruta/Varios"]

if 'categorias_fijos' not in st.session_state:
    st.session_state.categorias_fijos = ["Alquiler", "Luz", "Agua", "Gestoría", "Internet"]

# Función auxiliar para obtener AAAA-MM
def get_month_str(date_obj):
    return date_obj.strftime("%Y-%m")

# --- SIDEBAR: INTRODUCCIÓN DE DATOS ---
st.sidebar.title("🎮 Panel de Control")

# SECCIÓN 1: CONFIGURACIÓN DE CATEGORÍAS
with st.sidebar.expander("➕ Añadir Nueva Categoría", expanded=False):
    tipo_cat = st.radio("¿Qué tipo de gasto quieres crear?", ["Proveedor/Stock", "Gasto Fijo"])
    nueva_cat = st.text_input("Nombre de la categoría (ej: DJ, Limpieza, Seguridad)")
    if st.button("Crear Categoría"):
        if nueva_cat:
            if tipo_cat == "Proveedor/Stock":
                if nueva_cat not in st.session_state.categorias_stock:
                    st.session_state.categorias_stock.append(nueva_cat)
                    st.success(f"Añadido: {nueva_cat}")
            else:
                if nueva_cat not in st.session_state.categorias_fijos:
                    st.session_state.categorias_fijos.append(nueva_cat)
                    st.success(f"Añadido: {nueva_cat}")

# SECCIÓN 2: GASTOS FIJOS (MENSUALES)
with st.sidebar.expander("1. Gastos Fijos (Alquiler/Luz)", expanded=False):
    mes_gasto = st.date_input("Mes de la factura", key="fijo_date")
    cat_fijo = st.selectbox("Concepto", st.session_state.categorias_fijos)
    imp_fijo = st.number_input("Importe (€)", min_value=0.0, step=50.0, key="fijo_imp")
    
    if st.button("Guardar Gasto Fijo"):
        mes_str = get_month_str(mes_gasto)
        # Check duplicados
        duplicado = st.session_state.fijos[
            (st.session_state.fijos['Mes_Ref'] == mes_str) & 
            (st.session_state.fijos['Concepto'] == cat_fijo)
        ]
        if not duplicado.empty:
            st.error(f"⛔ ¡Error! Ya has introducido {cat_fijo} para {mes_str}.")
        else:
            nuevo = {'Mes_Ref': mes_str, 'Concepto': cat_fijo, 'Importe': imp_fijo}
            st.session_state.fijos = pd.concat([st.session_state.fijos, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("Guardado.")

# SECCIÓN 3: COMPRA DE STOCK (SEMANAL/PUNTUAL)
with st.sidebar.expander("2. Compras Stock (Bebida/Hielo)", expanded=False):
    st.caption("Introduce cada compra realizada.")
    fecha_stock = st.date_input("Fecha de Compra", key="stock_date")
    cat_stock = st.selectbox("Tipo de Producto", st.session_state.categorias_stock)
    imp_stock = st.number_input("Importe Compra (€)", min_value=0.0, step=10.0, key="stock_imp")
    
    if st.button("Registrar Compra"):
        mes_str = get_month_str(fecha_stock)
        # Aquí permitimos duplicados de categoría (puedes comprar hielo 4 veces al mes), 
        # pero no exactamente el mismo importe el mismo día (por si acaso le das dos veces al botón)
        duplicado = st.session_state.stock[
            (st.session_state.stock['Fecha'] == pd.to_datetime(fecha_stock)) & 
            (st.session_state.stock['Categoria'] == cat_stock) &
            (st.session_state.stock['Importe'] == imp_stock)
        ]
        
        if not duplicado.empty:
            st.warning("⚠️ Parece que ya has metido esta compra hoy. Si es correcta, ignora esto.")
            
        nuevo = {'Fecha': pd.to_datetime(fecha_stock), 'Mes_Ref': mes_str, 'Categoria': cat_stock, 'Importe': imp_stock}
        st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([nuevo])], ignore_index=True)
        st.success("Compra Registrada.")

# SECCIÓN 4: APERTURA DIARIA
with st.sidebar.expander("3. Cierre Diario (Apertura)", expanded=True):
    fecha_dia = st.date_input("Fecha de Apertura", key="dia_date")
    
    st.markdown("**Ingresos**")
    z_dia = st.number_input("Z Total", min_value=0.0, step=50.0)
    tarjeta = st.number_input("Tarjeta", min_value=0.0, step=50.0)
    efectivo_real = st.number_input("Efectivo en Cajón", min_value=0.0, step=50.0)
    
    st.markdown("**Personal del día**")
    personal = st.number_input("Nóminas/Personal Hoy", min_value=0.0, step=10.0)
    
    if st.button("Cerrar Día"):
        # Check duplicados de fecha
        if not st.session_state.diario.empty and pd.to_datetime(fecha_dia) in st.session_state.diario['Fecha'].values:
             st.error(f"⛔ ¡El día {fecha_dia} ya está registrado! Bórralo si quieres corregirlo.")
        else:
            mes_str = get_month_str(fecha_dia)
            teorico = z_dia - tarjeta
            descuadre = efectivo_real - teorico
            
            nuevo = {
                'Fecha': pd.to_datetime(fecha_dia),
                'Mes_Ref': mes_str,
                'Z_Total': z_dia,
                'Tarjeta': tarjeta,
                'Efectivo_Teorico': teorico,
                'Efectivo_Real': efectivo_real,
                'Descuadre_Caja': descuadre,
                'Personal_Dia': personal
            }
            st.session_state.diario = pd.concat([st.session_state.diario, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("Día Registrado.")

# --- DASHBOARD PRINCIPAL ---
st.title("🍹 Control de Cuentas Pub Wateqe")

# Selector de Mes
todos_meses = set(st.session_state.diario['Mes_Ref'].unique()) | set(st.session_state.stock['Mes_Ref'].unique()) | set(st.session_state.fijos['Mes_Ref'].unique())
lista_meses = sorted(list(todos_meses))

if lista_meses:
    mes_sel = st.selectbox("Seleccionar Mes a Analizar", lista_meses, index=len(lista_meses)-1)
    
    # FILTRADO DE DATOS
    df_d = st.session_state.diario[st.session_state.diario['Mes_Ref'] == mes_sel].copy()
    df_s = st.session_state.stock[st.session_state.stock['Mes_Ref'] == mes_sel].copy()
    df_f = st.session_state.fijos[st.session_state.fijos['Mes_Ref'] == mes_sel].copy()
    
    # --- CÁLCULOS GLOBALES DEL MES ---
    ventas_totales = df_d['Z_Total'].sum()
    personal_total = df_d['Personal_Dia'].sum()
    stock_total = df_s['Importe'].sum()
    fijos_total = df_f['Importe'].sum()
    
    descuadre_acumulado = df_d['Descuadre_Caja'].sum()
    dias_abiertos = len(df_d)
    
    # Beneficio Neto = Ventas - (Todo lo gastado en el mes)
    gastos_totales = personal_total + stock_total + fijos_total
    beneficio = ventas_totales - gastos_totales
    
    # --- VISUALIZACIÓN ---
    
    # 1. TARJETAS DE RESUMEN
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ventas Totales", f"{ventas_totales:.2f}€")
    col2.metric("Beneficio Neto", f"{beneficio:.2f}€", delta_color="normal")
    col3.metric("Descuadre Caja", f"{descuadre_acumulado:.2f}€")
    
    # Ratio Stock (El que querías)
    ratio_stock = (stock_total / ventas_totales * 100) if ventas_totales > 0 else 0
    col4.metric("% Gasto Stock/Ventas", f"{ratio_stock:.1f}%")
    if ratio_stock > 35:
        col4.error("⚠️ Stock Alto")
    else:
        col4.success("✅ Stock Correcto")

    st.markdown("---")

    # 2. COLUMNAS DE DETALLE
    c_izq, c_der = st.columns([1, 1])
    
    with c_izq:
        st.subheader("📦 Detalle de Compras (Stock)")
        if not df_s.empty:
            # Agrupar por categoría para ver resumen
            resumen_stock = df_s.groupby('Categoria')['Importe'].sum().reset_index()
            fig_pie = px.pie(resumen_stock, values='Importe', names='Categoria', title="Distribución de Compras")
            st.plotly_chart(fig_pie, use_container_width=True)
            
            with st.expander("Ver lista de todas las compras"):
                st.dataframe(df_s, hide_index=True)
        else:
            st.info("No hay compras registradas este mes.")

    with c_der:
        st.subheader("📉 Estructura de Gastos")
        # Gráfico de cascada o barras para ver dónde se va el dinero
        datos_gastos = pd.DataFrame({
            'Concepto': ['Personal', 'Stock/Proveedores', 'Fijos (Alquiler/Luz)'],
            'Importe': [personal_total, stock_total, fijos_total]
        })
        fig_bar = px.bar(datos_gastos, x='Concepto', y='Importe', text='Importe', color='Concepto', title="¿En qué se gasta el dinero?")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    
    # 3. DETALLE DIARIO (OPERATIVA)
    st.subheader(f"📅 Diario de Caja ({dias_abiertos} días abiertos)")
    
    if dias_abiertos > 0:
        # Calcular beneficio OPERATIVO diario (Venta - Personal) para ver si vale la pena abrir
        # OJO: Aquí no restamos alquiler ni stock, solo para ver si el día es rentable por sí mismo
        df_d['Margen_Operativo'] = df_d['Z_Total'] - df_d['Personal_Dia']
        
        st.dataframe(df_d[['Fecha', 'Z_Total', 'Descuadre_Caja', 'Personal_Dia', 'Margen_Operativo']].style.format("{:.2f}€"))
        
        if total_descuadre := df_d['Descuadre_Caja'].min() < -5:
             st.error("⚠️ Hay días con descuadres importantes (mirar tabla arriba)")
    else:
        st.warning("No hay días de apertura registrados en este mes.")

else:
    st.info("👋 Bienvenido a Pub Wateqe Control. Empieza añadiendo datos en el menú lateral.")
