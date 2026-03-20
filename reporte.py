"""
Claridad — Generador de informes PDF
Genera un informe mensual profesional para el dueño de la pyme.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import date

VERDE       = HexColor("#1D9E75")
VERDE_CLARO = HexColor("#E1F5EE")
ROJO        = HexColor("#E24B4A")
ROJO_CLARO  = HexColor("#FAECE7")
AMARILLO    = HexColor("#BA7517")
AMARILLO_CL = HexColor("#FAEEDA")
GRIS        = HexColor("#666666")
GRIS_CLARO  = HexColor("#F5F5F5")
OSCURO      = HexColor("#1A1A1A")

def generar_informe_pdf(pyme_nombre: str, pyme_rubro: str,
                        periodo: str, resumen: dict,
                        gastos: list, ingresos: list) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Estilos personalizados ──────────────────────
    titulo_style = ParagraphStyle(
        "Titulo", parent=styles["Normal"],
        fontSize=28, fontName="Helvetica-Bold",
        textColor=VERDE, alignment=TA_LEFT, spaceAfter=4
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"],
        fontSize=12, fontName="Helvetica",
        textColor=GRIS, alignment=TA_LEFT, spaceAfter=2
    )
    seccion_style = ParagraphStyle(
        "Seccion", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=OSCURO, spaceBefore=16, spaceAfter=8
    )
    cuerpo_style = ParagraphStyle(
        "Cuerpo", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=OSCURO, spaceAfter=4, leading=14
    )
    verde_style = ParagraphStyle(
        "Verde", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=VERDE, spaceAfter=4
    )
    rojo_style = ParagraphStyle(
        "Rojo", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=ROJO, spaceAfter=4
    )

    # ── ENCABEZADO ─────────────────────────────────
    story.append(Paragraph("💚 Claridad", titulo_style))
    story.append(Paragraph("Tu negocio, en claro", subtitulo_style))
    story.append(HRFlowable(width="100%", thickness=2, color=VERDE, spaceAfter=12))

    story.append(Paragraph(f"<b>Informe financiero — {pyme_nombre}</b>", ParagraphStyle(
        "NombreEmpresa", parent=styles["Normal"],
        fontSize=18, fontName="Helvetica-Bold", textColor=OSCURO, spaceAfter=4
    )))
    story.append(Paragraph(f"Rubro: {pyme_rubro or 'No especificado'} &nbsp;&nbsp;|&nbsp;&nbsp; Período: {periodo}", subtitulo_style))
    story.append(Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", ParagraphStyle(
        "Fecha", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica", textColor=GRIS, spaceAfter=16
    )))

    # ── KPIs PRINCIPALES ──────────────────────────
    story.append(Paragraph("Resumen del período", seccion_style))

    gan      = resumen.get("ganancia", 0)
    margen   = resumen.get("margen_pct", 0)
    ing      = resumen.get("total_ingresos", 0)
    gas      = resumen.get("total_gastos", 0)
    gf       = resumen.get("gastos_fijos", 0)
    gv       = resumen.get("gastos_variables", 0)

    color_margen = VERDE if margen >= 30 else (AMARILLO if margen >= 10 else ROJO)
    bg_margen    = VERDE_CLARO if margen >= 30 else (AMARILLO_CL if margen >= 10 else ROJO_CLARO)

    kpis = Table([
        [
            Paragraph("<b>Ingresos</b>", ParagraphStyle("kl", parent=styles["Normal"], fontSize=9, textColor=GRIS, fontName="Helvetica")),
            Paragraph("<b>Gastos</b>", ParagraphStyle("kl", parent=styles["Normal"], fontSize=9, textColor=GRIS, fontName="Helvetica")),
            Paragraph("<b>Ganancia neta</b>", ParagraphStyle("kl", parent=styles["Normal"], fontSize=9, textColor=GRIS, fontName="Helvetica")),
            Paragraph("<b>Margen</b>", ParagraphStyle("kl", parent=styles["Normal"], fontSize=9, textColor=GRIS, fontName="Helvetica")),
        ],
        [
            Paragraph(f"<b>USD {ing:,.0f}</b>", ParagraphStyle("kv", parent=styles["Normal"], fontSize=20, textColor=OSCURO, fontName="Helvetica-Bold")),
            Paragraph(f"<b>USD {gas:,.0f}</b>", ParagraphStyle("kv", parent=styles["Normal"], fontSize=20, textColor=OSCURO, fontName="Helvetica-Bold")),
            Paragraph(f"<b>USD {gan:,.0f}</b>", ParagraphStyle("kv", parent=styles["Normal"], fontSize=20, textColor=VERDE if gan >= 0 else ROJO, fontName="Helvetica-Bold")),
            Paragraph(f"<b>{margen:.1f}%</b>", ParagraphStyle("kv", parent=styles["Normal"], fontSize=20, textColor=color_margen, fontName="Helvetica-Bold")),
        ]
    ], colWidths=["25%", "25%", "25%", "25%"])

    kpis.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRIS_CLARO),
        ("BACKGROUND", (3,0), (3,1), bg_margen),
        ("ROWBACKGROUNDS", (0,1), (-1,1), [white]),
        ("BOX", (0,0), (-1,-1), 1, HexColor("#DDDDDD")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, HexColor("#EEEEEE")),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(kpis)
    story.append(Spacer(1, 12))

    # Gastos fijos vs variables
    gf_row = Table([[
        Paragraph(f"Gastos fijos: <b>USD {gf:,.0f}</b>", cuerpo_style),
        Paragraph(f"Gastos variables: <b>USD {gv:,.0f}</b>", cuerpo_style),
    ]], colWidths=["50%", "50%"])
    story.append(gf_row)

    # ── ANÁLISIS AUTOMÁTICO ────────────────────────
    story.append(Paragraph("Análisis del período", seccion_style))

    if ing == 0:
        story.append(Paragraph("No hay datos registrados para este período.", cuerpo_style))
    else:
        if gan > 0:
            story.append(Paragraph(
                f"✅ <b>Estás ganando dinero.</b> Por cada USD 100 que entraron, te quedaron USD {margen:.0f} limpios.",
                verde_style
            ))
        elif gan == 0:
            story.append(Paragraph("⚠️ <b>Estás en cero.</b> Todo lo que entra lo gastás. No estás creciendo.", ParagraphStyle(
                "Amarillo", parent=styles["Normal"], fontSize=10, textColor=AMARILLO, spaceAfter=4
            )))
        else:
            story.append(Paragraph(
                f"❌ <b>Estás perdiendo plata.</b> Gastaste USD {abs(gan):,.0f} más de lo que entraste.",
                rojo_style
            ))

        pct_fijo = gf / gas * 100 if gas > 0 else 0
        if pct_fijo > 60:
            story.append(Paragraph(
                f"⚠️ <b>{pct_fijo:.0f}% de tus gastos son fijos.</b> Si las ventas bajan un mes, tenés poco margen de maniobra.",
                ParagraphStyle("Amarillo2", parent=styles["Normal"], fontSize=10, textColor=AMARILLO, spaceAfter=4)
            ))

        if margen >= 30:
            story.append(Paragraph("✅ Tu margen está en zona saludable (≥30%). Seguí así.", verde_style))
        elif margen >= 10:
            story.append(Paragraph(f"⚠️ Tu margen de {margen:.1f}% está por debajo del objetivo de 30%. Revisá tus costos o ajustá precios.", ParagraphStyle(
                "Amarillo3", parent=styles["Normal"], fontSize=10, textColor=AMARILLO, spaceAfter=4
            )))
        else:
            story.append(Paragraph(f"❌ Tu margen de {margen:.1f}% es muy bajo. Necesitás acción urgente — reducir gastos o aumentar precios.", rojo_style))

    # ── GASTOS POR CATEGORÍA ───────────────────────
    story.append(Paragraph("Gastos por categoría", seccion_style))

    gastos_por_cat = resumen.get("gastos_por_cat", [])
    if gastos_por_cat:
        cat_data = [["Categoría", "Monto", "% del total"]]
        for cat in gastos_por_cat:
            pct = cat["total"] / gas * 100 if gas > 0 else 0
            cat_data.append([
                cat["nombre"] or "Sin categoría",
                f"USD {cat['total']:,.0f}",
                f"{pct:.1f}%"
            ])

        cat_table = Table(cat_data, colWidths=["55%", "25%", "20%"])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
            ("BOX", (0,0), (-1,-1), 0.5, HexColor("#DDDDDD")),
            ("INNERGRID", (0,0), (-1,-1), 0.3, HexColor("#EEEEEE")),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ]))
        story.append(cat_table)
    else:
        story.append(Paragraph("No hay gastos registrados.", cuerpo_style))

    # ── ÚLTIMOS MOVIMIENTOS ────────────────────────
    story.append(Paragraph("Últimos ingresos", seccion_style))
    if ingresos:
        ing_data = [["Fecha", "Descripción", "Cliente", "Monto"]]
        for i in ingresos[:10]:
            ing_data.append([
                i.get("fecha",""),
                (i.get("descripcion","") or "")[:35],
                (i.get("cliente","") or "")[:20],
                f"USD {i.get('monto',0):,.0f}"
            ])
        ing_table = Table(ing_data, colWidths=["15%", "45%", "25%", "15%"])
        ing_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
            ("BOX", (0,0), (-1,-1), 0.5, HexColor("#DDDDDD")),
            ("INNERGRID", (0,0), (-1,-1), 0.3, HexColor("#EEEEEE")),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("ALIGN", (3,0), (3,-1), "RIGHT"),
        ]))
        story.append(ing_table)
    else:
        story.append(Paragraph("No hay ingresos registrados.", cuerpo_style))

    story.append(Paragraph("Últimos gastos", seccion_style))
    if gastos:
        gas_data = [["Fecha", "Descripción", "Categoría", "Monto"]]
        for g in gastos[:10]:
            gas_data.append([
                g.get("fecha",""),
                (g.get("descripcion","") or "")[:35],
                (g.get("categoria_nombre","") or "")[:20],
                f"USD {g.get('monto',0):,.0f}"
            ])
        gas_table = Table(gas_data, colWidths=["15%", "45%", "25%", "15%"])
        gas_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), OSCURO),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
            ("BOX", (0,0), (-1,-1), 0.5, HexColor("#DDDDDD")),
            ("INNERGRID", (0,0), (-1,-1), 0.3, HexColor("#EEEEEE")),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("ALIGN", (3,0), (3,-1), "RIGHT"),
        ]))
        story.append(gas_table)
    else:
        story.append(Paragraph("No hay gastos registrados.", cuerpo_style))

    # ── PIE DE PÁGINA ──────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#EEEEEE"), spaceAfter=8))
    story.append(Paragraph(
        "Generado automáticamente por <b>Claridad</b> · claridad-whjefvtmdwdgukhnwzcgsh.streamlit.app",
        ParagraphStyle("Pie", parent=styles["Normal"], fontSize=8, textColor=GRIS, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buffer.getvalue()
