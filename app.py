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

# ─────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────
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
    idx     = st.selectbox("Empresa", range(len(pymes)), format_func=lambda i: nombres_pymes[i])
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
    st.caption("⚙️ Configuración")
    horas_semana   = st.number_input("Horas trabajadas por semana", min_value=1, max_value=100, value=50)
    caja_disponible = st.number_input("Caja disponible hoy (USD)", min_value=0.0, step=100.0, value=0.0)

    st.divider()
    with st.expander("+ Nueva empresa"):
        n = st.text_input("Nombre")
        r = st.text_input("Rubro")
        if st.button("Crear"):
            if n:
                crear_pyme(n, r)
                st.success("Creada.")

# ─────────────────────────────────────
# DATOS
# ─────────────────────────────────────
resumen   = get_resumen(pyme_id, desde_str, hasta_str)
gastos    = get_gastos(pyme_id, desde_str, hasta_str)
ingresos  = get_ingresos(pyme_id, desde_str, hasta_str)
evolucion = get_evolucion_mensual(pyme_id, meses=6)

# Calcular semana anterior para comparación
inicio_semana_actual  = hoy - timedelta(days=hoy.weekday())
inicio_semana_anterior = inicio_semana_actual - timedelta(days=7)
fin_semana_anterior    = inicio_semana_actual - timedelta(days=1)
resumen_semana_ant = get_resumen(pyme_id, inicio_semana_anterior.isoformat(), fin_semana_anterior.isoformat())
resumen_semana_act = get_resumen(pyme_id, inicio_semana_actual.isoformat(), hoy.isoformat())

# ─────────────────────────────────────
# CÁLCULOS WOW
# ─────────────────────────────────────
dias_periodo  = max((hasta - desde).days, 1)
semanas       = dias_periodo / 7
horas_totales = horas_semana * semanas
ganancia      = resumen["ganancia"]

# 1. Valor de la hora
valor_hora = ganancia / horas_totales if horas_totales > 0 else 0

# 2. Punto de equilibrio mensual
gastos_fijos_mes = resumen["gastos_fijos"] / (dias_periodo / 30) if dias_periodo > 0 else 0

# 3. Días de caja disponible
gastos_dia = resumen["total_gastos"] / dias_periodo if dias_periodo > 0 else 0
dias_caja  = caja_disponible / gastos_dia if gastos_dia > 0 else 0

# 4. Concentración de ingresos por cliente
clientes = {}
for ing in ingresos:
    c = ing.get("cliente") or "Sin nombre"
    clientes[c] = clientes.get(c, 0) + ing["monto"]
total_ing = resumen["total_ingresos"]
cliente_top     = max(clientes, key=clientes.get) if clientes else None
pct_cliente_top = (clientes[cliente_top] / total_ing * 100) if cliente_top and total_ing > 0 else 0

# 5. Comparación semanal
var_gastos_semanal   = resumen_semana_act["total_gastos"] - resumen_semana_ant["total_gastos"]
var_ingresos_semanal = resumen_semana_act["total_ingresos"] - resumen_semana_ant["total_ingresos"]

# ─────────────────────────────────────
# SEMÁFORO
# ─────────────────────────────────────
def get_semaforo(margen):
    if margen >= 30:
        return "🟢", "Saludable", "Tu negocio está en zona verde."
    elif margen >= 10:
        return "🟡", "Atención", "Tu margen está ajustado. Hay margen de mejora."
    else:
        return "🔴", "Riesgo", "Tu negocio está perdiendo dinero o casi sin margen."

semaforo_ico, semaforo_label, semaforo_msg = get_semaforo(resumen["margen_pct"])

# ─────────────────────────────────────
# TABS
# ─────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "💡 Insights", "➕ Registrar", "📋 Historial", "📈 Evolución"])

# ══════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════
with tab1:
    # Semáforo grande
    st.markdown(f"### {semaforo_ico} {pyme['nombre']} — {semaforo_label}")
    st.caption(semaforo_msg)
    st.divider()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Ingresos", f"USD {resumen['total_ingresos']:,.0f}")
    with col2:
        st.metric("💸 Gastos", f"USD {resumen['total_gastos']:,.0f}")
    with col3:
        st.metric("✅ Ganancia", f"USD {ganancia:,.0f}", delta=f"{resumen['margen_pct']}% margen")
    with col4:
        delta_ing = f"USD {var_ingresos_semanal:+,.0f} vs semana ant." if resumen_semana_ant["total_ingresos"] > 0 else None
        st.metric("📅 Esta semana", f"USD {resumen_semana_act['total_ingresos']:,.0f}", delta=delta_ing)

    st.divider()

    # Análisis automático
    st.markdown("#### 🤖 Qué está pasando en tu negocio")

    if resumen["total_ingresos"] == 0:
        st.info("Sin datos todavía. Cargá tus ingresos y gastos en la pestaña Registrar.")
    else:
        # Frase principal
        if ganancia > 0:
            st.success(f"**Estás ganando dinero.** Por cada USD 100 que entraron, te quedaron USD {resumen['margen_pct']:.0f} limpios.")
        elif ganancia == 0:
            st.warning("**Estás en cero.** Todo lo que entra lo gastás. No estás creciendo.")
        else:
            st.error(f"**Estás perdiendo plata.** Gastaste USD {abs(ganancia):,.0f} más de lo que entraste.")

        # Gasto más grande
        if resumen["gastos_por_cat"]:
            top = resumen["gastos_por_cat"][0]
            pct = top["total"] / resumen["total_gastos"] * 100 if resumen["total_gastos"] > 0 else 0
            st.warning(f"**Tu gasto más grande:** {top['nombre']} — USD {top['total']:,.0f} ({pct:.0f}% de todo lo que gastás)")

        # Comparación semanal
        if resumen_semana_ant["total_gastos"] > 0:
            if var_gastos_semanal > 0:
                st.warning(f"**Esta semana gastaste USD {var_gastos_semanal:,.0f} más que la semana pasada.** Revisá en qué.")
            elif var_gastos_semanal < 0:
                st.success(f"**Bien — esta semana gastaste USD {abs(var_gastos_semanal):,.0f} menos que la semana pasada.**")

        # Gastos fijos vs variables
        if resumen["total_gastos"] > 0:
            pct_fijo = resumen["gastos_fijos"] / resumen["total_gastos"] * 100
            if pct_fijo > 60:
                st.error(f"**{pct_fijo:.0f}% de tus gastos son fijos.** Si las ventas bajan un mes, tenés poco margen de maniobra.")
            else:
                st.info(f"**Gastos fijos:** {pct_fijo:.0f}% · **Variables:** {100-pct_fijo:.0f}%")

    st.divider()

    col_pie, col_ev = st.columns(2)
    with col_pie:
        if resumen["gastos_por_cat"]:
            df_pie = pd.DataFrame(resumen["gastos_por_cat"])
            fig = px.pie(df_pie, values="total", names="nombre",
                         title="Gastos por categoría",
                         color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
            fig.update_layout(height=280, margin=dict(t=40,b=0,l=0,r=0))
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(fig)

    with col_ev:
        if evolucion:
            df_ev = pd.DataFrame(evolucion)
            fig2 = go.Figure()
            fig2.add_bar(name="Ingresos", x=df_ev["mes"], y=df_ev["ingresos"], marker_color="#1D9E75", opacity=0.8)
            fig2.add_bar(name="Gastos",   x=df_ev["mes"], y=df_ev["gastos"],   marker_color="#E24B4A", opacity=0.8)
            fig2.update_layout(barmode="group", height=280, title="Últimos 6 meses",
                               margin=dict(t=40,b=0,l=0,r=0),
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2)

# ══════════════════════════════════════
# TAB 2 — INSIGHTS WOW
# ══════════════════════════════════════
with tab2:
    st.markdown("### 💡 Lo que tu negocio no te estaba diciendo")
    st.caption("Estos números la mayoría de los dueños nunca los vieron.")
    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        # 1. Valor de la hora
        st.markdown("#### ⏱ ¿Cuánto vale tu hora de trabajo?")
        if ganancia > 0 and horas_totales > 0:
            if valor_hora < 5:
                st.error(f"## USD {valor_hora:.2f} / hora")
                st.markdown(f"Trabajando **{horas_semana}h por semana**, tu hora vale **USD {valor_hora:.2f}**. Eso es menos que un empleado de mostrador. El problema no es que trabajás poco — es que el margen es muy bajo.")
            elif valor_hora < 15:
                st.warning(f"## USD {valor_hora:.2f} / hora")
                st.markdown(f"Tu hora vale **USD {valor_hora:.2f}**. Hay margen para mejorar — revisá tus precios o reducí gastos variables.")
            else:
                st.success(f"## USD {valor_hora:.2f} / hora")
                st.markdown(f"Bien. Tu hora vale **USD {valor_hora:.2f}**. Estás en zona saludable.")
        else:
            st.info("Cargá datos de ingresos y gastos para ver este indicador.")

        st.divider()

        # 3. Días de caja
        st.markdown("#### 🏦 ¿Cuántos días aguanta tu negocio sin ingresos?")
        if gastos_dia > 0 and caja_disponible > 0:
            if dias_caja < 15:
                st.error(f"## {dias_caja:.0f} días")
                st.markdown(f"Con tu caja actual de **USD {caja_disponible:,.0f}**, si mañana no entra nada, en **{dias_caja:.0f} días** no podés pagar los gastos. Eso es riesgo real.")
            elif dias_caja < 30:
                st.warning(f"## {dias_caja:.0f} días")
                st.markdown(f"Tenés **{dias_caja:.0f} días** de reserva. Lo mínimo recomendado es 30 días.")
            else:
                st.success(f"## {dias_caja:.0f} días")
                st.markdown(f"Tenés **{dias_caja:.0f} días** de reserva. Tu negocio tiene colchón financiero.")
        else:
            st.info("Ingresá tu caja disponible en el sidebar para ver este indicador.")

    with col_b:
        # 2. Punto de equilibrio
        st.markdown("#### ⚖️ ¿Cuánto tenés que vender para no perder plata?")
        if gastos_fijos_mes > 0:
            margen_decimal = resumen["margen_pct"] / 100 if resumen["margen_pct"] > 0 else 0.3
            if margen_decimal > 0:
                punto_eq = gastos_fijos_mes / margen_decimal
                falta    = punto_eq - resumen["total_ingresos"]
                if falta > 0:
                    st.error(f"## USD {punto_eq:,.0f} / mes")
                    st.markdown(f"Necesitás vender al menos **USD {punto_eq:,.0f} por mes** para cubrir tus gastos fijos. Te faltan **USD {falta:,.0f}** para llegar.")
                else:
                    st.success(f"## USD {punto_eq:,.0f} / mes")
                    st.markdown(f"Tu punto de equilibrio es **USD {punto_eq:,.0f}**. Ya lo superaste — estás ganando.")
            else:
                st.info("Necesitás tener margen positivo para calcular este indicador.")
        else:
            st.info("Registrá gastos fijos para ver este indicador.")

        st.divider()

        # 4. Dependencia de clientes
        st.markdown("#### ⚠️ ¿Qué tan dependiente sos de un solo cliente?")
        if clientes and total_ing > 0:
            if pct_cliente_top > 50:
                st.error(f"## {pct_cliente_top:.0f}% de tus ingresos")
                st.markdown(f"**{cliente_top}** representa el **{pct_cliente_top:.0f}%** de todo lo que ganás. Si ese cliente se va, tu negocio entra en crisis. Necesitás diversificar.")
            elif pct_cliente_top > 30:
                st.warning(f"## {pct_cliente_top:.0f}% de tus ingresos")
                st.markdown(f"**{cliente_top}** es tu cliente más importante con el **{pct_cliente_top:.0f}%** de los ingresos. Cuidalo — pero buscá más clientes.")
            else:
                st.success(f"## {pct_cliente_top:.0f}% de tus ingresos")
                st.markdown(f"Bien distribuido. Tu cliente más grande representa solo el **{pct_cliente_top:.0f}%**. Eso es saludable.")

            # Tabla de clientes
            df_cli = pd.DataFrame(list(clientes.items()), columns=["Cliente", "Ingresos USD"])
            df_cli = df_cli.sort_values("Ingresos USD", ascending=False)
            df_cli["% del total"] = (df_cli["Ingresos USD"] / total_ing * 100).apply(lambda x: f"{x:.1f}%")
            df_cli["Ingresos USD"] = df_cli["Ingresos USD"].apply(lambda x: f"USD {x:,.0f}")
            st.dataframe(df_cli, hide_index=True)
        else:
            st.info("Registrá ingresos con nombre de cliente para ver este indicador.")

    st.divider()

    # 5. Comparación semanal detallada
    st.markdown("#### 📅 Esta semana vs la semana pasada")
    if resumen_semana_ant["total_ingresos"] > 0 or resumen_semana_ant["total_gastos"] > 0:
        col_x, col_y, col_z = st.columns(3)
        with col_x:
            delta_i = resumen_semana_act["total_ingresos"] - resumen_semana_ant["total_ingresos"]
            st.metric("Ingresos", f"USD {resumen_semana_act['total_ingresos']:,.0f}", delta=f"USD {delta_i:+,.0f}")
        with col_y:
            delta_g = resumen_semana_act["total_gastos"] - resumen_semana_ant["total_gastos"]
            st.metric("Gastos", f"USD {resumen_semana_act['total_gastos']:,.0f}", delta=f"USD {delta_g:+,.0f}", delta_color="inverse")
        with col_z:
            delta_gan = resumen_semana_act["ganancia"] - resumen_semana_ant["ganancia"]
            st.metric("Ganancia", f"USD {resumen_semana_act['ganancia']:,.0f}", delta=f"USD {delta_gan:+,.0f}")
    else:
        st.info("Cargá datos de al menos dos semanas para ver la comparación.")

# ══════════════════════════════════════
# TAB 3 — REGISTRAR
# ══════════════════════════════════════
with tab3:
    col_gasto, col_ingreso = st.columns(2)

    with col_gasto:
        st.markdown("#### 💸 Nuevo gasto")
        cats_g    = get_categorias("gasto")
        nombres_g = [c["nombre"] for c in cats_g]
        desc_g    = st.text_input("Descripción", key="desc_g", placeholder="Ej: Compra materiales")
        monto_g   = st.number_input("Monto USD", min_value=0.0, step=1.0, key="monto_g")
        fecha_g   = st.date_input("Fecha", value=hoy, key="fecha_g")
        cat_g     = st.selectbox("Categoría", range(len(nombres_g)), format_func=lambda i: nombres_g[i], key="cat_g")
        fijo_g    = st.checkbox("¿Gasto fijo?", key="fijo_g")
        if st.button("✅ Guardar gasto", use_container_width=True):
            if desc_g and monto_g > 0:
                registrar_gasto(pyme_id, cats_g[cat_g]["id"], desc_g, monto_g, fecha_g.isoformat(), fijo_g)
                st.success(f"✅ Guardado: {desc_g} — USD {monto_g:,.0f}")
            else:
                st.error("Completá descripción y monto.")

    with col_ingreso:
        st.markdown("#### 💰 Nuevo ingreso")
        cats_i    = get_categorias("ingreso")
        nombres_i = [c["nombre"] for c in cats_i]
        desc_i    = st.text_input("Descripción", key="desc_i", placeholder="Ej: Venta del día")
        monto_i   = st.number_input("Monto USD", min_value=0.0, step=1.0, key="monto_i")
        fecha_i   = st.date_input("Fecha", value=hoy, key="fecha_i")
        cliente_i = st.text_input("Cliente (importante para el análisis)", key="cliente_i")
        cat_i     = st.selectbox("Categoría", range(len(nombres_i)), format_func=lambda i: nombres_i[i], key="cat_i")
        if st.button("✅ Guardar ingreso", use_container_width=True):
            if desc_i and monto_i > 0:
                registrar_ingreso(pyme_id, cats_i[cat_i]["id"], desc_i, monto_i, fecha_i.isoformat(), cliente_i)
                st.success(f"✅ Guardado: {desc_i} — USD {monto_i:,.0f}")
            else:
                st.error("Completá descripción y monto.")

# ══════════════════════════════════════
# TAB 4 — HISTORIAL
# ══════════════════════════════════════
with tab4:
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

# ══════════════════════════════════════
# TAB 5 — EVOLUCIÓN
# ══════════════════════════════════════
with tab5:
    st.markdown("#### 📈 Evolución de los últimos 6 meses")
    if evolucion:
        df_ev = pd.DataFrame(evolucion)
        fig = go.Figure()
        fig.add_bar(name="Ingresos", x=df_ev["mes"], y=df_ev["ingresos"], marker_color="#1D9E75", opacity=0.85)
        fig.add_bar(name="Gastos",   x=df_ev["mes"], y=df_ev["gastos"],   marker_color="#E24B4A", opacity=0.85)
        fig.add_scatter(name="Ganancia", x=df_ev["mes"], y=df_ev["ganancia"],
                        mode="lines+markers", line=dict(color="#7F77DD", width=2), marker=dict(size=7))
        fig.update_layout(barmode="group", height=380,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02),
                          margin=dict(t=20,b=20),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(title="USD"))
        st.plotly_chart(fig)
    else:
        st.info("Cargá datos para ver la evolución.")
