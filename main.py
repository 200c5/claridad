from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import hashlib
from db import init_db, get_conn, ph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ─── MODELOS ───────────────────────────────
class LoginBody(BaseModel):
    email: str
    password: str

class RegistroBody(BaseModel):
    nombre: str
    email: str
    password: str

class PymeBody(BaseModel):
    nombre: str
    rubro: Optional[str] = ""

class GastoBody(BaseModel):
    pyme_id: int
    categoria_id: int
    descripcion: str
    monto: float
    fecha: str
    es_fijo: bool = False
    notas: Optional[str] = ""

class IngresoBody(BaseModel):
    pyme_id: int
    categoria_id: int
    descripcion: str
    monto: float
    fecha: str
    cliente: Optional[str] = ""
    notas: Optional[str] = ""

# ─── HELPERS ───────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ─── AUTH ──────────────────────────────────
@app.post("/login")
def login(body: LoginBody):
    conn = get_conn()
    p = ph()
    if hasattr(conn, 'cursor'):
        from db import USE_POSTGRES
        if USE_POSTGRES:
            import psycopg2.extras
            c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            c = conn.cursor()
    c.execute(
        f"SELECT id, nombre, email FROM usuarios WHERE email={p} AND password={p}",
        (body.email.lower().strip(), hash_password(body.password))
    )
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos.")
    r = dict(row)
    return {"id": r["id"], "nombre": r["nombre"], "email": r["email"]}

@app.post("/registro")
def registro(body: RegistroBody):
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres.")
    conn = get_conn()
    p = ph()
    c = conn.cursor()
    try:
        c.execute(
            f"INSERT INTO usuarios (email, nombre, password) VALUES ({p},{p},{p})",
            (body.email.lower().strip(), body.nombre.strip(), hash_password(body.password))
        )
        conn.commit()
        from db import USE_POSTGRES
        if USE_POSTGRES:
            c.execute("SELECT id FROM usuarios WHERE email=%s", (body.email.lower().strip(),))
        else:
            c.execute("SELECT last_insert_rowid()")
        uid = c.fetchone()[0]
        conn.close()
        return {"id": uid, "nombre": body.nombre, "email": body.email}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail="Ese email ya está registrado.")

# ─── PYMES ─────────────────────────────────
@app.get("/pymes")
def get_pymes_usuario(usuario_id: int):
    conn = get_conn()
    p = ph()
    from db import USE_POSTGRES
    if USE_POSTGRES:
        import psycopg2.extras
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(
        f"SELECT p.* FROM pymes p JOIN usuario_pyme up ON p.id = up.pyme_id WHERE up.usuario_id={p} ORDER BY p.nombre",
        (usuario_id,)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/pymes")
def crear_pyme(body: PymeBody, usuario_id: int):
    conn = get_conn()
    p = ph()
    c = conn.cursor()
    c.execute(f"INSERT INTO pymes (nombre, rubro) VALUES ({p},{p})", (body.nombre, body.rubro))
    conn.commit()
    from db import USE_POSTGRES
    if USE_POSTGRES:
        c.execute("SELECT id FROM pymes WHERE nombre=%s ORDER BY id DESC LIMIT 1", (body.nombre,))
    else:
        c.execute("SELECT last_insert_rowid()")
    pyme_id = c.fetchone()[0]
    c.execute(f"INSERT INTO usuario_pyme (usuario_id, pyme_id) VALUES ({p},{p})", (usuario_id, pyme_id))
    conn.commit()
    conn.close()
    return {"id": pyme_id, "nombre": body.nombre}

# ─── CATEGORÍAS ────────────────────────────
@app.get("/categorias")
def get_categorias(tipo: str):
    conn = get_conn()
    p = ph()
    from db import USE_POSTGRES
    if USE_POSTGRES:
        import psycopg2.extras
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT * FROM categorias WHERE tipo={p} ORDER BY nombre", (tipo,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── GASTOS ────────────────────────────────
@app.post("/gastos")
def registrar_gasto(body: GastoBody):
    conn = get_conn()
    p = ph()
    c = conn.cursor()
    c.execute(
        f"INSERT INTO gastos (pyme_id, categoria_id, descripcion, monto, fecha, es_fijo, notas) VALUES ({p},{p},{p},{p},{p},{p},{p})",
        (body.pyme_id, body.categoria_id, body.descripcion, body.monto, body.fecha, int(body.es_fijo), body.notas)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/gastos/{pyme_id}")
def get_gastos(pyme_id: int, desde: str, hasta: str):
    conn = get_conn()
    p = ph()
    from db import USE_POSTGRES
    if USE_POSTGRES:
        import psycopg2.extras
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(
        f"SELECT g.*, c.nombre as categoria_nombre FROM gastos g LEFT JOIN categorias c ON g.categoria_id = c.id WHERE g.pyme_id={p} AND g.fecha BETWEEN {p} AND {p} ORDER BY g.fecha DESC",
        (pyme_id, desde, hasta)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── INGRESOS ──────────────────────────────
@app.post("/ingresos")
def registrar_ingreso(body: IngresoBody):
    conn = get_conn()
    p = ph()
    c = conn.cursor()
    c.execute(
        f"INSERT INTO ingresos (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas) VALUES ({p},{p},{p},{p},{p},{p},{p})",
        (body.pyme_id, body.categoria_id, body.descripcion, body.monto, body.fecha, body.cliente, body.notas)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/ingresos/{pyme_id}")
def get_ingresos(pyme_id: int, desde: str, hasta: str):
    conn = get_conn()
    p = ph()
    from db import USE_POSTGRES
    if USE_POSTGRES:
        import psycopg2.extras
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(
        f"SELECT i.*, c.nombre as categoria_nombre FROM ingresos i LEFT JOIN categorias c ON i.categoria_id = c.id WHERE i.pyme_id={p} AND i.fecha BETWEEN {p} AND {p} ORDER BY i.fecha DESC",
        (pyme_id, desde, hasta)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── RESUMEN ───────────────────────────────
@app.get("/resumen/{pyme_id}")
def get_resumen(pyme_id: int, desde: str, hasta: str):
    from db import get_resumen as db_resumen
    return db_resumen(pyme_id, desde, hasta)