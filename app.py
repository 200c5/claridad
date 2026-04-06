import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from db import (
    get_categorias, registrar_gasto, registrar_ingreso,
    get_gastos, get_ingresos, get_resumen, get_evolucion_mensual
)
from auth import (
    init_auth_tables, registrar_usuario, login_usuario,
    get_pymes_usuario, crear_pyme_usuario,
    get_todos_usuarios, get_stats_usuario
)

st.set_page_config(page_title="Claridad", page_icon="💚", layout="wide")

# Inicializar tablas
from db import init_db
init_db()
init_auth_tables()

# ─────────────────────────────────────
# SESIÓN
# ─────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ─────────────────────────────────────
# PANTALLA DE LOGIN / REGISTRO
# ─────────────────────────────────────
def pantalla_auth():
    st.markdown("""
    <div style='text-align:center;padding:40px 0 20px'>
        <span style='font-size:48px;font-weight:600;color:#1D9E75'>💚 Claridad</span><br>
        <span style='color:#888;font-size:16px'>Tu negocio, en claro</span>
    </div>
    """, unsafe_allow_html=True)

    col_esp1, col_form, col_esp2 = st.columns([1, 2, 1])

    with col_form:
        modo = st.radio("", ["Iniciar sesión", "Crear cuenta"], horizontal=True, label_visibility="collapsed")
        st.divider()

        if modo == "Iniciar sesión":
            email    = st.text_input("Email", placeholder="tu@email.com")
            password = st.text_input("Contraseña", type="password")

            if st.button("Entrar", use_container_width=True, type="primary"):
                if email and password:
                    ok, resultado = login_usuario(email, password)
                    if ok:
                        st.session_state.usuario = resultado
                        st.rerun()
                    else:
                        st.error(resultado)
                else:
                    st.error("Completá email y contraseña.")

        else:
            nombre   = st.text_input("Tu nombre")
            email    = st.text_input("Email", placeholder="tu@email.com")
            password = st.text_input("Contraseña (mínimo 6 caracteres)", type="password")
            password2 = st.text_input("Repetir contraseña", type="password")

            if st.button("Crear cuenta", use_container_width=True, type="primary"):
                if not (nombre and email and password):
                    st.error("Completá todos los campos.")
                elif password != password2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    ok, resultado = registrar_usuario(email, nombre, password)
                    if ok:
                        st.session_state.usuario = {"id": resultado, "nombre": nombre, "email": email}
                        st.success("Cuenta creada. Bienvenido/a.")
                        st.rerun()
                    else:
                        st.error(resultado)

if st.session_state.usuario is None:
    pantalla_auth()
    st.stop()

# ─────────────────────────────────────
# APP PRINCIPAL (usuario logueado)
# ─────────────────────────────────────
usuario    = st.session_state.usuario
usuario_id = usuario["id"]

with st.sidebar:
    st.markdown(f"## 💚 Claridad")
    st.caption(f"Hola, {usuario['nombre']}")
    st.divider()

    pymes = get_pymes_usuario(usuario_id)

    if not pymes:
        st.info("Aún no tenés empresas. Creá la primera.")
        nombre_p = st.text_input("Nombre de la empresa")
        rubro_p  = st.text_input("Rubro")
        if st.button("Crear empresa"):
            if nombre_p:
                crear_pyme_usuario(usuario_id, nombre_p, rubro_p)
                st.rerun()
        st.divider()
        if st.button("Cerrar sesión"):
            st.session_state.usuario = None
            st.rerun()
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
    st.caption("Configuración")
    horas_semana    = st.number_input("Horas trabajadas/semana", min_value=1, max_value=100, value=50)
    caja_disponible = st.number_input("Caja disponible hoy (USD)", min_value=0.0, step=100.0, value=0.0)

    st.divider()
    with st.expander("+ Nueva empresa"):
        n = st.text_input("Nombre", key="new_pyme_n")
        r = st.text_input("Rubro",  key="new_pyme_r")
        if st.button("Crear", key="btn_new_pyme"):
            if n:
                crear_pyme_usuario(usuario_id, n, r)
                st.rerun()

    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

# ─────────────────────────────────────
# DATOS
# ─────────────────────────────────────
resumen   = get_resumen(pyme_id, desde_str, hasta_str)
gastos    = get_gastos(pyme_id, desde_str, hasta_str)
ingresos  = get_ingresos(pyme_id, desde_str, hasta_str)
evolucion = get_evolucion_mensual(pyme_id, meses=6)

inicio_semana_actual   = hoy - timedelta(days=hoy.weekday())
inicio_semana_anterior = inicio_semana_actual - timedelta(days=7)
fin_semana_anterior    = inicio_semana_actual - timedelta(days=1)
resumen_semana_ant = get_resumen(pyme_id, inicio_semana_anterior.isoformat(), fin_semana_anterior.isoformat())
resumen_semana_act = get_resumen(pyme_id, inicio_semana_actual.isoformat(), hoy.isoformat())

# ─────────────────────────────────────
# CÁLCULOS
# ─────────────────────────────────────
dias_periodo  = max((hasta - desde).days, 1)
semanas       = dias_periodo / 7
horas_totales = horas_semana * semanas
ganancia      = resumen["ganancia"]
valor_hora    = ganancia / horas_totales if horas_totales > 0 else 0

gastos_fijos_mes = resumen["gastos_fijos"] / (dias_periodo / 30) if dias_periodo > 0 else 0
gastos_dia       = resumen["total_gastos"] / dias_periodo if dias_periodo > 0 else 0
dias_caja        = caja_disponible / gastos_dia if gastos_dia > 0 else 0

clientes = {}
for ing in ingresos:
    c = ing.get("cliente") or "Sin nombre"
    clientes[c] = clientes.get(c, 0) + ing["monto"]
total_ing       = resumen["total_ingresos"]
cliente_top     = max(clientes, key=clientes.get) if clientes else None
pct_cliente_top = (clientes[cliente_top] / total_ing * 100) if cliente_top and total_ing > 0 else 0

var_gastos_semanal   = resumen_semana_act["total_gastos"]   - resumen_semana_ant["total_gastos"]
var_ingresos_semanal = resumen_semana_act["total_ingresos"] - resumen_semana_ant["total_ingresos"]

def get_semaforo(margen):
    if margen >= 30:
        return "🟢", "Saludable", "Tu negocio está en zona verde."
    elif margen >= 10:
        return "🟡", "Atención", "Tu margen está ajustado."
    else:
        return "🔴", "Riesgo", "Tu negocio está perdiendo dinero o casi sin margen."

semaforo_ico, semaforo_label, semaforo_msg = get_semaforo(resumen["margen_pct"])
ingresos_base = resumen["total_ingresos"]
gastos_base   = resumen["total_gastos"]
margen_base   = resumen["margen_pct"]

# ─────────────────────────────────────
# TABS
# ─────────────────────────────────────
ADMIN_EMAIL = "clara2005perdomo@gmail.com"
es_admin = usuario["email"] == ADMIN_EMAIL

if es_admin:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab_admin = st.tabs([
        "📊 Dashboard", "💡 Insights", "🧮 Simulador",
        "➕ Registrar", "📋 Historial", "📈 Evolución", "📥 Importar Excel", "⚙️ Admin"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Dashboard", "💡 Insights", "🧮 Simulador",
        "➕ Registrar", "📋 Historial", "📈 Evolución", "📥 Importar Excel"
    ])
    tab_admin = None

# ══════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════
with tab1:
    st.markdown(f"### {semaforo_ico} {pyme['nombre']} — {semaforo_label}")
    st.caption(semaforo_msg)
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Ingresos", f"USD {resumen['total_ingresos']:,.0f}")
    with col2:
        st.metric("💸 Gastos", f"USD {resumen['total_gastos']:,.0f}")
    with col3:
        st.metric("✅ Ganancia", f"USD {ganancia:,.0f}", delta=f"{resumen['margen_pct']}% margen")
    with col4:
        delta_ing = f"USD {var_ingresos_semanal:+,.0f} vs sem. ant." if resumen_semana_ant["total_ingresos"] > 0 else None
        st.metric("📅 Esta semana", f"USD {resumen_semana_act['total_ingresos']:,.0f}", delta=delta_ing)

    st.divider()
    col_msg, col_pie = st.columns([2, 1])

    with col_msg:
        st.markdown("#### 🤖 Qué está pasando")
        if resumen["total_ingresos"] == 0:
            st.info("Sin datos todavía. Cargá tus ingresos y gastos en Registrar.")
        else:
            if ganancia > 0:
                st.success(f"**Estás ganando dinero.** Por cada USD 100 que entraron, te quedaron USD {resumen['margen_pct']:.0f} limpios.")
            elif ganancia == 0:
                st.warning("**Estás en cero.** Todo lo que entra lo gastás.")
            else:
                st.error(f"**Estás perdiendo plata.** Gastaste USD {abs(ganancia):,.0f} más de lo que entraste.")

            if resumen["gastos_por_cat"]:
                top = resumen["gastos_por_cat"][0]
                pct = top["total"] / resumen["total_gastos"] * 100 if resumen["total_gastos"] > 0 else 0
                st.warning(f"**Gasto más grande:** {top['nombre']} — USD {top['total']:,.0f} ({pct:.0f}%)")

            if resumen_semana_ant["total_gastos"] > 0:
                if var_gastos_semanal > 0:
                    st.warning(f"**Esta semana gastaste USD {var_gastos_semanal:,.0f} más que la semana pasada.**")
                elif var_gastos_semanal < 0:
                    st.success(f"**Bien — esta semana gastaste USD {abs(var_gastos_semanal):,.0f} menos que la semana pasada.**")

            if resumen["total_gastos"] > 0:
                pct_fijo = resumen["gastos_fijos"] / resumen["total_gastos"] * 100
                if pct_fijo > 60:
                    st.error(f"**{pct_fijo:.0f}% de tus gastos son fijos.** Si las ventas bajan, tenés poco margen.")
                else:
                    st.info(f"Gastos fijos: {pct_fijo:.0f}% · Variables: {100-pct_fijo:.0f}%")

    with col_pie:
        if resumen["gastos_por_cat"]:
            df_pie = pd.DataFrame(resumen["gastos_por_cat"])
            fig = px.pie(df_pie, values="total", names="nombre",
                         title="Gastos por categoría",
                         color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
            fig.update_layout(height=280, margin=dict(t=40,b=0,l=0,r=0))
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(fig)

# ══════════════════════════════════════
# TAB 2 — INSIGHTS
# ══════════════════════════════════════
with tab2:
    st.markdown("### 💡 Lo que tu negocio no te estaba diciendo")
    st.caption("Números que la mayoría de los dueños nunca vieron.")
    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### ⏱ ¿Cuánto vale tu hora?")
        if ganancia > 0 and horas_totales > 0:
            if valor_hora < 5:
                st.error(f"## USD {valor_hora:.2f} / hora")
                st.markdown(f"Trabajando {horas_semana}h/semana, tu hora vale **USD {valor_hora:.2f}**. Menos que un empleado de mostrador.")
            elif valor_hora < 15:
                st.warning(f"## USD {valor_hora:.2f} / hora")
                st.markdown(f"Tu hora vale **USD {valor_hora:.2f}**. Hay margen para mejorar.")
            else:
                st.success(f"## USD {valor_hora:.2f} / hora")
                st.markdown(f"Tu hora vale **USD {valor_hora:.2f}**. Estás en zona saludable.")
        else:
            st.info("Cargá datos para ver este indicador.")

        st.divider()

        st.markdown("#### 🏦 ¿Cuántos días aguantás sin ingresos?")
        if gastos_dia > 0 and caja_disponible > 0:
            if dias_caja < 15:
                st.error(f"## {dias_caja:.0f} días")
                st.markdown(f"Con USD {caja_disponible:,.0f} en caja, en **{dias_caja:.0f} días** no podés cubrir gastos. Riesgo real.")
            elif dias_caja < 30:
                st.warning(f"## {dias_caja:.0f} días")
                st.markdown(f"Tenés {dias_caja:.0f} días de reserva. El mínimo recomendado es 30.")
            else:
                st.success(f"## {dias_caja:.0f} días")
                st.markdown(f"Tenés {dias_caja:.0f} días de reserva. Buen colchón financiero.")
        else:
            st.info("Ingresá tu caja disponible en el sidebar.")

    with col_b:
        st.markdown("#### ⚖️ ¿Cuánto tenés que vender para no perder?")
        if gastos_fijos_mes > 0 and margen_base > 0:
            punto_eq = gastos_fijos_mes / (margen_base / 100)
            falta    = punto_eq - ingresos_base
            if falta > 0:
                st.error(f"## USD {punto_eq:,.0f} / mes")
                st.markdown(f"Te faltan **USD {falta:,.0f}** para cubrir tus gastos fijos.")
            else:
                st.success(f"## USD {punto_eq:,.0f} / mes")
                st.markdown(f"Ya superaste el punto de equilibrio. Estás ganando.")
        else:
            st.info("Registrá gastos fijos para ver este indicador.")

        st.divider()

        st.markdown("#### ⚠️ ¿Qué tan dependiente sos de un cliente?")
        if clientes and total_ing > 0:
            if pct_cliente_top > 50:
                st.error(f"## {pct_cliente_top:.0f}% en un cliente")
                st.markdown(f"**{cliente_top}** es el {pct_cliente_top:.0f}% de tus ingresos. Si se va, tu negocio entra en crisis.")
            elif pct_cliente_top > 30:
                st.warning(f"## {pct_cliente_top:.0f}% en un cliente")
                st.markdown(f"**{cliente_top}** es importante. Cuidalo — pero diversificá.")
            else:
                st.success(f"## {pct_cliente_top:.0f}% en un cliente")
                st.markdown("Ingresos bien distribuidos. Eso es saludable.")

            df_cli = pd.DataFrame(list(clientes.items()), columns=["Cliente", "USD"])
            df_cli = df_cli.sort_values("USD", ascending=False)
            df_cli["% del total"] = (df_cli["USD"] / total_ing * 100).apply(lambda x: f"{x:.1f}%")
            df_cli["USD"] = df_cli["USD"].apply(lambda x: f"USD {x:,.0f}")
            st.dataframe(df_cli, hide_index=True)
        else:
            st.info("Registrá ingresos con nombre de cliente.")

    st.divider()
    st.markdown("#### 📅 Esta semana vs la semana pasada")
    if resumen_semana_ant["total_ingresos"] > 0 or resumen_semana_ant["total_gastos"] > 0:
        cx, cy, cz = st.columns(3)
        with cx:
            st.metric("Ingresos", f"USD {resumen_semana_act['total_ingresos']:,.0f}",
                      delta=f"USD {resumen_semana_act['total_ingresos'] - resumen_semana_ant['total_ingresos']:+,.0f}")
        with cy:
            st.metric("Gastos", f"USD {resumen_semana_act['total_gastos']:,.0f}",
                      delta=f"USD {resumen_semana_act['total_gastos'] - resumen_semana_ant['total_gastos']:+,.0f}", delta_color="inverse")
        with cz:
            st.metric("Ganancia", f"USD {resumen_semana_act['ganancia']:,.0f}",
                      delta=f"USD {resumen_semana_act['ganancia'] - resumen_semana_ant['ganancia']:+,.0f}")
    else:
        st.info("Cargá datos de al menos dos semanas para ver la comparación.")

# ══════════════════════════════════════
# TAB 3 — SIMULADOR
# ══════════════════════════════════════
with tab3:
    st.markdown("### 🧮 Simulador de decisiones")
    st.caption("Probá escenarios antes de tomar una decisión.")
    st.divider()

    sim = st.radio("¿Qué querés simular?", [
        "📉 Aplicar un descuento",
        "📈 Subir precios",
        "👷 Contratar un empleado",
        "✂️ Reducir un gasto fijo",
        "🎯 Meta de margen",
    ])
    st.divider()

    if ingresos_base == 0:
        st.info("Cargá datos primero para usar el simulador.")
    else:
        if sim == "📉 Aplicar un descuento":
            st.markdown("#### ¿Qué pasa si aplicás un descuento?")
            c1, c2 = st.columns(2)
            with c1:
                descuento      = st.slider("Descuento (%)", 1, 50, 10)
                clientes_extra = st.slider("Clientes nuevos que atraerías (%)", 0, 100, 0)
            with c2:
                ing_new = ingresos_base * (1 - descuento/100) * (1 + clientes_extra/100)
                gan_new = ing_new - gastos_base
                mar_new = (gan_new / ing_new * 100) if ing_new > 0 else 0
                dif     = gan_new - ganancia
                st.metric("Ingresos estimados", f"USD {ing_new:,.0f}", delta=f"USD {ing_new-ingresos_base:+,.0f}")
                st.metric("Ganancia estimada",  f"USD {gan_new:,.0f}",  delta=f"USD {dif:+,.0f}")
                st.metric("Margen estimado",    f"{mar_new:.1f}%",       delta=f"{mar_new-margen_base:+.1f}%")
            if dif < 0:
                st.error(f"❌ Con ese descuento perdés USD {abs(dif):,.0f}. No conviene.")
            else:
                st.success(f"✅ Con más clientes, ganás USD {dif:,.0f} más.")

        elif sim == "📈 Subir precios":
            st.markdown("#### ¿Qué pasa si subís los precios?")
            c1, c2 = st.columns(2)
            with c1:
                aumento           = st.slider("Aumento (%)", 1, 50, 10)
                clientes_perdidos = st.slider("Clientes que podrías perder (%)", 0, 50, 5)
            with c2:
                ing_new = ingresos_base * (1 + aumento/100) * (1 - clientes_perdidos/100)
                gan_new = ing_new - gastos_base
                mar_new = (gan_new / ing_new * 100) if ing_new > 0 else 0
                dif     = gan_new - ganancia
                st.metric("Ingresos estimados", f"USD {ing_new:,.0f}", delta=f"USD {ing_new-ingresos_base:+,.0f}")
                st.metric("Ganancia estimada",  f"USD {gan_new:,.0f}",  delta=f"USD {dif:+,.0f}")
                st.metric("Margen estimado",    f"{mar_new:.1f}%",       delta=f"{mar_new-margen_base:+.1f}%")
            if dif > 0:
                st.success(f"✅ Aun perdiendo {clientes_perdidos}% de clientes, ganás USD {dif:,.0f} más.")
            else:
                st.error(f"❌ Perdés demasiados clientes. Bajá el precio o el % de pérdida estimada.")

        elif sim == "👷 Contratar un empleado":
            st.markdown("#### ¿Cuánto tenés que vender más si contratás a alguien?")
            c1, c2 = st.columns(2)
            with c1:
                sueldo       = st.number_input("Sueldo mensual (USD)", min_value=100.0, step=50.0, value=800.0)
                ventas_extra = st.slider("Ventas adicionales que generaría (%)", 0, 100, 20)
            with c2:
                gas_new = gastos_base + sueldo
                ing_new = ingresos_base * (1 + ventas_extra/100)
                gan_new = ing_new - gas_new
                mar_new = (gan_new / ing_new * 100) if ing_new > 0 else 0
                dif     = gan_new - ganancia
                ventas_min = gas_new / (1 - (gastos_base / ingresos_base)) if ingresos_base > 0 else 0
                st.metric("Ingresos estimados",    f"USD {ing_new:,.0f}",  delta=f"USD {ing_new-ingresos_base:+,.0f}")
                st.metric("Ganancia estimada",     f"USD {gan_new:,.0f}",   delta=f"USD {dif:+,.0f}")
                st.metric("Ventas mínimas necesarias", f"USD {ventas_min:,.0f}")
            if dif > 0:
                st.success(f"✅ Generando {ventas_extra}% más de ventas, ganás USD {dif:,.0f} más.")
            else:
                st.error(f"❌ Necesitás que produzca al menos USD {ventas_min:,.0f} en ventas para que valga la pena.")

        elif sim == "✂️ Reducir un gasto fijo":
            st.markdown("#### ¿Cuánto mejora tu margen si reducís un gasto?")
            c1, c2 = st.columns(2)
            with c1:
                nombre_gasto = st.text_input("¿Qué gasto?", placeholder="Ej: Alquiler")
                reduccion    = st.number_input("¿Cuánto ahorrarías por mes? (USD)", min_value=0.0, step=50.0, value=200.0)
            with c2:
                gas_new = gastos_base - reduccion
                gan_new = ingresos_base - gas_new
                mar_new = (gan_new / ingresos_base * 100) if ingresos_base > 0 else 0
                st.metric("Gastos estimados",  f"USD {gas_new:,.0f}",  delta=f"USD {-reduccion:+,.0f}", delta_color="inverse")
                st.metric("Ganancia estimada", f"USD {gan_new:,.0f}",  delta=f"USD {reduccion:+,.0f}")
                st.metric("Margen estimado",   f"{mar_new:.1f}%",      delta=f"{mar_new-margen_base:+.1f}%")
            if reduccion > 0:
                st.success(f"✅ Reduciendo {nombre_gasto or 'ese gasto'} USD {reduccion:,.0f}/mes, tu margen pasa de {margen_base:.1f}% a {mar_new:.1f}%.")

        elif sim == "🎯 Meta de margen":
            st.markdown("#### ¿Cuánto tenés que vender para llegar a tu meta?")
            c1, c2 = st.columns(2)
            with c1:
                margen_obj = st.slider("Margen objetivo (%)", 5, 70, 30)
            with c2:
                ventas_nec = resumen["gastos_fijos"] / (margen_obj/100) if margen_obj > 0 else 0
                dif_ventas = ventas_nec - ingresos_base
                st.metric("Ventas actuales",   f"USD {ingresos_base:,.0f}")
                st.metric("Ventas necesarias", f"USD {ventas_nec:,.0f}",  delta=f"USD {dif_ventas:+,.0f}")
                st.metric("Margen actual",     f"{margen_base:.1f}%")
            if dif_ventas > 0:
                st.warning(f"Necesitás vender USD {dif_ventas:,.0f} más — un {dif_ventas/ingresos_base*100:.0f}% más.")
            else:
                st.success(f"✅ Ya superás el {margen_obj}% de margen.")

# ══════════════════════════════════════
# TAB 4 — REGISTRAR
# ══════════════════════════════════════
with tab4:
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
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Completá descripción y monto.")

    with col_ingreso:
        st.markdown("#### 💰 Nuevo ingreso")
        cats_i    = get_categorias("ingreso")
        nombres_i = [c["nombre"] for c in cats_i]
        desc_i    = st.text_input("Descripción", key="desc_i", placeholder="Ej: Venta del día")
        monto_i   = st.number_input("Monto USD", min_value=0.0, step=1.0, key="monto_i")
        fecha_i   = st.date_input("Fecha", value=hoy, key="fecha_i")
        cliente_i = st.text_input("Cliente (importante para análisis)", key="cliente_i")
        cat_i     = st.selectbox("Categoría", range(len(nombres_i)), format_func=lambda i: nombres_i[i], key="cat_i")
        if st.button("✅ Guardar ingreso", use_container_width=True):
            if desc_i and monto_i > 0:
                registrar_ingreso(pyme_id, cats_i[cat_i]["id"], desc_i, monto_i, fecha_i.isoformat(), cliente_i)
                st.success(f"✅ Guardado: {desc_i} — USD {monto_i:,.0f}")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Completá descripción y monto.")

# ══════════════════════════════════════
# TAB 5 — HISTORIAL
# ══════════════════════════════════════
with tab5:
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
# TAB 6 — EVOLUCIÓN
# ══════════════════════════════════════
with tab6:
    st.markdown("#### 📈 Últimos 6 meses")
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
# ══════════════════════════════════════
# TAB 7 — IMPORTAR EXCEL
# ══════════════════════════════════════
with tab7:
    st.markdown("### 📥 Importar datos desde Excel")
    st.caption("Subí un reporte exportado de Dynamics u otro sistema y los datos se cargan solos.")
    st.divider()

    archivo = st.file_uploader("Subí tu archivo Excel", type=["xlsx", "xls"])

    if archivo:
        import pandas as pd
        try:
            df = pd.read_excel(archivo)
            st.success(f"✅ Archivo cargado — {len(df)} filas, {len(df.columns)} columnas")
            st.markdown("#### Columnas detectadas")
            st.write(list(df.columns))
            st.markdown("#### Vista previa")
            st.dataframe(df.head(5), hide_index=True)
            st.divider()

            st.markdown("#### Mapeá las columnas")
            col_fecha  = st.selectbox("¿Cuál es la columna de FECHA?",   ["-- No usar --"] + list(df.columns))
            col_monto  = st.selectbox("¿Cuál es la columna de MONTO?",   ["-- No usar --"] + list(df.columns))
            col_desc   = st.selectbox("¿Cuál es la columna de DESCRIPCIÓN?", ["-- No usar --"] + list(df.columns))
            col_tipo   = st.selectbox("¿Es ingreso o gasto?", ["gasto", "ingreso"])
            col_cliente = st.selectbox("¿Cuál es la columna de CLIENTE? (opcional)", ["-- No usar --"] + list(df.columns))

            if st.button("📥 Importar datos", use_container_width=True):
                if col_fecha == "-- No usar --" or col_monto == "-- No usar --":
                    st.error("Necesitás seleccionar al menos la columna de fecha y monto.")
                else:
                    cats = get_categorias(col_tipo)
                    cat_id = cats[0]["id"] if cats else 1
                    errores = 0
                    importados = 0

                    for _, row in df.iterrows():
                        try:
                            try:
                    from datetime import datetime
                    fecha_raw = row[col_fecha]
                    if hasattr(fecha_raw, 'strftime'):
                        fecha = fecha_raw.strftime('%Y-%m-%d')
                    else:
                        fecha = str(fecha_raw)[:10]
                except:
                    fecha = str(row[col_fecha])[:10]
    fecha_raw = row[col_fecha]
    if hasattr(fecha_raw, 'strftime'):
        fecha = fecha_raw.strftime('%Y-%m-%d')
    else:
        fecha = str(fecha_raw)[:10]
except:
    fecha = str(row[col_fecha])[:10]
                            monto  = float(str(row[col_monto]).replace(",", ".").replace("$", "").strip())
                            desc   = str(row[col_desc]) if col_desc != "-- No usar --" else "Importado"
                            cliente = str(row[col_cliente]) if col_cliente != "-- No usar --" else ""

                            if monto <= 0:
                                continue

                            if col_tipo == "gasto":
                                registrar_gasto(pyme_id, cat_id, desc, monto, fecha)
                            else:
                                registrar_ingreso(pyme_id, cat_id, desc, monto, fecha, cliente)
                            importados += 1
                        except:
                            errores += 1

                    st.success(f"✅ Importados: {importados} registros")
                    if errores > 0:
                        st.warning(f"⚠️ {errores} filas no se pudieron importar")
                    st.cache_data.clear()
                    st.rerun()

        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
    else:
        st.info("Subí un archivo Excel exportado de Dynamics, QuickBooks, o cualquier sistema que uses.")
# ══════════════════════════════════════
# TAB ADMIN — solo visible para el admin
# ══════════════════════════════════════
if es_admin and tab_admin:
    with tab_admin:
        st.markdown("### ⚙️ Panel de administrador")
        st.caption("Solo visible para vos.")
        st.divider()

        usuarios = get_todos_usuarios()
        total = len(usuarios)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("👥 Usuarios registrados", total)
        with col2:
            st.metric("🎯 Meta", "5 usuarios activos")

        st.divider()
        st.markdown("#### Usuarios registrados")

        for u in usuarios:
            stats = get_stats_usuario(u["id"])
            activo = stats["gastos"] > 0 or stats["ingresos"] > 0
            with st.expander(f"{'🟢' if activo else '⚪'} {u['nombre']} — {u['email']}"):
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Empresas", stats["pymes"])
                with col_b:
                    st.metric("Gastos cargados", stats["gastos"])
                with col_c:
                    st.metric("Ingresos cargados", stats["ingresos"])
                with col_d:
                    st.metric("Estado", "Activo" if activo else "Sin datos")
                st.caption(f"Registrado: {u['creado_en']}")

        st.divider()
        st.markdown("#### ¿Cuándo cobrar?")
        activos = sum(1 for u in usuarios if get_stats_usuario(u["id"])["gastos"] > 0 or get_stats_usuario(u["id"])["ingresos"] > 0)
        if activos >= 3:
            st.success(f"✅ Tenés {activos} usuarios activos. Es momento de ofrecer el plan pago.")
        else:
            st.info(f"Tenés {activos} usuarios activos. Cuando llegues a 3, ofrecé el plan pago.")
