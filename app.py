import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from db import (
    get_pymes, crear_pyme, get_categorias,
    registrar_gasto, registrar_ingreso,
    get_gastos, get_ingresos, eliminar_gasto, eliminar_ingreso,
    get_resumen, get_evolucion_mensual
)

st.set_page_config(page_title="Claridad", page_icon="💚", layout="wide")

with st.sidebar:
    st.markdown("## 💚 Claridad")
    st.caption("Tu negocio, en claro")
    st.divider()

    pymes = get_pymes()

    if not pymes:
        st.warning("No hay empresas registradas.")
        nombre = st.text_input("Nombre de la empresa")
        rubro  = st.text_input("Rubro")
        if st.button("Crear empresa"):
            if nombre:
                crear_pyme(nombre, rubro)
                st.success("Empresa creada.")
        st.stop()

    nombres_pymes = [p["nombre"] for p in pymes]
    idx = st.selectbox("Empresa", range(len(pymes)), format_func=lambda i: nombres_pymes[i])
    pyme    = pymes[idx]
    pyme_id = pyme["id"]

    st.divider()
    hoy            = date.today()
    primer_dia_mes = hoy.replace(day=1)
    periodo = st.radio("Ver", ["Este mes", "Esta semana", "Últimos 30 días", "Personalizado"])

    if periodo == "Este mes":
        desde, hasta = primer_dia_mes, hoy
    elif periodo == "Esta semana":
        desde, hasta = hoy - timedelta(days=hoy.weekday()), hoy
    elif periodo == "Últimos 30 días":
        desde, hasta = hoy - timedelta(days=30), hoy
    else:
        desde = st.date_input("Desde", primer_dia_mes)
        hasta = st.date_input("Hasta", hoy)

    desde_str = desde.isoformat()
    hasta_str = hasta.isoformat()

    st.divider()
    with st.expander("+ Nueva empresa"):
        n = st.text_input("Nombre")
        r = st.text_input("Rubro")
        if st.button("Crear"):
            if n:
                crear_pyme(n, r)
                st.success("Creada.")

resumen   = get_resumen(pyme_id, desde_str, hasta_str)
gastos    = get_gastos(pyme_id, desde_str, hasta_str)
ingresos  = get_ingresos(pyme_id, desde_str, hasta_str)
evolucion = get_evolucion_mensual(pyme_id, meses=6)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Registrar", "📋 Historial", "📈 Evolución"])

# ── DASHBOARD ──────────────────────────────────────────
with tab1:
    st.markdown(f"### {pyme['nombre']} — {periodo.lower()}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Ingresos", f"USD {resumen['total_ingresos']:,.0f}")
    with col2:
        st.metric("💸 Gastos", f"USD {resumen['total_gastos']:,.0f}")
    with col3:
        ganancia = resumen["ganancia"]
        st.metric("✅ Ganancia neta", f"USD {ganancia:,.0f}", delta=f"{resumen['margen_pct']}% margen")
    with col4:
        ico = "🟢" if resumen["margen_pct"] >= 30 else ("🟡" if resumen["margen_pct"] >= 10 else "🔴")
        st.metric(f"{ico} Margen", f"{resumen['margen_pct']}%")

    st.divider()
    col_msg, col_pie = st.columns([2, 1])
    with col_msg:
        st.markdown("#### 🤖 Tu resumen")
        if resumen["total_ingresos"] == 0:
            st.info("Sin datos aún. Andá a la pestaña Registrar y cargá tus primeros movimientos.")
        else:
            if ganancia > 0:
                st.success(f"**Estás ganando dinero.** Por cada USD 100 que entraron, te quedaron USD {resumen['margen_pct']:.0f} limpios.")
            elif ganancia == 0:
                st.warning("**Estás en cero.** Lo que entra lo gastás entero.")
            else:
                st.error(f"**Estás perdiendo plata.** Gastaste USD {abs(ganancia):,.0f} más de lo que entraste.")
            if resumen["gastos_por_cat"]:
                top = resumen["gastos_por_cat"][0]
                pct = top["total"] / resumen["total_gastos"] * 100
                st.info(f"**Gasto más grande:** {top['nombre']} — USD {top['total']:,.0f} ({pct:.0f}%)")
    with col_pie:
        if resumen["gastos_por_cat"]:
            df_pie = pd.DataFrame(resumen["gastos_por_cat"])
            fig = px.pie(df_pie, values="total", names="nombre",
                         title="Gastos por categoría",
                         color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
            fig.update_layout(height=260, margin=dict(t=40,b=0,l=0,r=0))
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(fig)

# ── REGISTRAR ──────────────────────────────────────────
with tab2:
    col_g, col_i = st.columns(2)

    with col_g:
        st.markdown("#### 💸 Nuevo gasto")
        cats_g  = get_categorias("gasto")
        nombres_g = [c["nombre"] for c in cats_g]
        desc_g  = st.text_input("Descripción", key="desc_g", placeholder="Ej: Compra materiales")
        monto_g = st.number_input("Monto USD", min_value=0.0, step=1.0, key="monto_g")
        fecha_g = st.date_input("Fecha", value=hoy, key="fecha_g")
        cat_g   = st.selectbox("Categoría", range(len(nombres_g)), format_func=lambda i: nombres_g[i], key="cat_g")
        fijo_g  = st.checkbox("¿Gasto fijo?", key="fijo_g")
        if st.button("✅ Guardar gasto", use_container_width=True):
            if desc_g and monto_g > 0:
                registrar_gasto(pyme_id, cats_g[cat_g]["id"], desc_g, monto_g, fecha_g.isoformat(), fijo_g)
                st.success(f"✅ Guardado: {desc_g} — USD {monto_g:,.0f}")
            else:
                st.error("Completá descripción y monto.")

    with col_i:
        st.markdown("#### 💰 Nuevo ingreso")
        cats_i    = get_categorias("ingreso")
        nombres_i = [c["nombre"] for c in cats_i]
        desc_i    = st.text_input("Descripción", key="desc_i", placeholder="Ej: Venta del día")
        monto_i   = st.number_input("Monto USD", min_value=0.0, step=1.0, key="monto_i")
        fecha_i   = st.date_input("Fecha", value=hoy, key="fecha_i")
        cliente_i = st.text_input("Cliente (opcional)", key="cliente_i")
        cat_i     = st.selectbox("Categoría", range(len(nombres_i)), format_func=lambda i: nombres_i[i], key="cat_i")
        if st.button("✅ Guardar ingreso", use_container_width=True):
            if desc_i and monto_i > 0:
                registrar_ingreso(pyme_id, cats_i[cat_i]["id"], desc_i, monto_i, fecha_i.isoformat(), cliente_i)
                st.success(f"✅ Guardado: {desc_i} — USD {monto_i:,.0f}")
            else:
                st.error("Completá descripción y monto.")

# ── HISTORIAL ──────────────────────────────────────────
with tab3:
    st.markdown("#### 📋 Historial")
    sg, si = st.tabs(["Gastos", "Ingresos"])
    with sg:
        if gastos:
            df_gh = pd.DataFrame(gastos)
            df_gh["tipo"] = df_gh["es_fijo"].apply(lambda x: "Fijo" if x else "Variable")
            st.dataframe(df_gh[["fecha","descripcion","categoria_nombre","monto","tipo","id"]].rename(
                columns={"fecha":"Fecha","descripcion":"Descripción","categoria_nombre":"Categoría",
                         "monto":"USD","tipo":"Tipo","id":"ID"}), hide_index=True)
        else:
            st.info("Sin gastos en este período.")
    with si:
        if ingresos:
            df_ih = pd.DataFrame(ingresos)
            st.dataframe(df_ih[["fecha","descripcion","cliente","monto","id"]].rename(
                columns={"fecha":"Fecha","descripcion":"Descripción","cliente":"Cliente",
                         "monto":"USD","id":"ID"}), hide_index=True)
        else:
            st.info("Sin ingresos en este período.")

# ── EVOLUCIÓN ──────────────────────────────────────────
with tab4:
    st.markdown("#### 📈 Últimos 6 meses")
    if evolucion:
        df_ev = pd.DataFrame(evolucion)
        fig = go.Figure()
        fig.add_bar(name="Ingresos", x=df_ev["mes"], y=df_ev["ingresos"], marker_color="#1D9E75", opacity=0.85)
        fig.add_bar(name="Gastos",   x=df_ev["mes"], y=df_ev["gastos"],   marker_color="#E24B4A", opacity=0.85)
        fig.add_scatter(name="Ganancia", x=df_ev["mes"], y=df_ev["ganancia"],
                        mode="lines+markers", line=dict(color="#7F77DD", width=2), marker=dict(size=7))
        fig.update_layout(barmode="group", height=360,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02),
                          margin=dict(t=20,b=20),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(title="USD"))
        st.plotly_chart(fig)
    else:
        st.info("Cargá datos para ver la evolución.")
