# 🤖 SQLTalk-AI: Asistente Inteligente para Consultas SQL

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-red.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/powered%20by-OpenAI-green.svg)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Transforma consultas en lenguaje natural en SQL con análisis empresarial inteligente y visualizaciones automáticas**

![SQLTalk Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=SQLTalk-AI+Demo)

## ✨ Características Principales

### 🧠 **Inteligencia Artificial Avanzada**
- **Natural Language Processing** para convertir preguntas a SQL
- **Asistente IA con GPT-4** para análisis empresarial profundo
- **Detección automática** de tendencias, anomalías y patrones
- **Generación de insights** accionables para toma de decisiones

### 🗄️ **Soporte Multi-Base de Datos**
- **SQL Server** - Autenticación Windows integrada
- **PostgreSQL** - Soporte completo con SSL
- **MySQL** - Compatible con todas las versiones
- **SQLite** - Para prototipado y desarrollo

### 📊 **Visualizaciones Inteligentes**
- **Gráficos automáticos** basados en el tipo de datos
- **Visualizaciones interactivas** con Plotly
- **Gráficos personalizables** por el usuario
- **Estadísticas descriptivas** automáticas

### 🔍 **Análisis Empresarial**
- **Contexto empresarial** automático (ventas, productos, clientes)
- **Métricas KPI** predefinidas
- **Sugerencias de consultas** de seguimiento
- **Memoria de sesión** para análisis continuado

## 🚀 Instalación Rápida

### Prerrequisitos
- Python 3.8 o superior
- OpenAI API Key
- Drivers de base de datos (según tu motor)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Edwin1719/SQL_Talk.git
cd SQL_Talk
```

### 2. Crear Entorno Virtual
```bash
# Con conda (recomendado)
conda create -n sqltalk python=3.11
conda activate sqltalk

# O con venv
python -m venv sqltalk
source sqltalk/bin/activate  # Linux/Mac
# o
sqltalk\Scripts\activate     # Windows
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus credenciales
nano .env
```

### 5. Ejecutar la Aplicación
```bash
streamlit run app_sql.py
```

La aplicación se abrirá en `http://localhost:8501`

## 📖 Guía de Uso

### Conexión a Base de Datos

#### SQL Server (Recomendado para Windows)
- **Autenticación Windows**: Deja los campos vacíos para detección automática
- **Servidor personalizado**: `servidor\instancia` o IP
- **Base de datos**: Especifica o usa `master` por defecto

#### PostgreSQL/MySQL
```bash
Host: localhost
Puerto: 5432 (PostgreSQL) / 3306 (MySQL)
Usuario: tu_usuario
Contraseña: tu_contraseña
Base de datos: nombre_db
```

#### SQLite
```bash
Ruta: /ruta/a/tu/archivo.db
```

### Ejemplos de Consultas

#### 📈 **Análisis de Ventas**
```
"¿Cuáles fueron las ventas totales por producto el mes pasado?"
"Muéstrame el top 10 de clientes por ingresos"
"¿Cómo han evolucionado las ventas en los últimos 6 meses?"
```

#### 👥 **Análisis de Clientes**
```
"¿Qué clientes no han comprado en los últimos 90 días?"
"¿Cuál es la segmentación de clientes por región?"
"¿Quiénes son los clientes más rentables?"
```

#### 📦 **Análisis de Inventario**
```
"¿Qué productos tienen stock por debajo del mínimo?"
"¿Cuál es la rotación de inventario por categoría?"
"Muéstrame los productos con menor movimiento"
```

## 🎯 Casos de Uso Reales

### 💼 **Para Analistas de Negocio**
- Consultas ad-hoc sin conocimiento SQL
- Análisis exploratorio rápido
- Generación de reportes ejecutivos

### 👨‍💼 **Para Gerentes y Directores**
- Insights empresariales inmediatos
- Monitoreo de KPIs en tiempo real
- Análisis de tendencias y patrones

### 🏢 **Para Equipos de TI**
- Prototipado rápido de consultas
- Validación de datos
- Auditorías automatizadas

## 🔧 Arquitectura del Sistema

```
📦 SQLTalk-AI/
├── 🎨 app_sql.py              # Interfaz Streamlit principal
├── 🧠 intelligent_assistant.py # Motor de IA y análisis
├── 🔌 sql_agent_utils.py      # Conectores de base de datos
├── 📊 visualization_utils.py   # Utilidades de visualización
├── 📋 requirements.txt        # Dependencias del proyecto
└── 📖 README.md              # Este archivo
```

### Componentes Principales

#### 🤖 **IntelligentAssistant**
- Análisis de contexto empresarial
- Detección de patrones y anomalías
- Generación de insights con GPT-4
- Sugerencias de consultas de seguimiento

#### 🔍 **SQL Agent Utils**
- Conexión multi-motor de BD
- Limpieza y validación de consultas SQL
- Manejo robusto de errores
- Optimización de queries

#### 📈 **Visualization Utils**
- Detección automática del mejor gráfico
- Parsing inteligente de respuestas texto
- Gráficos interactivos con Plotly
- Estadísticas descriptivas

## 🛠️ Configuración Avanzada

### Variables de Entorno

```bash
# OpenAI Configuration
OPENAI_API_KEY=tu_clave_openai_aqui

# SQL Server (opcional para autenticación Windows)
SERVER_NAME=servidor\instancia
DATABASE_NAME=nombre_base_datos

# Logging
LOG_LEVEL=INFO
LOG_FILE=sqltalk.log

# UI Configuration
STREAMLIT_THEME=dark
MAX_ROWS_DISPLAY=1000
```

### Personalización del Asistente IA

```python
# En intelligent_assistant.py
assistant = IntelligentAssistant(
    model_name='gpt-4',  # o 'gpt-3.5-turbo' para mayor velocidad
    temperature=0.1,     # Creatividad vs Precisión
)
```

## 🧪 Testing y Desarrollo

### Ejecutar Tests
```bash
# Tests unitarios
python -m pytest tests/

# Tests de integración
python -m pytest tests/integration/

# Coverage
python -m pytest --cov=. tests/
```

### Desarrollo Local
```bash
# Modo debug
streamlit run app_sql.py --logger.level=debug

# Hot reload
streamlit run app_sql.py --server.runOnSave=true
```

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Por favor:

1. **Fork** el proyecto
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Guías de Contribución
- Sigue PEP 8 para el estilo de código
- Añade tests para nuevas funcionalidades
- Actualiza la documentación
- Mantén compatibilidad hacia atrás

## 📊 Roadmap

### 🎯 **Próximas Características**
- [ ] **Soporte para Oracle y DB2**
- [ ] **Exportación a Excel/PDF**
- [ ] **Dashboards persistentes**
- [ ] **Alertas automáticas**
- [ ] **API REST**
- [ ] **Autenticación multi-usuario**

### 🚀 **En Desarrollo**
- [ ] **Docker containerization**
- [ ] **CI/CD pipeline**
- [ ] **Documentación API**
- [ ] **Tests automatizados**

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## ⚠️ Disclaimer

Esta herramienta es para fines **educativos y profesionales**. Siempre valida los resultados antes de tomar decisiones empresariales críticas. No nos hacemos responsables por decisiones basadas únicamente en los insights generados.

## 🙏 Reconocimientos

- **OpenAI** por los modelos GPT-4 y GPT-3.5
- **Streamlit** por el framework de UI
- **Plotly** por las visualizaciones interactivas
- **LangChain** por las utilidades de LLM

## 📞 Contacto y Soporte

**Desarrollador:** Edwin Quintero Alzate  
**Email:** egqa1975@gmail.com  
**GitHub:** [@Edwin1719](https://github.com/Edwin1719)  
**LinkedIn:** [edwinquintero0329](https://www.linkedin.com/in/edwinquintero0329/)

---

### 📈 **¿Te gusta el proyecto?** 
¡Dale una ⭐ en GitHub y compártelo con tu equipo!

**[🚀 Demo en Vivo](https://sqltalk-ai.streamlit.app/)** | **[📚 Documentación](https://github.com/Edwin1719/SQL_Talk/wiki)** | **[🐛 Reportar Bug](https://github.com/Edwin1719/SQL_Talk/issues)**