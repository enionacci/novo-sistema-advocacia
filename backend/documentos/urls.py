from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, TagViewSet, DocumentoViewSet
from .views import salvar_documento_scanner, extrair_texto_pdf
from .views import merge_pdfs, split_pdf, compress_pdf, convert_images_to_pdf
from .views import pdf_to_images_view, extract_pdf_pages, insert_blank_page_view, rotate_pdf_pages_view
from .ai_views import (
    DocumentoAnaliseIAListCreateView,
    DocumentoAnaliseIADetailView,
    DocumentoAnaliseIAReprocessView,
    DocumentoOCRAsyncView,
    DocumentoOCRProgressView
)
from .anonymization_views import (
    anonymize_document,
    restore_document,
    list_anonymizations,
    anonymization_details,
    delete_anonymization,
    deanonymize_text,
    manual_anonymize,
    undo_manual_anonymize,
    suggest_type,
    list_manual_anonymizations,
    get_updated_text
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'', DocumentoViewSet, basename='documento')

urlpatterns = [
    # ✅ OCR ASSÍNCRONO - Para PDFs grandes/escaneados (processa em background)
    path('ocr-async/', DocumentoOCRAsyncView.as_view(), name='documento-ocr-async'),
    path('ocr-progress/<str:task_id>/', DocumentoOCRProgressView.as_view(), name='documento-ocr-progress'),

    # ✅ EXTRAÇÃO DE TEXTO SIMPLES - Para PDFs digitais (instantâneo)
    path('extrair-texto/', extrair_texto_pdf, name='documento-extrair-texto'),
    
    # Análises com IA
    path('analises/', DocumentoAnaliseIAListCreateView.as_view(), name='analises-list-create'),
    path('analises/<int:pk>/', DocumentoAnaliseIADetailView.as_view(), name='analises-detail'),
    path('analises/<int:pk>/reprocessar/', DocumentoAnaliseIAReprocessView.as_view(), name='analises-reprocess'),
    
    # Anonimização
    path('<int:documento_id>/anonymize/', anonymize_document, name='documento-anonymize'),
    path('<int:documento_id>/restore/', restore_document, name='documento-restore'),
    path('anonymizations/', list_anonymizations, name='anonymizations-list'),
    path('anonymizations/<int:anonimizacao_id>/', anonymization_details, name='anonymization-details'),
    path('anonymizations/<int:anonimizacao_id>/delete/', delete_anonymization, name='anonymization-delete'),
    path('anonymizations/<int:anonimizacao_id>/deanonymize/', deanonymize_text, name='deanonymize-text'),
    path('manual-anonymize/', manual_anonymize, name='manual-anonymize'),
    path('undo-manual-anonymize/', undo_manual_anonymize, name='undo-manual-anonymize'),
    path('suggest-type/', suggest_type, name='suggest-type'),
    path('anonymizations/<int:anonimizacao_id>/manual/', list_manual_anonymizations, name='list-manual-anonymizations'),
    path('anonymizations/<int:anonimizacao_id>/updated-text/', get_updated_text, name='get-updated-text'),
    
    # Scanner básico (salvar documento digitalizado)
    path('salvar-scanner/', salvar_documento_scanner, name='salvar-documento-scanner'),
    
    # Ferramentas de PDF
    path('pdf/merge/', merge_pdfs, name='pdf-merge'),
    path('pdf/split/', split_pdf, name='pdf-split'),
    path('pdf/compress/', compress_pdf, name='pdf-compress'),
    path('pdf/convert-image/', convert_images_to_pdf, name='pdf-convert-image'),
    path('pdf/to-images/', pdf_to_images_view, name='pdf-to-images'),
    path('pdf/extract-pages/', extract_pdf_pages, name='pdf-extract-pages'),
    path('pdf/insert-blank/', insert_blank_page_view, name='pdf-insert-blank'),
    path('pdf/rotate/', rotate_pdf_pages_view, name='pdf-rotate'),
    
    # ViewSets (deve vir por último)
    path('', include(router.urls)),
]