"""Teste rápido para verificar detecção de páginas escaneadas"""
import sys
import os

# Adiciona o diretório backend ao path e muda para ele
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import fitz
from documentos.ai_service import is_page_scanned

pdf_path = os.path.join(os.path.dirname(__file__), 'ilovepdf_merged (1).pdf')
doc = fitz.open(pdf_path)
print(f"Total de páginas: {len(doc)}")
print()

for i in range(len(doc)):
    page = doc.load_page(i)
    text = page.get_text().strip()
    images = page.get_images()
    resultado = "ESCANEADA" if is_page_scanned(page) else "DIGITAL"
    print(f"Página {i+1}: {resultado} | texto: {len(text)} chars | imagens: {len(images)}")

doc.close()
