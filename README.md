# Claridad — Tu negocio, en claro

MVP semana 1-2. Dashboard financiero para pymes.

## Instalación (5 minutos)

### 1. Instalar dependencias
```bash
pip install streamlit sqlalchemy pandas plotly
```

### 2. Crear la base de datos
```bash
python setup_db.py
```
Esto crea el archivo `claridad.db` con datos de ejemplo.

### 3. Correr la app
```bash
streamlit run app.py
```
Se abre automáticamente en `http://localhost:8501`

---

## Qué hace este MVP

| Módulo | Qué hace |
|--------|----------|
| Dashboard | Muestra ingresos, gastos, ganancia y margen del período |
| Registrar | Formulario para cargar gastos e ingresos |
| Historial | Tabla con todos los movimientos, opción de eliminar |
| Evolución | Gráfico de los últimos 6 meses |

## Estructura de archivos

```
claridad/
├── app.py          ← App principal (Streamlit)
├── db.py           ← Todas las funciones de base de datos
├── setup_db.py     ← Crea la base de datos (correr una sola vez)
├── claridad.db     ← Se genera automáticamente
└── README.md
```

## Próximos pasos (semana 3-4)

- [ ] Escaneo de tickets con OCR (Google Vision API)
- [ ] Alertas automáticas por WhatsApp o email
- [ ] Asistente IA con Claude API
- [ ] Multi-usuario con login
- [ ] Deploy en la nube (Railway o Render)

## Stack

- **Frontend:** Streamlit
- **Backend:** Python puro
- **Base de datos:** SQLite (local) → migrar a PostgreSQL/Supabase al deployar
- **Gráficos:** Plotly
