# Master Lead Finder

**Master Lead Finder** es una herramienta profesional B2B diseñada para detectar oportunidades comerciales analizando sitios web públicos. Permite transformar listas de URLs o dominios en leads enriquecidos con datos de contacto, puntuación de calidad y análisis de oportunidad de negocio.

## 🚀 Funcionalidades Principales

- **Análisis de URLs Públicas:** Extrae automáticamente nombre de empresa, emails genéricos, teléfonos y redes sociales de cualquier sitio web.
- **Importación Masiva:** Procesa listas de dominios desde archivos TXT o CSV para generar leads a gran escala.
- **Inteligencia Comercial:** Calcula automáticamente el **Lead Score** (completitud de datos) y el **Nivel de Oportunidad** (necesidad potencial de servicios digitales).
- **Enriquecimiento de Datos:** Mejora la información de los leads mediante reglas de negocio para identificar puntos de contacto débiles o falta de presencia digital.
- **Gestión y Filtros:** Interfaz avanzada para segmentar leads por sector, ciudad, calidad o etiquetas de oportunidad.
- **Exportación Profesional:** Genera informes detallados en Excel con hojas de resumen y análisis técnico, listos para CRM o equipos de prospección.
- **Limpieza de Datos:** Función para reiniciar la base de datos de leads de forma segura.

## 🛠️ Stack Técnico

- **Backend:** Python 3.10+ con [FastAPI](https://fastapi.tiangolo.com/)
- **Base de Datos:** SQLite con [SQLModel](https://sqlmodel.tiangolo.com/) (ORM)
- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript, Jinja2
- **Análisis Web:** BeautifulSoup4 y Requests
- **Informes:** openpyxl para generación de Excel

## 📂 Estructura del Proyecto

```text
scraping/
├── app/
│   ├── routes/          # Endpoints de la API (leads, análisis, exportación)
│   ├── services/        # Lógica de negocio (url_analyzer, enrichment, exporters)
│   ├── static/          # Archivos CSS y JavaScript
│   ├── templates/       # Plantillas HTML con Jinja2
│   ├── database.py      # Configuración de SQLite
│   ├── main.py          # Punto de entrada de la aplicación
│   ├── models.py        # Modelos de datos SQLModel
│   └── schemas.py       # Esquemas de validación Pydantic
├── exports/             # Carpeta de salida para informes generados
├── requirements.txt     # Dependencias del proyecto
└── README.md            # Documentación
```

## ⚙️ Instalación (Windows)

1. **Crear entorno virtual:**
   ```powershell
   python -m venv venv
   ```

2. **Activar entorno virtual:**
   ```powershell
   .\venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

## 🖥️ Ejecución

Inicia el servidor con:
```powershell
uvicorn app.main:app --reload
```
La aplicación estará disponible en [http://127.0.0.1:8000](http://127.0.0.1:8000).

*Nota: La base de datos `leads.db` se crea automáticamente en el primer arranque.*

## 📖 Guía de Uso

1. **Analizar URLs:** Pega una o varias URLs en el formulario de la página principal para un análisis rápido.
2. **Importar Archivos:** Sube un archivo `.txt` o `.csv` con un dominio por línea.
3. **Exportar:** Utiliza el botón "Exportar Excel" para obtener el informe profesional descargable.
4. **Limpiar:** Si deseas borrar todos los resultados, usa el botón "Limpiar leads" en la sección de acciones rápidas.

## ⚖️ Uso Ético y Legal

Esta herramienta ha sido desarrollada bajo principios de responsabilidad B2B:
- **Datos Públicos:** Solo procesa información accesible abiertamente en internet.
- **No Spam:** Diseñada para identificación de oportunidades, no para automatización de comunicaciones no deseadas.
- **Privacidad:** No se trabajan ni almacenan datos personales privados; la herramienta se centra exclusivamente en datos de contacto públicos de empresas y negocios.

---
Desarrollado para profesionales de ventas y crecimiento B2B.
