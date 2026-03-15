"""
Claridad — Setup de base de datos
Corre esto UNA SOLA VEZ para crear la base de datos local.
Usa SQLite para que no necesites instalar nada extra.

Ejecutar: python setup_db.py
"""

import sqlite3
from datetime import datetime, date
import os

DB_PATH = "claridad.db"

def crear_base_de_datos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Tabla: pymes (empresas que usan el sistema) ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS pymes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            rubro       TEXT,
            moneda      TEXT DEFAULT 'USD',
            creado_en   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Tabla: categorias de gastos ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT NOT NULL,
            tipo    TEXT NOT NULL  -- 'gasto' o 'ingreso'
        )
    """)

    # ── Tabla: gastos ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pyme_id      INTEGER NOT NULL,
            categoria_id INTEGER,
            descripcion  TEXT,
            monto        REAL NOT NULL,
            fecha        TEXT NOT NULL,
            es_fijo      INTEGER DEFAULT 0,  -- 1 = fijo, 0 = variable
            notas        TEXT,
            creado_en    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pyme_id) REFERENCES pymes(id),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    # ── Tabla: ingresos ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS ingresos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pyme_id      INTEGER NOT NULL,
            categoria_id INTEGER,
            descripcion  TEXT,
            monto        REAL NOT NULL,
            fecha        TEXT NOT NULL,
            cliente      TEXT,
            notas        TEXT,
            creado_en    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pyme_id) REFERENCES pymes(id),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    # ── Datos de ejemplo: categorías ──
    categorias_gastos = [
        ("Materias primas", "gasto"),
        ("Sueldos y personal", "gasto"),
        ("Alquiler", "gasto"),
        ("Servicios (luz, agua, internet)", "gasto"),
        ("Marketing y publicidad", "gasto"),
        ("Transporte y logística", "gasto"),
        ("Equipamiento", "gasto"),
        ("Impuestos y tasas", "gasto"),
        ("Otros gastos", "gasto"),
    ]
    categorias_ingresos = [
        ("Venta de productos", "ingreso"),
        ("Venta de servicios", "ingreso"),
        ("Cobro de factura", "ingreso"),
        ("Otros ingresos", "ingreso"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO categorias (nombre, tipo) VALUES (?, ?)",
        categorias_gastos + categorias_ingresos
    )

    # ── Pyme de ejemplo ──
    c.execute("""
        INSERT OR IGNORE INTO pymes (id, nombre, rubro, moneda)
        VALUES (1, 'Mi Empresa', 'Servicios', 'USD')
    """)

    # ── Datos de ejemplo para ver el dashboard en acción ──
    hoy = date.today().isoformat()
    gastos_ejemplo = [
        (1, 1, "Compra materiales",       350.0, hoy, 0),
        (1, 2, "Sueldo empleado marzo",  1200.0, hoy, 1),
        (1, 3, "Alquiler local",          800.0, hoy, 1),
        (1, 4, "Internet y teléfono",      80.0, hoy, 1),
    ]
    ingresos_ejemplo = [
        (1, 10, "Venta semana 1", "Cliente A", 2800.0, hoy),
        (1, 10, "Venta semana 2", "Cliente B", 3100.0, hoy),
        (1, 11, "Servicio consultoría", "Cliente C", 1500.0, hoy),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO gastos (pyme_id, categoria_id, descripcion, monto, fecha, es_fijo) VALUES (?,?,?,?,?,?)",
        gastos_ejemplo
    )
    c.executemany(
        "INSERT OR IGNORE INTO ingresos (pyme_id, categoria_id, descripcion, cliente, monto, fecha) VALUES (?,?,?,?,?,?)",
        ingresos_ejemplo
    )

    conn.commit()
    conn.close()
    print(f"✅ Base de datos creada: {DB_PATH}")
    print(f"   Tablas: pymes, categorias, gastos, ingresos")
    print(f"   Datos de ejemplo cargados.")

if __name__ == "__main__":
    crear_base_de_datos()
