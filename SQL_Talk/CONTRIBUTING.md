# 🤝 Contribuyendo a SQLTalk-AI

¡Gracias por tu interés en contribuir a SQLTalk-AI! Este documento te guiará a través del proceso de contribución.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Puedo Contribuir?](#cómo-puedo-contribuir)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Guías de Estilo](#guías-de-estilo)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Mejoras](#sugerir-mejoras)

## 📜 Código de Conducta

Este proyecto adhiere a un código de conducta. Al participar, se espera que mantengas este código. Por favor reporta comportamientos inaceptables.

**Principios básicos:**
- **Respeto**: Trata a todos con cortesía y profesionalismo
- **Inclusión**: Bienvenimos contribuciones de desarrolladores de todos los niveles
- **Colaboración**: Trabajamos juntos para hacer el proyecto mejor
- **Constructividad**: Las críticas deben ser constructivas y específicas

## 🛠️ ¿Cómo Puedo Contribuir?

### 🐛 Reportando Bugs

Si encuentras un bug, por favor:

1. **Busca** en los issues existentes para ver si ya fue reportado
2. **Crea un nuevo issue** con:
   - Título descriptivo y conciso
   - Descripción detallada del problema
   - Pasos para reproducir el bug
   - Comportamiento esperado vs comportamiento actual
   - Screenshots si es aplicable
   - Información del entorno (OS, Python version, etc.)

### ✨ Sugiriendo Mejoras

Para sugerir nuevas características:

1. **Abre un issue** con la etiqueta "enhancement"
2. **Describe claramente**:
   - ¿Qué problema resuelve la mejora?
   - ¿Cómo beneficiaría a los usuarios?
   - ¿Tienes alguna idea de implementación?

### 🔧 Contribuciones de Código

#### Tipos de Contribuciones Bienvenidas:

- **Corrección de bugs**
- **Nuevas características**
- **Mejoras en la documentación**
- **Optimizaciones de rendimiento**
- **Tests adicionales**
- **Soporte para nuevas bases de datos**

## 🚀 Configuración del Entorno de Desarrollo

### 1. Fork y Clona

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/tu-usuario/SQL_Talk.git
cd SQL_Talk

# Agrega el repositorio original como upstream
git remote add upstream https://github.com/Edwin1719/SQL_Talk.git
```

### 2. Configurar Entorno

```bash
# Crear entorno virtual
python -m venv sqltalk-dev
source sqltalk-dev/bin/activate  # En Windows: sqltalk-dev\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar dependencias de desarrollo
pip install pytest black flake8 mypy pre-commit
```

### 3. Configurar Pre-commit Hooks

```bash
pre-commit install
```

### 4. Configurar Variables de Entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales de API
```

### 5. Verificar Instalación

```bash
# Ejecutar tests
pytest

# Ejecutar la aplicación
streamlit run app_sql.py
```

## 📤 Proceso de Pull Request

### 1. Crear Rama de Feature

```bash
# Asegúrate de estar en main y actualizado
git checkout main
git pull upstream main

# Crea una nueva rama
git checkout -b feature/mi-nueva-caracteristica
# o
git checkout -b bugfix/arreglar-problema-x
```

### 2. Hacer Cambios

- **Escribe código** siguiendo las guías de estilo
- **Agrega tests** para nueva funcionalidad
- **Actualiza documentación** si es necesario
- **Commit frecuentemente** con mensajes descriptivos

### 3. Testing

```bash
# Ejecutar todos los tests
pytest

# Verificar cobertura
pytest --cov=.

# Linting y formato
black .
flake8 .
mypy .
```

### 4. Enviar Pull Request

```bash
# Push a tu fork
git push origin feature/mi-nueva-caracteristica
```

Luego crea el PR en GitHub con:

- **Título descriptivo**
- **Descripción detallada** de los cambios
- **Referencias** a issues relacionados
- **Screenshots** si aplica
- **Checklist** de verificación

### 5. Checklist del Pull Request

- [ ] Los tests pasan
- [ ] El código sigue las guías de estilo
- [ ] Se agregó documentación
- [ ] Se actualizó el CHANGELOG si es necesario
- [ ] Se probó manualmente la funcionalidad

## 🎨 Guías de Estilo

### Python

- **Sigue PEP 8** para el estilo de código
- **Usa Black** para formateo automático
- **Líneas máximo 88 caracteres**
- **Type hints** en todas las funciones nuevas

```python
def mi_funcion(parametro: str, opcional: Optional[int] = None) -> bool:
    """
    Descripción breve de la función
    
    Args:
        parametro: Descripción del parámetro
        opcional: Parámetro opcional
        
    Returns:
        Descripción del valor de retorno
    """
    pass
```

### Commits

Usa **Conventional Commits**:

```
feat: agregar soporte para Oracle DB
fix: corregir parsing de consultas complejas
docs: actualizar README con nuevos ejemplos
test: agregar tests para visualization_utils
refactor: mejorar estructura del IntelligentAssistant
```

### Documentación

- **Docstrings en español** para funciones públicas
- **Comentarios claros** en código complejo
- **README actualizado** con nuevas características
- **Ejemplos prácticos** en la documentación

## 🧪 Testing

### Escribir Tests

```python
def test_consulta_sql_exitosa():
    """Test que verifica consulta SQL exitosa"""
    # Arrange
    mock_db_chain = Mock()
    mock_engine = Mock()
    
    # Act
    resultado = consulta(mock_db_chain, mock_engine, "test query")
    
    # Assert
    assert resultado is not None
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_sql_agent_utils.py

# Con verbose
pytest -v

# Con cobertura
pytest --cov=. --cov-report=html
```

## 🐛 Reportar Bugs

### Template de Bug Report

```markdown
**Descripción del Bug**
Descripción clara y concisa del problema.

**Pasos para Reproducir**
1. Ve a '...'
2. Haz click en '....'
3. Scroll down to '....'
4. Ver error

**Comportamiento Esperado**
Lo que esperabas que pasara.

**Screenshots**
Si aplica, agrega screenshots.

**Entorno:**
 - OS: [e.g. Windows 10, macOS, Ubuntu]
 - Python Version: [e.g. 3.11]
 - SQLTalk Version: [e.g. 1.0.0]

**Contexto Adicional**
Cualquier otro contexto sobre el problema.
```

## 💡 Sugerir Mejoras

### Template de Feature Request

```markdown
**¿Tu solicitud está relacionada con un problema?**
Descripción clara del problema. Ej. "Estoy frustrado cuando [...]"

**Describe la solución que te gustaría**
Descripción clara de lo que quieres que pase.

**Describe alternativas consideradas**
Descripción de soluciones alternativas que consideraste.

**Contexto adicional**
Contexto adicional o screenshots sobre la solicitud.
```

## 🏷️ Labels de Issues

- `bug` - Algo no está funcionando
- `enhancement` - Nueva característica o solicitud
- `documentation` - Mejoras en documentación
- `good first issue` - Buenos para nuevos contribuidores
- `help wanted` - Ayuda extra es bienvenida
- `question` - Pregunta adicional sobre el proyecto

## 🎉 Reconocimiento

Todos los contribuidores serán reconocidos en el README del proyecto. ¡Tu trabajo es valioso y apreciado!

## 📞 ¿Necesitas Ayuda?

Si tienes preguntas sobre el proceso de contribución:

- **Abre un issue** con la etiqueta "question"
- **Contacta al mantenedor**: egqa1975@gmail.com
- **Únete a las discusiones** en GitHub Discussions

---

¡Gracias por hacer SQLTalk-AI mejor! 🚀