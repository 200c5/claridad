"""
Claridad — Módulo de Benchmark del Sector
Datos basados en fuentes de la industria: Stripe, DoorDash, Vibetrace,
estudios de hostelería y retail para América Latina 2024-2025.
"""

BENCHMARKS = {
    "Gastronomía": {
        "margen_neto_min": 3,
        "margen_neto_max": 9,
        "margen_neto_promedio": 5.5,
        "margen_neto_bueno": 10,
        "gastos_fijos_pct": 45,
        "descripcion": "Restaurantes, cafés, bares y delivery",
        "insight_bajo": "Los restaurantes tienen márgenes ajustados (3-9%). Tu prioridad es reducir el costo de ingredientes (debe ser max 30% de los ingresos) y optimizar el personal.",
        "insight_bueno": "Estás por encima del promedio del sector gastronómico. El promedio regional es 5.5%. Mantenés una operación eficiente.",
        "insight_alto": "Excelente. Muy pocos restaurantes superan el 10% de margen neto. Tu modelo de negocio es muy eficiente.",
        "fuente": "DoorDash Industry Report 2024, Stripe Business Benchmarks 2024"
    },
    "Comercio / Retail": {
        "margen_neto_min": 1,
        "margen_neto_max": 5,
        "margen_neto_promedio": 3.0,
        "margen_neto_bueno": 6,
        "gastos_fijos_pct": 40,
        "descripcion": "Tiendas, comercios, ferreterías, almacenes",
        "insight_bajo": "El retail tiene márgenes muy ajustados (1-5%). Enfocate en rotación de stock y reducir merma. Cada punto de margen cuenta.",
        "insight_bueno": "Estás en la zona media del retail. El promedio regional es 3%. Para crecer, buscá productos con mayor margen o reducí gastos fijos.",
        "insight_alto": "Excelente para el sector. Los comercios que superan el 6% generalmente tienen productos exclusivos o muy bajo costo de alquiler.",
        "fuente": "Vibetrace Industry Benchmarks 2023, Stripe Resources 2024"
    },
    "Servicios profesionales": {
        "margen_neto_min": 15,
        "margen_neto_max": 35,
        "margen_neto_promedio": 22.0,
        "margen_neto_bueno": 25,
        "gastos_fijos_pct": 30,
        "descripcion": "Consultoras, agencias, estudios, freelancers",
        "insight_bajo": "Los servicios profesionales deberían tener márgenes de 15-35%. Si estás por debajo, revisá tu precio hora y los proyectos que aceptás.",
        "insight_bueno": "Buen margen para servicios. El promedio del sector es 22%. Podés seguir creciendo optimizando el tiempo dedicado a cada cliente.",
        "insight_alto": "Excelente. Estás en el top del sector de servicios. Tu precio y estructura de costos están muy bien calibrados.",
        "fuente": "Stripe Business Benchmarks 2024, DoorDash SMB Report"
    },
    "Alquileres temporarios": {
        "margen_neto_min": 20,
        "margen_neto_max": 45,
        "margen_neto_promedio": 30.0,
        "margen_neto_bueno": 35,
        "gastos_fijos_pct": 35,
        "descripcion": "Apartamentos, casas y propiedades en alquiler",
        "insight_bajo": "Los alquileres temporarios bien gestionados deberían tener 20-45% de margen. Revisá los gastos de mantenimiento y las comisiones.",
        "insight_bueno": "Margen saludable. El promedio del sector es 30%. Optimizá la ocupación en temporada baja para mejorar el resultado anual.",
        "insight_alto": "Excelente rendimiento. Estás aprovechando muy bien la propiedad. Considerá expandir si tenés oportunidad.",
        "fuente": "Estimación basada en informes de mercado inmobiliario Uruguay 2024"
    },
    "Salud": {
        "margen_neto_min": 5,
        "margen_neto_max": 15,
        "margen_neto_promedio": 8.0,
        "margen_neto_bueno": 12,
        "gastos_fijos_pct": 50,
        "descripcion": "Consultorios, clínicas, odontología, fisioterapia",
        "insight_bajo": "Los servicios de salud tienen altos costos fijos. Si estás por debajo del 5%, revisá la ocupación de turnos y los gastos administrativos.",
        "insight_bueno": "Margen razonable para el sector salud. El promedio es 8%. Optimizá la agenda para reducir turnos vacíos.",
        "insight_alto": "Muy buen margen para salud. Los consultorios que superan el 12% generalmente tienen alta ocupación y pocos intermediarios.",
        "fuente": "Stripe Resources 2024, estudios de gestión de consultorios"
    },
    "Indumentaria / Moda": {
        "margen_neto_min": 4,
        "margen_neto_max": 13,
        "margen_neto_promedio": 7.5,
        "margen_neto_bueno": 10,
        "gastos_fijos_pct": 38,
        "descripcion": "Marcas de ropa, boutiques, accesorios",
        "insight_bajo": "La indumentaria tiene márgenes variables. Si estás por debajo del 4%, revisá el costo de producción y las pérdidas por stock sin rotar.",
        "insight_bueno": "Margen correcto para moda. El promedio del sector es 7.5%. Para mejorar, reducí la merma y enfocate en los productos de mayor rotación.",
        "insight_alto": "Excelente para el sector. Las marcas con más del 10% generalmente tienen buena identidad de marca y baja dependencia de descuentos.",
        "fuente": "Vibetrace Industry Benchmarks 2023, Statista Latin America Fashion 2024"
    },
    "Otros": {
        "margen_neto_min": 5,
        "margen_neto_max": 20,
        "margen_neto_promedio": 10.0,
        "margen_neto_bueno": 12,
        "gastos_fijos_pct": 40,
        "descripcion": "Otros rubros y actividades",
        "insight_bajo": "Para la mayoría de los negocios, un margen menor al 7% es señal de alerta. Revisá tus principales gastos.",
        "insight_bueno": "Margen saludable. El promedio general de pymes es 10%. Seguí monitoreando tus costos.",
        "insight_alto": "Excelente margen. Estás por encima del promedio general de pymes de la región.",
        "fuente": "Stripe Business Benchmarks 2024, DoorDash SMB Industry Report"
    }
}

def get_benchmark(rubro: str) -> dict:
    """Retorna el benchmark para un rubro dado."""
    for key in BENCHMARKS:
        if key.lower() in (rubro or "").lower() or (rubro or "").lower() in key.lower():
            return {"rubro_benchmark": key, **BENCHMARKS[key]}
    return {"rubro_benchmark": "Otros", **BENCHMARKS["Otros"]}

def analizar_vs_sector(margen_actual: float, rubro: str) -> dict:
    """
    Compara el margen actual con el benchmark del sector.
    Retorna un diccionario con el análisis completo.
    """
    bench = get_benchmark(rubro)
    promedio = bench["margen_neto_promedio"]
    bueno    = bench["margen_neto_bueno"]
    minimo   = bench["margen_neto_min"]

    diferencia = margen_actual - promedio
    diferencia_abs = abs(diferencia)

    if margen_actual >= bueno:
        estado = "excelente"
        emoji  = "🏆"
        color  = "success"
        mensaje = bench["insight_alto"]
    elif margen_actual >= promedio:
        estado = "bueno"
        emoji  = "✅"
        color  = "success"
        mensaje = bench["insight_bueno"]
    elif margen_actual >= minimo:
        estado = "regular"
        emoji  = "⚠️"
        color  = "warning"
        mensaje = bench["insight_bajo"]
    else:
        estado = "bajo"
        emoji  = "🔴"
        color  = "error"
        mensaje = bench["insight_bajo"]

    if diferencia > 0:
        comparacion = f"Estás {diferencia_abs:.1f} puntos POR ENCIMA del promedio del sector ({promedio:.1f}%)"
    elif diferencia < 0:
        comparacion = f"Estás {diferencia_abs:.1f} puntos POR DEBAJO del promedio del sector ({promedio:.1f}%)"
    else:
        comparacion = f"Estás exactamente en el promedio del sector ({promedio:.1f}%)"

    return {
        "rubro_benchmark": bench["rubro_benchmark"],
        "margen_actual":   round(margen_actual, 1),
        "margen_promedio": promedio,
        "margen_minimo":   minimo,
        "margen_bueno":    bueno,
        "diferencia":      round(diferencia, 1),
        "estado":          estado,
        "emoji":           emoji,
        "color":           color,
        "comparacion":     comparacion,
        "mensaje":         mensaje,
        "fuente":          bench["fuente"],
        "gastos_fijos_pct_ideal": bench["gastos_fijos_pct"],
    }

def get_rubros_disponibles() -> list:
    return list(BENCHMARKS.keys())
