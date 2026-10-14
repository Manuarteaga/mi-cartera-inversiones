from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Configuración de la página en modo ancho
st.set_page_config(
    page_title="Mi Cartera de Inversiones", page_icon="📈", layout="wide"
)

# --- CONFIGURACIÓN DE CONEXIÓN CON GOOGLE SHEETS ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def conectar_google_sheets():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("MiCarteraInversiones").sheet1
    return sheet

@st.cache_data(ttl=1)
def cargar_datos():
    try:
        sheet = conectar_google_sheets()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
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
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

def guardar_dataframe(df):
    try:
        sheet = conectar_google_sheets()
        sheet.clear()
        if "Fecha" in df.columns:
            df["Fecha"] = df["Fecha"].astype(str)
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")

df = cargar_datos()

st.title("📈 Mi Cartera de Inversiones Personal (Sincronizada)")

if not df.empty and "Fecha" in df.columns:
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date

# --- BARRA LATERAL: FORMULARIO Y FILTROS ---
st.sidebar.header("➕ Añadir Operación")

# Selector de bróker FUERA del formulario para que reaccione al instante
broker = st.sidebar.selectbox(
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
    key="select_broker"
)

# Cálculo automático de comisión en tiempo real según el bróker seleccionado fuera
comision_default = 0.0
if "Trade Republic" in broker:
    comision_default = 1.00
elif "Degiro" in broker:
    comision_default = 2.00
elif "Interactive Brokers" in broker:
    comision_default = 1.25
else:
    comision_default = 0.00

with st.sidebar.form("formulario_operacion", clear_on_submit=False):
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

    comision = st.number_input(
        "Comisión estimada / aplicada (€)",
        min_value=0.0,
        format="%.2f",
        value=float(comision_default),
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
                        "Fecha": str(fecha),
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
            df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
            guardar_dataframe(df_actualizado)
            st.sidebar.success(f"¡Operación en {activo} guardada en Google Sheets!")
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
        return float(row.get("Importe_Manual", 0.0)) + float(row.get("Comision", 0.0))
    else:
        return (float(row.get("Participaciones", 0.0)) * float(row.get("Precio_Unitario", 0.0))) + float(row.get("Comision", 0.0))


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
        "👋 ¡Bienvenido! Conecta tu Google Sheet para empezar a registrar operaciones."
    )
else:
    compras_total = df_filtrado[df_filtrado["Tipo_Movimiento"] == "Compra"]["Importe_Total"].sum()
    ventas_total = df_filtrado[df_filtrado["Tipo_Movimiento"] == "Venta"]["Importe_Total"].sum()
    dividendos_total = df_filtrado[df_filtrado["Tipo_Movimiento"].isin(["Dividendo", "Dividendos"])]["Importe_Total"].sum()
    
    total_invertido = compras_total - ventas_total
    total_comisiones = df_filtrado["Comision"].astype(float).sum()

    impuestos_dividendos = calcular_impuestos_tramos(dividendos_total)
    plusvalia_estimada = max(0.0, total_invertido * 0.12)
    impuestos_retirada = calcular_impuestos_tramos(plusvalia_estimada)

    # --- DISPOSICIÓN SUPERIOR: MÉTRICAS Y GRÁFICO DONUT ---
    col_sup_izq, col_sup_der = st.columns([1.1, 0.9])

    with col_sup_izq:
        st.subheader("💵 Resumen Financiero y Fiscal")
        m1, m2 = st.columns(2)
        with m1:
            st.metric(label="Dinero Neto Invertido", value=f"{total_invertido:,.2f} €")
            st.metric(label="Impuestos Est. Dividendos", value=f"{impuestos_dividendos:,.2f} €")
        with m2:
            st.metric(label="Comisiones Totales", value=f"{total_comisiones:,.2f} €")
            st.metric(label="Impuestos Est. Retirada", value=f"{impuestos_retirada:,.2f} €")

    with col_sup_der:
        if not df_filtrado.empty:
            vista_grafico = st.selectbox(
                "Ver distribución por:",
                ["Activo", "Categoría", "Región / País"],
                key="select_distribucion"
            )
            columna_map = {
                "Activo": "Activo",
                "Categoría": "Categoría",
                "Región / País": "Región_País",
            }
            columna_seleccionada = columna_map[vista_grafico]
            df_agrupado = df_filtrado.groupby(columna_seleccionada)["Importe_Total"].sum().reset_index()

            fig_donut = px.pie(
                df_agrupado,
                names=columna_seleccionada,
                values="Importe_Total",
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_donut.update_traces(
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>Inversión: %{value:,.2f} €<br>Porcentaje: %{percent}<extra></extra>"
            )
            fig_donut.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), 
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    if df_filtrado.empty:
        st.warning("No hay operaciones que coincidan con los filtros seleccionados.")
    else:
        # --- SEGUNDA FILA: EVOLUCIÓN TEMPORAL Y DATOS ---
        col_inf_izq, col_inf_der = st.columns([1.1, 0.9])

        with col_inf_der:
            st.subheader("📈 Evolución y Proyección Temporal")
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

            modo_evolucion = st.selectbox(
                "Ver proyección de evolución:",
                ["Evolución Global de la Cartera", "Desglosado por Activos Individuales"],
                key="select_evolucion"
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
                fig_line.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                fig_activos = px.line(
                    df_filtrado.sort_values("Fecha"),
                    x="Fecha",
                    y="Importe_Total",
                    color="Activo",
                    markers=True,
                )
                fig_activos.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
                st.plotly_chart(fig_activos, use_container_width=True)

        with col_inf_izq:
            st.subheader("📋 Datos y Gestión Operativa")

            sub_c1, sub_c2 = st.columns(2)
            with sub_c1:
                st.markdown("**💵 Dividendos**")
                df_divs = df_filtrado[df_filtrado["Tipo_Movimiento"].isin(["Dividendo", "Dividendos"])]
                if df_divs.empty:
                    st.caption("Sin dividendos.")
                else:
                    st.dataframe(df_divs[["Fecha", "Activo", "Importe_Total"]], use_container_width=True, height=130)

            with sub_c2:
                st.markdown("**💸 Ventas**")
                df_ventas = df_filtrado[df_filtrado["Tipo_Movimiento"] == "Venta"]
                if df_ventas.empty:
                    st.caption("Sin ventas.")
                else:
                    st.dataframe(df_ventas[["Fecha", "Activo", "Importe_Total"]], use_container_width=True, height=130)

            st.divider()

            st.subheader("⚖️ Alertas de Rebalanceo")
            categorias_existentes = df_filtrado["Categoría"].unique()
            if len(categorias_existentes) > 0:
                pesos_objetivo = {}
                suma_pesos = 0
                cols_reb = st.columns(len(categorias_existentes))
                for i, cat in enumerate(categorias_existentes):
                    with cols_reb[i]:
                        pesos_objetivo[cat] = st.slider(f"Obj%: {cat}", 0, 100, int(100 / len(categorias_existentes)))
                        suma_pesos += pesos_objetivo[cat]
                
                if suma_pesos != 100:
                    st.warning(f"⚠️ Suma objetivo: {suma_pesos}%")
                
                df_rebal = df_filtrado.groupby("Categoría")["Importe_Total"].sum().reset_index()
                total_port = df_rebal["Importe_Total"].sum()
                if total_port > 0:
                    df_rebal["Porcentaje_Real"] = (df_rebal["Importe_Total"] / total_port) * 100
                    df_rebal["Objetivo_%"] = df_rebal["Categoría"].map(pesos_objetivo)
                    df_rebal["Desvío_%"] = df_rebal["Porcentaje_Real"] - df_rebal["Objetivo_%"]
                    st.dataframe(
                        df_rebal[["Categoría", "Porcentaje_Real", "Objetivo_%", "Desvío_%"]].style.format({
                            "Porcentaje_Real": "{:.2f}%",
                            "Objetivo_%": "{:.2f}%",
                            "Desvío_%": "{:+.2f}%"
                        }),
                        use_container_width=True,
                        height=140
                    )

            st.divider()

            st.subheader("📑 Historial de Movimientos")
            st.dataframe(df_filtrado, use_container_width=True, height=180)

            st.subheader("🗑️ Borrado de Operaciones")
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
                if st.button("🗑️ Eliminar Operación Seleccionada", type="primary"):
                    idx_a_eliminar = opciones_borrar[operacion_a_borrar]
                    df_nuevo = df.drop(idx_a_eliminar).reset_index(drop=True)
                    guardar_dataframe(df_nuevo)
                    st.success("¡Operación eliminada de Google Sheets!")
                    st.rerun()
