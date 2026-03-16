import os
import hashlib
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

DB_PATH = "claridad.db"

def get_conn():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ph():
    return "%s" if USE_POSTGRES else "?"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_auth_tables():
    pass  # init_db en db.py ya crea las tablas de usuarios

def registrar_usuario(email, nombre, password):
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if "@" not in email:
        return False, "Email inválido."
    conn = get_conn()
    c = conn.cursor()
    p = ph()
    try:
        c.execute(f"INSERT INTO usuarios (email, nombre, password) VALUES ({p},{p},{p})", (email.lower().strip(), nombre.strip(), hash_password(password)))
        conn.commit()
        if USE_POSTGRES:
            c.execute("SELECT id FROM usuarios WHERE email=%s", (email.lower().strip(),))
        else:
            c.execute("SELECT id FROM usuarios WHERE email=?", (email.lower().strip(),))
        usuario_id = c.fetchone()[0]
        conn.close()
        return True, usuario_id
    except Exception as e:
        conn.close()
        if "unique" in str(e).lower() or "UNIQUE" in str(e):
            return False, "Ese email ya está registrado."
        return False, str(e)

def login_usuario(email, password):
    conn = get_conn()
    p = ph()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT id, nombre, email FROM usuarios WHERE email={p} AND password={p}", (email.lower().strip(), hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        r = dict(row)
        return True, {"id": r["id"], "nombre": r["nombre"], "email": r["email"]}
    return False, "Email o contraseña incorrectos."

def get_pymes_usuario(usuario_id):
    conn = get_conn()
    p = ph()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT p.* FROM pymes p JOIN usuario_pyme up ON p.id = up.pyme_id WHERE up.usuario_id={p} ORDER BY p.nombre", (usuario_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crear_pyme_usuario(usuario_id, nombre, rubro, moneda="USD"):
    conn = get_conn()
    p = ph()
    c = conn.cursor()
    c.execute(f"INSERT INTO pymes (nombre, rubro, moneda) VALUES ({p},{p},{p})", (nombre, rubro, moneda))
    if USE_POSTGRES:
        c.execute("SELECT id FROM pymes WHERE nombre=%s ORDER BY id DESC LIMIT 1", (nombre,))
    else:
        c.execute("SELECT last_insert_rowid()")
    pyme_id = c.fetchone()[0]
    c.execute(f"INSERT INTO usuario_pyme (usuario_id, pyme_id) VALUES ({p},{p})", (usuario_id, pyme_id))
    conn.commit()
    conn.close()
    return pyme_id


def get_todos_usuarios():
    conn = get_conn()
    p = ph()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        c = conn.cursor()
    c.execute("SELECT id, email, nombre, creado_en FROM usuarios ORDER BY creado_en DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats_usuario(usuario_id):
    conn = get_conn()
    p = ph()
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM pymes p JOIN usuario_pyme up ON p.id = up.pyme_id WHERE up.usuario_id={p}", (usuario_id,))
    pymes = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM gastos g JOIN pymes p ON g.pyme_id = p.id JOIN usuario_pyme up ON p.id = up.pyme_id WHERE up.usuario_id={p}", (usuario_id,))
    gastos = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM ingresos i JOIN pymes p ON i.pyme_id = p.id JOIN usuario_pyme up ON p.id = up.pyme_id WHERE up.usuario_id={p}", (usuario_id,))
    ingresos = c.fetchone()[0]
    conn.close()
    return {"pymes": pymes, "gastos": gastos, "ingresos": ingresos}
