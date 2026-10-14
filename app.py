from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Mi Cartera de Inversiones", page_icon="📈", layout="wide"
)

# Archivo donde se guardan los datos
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
                "Categoría",
                "Región_País",
                "Participaciones",
                "Precio_Unitario",
                "Comision",
            ]
        )


df = cargar_datos()

st.title("📈 Mi Cartera de Inversiones Personal")

# Asegurarse de que la fecha sea tipo fecha para los filtros
if not df.empty:
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
        "Comisiones / Gastos (€)", min_value=0.0, format="%.2f", value=0.0
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
                        "Categoría": categoria,
                        "Región_País": region,
                        "Participaciones": participaciones,
                        "Precio_Unitario": precio_unitario,
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

if not df.empty:
    # Filtro por Tipo de Activo
    tipos_disponibles = ["Todos"] + list(df["Tipo_Activo"].unique())
    filtro_tipo = st.sidebar.selectbox("Filtrar por Tipo de Activo", tipos_disponibles)
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo_Activo"] == filtro_tipo]

    # Filtro por Activo específico
    activos_disponibles = ["Todos"] + list(df_filtrado["Activo"].unique())
    filtro_activo = st.sidebar.selectbox("Filtrar por Activo", activos_disponibles)
    if filtro_activo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Activo"] == filtro_activo]

    # Filtro por Rango de Fechas
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


# --- PANEL PRINCIPAL ---
if df.empty:
    st.info(
        "👋 ¡Bienvenido! Añade tu primera operación desde el menú desplegable de la izquierda."
    )
else:
    # Calcular Importes
    df["Importe_Total"] = (df["Participaciones"] * df["Precio_Unitario"]) + df[
        "Comision"
    ]
    df_filtrado["Importe_Total"] = (
        df_filtrado["Participaciones"] * df_filtrado["Precio_Unitario"]
    ) + df_filtrado["Comision"]

    total_invertido = df_filtrado[df_filtrado["Tipo_Movimiento"] == "Compra"][
        "Importe_Total"
    ].sum() - df_filtrado[df_filtrado["Tipo_Movimiento"] == "Venta"][
        "Importe_Total"
    ].sum()
    total_comisiones = df_filtrado["Comision"].sum()

    # Métricas Superiores
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Dinero Neto Invertido", value=f"{total_invertido:,.2f} €"
        )
    with col2:
        st.metric(label="Comisiones Totales", value=f"{total_comisiones:,.2f} €")
    with col3:
        st.metric(label="Operaciones (Filtradas / Total)", value=f"{len(df_filtrado)} / {len(df)}")
    with col4:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Cartera CSV",
            data=csv_data,
            file_name="mi_cartera_inversiones.csv",
            mime="text/csv",
        )

    st.divider()

    # Gráficos con base en los datos filtrados
    if df_filtrado.empty:
        st.warning("No hay operaciones que coincidan con los filtros seleccionados.")
    else:
        col_g1, col_g2, col_g3 = st.columns(3)

        with col_g1:
            st.subheader("📊 Por Tipo de Activo")
            df_tipo = (
                df_filtrado.groupby("Tipo_Activo")["Importe_Total"].sum().reset_index()
            )
            fig_tipo = px.pie(
                df_tipo,
                names="Tipo_Activo",
                values="Importe_Total",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            st.plotly_chart(fig_tipo, use_container_width=True)

        with col_g2:
            st.subheader("📈 Por Categoría")
            df_cat = (
                df_filtrado.groupby("Categoría")["Importe_Total"].sum().reset_index()
            )
            fig_pie = px.pie(
                df_cat,
                names="Categoría",
                values="Importe_Total",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g3:
            st.subheader("🌍 Por Región")
            df_reg = (
                df_filtrado.groupby("Región_País")["Importe_Total"].sum().reset_index()
            )
            fig_reg = px.pie(
                df_reg,
                names="Región_País",
                values="Importe_Total",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig_reg, use_container_width=True)

    # Tabla detallada filtrada
    st.subheader("📋 Historial de Movimientos")
    st.dataframe(df_filtrado, use_container_width=True)

    # --- SECCIÓN DE BORRADO DE OPERACIONES ---
    st.divider()
    st.subheader("🗑️ Gestión de Borrado")
    st.write(
        "Si te has equivocado al introducir alguna operación, puedes seleccionarla por su número de fila y eliminarla:"
    )

    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        # Creamos una lista con el índice y una descripción de la operación para identificarla fácil
        opciones_borrar = {
            f"Fila {idx}: [{row['Fecha']}] {row['Tipo_Movimiento']} de {row['Participaciones']} de {row['Activo']}": idx
            for idx, row in df.iterrows()
        }
        
        if opciones_borrar:
            operacion_a_borrar = st.selectbox(
                "Selecciona la operación a eliminar", list(opciones_borrar.keys())
            )
        else:
            operacion_a_borrar = None

    with col_b2:
        st.write("")  # Espaciador visual
        st.write("")
        if opciones_borrar and st.button("🗑️ Eliminar Operación Seleccionada", type="primary"):
            idx_a_eliminar = opciones_borrar[operacion_a_borrar]
            df_nuevo = df.drop(idx_a_eliminar).reset_index(drop=True)
            # Guardamos el archivo sin la fila eliminada
            df_nuevo.to_csv(DATA_FILE, index=False)
            st.success("¡Operación eliminada correctamente!")
            st.rerun()
