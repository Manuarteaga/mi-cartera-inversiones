from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Mi Cartera de Inversiones", page_icon="📈", layout="wide"
)

DATA_FILE = "cartera_datos.csv"


@st.cache_data
def cargar_datos():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(
            columns=[
                "Fecha",
                "Tipo_Movimiento",
                "Activo",
                "Tipo_Activo",
                "Subtipo_Aportacion",
                "Broker",
                "Categoría",
                "Región_País",
                "Participaciones",
                "Precio_Unitario",
                "Importe_Manual",
                "Comision",
            ]
        )


df = cargar_datos()

st.title("📈 Mi Cartera de Inversiones Personal")

if not df.empty and "Fecha" in df.columns:
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date

# --- BARRA LATERAL: FORMULARIO Y FILTROS ---
st.sidebar.header("➕ Añadir Operación")

with st.sidebar.form("formulario_operacion", clear_on_submit=True):
    fecha = st.date_input("Fecha de operación", value=date.today())
    tipo_movimiento = st.selectbox(
        "Tipo de movimiento", ["Compra", "Venta", "Dividendo"]
    )
    activo = st.text_input(
        "Nombre del Activo / Fondo", placeholder="Ej. MSCI World / Telefónica"
    )

    tipo_activo = st.selectbox(
        "Tipo de Activo",
        ["Fondos Indexados", "ETFs", "Acciones", "Fondos Monetarios", "Otro"],
    )

    subtipo_aportacion = "N/A"
    participaciones = 0.0
    precio_unitario = 0.0
    importe_manual = 0.0

    if tipo_activo in ["Fondos Indexados", "ETFs"]:
        subtipo_aportacion = st.radio(
            "Modalidad de aportación",
            ["Inversión Inicial", "Aportación Mensual / Periódica"],
        )
        importe_manual = st.number_input(
            "Cantidad a Invertir (€)",
            min_value=0.01,
            format="%.2f",
            value=100.0,
        )
    else:
        subtipo_aportacion = "Acciones / Unidades"
        participaciones = st.number_input(
            "Número de Participaciones / Acciones",
            min_value=0.0001,
            format="%.4f",
            value=1.0,
        )
        precio_unitario = st.number_input(
            "Precio por Participación (€)",
            min_value=0.01,
            format="%.2f",
            value=10.0,
        )

    broker = st.selectbox(
        "Bróker",
        [
            "MyInvestor (0 € - Fondos)",
            "Indexa Capital (Gestión automatizada)",
            "Interactive Brokers",
            "Degiro",
            "Trade Republic",
            "XTB",
            "Otro / Personalizado",
        ],
    )

    comision_calculada = 0.0
    importe_base = (
        importe_manual
        if tipo_activo in ["Fondos Indexados", "ETFs"]
        else (participaciones * precio_unitario)
    )

    if "MyInvestor" in broker or "Indexa Capital" in broker:
        comision_calculada = 0.0
    elif "Trade Republic" in broker:
        comision_calculada = 1.00
    elif "XTB" in broker:
        comision_calculada = 0.0
    elif "Degiro" in broker:
        comision_calculada = 2.00
    elif "Interactive Brokers" in broker:
        comision_calculada = 1.25

    comision = st.number_input(
        "Comisión estimada / aplicada (€) [Calculada automáticamente]",
        min_value=0.0,
        format="%.2f",
        value=float(comision_calculada),
    )

    categoria = st.selectbox(
        "Categoría / Estrategia",
        [
            "Renta Variable Global",
            "Renta Fija",
            "Emergentes",
            "Sectorial",
            "Cripto / Efectivo",
        ],
    )
    region = st.selectbox(
        "Región / País principal",
        ["Global / Multirregión", "EE. UU.", "Europa", "Emergentes", "España"],
    )

    submitted = st.form_submit_button("Guardar Operación")

    if submitted:
        if not activo.strip():
            st.error("Por favor, introduce el nombre del activo.")
        else:
            nueva_fila = pd.DataFrame(
                [
                    {
                        "Fecha": fecha,
                        "Tipo_Movimiento": tipo_movimiento,
                        "Activo": activo,
                        "Tipo_Activo": tipo_activo,
                        "Subtipo_Aportacion": subtipo_aportacion,
                        "Broker": broker,
                        "Categoría": categoria,
                        "Región_País": region,
                        "Participaciones": participaciones,
                        "Precio_Unitario": precio_unitario,
                        "Importe_Manual": importe_manual,
                        "Comision": comision,
                    }
                ]
            )
            df = pd.concat([df, nueva_fila], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.sidebar.success(f"¡Operación en {activo} guardada!")
            st.rerun()

# --- FILTROS DE BÚSQUEDA EN BARRA LATERAL ---
st.sidebar.divider()
st.sidebar.header("🔍 Filtros de Búsqueda")

df_filtrado = df.copy()

if not df.empty and "Tipo_Activo" in df.columns:
    tipos_disponibles = ["Todos"] + list(df["Tipo_Activo"].unique())
    filtro_tipo = st.sidebar.selectbox("Filtrar por Tipo de Activo", tipos_disponibles)
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo_Activo"] == filtro_tipo]

    if "Activo" in df_filtrado.columns:
        activos_disponibles = ["Todos"] + list(df_filtrado["Activo"].unique())
        filtro_activo = st.sidebar.selectbox("Filtrar por Activo", activos_disponibles)
        if filtro_activo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Activo"] == filtro_activo]

    if "Fecha" in df.columns and not df["Fecha"].empty:
        min_f = min(df["Fecha"])
        max_f = max(df["Fecha"])
        rango_fechas = st.sidebar.date_input(
            "Rango de fechas", value=(min_f, max_f), min_value=min_f, max_value=max_f
        )
        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            inicio, fin = rango_fechas
            df_filtrado = df_filtrado[
                (df_filtrado["Fecha"] >= inicio) & (df_filtrado["Fecha"] <= fin)
            ]


# --- CÁLCULO DE IMPORTES TOTALES ---
def calcular_importe(row):
    if row.get("Tipo_Activo") in ["Fondos Indexados", "ETFs"]:
        return row.get("Importe_Manual", 0.0) + row.get("Comision", 0.0)
    else:
        return (row.get("Participaciones", 0.0) * row.get("Precio_Unitario", 0.0)) + row.get("Comision", 0.0)


if not df.empty:
    df["Importe_Total"] = df.apply(calcular_importe, axis=1)
    df_filtrado["Importe_Total"] = df_filtrado.apply(calcular_importe, axis=1)


# Función auxiliar para calcular impuestos por tramos del ahorro en España
def calcular_impuestos_tramos(base_imponible):
    if base_imponible <= 0:
        return 0.0
    impuesto = 0.0
    if base_imponible <= 6000:
        return base_imponible * 0.19
    else:
        impuesto += 6000 * 0.19
        resto = base_imponible - 6000

    if resto <= 44000:
        return impuesto + (resto * 0.21)
    else:
        impuesto += 44000 * 0.21
        resto = resto - 44000

    if resto <= 150000:
        return impuesto + (resto * 0.23)
    else:
        impuesto += 150000 * 0.23
        resto = resto - 150000

    if resto <= 100000:
        return impuesto + (resto * 0.27)
    else:
        impuesto += 100000 * 0.27
        resto = resto - 100000

    impuesto += resto * 0.30
    return impuesto


# --- PANEL PRINCIPAL ---
if df.empty:
    st.info(
        "👋 ¡Bienvenido! Añade tu primera operación desde el menú desplegable de la izquierda para empezar."
    )
else:
    # Métricas financieras desglosadas
    compras_total = df_filtrado[df_filtrado["Tipo_Movimiento"] == "Compra"]["Importe_Total"].sum()
    ventas_total = df_filtrado[df_filtrado["Tipo_Movimiento"] == "Venta"]["Importe_Total"].sum()
    dividendos_total = df_filtrado[df_filtrado["Tipo_Movimiento"].isin(["Dividendo", "Dividendos"])]["Importe_Total"].sum()
    
    total_invertido = compras_total - ventas_total
    total_comisiones = df_filtrado["Comision"].sum()

    # Cálculo fiscal
    impuestos_dividendos = calcular_impuestos_tramos(dividendos_total)
    plusvalia_estimada = max(0.0, total_invertido * 0.12)
    impuestos_retirada = calcular_impuestos_tramos(plusvalia_estimada)

    # Tarjetas superiores de KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Dinero Neto Invertido", value=f"{total_invertido:,.2f} €")
    with col2:
        st.metric(label="Comisiones Totales", value=f"{total_comisiones:,.2f} €")
    with col3:
        st.metric(label="Impuestos Est. Dividendos", value=f"{impuestos_dividendos:,.2f} €")
    with col4:
        st.metric(label="Impuestos Est. Retirada", value=f"{impuestos_retirada:,.2f} €")

    st.divider()

    if df_filtrado.empty:
        st.warning("No hay operaciones que coincidan con los filtros seleccionados.")
    else:
        # --- 1. DIVIDENDOS Y VENTAS EN LA MISMA FILA ---
        col_fila1, col_fila2 = st.columns(2)

        with col_fila1:
            st.subheader("💵 Dividendos y Rendimientos")
            df_divs = df_filtrado[df_filtrado["Tipo_Movimiento"].isin(["Dividendo", "Dividendos"])]
            if df_divs.empty:
                st.info("No hay dividendos registrados.")
            else:
                st.metric(label="Total Dividendos Cobrados", value=f"{dividendos_total:,.2f} €")
                st.dataframe(df_divs[["Fecha", "Activo", "Importe_Total"]], use_container_width=True)

        with col_fila2:
            st.subheader("💸 Gestión de Ventas")
            df_ventas = df_filtrado[df_filtrado["Tipo_Movimiento"] == "Venta"]
            if df_ventas.empty:
                st.info("No hay ventas registradas.")
            else:
                st.metric(label="Total Ventas Realizadas", value=f"{ventas_total:,.2f} €")
                st.dataframe(df_ventas[["Fecha", "Activo", "Importe_Total"]], use_container_width=True)

        st.divider()

        # --- 2. PANEL DE ALERTAS DE REBALANCEO ---
        st.subheader("⚖️ Panel de Alertas y Rebalanceo por Categoría")
        st.write("Establece qué porcentaje ideal te gustaría tener en cada categoría de inversión para comprobar desvíos:")
        
        categorias_existentes = df_filtrado["Categoría"].unique()
        if len(categorias_existentes) > 0:
            cols_reb = st.columns(len(categorias_existentes))
            pesos_objetivo = {}
            suma_pesos = 0
            
            for i, cat in enumerate(categorias_existentes):
                with cols_reb[i]:
                    pesos_objetivo[cat] = st.slider(f"Objetivo %: {cat}", 0, 100, int(100 / len(categorias_existentes)))
                    suma_pesos += pesos_objetivo[cat]
            
            if suma_pesos != 100:
                st.warning(f"⚠️ La suma de los porcentajes objetivo actuales es {suma_pesos}%. Lo ideal es que sume exactamente el 100%.")
            
            df_rebal = df_filtrado.groupby("Categoría")["Importe_Total"].sum().reset_index()
            total_port = df_rebal["Importe_Total"].sum()
            
            if total_port > 0:
                df_rebal["Porcentaje_Real"] = (df_rebal["Importe_Total"] / total_port) * 100
                df_rebal["Objetivo_%"] = df_rebal["Categoría"].map(pesos_objetivo)
                df_rebal["Desvío_%"] = df_rebal["Porcentaje_Real"] - df_rebal["Objetivo_%"]
                
                st.dataframe(
                    df_rebal[["Categoría", "Importe_Total", "Porcentaje_Real", "Objetivo_%", "Desvío_%"]].style.format({
                        "Importe_Total": "{:,.2f} €",
                        "Porcentaje_Real": "{:.2f}%",
                        "Objetivo_%": "{:.2f}%",
                        "Desvío_%": "{:+.2f}%"
                    }),
                    use_container_width=True
                )
                st.info("💡 **Consejo de aportación:** Dirige tus próximas aportaciones al activo o categoría con desvío negativo para reequilibrar la cartera.")

        st.divider()

        # --- 3. GRÁFICO DINÁMICO DE DISTRIBUCIÓN (DONUT) ---
        st.subheader("📊 Distribución de la Cartera")
        
        vista_grafico = st.radio(
            "Ver distribución por:",
            ["Tipo de Activo", "Categoría", "Región / País"],
            horizontal=True,
            key="radio_distribucion"
        )

        columna_map = {
            "Tipo de Activo": "Tipo_Activo",
            "Categoría": "Categoría",
            "Región / País": "Región_País",
        }
        columna_seleccionada = columna_map[vista_grafico]

        df_agrupado = (
            df_filtrado.groupby(columna_seleccionada)["Importe_Total"]
            .sum()
            .reset_index()
        )

        fig_donut = px.pie(
            df_agrupado,
            names=columna_seleccionada,
            values="Importe_Total",
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_donut.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Inversión: %{value:,.2f} €<br>Porcentaje: %{percent}<extra></extra>"
        )
        fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=380)
        st.plotly_chart(fig_donut, use_container_width=True)

        st.divider()

        # --- 4. GRÁFICO DE EVOLUCIÓN TEMPORAL Y PROYECCIÓN FUTURA ---
        st.subheader("📈 Evolución Temporal y Proyección Futura")

        df_temporal = df_filtrado.sort_values("Fecha").copy()
        df_temporal["Flujo"] = df_temporal.apply(
            lambda r: r["Importe_Total"] if r["Tipo_Movimiento"] == "Compra" else (-r["Importe_Total"] if r["Tipo_Movimiento"] == "Venta" else 0),
            axis=1
        )
        df_temporal["Patrimonio_Acumulado"] = df_temporal["Flujo"].cumsum()

        if not df_temporal.empty:
            ultima_fecha = pd.to_datetime(df_temporal["Fecha"].max())
            ultimo_valor = df_temporal["Patrimonio_Acumulado"].iloc[-1]
            
            fechas_futuras = [ultima_fecha + timedelta(days=30*i) for i in range(1, 61)]
            valores_futuros = [ultimo_valor * ((1 + 0.06/12) ** i) for i in range(1, 61)]
            
            df_proyeccion = pd.DataFrame({
                "Fecha": [f.date() for f in fechas_futuras],
                "Patrimonio_Acumulado": valores_futuros,
                "Tipo": "Proyección Futura (Est. 6% anual)"
            })
            
            df_temporal["Tipo"] = "Evolución Real Histórica"
            df_combinado = pd.concat([df_temporal[["Fecha", "Patrimonio_Acumulado", "Tipo"]], df_proyeccion])
        else:
            df_combinado = df_temporal

        modo_evolucion = st.radio(
            "Ver proyección de evolución:",
            ["Evolución Global de la Cartera", "Desglosado por Activos Individuales"],
            horizontal=True,
            key="radio_evolucion"
        )

        if modo_evolucion == "Evolución Global de la Cartera":
            fig_line = px.line(
                df_combinado,
                x="Fecha",
                y="Patrimonio_Acumulado",
                color="Tipo",
                markers=True,
                color_discrete_map={"Evolución Real Histórica": "#1f77b4", "Proyección Futura (Est. 6% anual)": "#2ca02c"}
            )
            fig_line.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=400)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            fig_activos = px.line(
                df_filtrado.sort_values("Fecha"),
                x="Fecha",
                y="Importe_Total",
                color="Activo",
                markers=True,
                title="Evolución de aportaciones por Activo Individual"
            )
            fig_activos.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=400)
            st.plotly_chart(fig_activos, use_container_width=True)

    st.divider()
    st.subheader("📋 Historial de Movimientos")
    st.dataframe(df_filtrado, use_container_width=True)

    # --- SECCIÓN DE BORRADO DE OPERACIONES ---
    st.divider()
    st.subheader("🗑️ Gestión de Borrado")
    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        opciones_borrar = {}
        for idx, row in df.iterrows():
            tipo_mov = row.get("Tipo_Movimiento", "Operación")
            activo_nom = row.get("Activo", "Desconocido")
            broker_nom = row.get("Broker", "N/A")
            fecha_op = row.get("Fecha", "")
            label = f"Fila {idx}: [{fecha_op}] {tipo_mov} de {activo_nom} ({broker_nom})"
            opciones_borrar[label] = idx

        if opciones_borrar:
            operacion_a_borrar = st.selectbox(
                "Selecciona la operación a eliminar",
                list(opciones_borrar.keys()),
            )
        else:
            operacion_a_borrar = None

    with col_b2:
        st.write("")
        st.write("")
        if opciones_borrar and st.button(
            "🗑️ Eliminar Operación Seleccionada", type="primary"
        ):
            idx_a_eliminar = opciones_borrar[operacion_a_borrar]
            df_nuevo = df.drop(idx_a_eliminar).reset_index(drop=True)
            df_nuevo.to_csv(DATA_FILE, index=False)
            st.success("¡Operación eliminada correctamente!")
            st.rerun()
