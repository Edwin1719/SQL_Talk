"""
SQLTalk-AI: Asistente Inteligente para Consultas SQL
Transforma consultas en lenguaje natural en SQL con análisis empresarial inteligente
"""

from setuptools import setup, find_packages
import pathlib

# Directorio actual
HERE = pathlib.Path(__file__).parent

# README del proyecto
README = (HERE / "README.md").read_text(encoding="utf-8")

# Versión del proyecto
VERSION = "1.0.0"

# Dependencias del requirements.txt
def get_requirements():
    """Lee requirements.txt y retorna lista de dependencias"""
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = []
        for line in f:
            line = line.strip()
            # Ignorar comentarios y líneas vacías
            if line and not line.startswith('#'):
                requirements.append(line)
        return requirements

setup(
    name="sqltalk-ai",
    version=VERSION,
    description="🤖 Asistente Inteligente para Consultas SQL con IA",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Edwin1719/SQL_Talk",
    author="Edwin Quintero Alzate",
    author_email="egqa1975@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "sql", "ai", "chatbot", "database", "natural-language",
        "business-intelligence", "data-analysis", "streamlit",
        "openai", "gpt", "langchain", "visualization"
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=8.2.0",
            "black>=24.4.0",
            "flake8>=7.0.0",
            "mypy>=1.10.0",
            "pre-commit>=3.7.0",
        ],
        "test": [
            "pytest>=8.2.0",
            "pytest-cov>=5.0.0",
            "pytest-mock>=3.14.0",
        ],
        "docs": [
            "sphinx>=7.3.0",
            "sphinx-rtd-theme>=2.0.0",
            "myst-parser>=3.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "sqltalk-cli=scripts.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/Edwin1719/SQL_Talk/issues",
        "Source": "https://github.com/Edwin1719/SQL_Talk",
        "Documentation": "https://github.com/Edwin1719/SQL_Talk/wiki",
        "Funding": "https://github.com/sponsors/Edwin1719",
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    zip_safe=False,
)