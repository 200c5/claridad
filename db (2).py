import os
import sqlite3
from datetime import date, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

DB_PATH = "claridad.db"

def get_conn():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def ph():
    return "%s" if USE_POSTGRES else "?"

def fetchdict(rows):
    if USE_POSTGRES:
        return [dict(r) for r in rows]
    return [dict(r) for r in rows]

def init_db():
    conn = get_conn()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute("""CREATE TABLE IF NOT EXISTS pymes (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, rubro TEXT, moneda TEXT DEFAULT 'USD', creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS categorias (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, tipo TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS gastos (id SERIAL PRIMARY KEY, pyme_id INTEGER NOT NULL, categoria_id INTEGER, descripcion TEXT, monto REAL NOT NULL, fecha TEXT NOT NULL, es_fijo INTEGER DEFAULT 0, notas TEXT, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ingresos (id SERIAL PRIMARY KEY, pyme_id INTEGER NOT NULL, categoria_id INTEGER, descripcion TEXT, monto REAL NOT NULL, fecha TEXT NOT NULL, cliente TEXT, notas TEXT, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, password TEXT NOT NULL, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS usuario_pyme (usuario_id INTEGER NOT NULL, pyme_id INTEGER NOT NULL, PRIMARY KEY (usuario_id, pyme_id))""")
    else:
        c.execute("CREATE TABLE IF NOT EXISTS pymes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, rubro TEXT, moneda TEXT DEFAULT 'USD', creado_en TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, tipo TEXT NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, pyme_id INTEGER NOT NULL, categoria_id INTEGER, descripcion TEXT, monto REAL NOT NULL, fecha TEXT NOT NULL, es_fijo INTEGER DEFAULT 0, notas TEXT, creado_en TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS ingresos (id INTEGER PRIMARY KEY AUTOINCREMENT, pyme_id INTEGER NOT NULL, categoria_id INTEGER, descripcion TEXT, monto REAL NOT NULL, fecha TEXT NOT NULL, cliente TEXT, notas TEXT, creado_en TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, password TEXT NOT NULL, creado_en TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS usuario_pyme (usuario_id INTEGER NOT NULL, pyme_id INTEGER NOT NULL, PRIMARY KEY (usuario_id, pyme_id))")

    c.execute("SELECT COUNT(*) FROM categorias")
    if c.fetchone()[0] == 0:
        cats = [("Materias primas","gasto"),("Sueldos y personal","gasto"),("Alquiler","gasto"),("Servicios","gasto"),("Marketing","gasto"),("Transporte","gasto"),("Equipamiento","gasto"),("Impuestos","gasto"),("Otros gastos","gasto"),("Venta de productos","ingreso"),("Venta de servicios","ingreso"),("Cobro de factura","ingreso"),("Otros ingresos","ingreso")]
        p = ph()
        c.executemany(f"INSERT INTO categorias (nombre, tipo) VALUES ({p}, {p})", cats)

    conn.commit()
    conn.close()

def get_pymes():
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT * FROM pymes ORDER BY nombre")
        rows = c.fetchall()
    else:
        rows = conn.execute("SELECT * FROM pymes ORDER BY nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crear_pyme(nombre, rubro, moneda="USD"):
    conn = get_conn()
    p = ph()
    conn.cursor().execute(f"INSERT INTO pymes (nombre, rubro, moneda) VALUES ({p},{p},{p})", (nombre, rubro, moneda))
    conn.commit()
    conn.close()

def get_categorias(tipo):
    conn = get_conn()
    p = ph()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute(f"SELECT * FROM categorias WHERE tipo={p} ORDER BY nombre", (tipo,))
        rows = c.fetchall()
    else:
        rows = conn.execute(f"SELECT * FROM categorias WHERE tipo={p} ORDER BY nombre", (tipo,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def registrar_gasto(pyme_id, categoria_id, descripcion, monto, fecha, es_fijo=False, notas=""):
    conn = get_conn()
    p = ph()
    conn.cursor().execute(f"INSERT INTO gastos (pyme_id, categoria_id, descripcion, monto, fecha, es_fijo, notas) VALUES ({p},{p},{p},{p},{p},{p},{p})", (pyme_id, categoria_id, descripcion, monto, fecha, int(es_fijo), notas))
    conn.commit()
    conn.close()

def registrar_ingreso(pyme_id, categoria_id, descripcion, monto, fecha, cliente="", notas=""):
    conn = get_conn()
    p = ph()
    conn.cursor().execute(f"INSERT INTO ingresos (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas) VALUES ({p},{p},{p},{p},{p},{p},{p})", (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas))
    conn.commit()
    conn.close()

def get_gastos(pyme_id, desde, hasta):
    conn = get_conn()
    p = ph()
    sql = f"SELECT g.*, c.nombre as categoria_nombre FROM gastos g LEFT JOIN categorias c ON g.categoria_id = c.id WHERE g.pyme_id={p} AND g.fecha BETWEEN {p} AND {p} ORDER BY g.fecha DESC"
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute(sql, (pyme_id, desde, hasta))
        rows = c.fetchall()
    else:
        rows = conn.execute(sql, (pyme_id, desde, hasta)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_ingresos(pyme_id, desde, hasta):
    conn = get_conn()
    p = ph()
    sql = f"SELECT i.*, c.nombre as categoria_nombre FROM ingresos i LEFT JOIN categorias c ON i.categoria_id = c.id WHERE i.pyme_id={p} AND i.fecha BETWEEN {p} AND {p} ORDER BY i.fecha DESC"
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute(sql, (pyme_id, desde, hasta))
        rows = c.fetchall()
    else:
        rows = conn.execute(sql, (pyme_id, desde, hasta)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def eliminar_gasto(gasto_id):
    conn = get_conn()
    p = ph()
    conn.cursor().execute(f"DELETE FROM gastos WHERE id={p}", (gasto_id,))
    conn.commit()
    conn.close()

def eliminar_ingreso(ingreso_id):
    conn = get_conn()
    p = ph()
    conn.cursor().execute(f"DELETE FROM ingresos WHERE id={p}", (ingreso_id,))
    conn.commit()
    conn.close()

def get_resumen(pyme_id, desde, hasta):
    conn = get_conn()
    p = ph()
    if USE_POSTGRES:
        c = conn.cursor()
    else:
        c = conn.cursor()

    c.execute(f"SELECT COALESCE(SUM(monto),0) FROM ingresos WHERE pyme_id={p} AND fecha BETWEEN {p} AND {p}", (pyme_id, desde, hasta))
    ti = c.fetchone()[0]
    c.execute(f"SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id={p} AND fecha BETWEEN {p} AND {p}", (pyme_id, desde, hasta))
    tg = c.fetchone()[0]
    c.execute(f"SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id={p} AND fecha BETWEEN {p} AND {p} AND es_fijo=1", (pyme_id, desde, hasta))
    gf = c.fetchone()[0]
    c.execute(f"SELECT c.nombre, SUM(g.monto) as total FROM gastos g LEFT JOIN categorias c ON g.categoria_id = c.id WHERE g.pyme_id={p} AND g.fecha BETWEEN {p} AND {p} GROUP BY c.nombre ORDER BY total DESC", (pyme_id, desde, hasta))
    gpc = c.fetchall()
    conn.close()
    gan = float(ti) - float(tg)
    mar = (gan / float(ti) * 100) if float(ti) > 0 else 0
    return {"total_ingresos":round(float(ti),2),"total_gastos":round(float(tg),2),"gastos_fijos":round(float(gf),2),"gastos_variables":round(float(tg)-float(gf),2),"ganancia":round(gan,2),"margen_pct":round(mar,1),"gastos_por_cat":[{"nombre":r[0],"total":r[1]} for r in gpc]}

def get_evolucion_mensual(pyme_id, meses=6):
    conn = get_conn()
    p = ph()
    c = conn.cursor()
    res = []
    hoy = date.today()
    for i in range(meses-1,-1,-1):
        pd2 = (hoy.replace(day=1)-timedelta(days=30*i)).replace(day=1)
        ud = pd2.replace(day=31) if pd2.month==12 else pd2.replace(month=pd2.month+1)-timedelta(days=1)
        d,h = pd2.isoformat(),ud.isoformat()
        c.execute(f"SELECT COALESCE(SUM(monto),0) FROM ingresos WHERE pyme_id={p} AND fecha BETWEEN {p} AND {p}", (pyme_id,d,h))
        ing = c.fetchone()[0]
        c.execute(f"SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id={p} AND fecha BETWEEN {p} AND {p}", (pyme_id,d,h))
        gas = c.fetchone()[0]
        res.append({"mes":pd2.strftime("%b %Y"),"ingresos":round(float(ing),2),"gastos":round(float(gas),2),"ganancia":round(float(ing)-float(gas),2)})
    conn.close()
    return res
