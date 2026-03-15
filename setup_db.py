"""
Claridad — Setup de base de datos
Corre esto UNA SOLA VEZ para crear la base de datos local.

Ejecutar: python setup_db.py
"""

import sqlite3

DB_PATH = "claridad.db"

def crear_base_de_datos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS pymes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            rubro       TEXT,
            moneda      TEXT DEFAULT 'USD',
            creado_en   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT NOT NULL,
            tipo    TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pyme_id      INTEGER NOT NULL,
            categoria_id INTEGER,
            descripcion  TEXT,
            monto        REAL NOT NULL,
            fecha        TEXT NOT NULL,
            es_fijo      INTEGER DEFAULT 0,
            notas        TEXT,
            creado_en    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pyme_id) REFERENCES pymes(id),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

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
    c.executemany(
        "INSERT OR IGNORE INTO categorias (nombre, tipo) VALUES (?, ?)",
        categorias
    )

    conn.commit()
    conn.close()
    print(f"✅ Base de datos creada: {DB_PATH}")
    print(f"   Tablas: pymes, categorias, gastos, ingresos")
    print(f"   Lista para usar — sin datos de ejemplo.")

if __name__ == "__main__":
    crear_base_de_datos()
