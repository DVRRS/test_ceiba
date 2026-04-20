#!/bin/bash
# Script para limpiar archivos temporales y cache del proyecto

echo "🧹 Limpiando proyecto..."

# Limpiar cache de Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null
find . -name "*.pyd" -delete 2>/dev/null

# Limpiar logs si existen
rm -f *.log 2>/dev/null

echo "✅ Limpieza completada"
echo ""
echo "Archivos eliminados:"
echo "  - __pycache__/"
echo "  - .pytest_cache/"
echo "  - *.pyc, *.pyo, *.pyd"
echo "  - *.log"
