import sqlite3
from datetime import date, timedelta
DB_PATH = "claridad.db"
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS pymes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, rubro TEXT, moneda TEXT DEFAULT 'USD', creado_en TEXT DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, tipo TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, pyme_id INTEGER NOT NULL, categoria_id INTEGER, descripcion TEXT, monto REAL NOT NULL, fecha TEXT NOT NULL, es_fijo INTEGER DEFAULT 0, notas TEXT, creado_en TEXT DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS ingresos (id INTEGER PRIMARY KEY AUTOINCREMENT, pyme_id INTEGER NOT NULL, categoria_id INTEGER, descripcion TEXT, monto REAL NOT NULL, fecha TEXT NOT NULL, cliente TEXT, notas TEXT, creado_en TEXT DEFAULT CURRENT_TIMESTAMP)")
    c.execute("SELECT COUNT(*) FROM categorias")
    if c.fetchone()[0] == 0:
        cats = [("Materias primas","gasto"),("Sueldos y personal","gasto"),("Alquiler","gasto"),("Servicios","gasto"),("Marketing","gasto"),("Transporte","gasto"),("Equipamiento","gasto"),("Impuestos","gasto"),("Otros gastos","gasto"),("Venta de productos","ingreso"),("Venta de servicios","ingreso"),("Cobro de factura","ingreso"),("Otros ingresos","ingreso")]
        c.executemany("INSERT INTO categorias (nombre, tipo) VALUES (?, ?)", cats)
    conn.commit()
    conn.close()
def get_pymes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM pymes ORDER BY nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]
def crear_pyme(nombre, rubro, moneda="USD"):
    conn = get_conn()
    conn.execute("INSERT INTO pymes (nombre, rubro, moneda) VALUES (?, ?, ?)", (nombre, rubro, moneda))
    conn.commit()
    conn.close()
def get_categorias(tipo):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM categorias WHERE tipo=? ORDER BY nombre", (tipo,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
def registrar_gasto(pyme_id, categoria_id, descripcion, monto, fecha, es_fijo=False, notas=""):
    conn = get_conn()
    conn.execute("INSERT INTO gastos (pyme_id, categoria_id, descripcion, monto, fecha, es_fijo, notas) VALUES (?,?,?,?,?,?,?)", (pyme_id, categoria_id, descripcion, monto, fecha, int(es_fijo), notas))
    conn.commit()
    conn.close()
def registrar_ingreso(pyme_id, categoria_id, descripcion, monto, fecha, cliente="", notas=""):
    conn = get_conn()
    conn.execute("INSERT INTO ingresos (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas) VALUES (?,?,?,?,?,?,?)", (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas))
    conn.commit()
    conn.close()
def get_gastos(pyme_id, desde, hasta):
    conn = get_conn()
    rows = conn.execute("SELECT g.*, c.nombre as categoria_nombre FROM gastos g LEFT JOIN categorias c ON g.categoria_id = c.id WHERE g.pyme_id=? AND g.fecha BETWEEN ? AND ? ORDER BY g.fecha DESC", (pyme_id, desde, hasta)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
def get_ingresos(pyme_id, desde, hasta):
    conn = get_conn()
    rows = conn.execute("SELECT i.*, c.nombre as categoria_nombre FROM ingresos i LEFT JOIN categorias c ON i.categoria_id = c.id WHERE i.pyme_id=? AND i.fecha BETWEEN ? AND ? ORDER BY i.fecha DESC", (pyme_id, desde, hasta)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
def eliminar_gasto(gasto_id):
    conn = get_conn()
    conn.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))
    conn.commit()
    conn.close()
def eliminar_ingreso(ingreso_id):
    conn = get_conn()
    conn.execute("DELETE FROM ingresos WHERE id=?", (ingreso_id,))
    conn.commit()
    conn.close()
def get_resumen(pyme_id, desde, hasta):
    conn = get_conn()
    c = conn.cursor()
    ti = c.execute("SELECT COALESCE(SUM(monto),0) FROM ingresos WHERE pyme_id=? AND fecha BETWEEN ? AND ?", (pyme_id, desde, hasta)).fetchone()[0]
    tg = c.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id=? AND fecha BETWEEN ? AND ?", (pyme_id, desde, hasta)).fetchone()[0]
    gf = c.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id=? AND fecha BETWEEN ? AND ? AND es_fijo=1", (pyme_id, desde, hasta)).fetchone()[0]
    gpc = c.execute("SELECT c.nombre, SUM(g.monto) as total FROM gastos g LEFT JOIN categorias c ON g.categoria_id = c.id WHERE g.pyme_id=? AND g.fecha BETWEEN ? AND ? GROUP BY c.nombre ORDER BY total DESC", (pyme_id, desde, hasta)).fetchall()
    conn.close()
    gan = ti - tg
    mar = (gan / ti * 100) if ti > 0 else 0
    return {"total_ingresos":round(float(ti),2),"total_gastos":round(float(tg),2),"gastos_fijos":round(float(gf),2),"gastos_variables":round(float(tg-gf),2),"ganancia":round(float(gan),2),"margen_pct":round(float(mar),1),"gastos_por_cat":[{"nombre":r[0],"total":r[1]} for r in gpc]}
def get_evolucion_mensual(pyme_id, meses=6):
    conn = get_conn()
    c = conn.cursor()
    res = []
    hoy = date.today()
    for i in range(meses-1,-1,-1):
        pd2 = (hoy.replace(day=1)-timedelta(days=30*i)).replace(day=1)
        ud = pd2.replace(day=31) if pd2.month==12 else pd2.replace(month=pd2.month+1)-timedelta(days=1)
        d,h = pd2.isoformat(),ud.isoformat()
        ing = c.execute("SELECT COALESCE(SUM(monto),0) FROM ingresos WHERE pyme_id=? AND fecha BETWEEN ? AND ?", (pyme_id,d,h)).fetchone()[0]
        gas = c.execute("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id=? AND fecha BETWEEN ? AND ?", (pyme_id,d,h)).fetchone()[0]
        res.append({"mes":pd2.strftime("%b %Y"),"ingresos":round(float(ing),2),"gastos":round(float(gas),2),"ganancia":round(float(ing-gas),2)})
    conn.close()
    return res