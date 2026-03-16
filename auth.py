"""
Claridad — Sistema de autenticación
Maneja registro, login y sesiones de usuarios.
"""

import sqlite3
import hashlib
import os

DB_PATH = "claridad.db"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_auth_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT UNIQUE NOT NULL,
            nombre     TEXT NOT NULL,
            password   TEXT NOT NULL,
            creado_en  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Relación usuario-pyme
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuario_pyme (
            usuario_id INTEGER NOT NULL,
            pyme_id    INTEGER NOT NULL,
            PRIMARY KEY (usuario_id, pyme_id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (pyme_id) REFERENCES pymes(id)
        )
    """)
    conn.commit()
    conn.close()

def registrar_usuario(email: str, nombre: str, password: str) -> tuple:
    """Retorna (True, mensaje) o (False, error)"""
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if "@" not in email:
        return False, "Email inválido."
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO usuarios (email, nombre, password) VALUES (?, ?, ?)",
            (email.lower().strip(), nombre.strip(), hash_password(password))
        )
        conn.commit()
        usuario_id = c.lastrowid
        conn.close()
        return True, usuario_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Ese email ya está registrado."

def login_usuario(email: str, password: str) -> tuple:
    """Retorna (True, usuario_dict) o (False, error)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, nombre, email FROM usuarios WHERE email=? AND password=?",
        (email.lower().strip(), hash_password(password))
    )
    row = c.fetchone()
    conn.close()
    if row:
        return True, {"id": row[0], "nombre": row[1], "email": row[2]}
    return False, "Email o contraseña incorrectos."

def get_pymes_usuario(usuario_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT p.* FROM pymes p
        JOIN usuario_pyme up ON p.id = up.pyme_id
        WHERE up.usuario_id = ?
        ORDER BY p.nombre
    """, (usuario_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crear_pyme_usuario(usuario_id: int, nombre: str, rubro: str, moneda: str = "USD") -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO pymes (nombre, rubro, moneda) VALUES (?, ?, ?)",
        (nombre, rubro, moneda)
    )
    pyme_id = c.lastrowid
    c.execute(
        "INSERT INTO usuario_pyme (usuario_id, pyme_id) VALUES (?, ?)",
        (usuario_id, pyme_id)
    )
    conn.commit()
    conn.close()
    return pyme_id
