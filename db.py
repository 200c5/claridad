"""
Claridad — Módulo de base de datos
Todas las funciones para leer y escribir datos.
"""

import sqlite3
from datetime import date, timedelta
from typing import Optional

DB_PATH = "claridad.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder por nombre de columna
    return conn


# ─────────────────────────────────────
# PYMES
# ─────────────────────────────────────

def get_pymes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM pymes ORDER BY nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crear_pyme(nombre: str, rubro: str, moneda: str = "USD"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO pymes (nombre, rubro, moneda) VALUES (?, ?, ?)",
        (nombre, rubro, moneda)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────
# CATEGORÍAS
# ─────────────────────────────────────

def get_categorias(tipo: str):
    """tipo = 'gasto' o 'ingreso'"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM categorias WHERE tipo = ? ORDER BY nombre", (tipo,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────
# GASTOS
# ─────────────────────────────────────

def registrar_gasto(pyme_id: int, categoria_id: int, descripcion: str,
                    monto: float, fecha: str, es_fijo: bool = False, notas: str = ""):
    conn = get_conn()
    conn.execute(
        """INSERT INTO gastos (pyme_id, categoria_id, descripcion, monto, fecha, es_fijo, notas)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (pyme_id, categoria_id, descripcion, monto, fecha, int(es_fijo), notas)
    )
    conn.commit()
    conn.close()

def get_gastos(pyme_id: int, desde: str, hasta: str):
    conn = get_conn()
    rows = conn.execute(
        """SELECT g.*, c.nombre as categoria_nombre
           FROM gastos g
           LEFT JOIN categorias c ON g.categoria_id = c.id
           WHERE g.pyme_id = ? AND g.fecha BETWEEN ? AND ?
           ORDER BY g.fecha DESC""",
        (pyme_id, desde, hasta)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def eliminar_gasto(gasto_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────
# INGRESOS
# ─────────────────────────────────────

def registrar_ingreso(pyme_id: int, categoria_id: int, descripcion: str,
                      monto: float, fecha: str, cliente: str = "", notas: str = ""):
    conn = get_conn()
    conn.execute(
        """INSERT INTO ingresos (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (pyme_id, categoria_id, descripcion, monto, fecha, cliente, notas)
    )
    conn.commit()
    conn.close()

def get_ingresos(pyme_id: int, desde: str, hasta: str):
    conn = get_conn()
    rows = conn.execute(
        """SELECT i.*, c.nombre as categoria_nombre
           FROM ingresos i
           LEFT JOIN categorias c ON i.categoria_id = c.id
           WHERE i.pyme_id = ? AND i.fecha BETWEEN ? AND ?
           ORDER BY i.fecha DESC""",
        (pyme_id, desde, hasta)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def eliminar_ingreso(ingreso_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM ingresos WHERE id = ?", (ingreso_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────
# RESUMEN FINANCIERO (el corazón del dashboard)
# ─────────────────────────────────────

def get_resumen(pyme_id: int, desde: str, hasta: str) -> dict:
    conn = get_conn()

    total_ingresos = conn.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM ingresos WHERE pyme_id = ? AND fecha BETWEEN ? AND ?",
        (pyme_id, desde, hasta)
    ).fetchone()[0]

    total_gastos = conn.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE pyme_id = ? AND fecha BETWEEN ? AND ?",
        (pyme_id, desde, hasta)
    ).fetchone()[0]

    gastos_fijos = conn.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE pyme_id = ? AND fecha BETWEEN ? AND ? AND es_fijo = 1",
        (pyme_id, desde, hasta)
    ).fetchone()[0]

    gastos_variables = total_gastos - gastos_fijos
    ganancia = total_ingresos - total_gastos
    margen = (ganancia / total_ingresos * 100) if total_ingresos > 0 else 0

    # Gastos por categoría
    gastos_por_cat = conn.execute(
        """SELECT c.nombre, SUM(g.monto) as total
           FROM gastos g
           LEFT JOIN categorias c ON g.categoria_id = c.id
           WHERE g.pyme_id = ? AND g.fecha BETWEEN ? AND ?
           GROUP BY c.nombre ORDER BY total DESC""",
        (pyme_id, desde, hasta)
    ).fetchall()

    conn.close()

    return {
        "total_ingresos":   round(total_ingresos, 2),
        "total_gastos":     round(total_gastos, 2),
        "gastos_fijos":     round(gastos_fijos, 2),
        "gastos_variables": round(gastos_variables, 2),
        "ganancia":         round(ganancia, 2),
        "margen_pct":       round(margen, 1),
        "gastos_por_cat":   [dict(r) for r in gastos_por_cat],
    }


def get_evolucion_mensual(pyme_id: int, meses: int = 6) -> list:
    """Devuelve ingresos y gastos de los últimos N meses."""
    conn = get_conn()
    resultados = []
    hoy = date.today()

    for i in range(meses - 1, -1, -1):
        # Primer y último día del mes
        primer_dia = (hoy.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if primer_dia.month == 12:
            ultimo_dia = primer_dia.replace(day=31)
        else:
            ultimo_dia = primer_dia.replace(month=primer_dia.month + 1) - timedelta(days=1)

        desde = primer_dia.isoformat()
        hasta = ultimo_dia.isoformat()

        ing = conn.execute(
            "SELECT COALESCE(SUM(monto),0) FROM ingresos WHERE pyme_id=? AND fecha BETWEEN ? AND ?",
            (pyme_id, desde, hasta)
        ).fetchone()[0]

        gas = conn.execute(
            "SELECT COALESCE(SUM(monto),0) FROM gastos WHERE pyme_id=? AND fecha BETWEEN ? AND ?",
            (pyme_id, desde, hasta)
        ).fetchone()[0]

        resultados.append({
            "mes":       primer_dia.strftime("%b %Y"),
            "ingresos":  round(ing, 2),
            "gastos":    round(gas, 2),
            "ganancia":  round(ing - gas, 2),
        })

    conn.close()
    return resultados
