"""
Claridad — Base de datos (Supabase / PostgreSQL)
"""

import os
import psycopg2
import psycopg2.extras
from datetime import date, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL", "")

def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Crea las tablas si no existen."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS pymes (
            id         SERIAL PRIMARY KEY,
            nombre     TEXT NOT NULL,
            rubro      TEXT,
            moneda     TEXT DEFAULT 'USD',
            creado_en  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id     SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            tipo   TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id           SERIAL PRIMARY KEY,
            pyme_id      INTEGER NOT NULL REFERENCES pymes(id),
            categoria_id INTEGER REFERENCES categorias(id),
            descripcion  TEXT,
            monto        REAL NOT NULL,
            fecha        TEXT NOT NULL,
            es_fijo      INTEGER DEFAULT 0,
            notas        TEXT,
            creado_en    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ingresos (
            id           SERIAL PRIMARY KEY,
            pyme_id      INTEGER NOT NULL REFERENCES pymes(id),
            categoria_id INTEGER REFERENCES categorias(id),
            descripcion  TEXT,
            monto        REAL NOT NULL,
            fecha        TEXT NOT NULL,
            cliente      TEXT,
            notas        TEXT,
            creado_en    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Categorías por defecto
    c.execute("SELECT COUNT(*) FROM categorias")
    if c.fetchone()[0] == 0:
        categorias = [
            ("Materias primas", "gasto"),
            ("Sueldos y personal", "gasto"),
            ("Alquiler", "gasto"),
            ("Servicios (luz, agua, internet)", "gasto"),
            ("Marketing y publicidad", "gasto"),
            ("Transporte y logística", "gasto"),
            ("Equipamiento", "gasto"),
            ("Impuestos y tasas", "gasto"),
            ("Otros gastos", "gasto"),
            ("Venta de productos", "ingreso"),
            ("Venta de servicios", "ingreso"),
            ("Cobro de factura", "ingreso"),
            ("Otros ingresos", "ingreso"),
        ]
        c.executemany("INSERT INTO categorias (nombre, tipo) VALUES (%s, %s)", categorias)

    conn.commit()
    conn.close()

def get_pymes():
    conn = get_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM pymes ORDER BY nombre")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crear_pyme(nombre, rubro, moneda="USD", retornar_id=False):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO pymes (nombre, rubro, moneda) VALUES (%s, %s, %s) RETURNING id", (nombre, rubro, moneda))
    pyme_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    if retornar_id:
        return pyme_id

def get_categorias(tipo):
    conn = get_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM categorias WHERE tipo = %s ORDER BY nombre", (tipo,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def registrar_gasto(pyme_id, categoria_id, descripcion, monto, fecha, es_fijo=False, notas=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO gastos (pyme_id, categoria_id, descripcion, monto, fecha, es_fijo, notas) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (pyme_id, categoria_id, descripcion, monto, fecha, int(es_fijo), notas)
    )
    conn.commit()
    conn.close()

def registrar_ingreso(pyme_id, categoria_id, descripcion, monto, fecha, cliente="", notas=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO ingresos (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas)
    )
    conn.commit()
    conn.close()

def get_gastos(pyme_id, desde, hasta):
    conn = get_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("""
        SELECT g.*, cat.nombre as categoria_nombre
        FROM gastos g
        LEFT JOIN categorias cat ON g.categoria_id = cat.id
        WHERE g.pyme_id = %s AND g.fecha BETWEEN %s AND %s
        ORDER BY g.fecha DESC
    """, (pyme_id, desde, hasta))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_ingresos(pyme_id, desde, hasta):
    conn = get_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("""
        SELECT i.*, cat.nombre as categoria_nombre
        FROM ingresos i
        LEFT JOIN categorias cat ON i.categoria_id = cat.id
        WHERE i.pyme_id = %s AND i.fecha BETWEEN %s AND %s
        ORDER BY i.fecha DESC
    """, (pyme_id, desde, hasta))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def eliminar_gasto(gasto_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id = %s", (gasto_id,))
    conn.commit()
    conn.close()

def eliminar_ingreso(ingreso_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM ingresos WHERE id = %s", (ingreso_id,))
    conn.commit()
    conn.close()

def get_resumen(pyme_id, desde, hasta):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT COALESCE(SUM(monto),0) FROM ingresos WHERE pyme_id=%s AND fecha BETWEEN %s AND %s", (pyme_id, desde, hasta))
    total_ingresos = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id=%s AND fecha BETWEEN %s AND %s", (pyme_id, desde, hasta))
    total_gastos = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id=%s AND fecha BETWEEN %s AND %s AND es_fijo=1", (pyme_id, desde, hasta))
    gastos_fijos = c.fetchone()[0]

    c.execute("""
        SELECT cat.nombre, SUM(g.monto) as total
        FROM gastos g
        LEFT JOIN categorias cat ON g.categoria_id = cat.id
        WHERE g.pyme_id = %s AND g.fecha BETWEEN %s AND %s
        GROUP BY cat.nombre ORDER BY total DESC
    """, (pyme_id, desde, hasta))
    gastos_por_cat = [{"nombre": r[0], "total": r[1]} for r in c.fetchall()]

    conn.close()

    ganancia = total_ingresos - total_gastos
    margen   = (ganancia / total_ingresos * 100) if total_ingresos > 0 else 0

    return {
        "total_ingresos":   round(float(total_ingresos), 2),
        "total_gastos":     round(float(total_gastos), 2),
        "gastos_fijos":     round(float(gastos_fijos), 2),
        "gastos_variables": round(float(total_gastos - gastos_fijos), 2),
        "ganancia":         round(float(ganancia), 2),
        "margen_pct":       round(float(margen), 1),
        "gastos_por_cat":   gastos_por_cat,
    }

def get_evolucion_mensual(pyme_id, meses=6):
    conn = get_conn()
    c = conn.cursor()
    resultados = []
    hoy = date.today()

    for i in range(meses - 1, -1, -1):
        primer_dia = (hoy.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if primer_dia.month == 12:
            ultimo_dia = primer_dia.replace(day=31)
        else:
            ultimo_dia = primer_dia.replace(month=primer_dia.month + 1) - timedelta(days=1)

        desde = primer_dia.isoformat()
        hasta = ultimo_dia.isoformat()

        c.execute("SELECT COALESCE(SUM(monto),0) FROM ingresos WHERE pyme_id=%s AND fecha BETWEEN %s AND %s", (pyme_id, desde, hasta))
        ing = float(c.fetchone()[0])

        c.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id=%s AND fecha BETWEEN %s AND %s", (pyme_id, desde, hasta))
        gas = float(c.fetchone()[0])

        resultados.append({
            "mes":      primer_dia.strftime("%b %Y"),
            "ingresos": round(ing, 2),
            "gastos":   round(gas, 2),
            "ganancia": round(ing - gas, 2),
        })

    conn.close()
    return resultados
