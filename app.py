import io
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
                "Tipo",
                "Activo",
                "Categoría",
                "Región_País",
                "Participaciones",
                "Precio_Unitario",
                "Comision",
            ]
        )


df = cargar_datos()

st.title("📈 Mi Cartera de Inversiones Personal")

# --- FORMULARIO LATERAL ---
st.sidebar.header("➕ Añadir Operación")

with st.sidebar.form("formulario_operacion", clear_on_submit=True):
    fecha = st.date_input("Fecha de operación", value=date.today())
    tipo = st.selectbox("Tipo de movimiento", ["Compra", "Venta", "Dividendo"])
    activo = st.text_input(
        "Nombre del Activo / Fondo", placeholder="Ej. Vanguard Global Stock"
    )
    categoria = st.selectbox(
        "Categoría",
        [
            "Renta Variable Global",
            "Renta Fija",
            "Emergentes",
            "Sectorial",
            "Cripto / Otro",
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
                        "Tipo": tipo,
                        "Activo": activo,
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

# --- PANEL PRINCIPAL ---
if df.empty:
    st.info(
        "👋 ¡Bienvenido! Añade tu primera operación desde el menú desplegable de la izquierda."
    )
else:
    df["Importe_Total"] = (df["Participaciones"] * df["Precio_Unitario"]) + df[
        "Comision"
    ]

    total_invertido = df[df["Tipo"] == "Compra"][
        "Importe_Total"
    ].sum() - df[df["Tipo"] == "Venta"]["Importe_Total"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Dinero Neto Invertido", value=f"{total_invertido:,.2f} €"
        )
    with col2:
        st.metric(label="Total Operaciones", value=len(df))
    with col3:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Cartera en CSV",
            data=csv_data,
            file_name="mi_cartera_inversiones.csv",
            mime="text/csv",
        )

    st.divider()

    # Gráficos
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 Distribución por Categoría")
        df_cat = df.groupby("Categoría")["Importe_Total"].sum().reset_index()
        fig_pie = px.pie(
            df_cat,
            names="Categoría",
            values="Importe_Total",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.subheader("🌍 Distribución por Región / País")
        df_reg = df.groupby("Región_País")["Importe_Total"].sum().reset_index()
        fig_reg = px.pie(
            df_reg,
            names="Región_País",
            values="Importe_Total",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    st.subheader("📋 Historial de Movimientos")
    st.dataframe(df, use_container_width=True)
