"""
Serviço para processamento de OCR e Análise com IA
"""

import os
import io
import platform
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.core.files.base import ContentFile
from django.conf import settings
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from openai import OpenAI
# import fitz  # Removido import top-level para evitar crash
from .progress_service import progress_tracker

# EasyOCR foi removido para simplificar e reduzir consumo de memória.
# Para PDFs digitais, pypdf é suficiente e instantâneo.
# Para PDFs escaneados, Tesseract (já instalado) é usado como fallback.
EASYOCR_AVAILABLE = False

# Configuração do Tesseract para Windows
if platform.system() == 'Windows':
    # Atualizado com base na versão 5.5.0 da UB Mannheim
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\tesseract\tesseract.exe',  # Pasta personalizada
    ]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"✅ Tesseract encontrado em: {path}")
            # Verifica versão
            try:
                version = pytesseract.get_tesseract_version()
                print(f"📋 Versão do Tesseract: {version}")
            except:
                pass
            break
    else:
        print("⚠️ Tesseract não encontrado. Instale a versão 5.5.0 em: https://github.com/UB-Mannheim/tesseract/wiki")

# Configuração do Poppler para Windows e Linux
POPPLER_PATH = None
if platform.system() == 'Windows':
    possible_poppler_paths = [
        r'C:\poppler\poppler-24.08.0\Library\bin',
        r'C:\Program Files\poppler\Library\bin',
        r'C:\ProgramData\chocolatey\lib\poppler\tools\Library\bin',
    ]
    for path in possible_poppler_paths:
        if os.path.exists(path):
            POPPLER_PATH = path
            print(f"✅ Poppler encontrado em: {path}")
            break
    else:
        print("⚠️ Poppler não encontrado. PDFs não serão suportados para OCR.")
elif platform.system() == 'Linux':
    import shutil
    if shutil.which('pdftoppm'):
        POPPLER_PATH = None
        print("✅ Poppler encontrado no sistema Linux")
    else:
        print("⚠️ Poppler não encontrado no Linux. Instale: apt-get install poppler-utils")


def smart_text_reconstruction(texto_ocr: str) -> str:
    """
    Reconstrução inteligente de texto OCR quebrado
    """
    if not texto_ocr:
        return texto_ocr
    
    # Separa por páginas primeiro
    paginas = re.split(r'(--- Página \d+ ---)', texto_ocr)
    
    texto_final = []
    
    for i, secao in enumerate(paginas):
        if secao.startswith('--- Página'):
            # Mantém separador de página
            texto_final.append(f"\n\n{secao}\n")
            continue
        
        if not secao.strip():
            continue
        
        # Processa o conteúdo da página
        linhas = secao.strip().split('\n')
        linhas_processadas = []
        buffer_linha = ""
        
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            
            # Regras específicas para texto jurídico
            if (
                # Linha muito curta (provavelmente quebrada)
                len(linha) < 40 and
                # Não termina com pontuação final
                not linha.endswith(('.', '!', '?', ':')) and
                # Não é numeração ou artigo
                not re.match(r'^[IVX]+\.|^\d+\.|^Art\.|^Artigo', linha) and
                # Não é endereço/CEP
                not re.search(r'\d{5}-?\d{3}|CEP|SP|RJ|MG', linha) and
                # Não é CPF/CNPJ
                not re.search(r'\d{3}\.\d{3}\.\d{3}-?\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-?\d{2}', linha) and
                # Não é assinatura digital
                not 'assinado digitalmente' in linha.lower() and
                # Não é OAB
                not re.search(r'OAB|n[ºª°]\s*\d+', linha)
            ):
                # Adiciona ao buffer para juntar
                buffer_linha += " " + linha if buffer_linha else linha
            else:
                # Finaliza linha anterior se existir
                if buffer_linha:
                    linhas_processadas.append(buffer_linha.strip())
                    buffer_linha = ""
                
                # Adiciona linha atual
                linhas_processadas.append(linha)
        
        # Adiciona último buffer se existir
        if buffer_linha:
            linhas_processadas.append(buffer_linha.strip())
        
        # Junta as linhas processadas
        texto_pagina = '\n'.join(linhas_processadas)
        
        # Limpeza final
        texto_pagina = re.sub(r'\s+', ' ', texto_pagina)  # Remove espaços múltiplos
        texto_pagina = re.sub(r'\s*\n\s*', '\n', texto_pagina)  # Limpa quebras
        
        texto_final.append(texto_pagina)
    
    resultado = ''.join(texto_final)
    
    print(f"🔧 Texto reconstruído: {len(texto_ocr)} → {len(resultado)} caracteres")
    
    return resultado


def is_meaningful_text(text: str) -> bool:
    """
    Verifica se o texto é realmente significativo (não apenas símbolos/caracteres especiais)
    """
    if not text or len(text.strip()) < 20:
        return False
    
    # Remove espaços e quebras de linha
    clean_text = re.sub(r'\s+', ' ', text.strip())
    
    # Conta caracteres alfabéticos vs total
    alpha_chars = sum(1 for c in clean_text if c.isalpha())
    total_chars = len(clean_text)
    
    if total_chars == 0:
        return False
    
    # Pelo menos 60% deve ser texto alfabético
    alpha_ratio = alpha_chars / total_chars
    
    # Conta palavras reais (3+ caracteres alfabéticos)
    words = re.findall(r'[a-zA-ZàáâãéêíóôõúçÀÁÂÃÉÊÍÓÔÕÚÇ]{3,}', text)
    
    print(f"🔍 Análise de texto: {len(words)} palavras, {alpha_ratio:.2f} ratio alfabético")
    
    return len(words) >= 10 and alpha_ratio >= 0.6


def analyze_pdf_type_simple(arquivo_bytes: bytes) -> dict:
    """
    Análise MUITO mais agressiva para detectar PDFs escaneados
    """
    try:
        import fitz
        doc = fitz.open(stream=arquivo_bytes, filetype="pdf")
        
        total_pages = len(doc)
        has_meaningful_text = False
        has_images = False
        
        # Analisa apenas primeira página para ser mais rápido
        page = doc.load_page(0)
        
        # 1. Verifica texto
        text = page.get_text()
        if is_meaningful_text(text):
            has_meaningful_text = True
            print(f"✅ Texto significativo encontrado na primeira página")
        else:
            print(f"❌ Texto não significativo na primeira página: '{text[:100]}...'")
        
        # 2. Verifica imagens
        image_list = page.get_images()
        if image_list:
            has_images = True
            print(f"📸 {len(image_list)} imagem(ns) encontrada(s) na primeira página")
        
        doc.close()
        
        # LÓGICA SUPER SIMPLES E AGRESSIVA
        if not has_meaningful_text:
            # SEM texto significativo = ESCANEADO
            pdf_type = "escaneado"
            confidence = 0.95
            reason = "Sem texto significativo detectado"
        elif has_images and not has_meaningful_text:
            # Imagens sem texto = ESCANEADO  
            pdf_type = "escaneado"
            confidence = 0.9
            reason = "Imagens presentes sem texto significativo"
        elif has_meaningful_text and not has_images:
            # Texto sem imagens = GERADO
            pdf_type = "gerado"
            confidence = 0.9
            reason = "Texto significativo sem imagens"
        else:
            # DÚVIDA = ESCANEADO (conservador)
            pdf_type = "escaneado"
            confidence = 0.7
            reason = "Caso duvidoso - assumindo escaneado por segurança"
        
        print(f"🎯 DECISÃO: {pdf_type.upper()} (confiança: {confidence:.2f}) - {reason}")
        
        return {
            'type': pdf_type,
            'confidence': confidence,
            'reason': reason,
            'stats': {
                'total_pages': total_pages,
                'has_meaningful_text': has_meaningful_text,
                'has_images': has_images
            }
        }
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        # EM CASO DE ERRO = ESCANEADO (força OCR)
        return {
            'type': 'escaneado',
            'confidence': 0.8,
            'reason': f"Erro na análise - forçando OCR: {str(e)}",
            'stats': {}
        }


def extract_text_direct_method(arquivo_bytes: bytes, task_id: str) -> str:
    """Extração direta para PDFs gerados digitalmente"""
    from pypdf import PdfReader
    
    progress_tracker.update_progress(task_id, 0, "Extraindo texto diretamente...")
    
    pdf_reader = PdfReader(io.BytesIO(arquivo_bytes))
    texto_completo = []
    
    progress_tracker.set_total_pages(task_id, len(pdf_reader.pages))
    
    for i, page in enumerate(pdf_reader.pages):
        texto_pagina = page.extract_text()
        if texto_pagina and texto_pagina.strip():
            texto_completo.append(f"--- Página {i + 1} ---\n{texto_pagina}")
        progress_tracker.update_progress(task_id, i + 1)
    
    texto_final = "\n\n".join(texto_completo)
    progress_tracker.complete_progress(task_id, True)
    
    print(f"✅ Extração direta concluída: {len(texto_final)} caracteres")
    return texto_final


def extract_text_tesseract_fallback(arquivo_bytes: bytes, task_id: str) -> str:
    """Fallback usando Tesseract otimizado"""
    try:
        progress_tracker.update_progress(task_id, 0, "Convertendo PDF para imagens...")
        
        images = convert_from_bytes(
            arquivo_bytes,
            dpi=300,
            fmt='png',
            poppler_path=POPPLER_PATH if platform.system() == 'Windows' else None
        )

        total_paginas = len(images)
        progress_tracker.set_total_pages(task_id, total_paginas)
        texto_ocr = []
        
        # Cria instância do OCR
        ocr_service = OCRService()

        for i, image in enumerate(images):
            pagina_atual = i + 1
            progress_tracker.update_progress(
                task_id, 
                pagina_atual, 
                f"OCR Tesseract página {pagina_atual}/{total_paginas}"
            )
            
            # Converte para bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            texto = ocr_service.extract_text_from_image_tesseract(img_bytes)
            if texto.strip():
                texto_ocr.append(f"--- Página {i + 1} ---\n{texto}")

        texto_bruto = "\n\n".join(texto_ocr)
        
        # APLICA RECONSTRUÇÃO INTELIGENTE
        texto_final = smart_text_reconstruction(texto_bruto)
        
        progress_tracker.complete_progress(task_id, True)
        return texto_final
        
    except Exception as e:
        error_message = f"Erro no OCR Tesseract: {str(e)}"
        progress_tracker.complete_progress(task_id, False, error_message)
        raise Exception(error_message)


class OCRService:
    """
    Serviço para extração de texto de documentos (OCR)
    Usa Tesseract como método principal para PDFs escaneados.
    Para PDFs digitais, use pypdf (mais rápido) via extrair_texto_pdf().
    """
    
    def __init__(self):
        """Inicializa o serviço OCR"""
        pass
    
    def extract_text_from_image_tesseract(self, arquivo_bytes: bytes) -> str:
        """
        Extrai texto usando Tesseract otimizado (execução única para velocidade)
        """
        try:
            image = Image.open(io.BytesIO(arquivo_bytes))
            
            # Configuração única otimizada - executa apenas 1 vez para ser rápido
            config = '--psm 3 -c tessedit_ocr_engine_mode=1'
            
            resultado = pytesseract.image_to_string(
                image,
                lang='por',
                config=config
            )
            
            if not resultado or len(resultado.strip()) < 10:
                # Fallback rápido com configuração alternativa
                resultado = pytesseract.image_to_string(
                    image,
                    lang='por',
                    config='--psm 6'
                )
            
            # APLICA RECONSTRUÇÃO INTELIGENTE
            texto_final = smart_text_reconstruction(resultado)
            
            print(f"✅ Tesseract extraiu {len(texto_final)} caracteres")
            return texto_final
            
        except Exception as e:
            raise Exception(f"Erro no Tesseract: {str(e)}")
    
    def extract_text_from_image_hybrid(self, arquivo_bytes: bytes) -> str:
        """Extrai texto de imagem usando Tesseract"""
        try:
            return self.extract_text_from_image_tesseract(arquivo_bytes)
        except Exception as e:
            error_message = f"Erro no OCR da imagem: {str(e)}"
            raise Exception(error_message)
    
    @staticmethod
    def extract_text_from_pdf(arquivo_bytes: bytes, task_id: str = None) -> str:
        """
        Método SUPER SIMPLIFICADO que força OCR na menor dúvida
        """
        if not task_id:
            task_id = str(uuid.uuid4())

        # Análise simplificada e agressiva
        pdf_analysis = analyze_pdf_type_simple(arquivo_bytes)
        pdf_type = pdf_analysis['type']
        confidence = pdf_analysis['confidence']
        
        print(f"🎯 PDF detectado como: {pdf_type.upper()} (confiança: {confidence:.2f})")
        print(f"📋 Razão: {pdf_analysis['reason']}")
        
        progress_tracker.update_progress(
            task_id, 0, 
            f"PDF {pdf_type}: {pdf_analysis['reason']}"
        )
        
        try:
            # LÓGICA ULTRA SIMPLES: se não for GERADO com alta confiança, usa OCR
            if pdf_type == "gerado" and confidence >= 0.9:
                print("🔄 PDF claramente gerado - usando extração direta")
                return extract_text_direct_method(arquivo_bytes, task_id)
            else:
                # QUALQUER DÚVIDA = OCR
                print("🔄 PDF duvidoso ou escaneado - FORÇANDO OCR")
                progress_tracker.update_progress(task_id, 0, "Forçando OCR por segurança...")
                
                if platform.system() == 'Windows' and not POPPLER_PATH:
                    msg = "Poppler não configurado para OCR em PDF de imagem."
                    progress_tracker.complete_progress(task_id, False, msg)
                    raise Exception(msg)
                
                # Vai direto para OCR com Tesseract (já instalado no Docker)
                print("🚀 Usando Tesseract para OCR...")
                return extract_text_tesseract_fallback(arquivo_bytes, task_id)
                
        except Exception as e:
            error_message = f"Erro ao extrair texto do PDF: {str(e)}"
            progress_tracker.complete_progress(task_id, False, error_message)
            print(f"❌ {error_message}")
            raise Exception(error_message)

    @staticmethod
    def extract_text_from_region(arquivo_path: str, tipo_arquivo: str, task_id: str, region: dict) -> str:
        """
        Extrai texto de uma região específica de uma página de um PDF.
        """
        if tipo_arquivo.lower() != 'pdf':
            raise ValueError("A extração de região só é suportada para arquivos PDF.")

        try:
            progress_tracker.update_progress(task_id, 0, "Iniciando extração de região...")
            
            import fitz
            doc = fitz.open(arquivo_path)
            
            # Valida número da página
            page_num = region.get('pageNumber', 1) - 1
            if page_num < 0 or page_num >= doc.page_count:
                raise ValueError(f"Número de página inválido: {page_num + 1}")
            
            page = doc.load_page(page_num)
            
            # Dimensões da página no PDF
            pdf_page_rect = page.rect
            pdf_width = pdf_page_rect.width
            pdf_height = pdf_page_rect.height
            
            # Dimensões da página renderizada no frontend
            frontend_width = region.get('pageWidth')
            frontend_height = region.get('pageHeight')
            
            if not frontend_width or not frontend_height:
                raise ValueError("Dimensões da página do frontend não fornecidas.")

            # Escala as coordenadas do frontend para as do PDF
            x1 = (region['x1'] / frontend_width) * pdf_width
            y1 = (region['y1'] / frontend_height) * pdf_height
            x2 = (region['x2'] / frontend_width) * pdf_width
            y2 = (region['y2'] / frontend_height) * pdf_height
            
            # Cria o retângulo de corte (clip)
            clip_rect = fitz.Rect(x1, y1, x2, y2)
            
            progress_tracker.update_progress(task_id, 50, "Extraindo texto da área selecionada...")
            
            text = page.get_text("text", clip=clip_rect)
            
            progress_tracker.complete_progress(task_id, True)
            
            print(f"✅ Texto extraído da região: {len(text)} caracteres")
            return text

        except Exception as e:
            error_message = f"Erro ao extrair texto da região do PDF: {str(e)}"
            progress_tracker.complete_progress(task_id, False, error_message)
            print(f"❌ {error_message}")
            raise Exception(error_message)
    
    @staticmethod
    def extract_text_with_margins(arquivo_path: str, task_id: str, margins: dict) -> str:
        """
        Extrai texto de todas as páginas de um PDF, aplicando margens percentuais
        AGORA COM DETECÇÃO INTELIGENTE para usar OCR se necessário
        """
        try:
            progress_tracker.update_progress(task_id, 0, "Analisando tipo do PDF...")
            
            # LÊ O ARQUIVO PARA ANÁLISE
            with open(arquivo_path, 'rb') as f:
                arquivo_bytes = f.read()
            
            # USA A MESMA DETECÇÃO INTELIGENTE
            pdf_analysis = analyze_pdf_type_simple(arquivo_bytes)
            pdf_type = pdf_analysis['type']
            confidence = pdf_analysis['confidence']
            
            print(f"📋 PDF com margens detectado como: {pdf_type.upper()} (confiança: {confidence:.2f})")
            print(f"📋 Razão: {pdf_analysis['reason']}")
            
            progress_tracker.update_progress(task_id, 0, f"PDF {pdf_type} - aplicando margens")
            
            if pdf_type == "gerado" and confidence >= 0.9:
                # PDF GERADO - USA EXTRAÇÃO DIRETA COM MARGENS
                print("🔄 PDF gerado - usando extração direta com margens")
                return OCRService._extract_text_with_margins_direct(arquivo_path, task_id, margins)
            else:
                # PDF ESCANEADO/DUVIDOSO - USA OCR COM MARGENS
                print("🔄 PDF escaneado/duvidoso - usando OCR com margens")
                return OCRService._extract_text_with_margins_ocr(arquivo_bytes, task_id, margins)
                
        except Exception as e:
            error_message = f"Erro ao extrair texto com margens: {str(e)}"
            progress_tracker.complete_progress(task_id, False, error_message)
            print(f"❌ {error_message}")
            raise Exception(error_message)

    @staticmethod
    def _extract_text_with_margins_direct(arquivo_path: str, task_id: str, margins: dict) -> str:
        """
        Extração direta com margens (para PDFs gerados)
        """
        try:
            progress_tracker.update_progress(task_id, 0, "Extraindo texto diretamente com margens...")
            
            import fitz
            doc = fitz.open(arquivo_path)
            progress_tracker.set_total_pages(task_id, doc.page_count)

            textos_completos = []

            for i in range(doc.page_count):
                pagina_atual = i + 1
                progress_tracker.update_progress(task_id, pagina_atual, f"Processando página {pagina_atual}/{doc.page_count}")
                
                page = doc.load_page(i)
                pdf_page_rect = page.rect

                # Converte margens percentuais para coordenadas absolutas da página
                x1 = pdf_page_rect.width * (margins.get('left', 0) / 100)
                y1 = pdf_page_rect.height * (margins.get('top', 0) / 100)
                x2 = pdf_page_rect.width * (1 - (margins.get('right', 0) / 100))
                y2 = pdf_page_rect.height * (1 - (margins.get('bottom', 0) / 100))

                clip_rect = fitz.Rect(x1, y1, x2, y2)
                
                texto_pagina = page.get_text("text", clip=clip_rect)
                if texto_pagina.strip():
                    textos_completos.append(f"--- Página {pagina_atual} ---\n{texto_pagina}")

            doc.close()
            texto_final = "\n\n".join(textos_completos)
            progress_tracker.complete_progress(task_id, True)
            
            print(f"✅ Texto extraído diretamente com margens: {len(texto_final)} caracteres")
            return texto_final

        except Exception as e:
            error_message = f"Erro na extração direta com margens: {str(e)}"
            progress_tracker.complete_progress(task_id, False, error_message)
            raise Exception(error_message)

    @staticmethod
    def _extract_text_with_margins_ocr(arquivo_bytes: bytes, task_id: str, margins: dict) -> str:
        """
        OCR com margens aplicadas (para PDFs escaneados)
        """
        try:
            progress_tracker.update_progress(task_id, 0, "Convertendo PDF para imagens com margens...")
            
            if platform.system() == 'Windows' and not POPPLER_PATH:
                msg = "Poppler não configurado para OCR em PDF."
                progress_tracker.complete_progress(task_id, False, msg)
                raise Exception(msg)
            
            # Converte PDF para imagens
            images = convert_from_bytes(
                arquivo_bytes,
                dpi=300,
                fmt='png',
                poppler_path=POPPLER_PATH if platform.system() == 'Windows' else None
            )

            total_paginas = len(images)
            progress_tracker.set_total_pages(task_id, total_paginas)
            textos_ocr = []
            
            # Cria instância do OCR
            ocr_service = OCRService()

            for i, image in enumerate(images):
                pagina_atual = i + 1
                progress_tracker.update_progress(
                    task_id, 
                    pagina_atual, 
                    f"OCR com margens página {pagina_atual}/{total_paginas}"
                )
                
                # APLICA MARGENS NA IMAGEM
                width, height = image.size
                
                # Calcula coordenadas das margens
                left_margin = int(width * (margins.get('left', 0) / 100))
                top_margin = int(height * (margins.get('top', 0) / 100))
                right_margin = int(width * (1 - (margins.get('right', 0) / 100)))
                bottom_margin = int(height * (1 - (margins.get('bottom', 0) / 100)))
                
                # Corta a imagem aplicando as margens
                cropped_image = image.crop((left_margin, top_margin, right_margin, bottom_margin))
                
                # Converte imagem cortada para bytes
                img_byte_arr = io.BytesIO()
                cropped_image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                # Faz OCR na imagem cortada usando Tesseract
                texto = ocr_service.extract_text_from_image_tesseract(img_bytes)
                
                if texto.strip():
                    textos_ocr.append(f"--- Página {pagina_atual} ---\n{texto}")

            texto_bruto = "\n\n".join(textos_ocr)
            
            # APLICA RECONSTRUÇÃO INTELIGENTE FINAL
            texto_final = smart_text_reconstruction(texto_bruto)
            
            progress_tracker.complete_progress(task_id, True)
            
            print(f"✅ OCR com margens concluído: {len(texto_final)} caracteres")
            return texto_final
            
        except Exception as e:
            error_message = f"Erro no OCR com margens: {str(e)}"
            progress_tracker.complete_progress(task_id, False, error_message)
            raise Exception(error_message)

    @staticmethod
    def extract_text_from_image(arquivo_bytes: bytes) -> str:
        """
        Extrai texto de uma imagem usando método híbrido (EasyOCR + Tesseract)
        """
        ocr_service = OCRService()
        return ocr_service.extract_text_from_image_hybrid(arquivo_bytes)
    
    @staticmethod
    def extract_text(arquivo_path: str, tipo_arquivo: str, task_id: str = None) -> str:
        """
        Extrai texto de um arquivo (PDF ou imagem)
        """
        with open(arquivo_path, 'rb') as f:
            arquivo_bytes = f.read()
        
        if tipo_arquivo.lower() == 'pdf':
            return OCRService.extract_text_from_pdf(arquivo_bytes, task_id)
        elif tipo_arquivo.lower() in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
            return OCRService.extract_text_from_image(arquivo_bytes)
        else:
            raise ValueError(f"Tipo de arquivo não suportado para OCR: {tipo_arquivo}")


class AIAnalysisService:
    """
    Serviço para análise de documentos usando IA (OpenAI GPT)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o serviço de IA
        
        Args:
            api_key: Chave da API da OpenAI (opcional, usa do escritório se não fornecida)
        """
        self.api_key = api_key
        self.client = None
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
    
    def get_prompt_template(self, tipo_analise: str) -> str:
        """
        Retorna o template de prompt para cada tipo de análise
        
        Args:
            tipo_analise: Tipo da análise
            
        Returns:
            Template do prompt
        """
        templates = {
            'resumo': """
                Você é um assistente jurídico especializado. Analise o seguinte documento e forneça um resumo executivo detalhado.
                
                O resumo deve conter:
                - Tipo de documento
                - Principais pontos e informações relevantes
                - Partes envolvidas (se aplicável)
                - Valores e datas importantes
                - Conclusão/Síntese
                
                Documento:
                {texto}
            """,
            
            'extracao_dados': """
                Você é um assistente jurídico especializado em extração de dados. Analise o seguinte documento e extraia todas as informações estruturadas possíveis.
                
                Retorne um JSON com os seguintes campos (quando aplicável):
                - tipo_documento
                - numero_documento
                - data_emissao
                - data_vencimento
                - partes: [lista de pessoas/empresas envolvidas]
                - valores: [lista de valores monetários]
                - enderecos: [lista de endereços]
                - telefones: [lista de telefones]
                - emails: [lista de emails]
                - outras_informacoes_relevantes
                
                Documento:
                {texto}
                
                IMPORTANTE: Retorne APENAS o JSON, sem texto adicional.
            """,
            
            'juridico': """
                Você é um advogado especialista. Analise o seguinte documento sob a perspectiva jurídica.
                
                Forneça:
                1. **Natureza Jurídica**: Tipo de documento e sua finalidade legal
                2. **Análise de Cláusulas**: Pontos importantes e suas implicações
                3. **Riscos Identificados**: Possíveis problemas ou riscos legais
                4. **Recomendações**: Sugestões de ação ou pontos de atenção
                5. **Base Legal**: Leis e normas aplicáveis (se identificadas)
                
                Documento:
                {texto}
            """,
            
            'contrato': """
                Você é um advogado especialista em contratos. Analise o seguinte contrato detalhadamente.
                
                Forneça análise completa contendo:
                1. **Tipo de Contrato**: Classificação e natureza
                2. **Partes Contraentes**: Identificação das partes
                3. **Objeto do Contrato**: O que está sendo contratado
                4. **Obrigações das Partes**: Resumo das obrigações de cada parte
                5. **Prazo e Vigência**: Duração e renovação
                6. **Valores e Pagamento**: Condições financeiras
                7. **Cláusulas Importantes**: Destaque de cláusulas relevantes
                8. **Penalidades**: Multas, juros, rescisão
                9. **Pontos de Atenção**: Cláusulas que merecem atenção especial
                10. **Recomendações**: Sugestões de alteração ou negociação
                
                Contrato:
                {texto}
            """,
            
            'risco': """
                Você é um advogado especialista em análise de risco. Analise o seguinte documento para identificar possíveis riscos jurídicos e financeiros.
                
                Forneça:
                1. **Riscos Jurídicos**: Potenciais problemas legais
                2. **Riscos Financeiros**: Possíveis impactos financeiros
                3. **Riscos Contratuais**: Problemas nas cláusulas
                4. **Nível de Risco**: Baixo, Médio ou Alto (justifique)
                5. **Medidas Mitigadoras**: Ações para reduzir riscos
                6. **Recomendação Final**: Proceder, renegociar ou rejeitar
                
                Documento:
                {texto}
            """
        }
        
        return templates.get(tipo_analise, "{texto}")
    
    def analyze_document(
        self,
        texto: str,
        tipo_analise: str,
        prompt_personalizado: Optional[str] = None,
        modelo: str = 'gpt-4'
    ) -> Dict[str, Any]:
        """
        Analisa um documento usando IA
        
        Args:
            texto: Texto do documento
            tipo_analise: Tipo de análise
            prompt_personalizado: Prompt personalizado (opcional)
            modelo: Modelo da OpenAI a usar
            
        Returns:
            Dict com resultado, tokens e custo
        """
        if not self.client:
            raise Exception("API Key da OpenAI não configurada")
        
        inicio = datetime.now()
        
        try:
            # Monta o prompt
            if prompt_personalizado:
                prompt = f"{prompt_personalizado}\n\nDocumento:\n{texto}"
            else:
                prompt_template = self.get_prompt_template(tipo_analise)
                prompt = prompt_template.format(texto=texto)
            
            # Determina parâmetros baseado no modelo
            api_params = {}
            
            # Modelos que usam max_completion_tokens e não suportam temperature personalizado
            if any(model_name in modelo.lower() for model_name in ['gpt-5', 'o1']):
                api_params['max_completion_tokens'] = 4000
                # Não adiciona temperature (usa padrão 1)
            # Modelos que usam max_completion_tokens mas suportam temperature
            elif any(model_name in modelo.lower() for model_name in ['gpt-4.1', 'gpt-4o-2024']):
                api_params['max_completion_tokens'] = 4000
                api_params['temperature'] = 0.3
            # Modelos antigos (GPT-4, GPT-3.5) e padrão
            else:
                api_params['max_tokens'] = 4000
                api_params['temperature'] = 0.3
            
            # Chama a API da OpenAI
            print(f"🔧 Chamando OpenAI com modelo: {modelo}")
            print(f"🔧 Parâmetros: {api_params}")
            print(f"🔧 Tamanho do prompt: {len(prompt)} caracteres")
            print(f"🔧 Primeiros 500 chars do prompt: {prompt[:500]}")
            
            response = self.client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente jurídico especializado em análise de documentos legais."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                **api_params
            )
            
            # 🐛 DEBUG - Resposta completa
            print(f"📥 Resposta da API recebida")
            print(f"   - Choices: {len(response.choices)}")
            print(f"   - Finish reason: {response.choices[0].finish_reason}")
            print(f"   - Role: {response.choices[0].message.role}")
            print(f"   - Content type: {type(response.choices[0].message.content)}")
            print(f"   - Content is None: {response.choices[0].message.content is None}")
            print(f"   - Content repr: {repr(response.choices[0].message.content)}")
            
            # Extrai resposta
            resultado = response.choices[0].message.content
            tokens_usados = response.usage.total_tokens
            
            # Verificação adicional
            if not resultado:
                print(f"⚠️ ATENÇÃO: Resposta vazia da OpenAI!")
                print(f"   - Finish reason: {response.choices[0].finish_reason}")
                print(f"   - Model usado: {response.model}")
                print(f"   - Resposta completa: {response}")
                # Se vazio, tenta pegar de outro lugar ou lança erro
                if response.choices[0].finish_reason == 'length':
                    resultado = "[RESPOSTA INCOMPLETA] O resultado foi truncado devido ao limite de tokens."
                elif response.choices[0].finish_reason == 'content_filter':
                    raise Exception("OpenAI bloqueou a resposta devido ao filtro de conteúdo.")
                else:
                    raise Exception(f"OpenAI retornou resposta vazia. Finish reason: {response.choices[0].finish_reason}. Modelo: {response.model}")
            
            # 🐛 DEBUG
            print(f"🤖 IA Respondeu:")
            print(f"   - Modelo usado: {modelo}")
            print(f"   - Tokens: {tokens_usados}")
            print(f"   - Resultado (primeiros 200 chars): {resultado[:200] if resultado else 'VAZIO!'}")
            print(f"   - Tamanho total resultado: {len(resultado) if resultado else 0} caracteres")
            
            # Calcula custo estimado (valores aproximados GPT-4)
            custo_por_mil_tokens = 0.03  # USD
            custo_estimado = (tokens_usados / 1000) * custo_por_mil_tokens
            
            tempo_processamento = datetime.now() - inicio
            
            resultado_dict = {
                'resultado': resultado,
                'tokens_usados': tokens_usados,
                'custo_estimado': round(custo_estimado, 4),
                'tempo_processamento': tempo_processamento,
                'modelo_ia': modelo,
                'status': 'concluido'
            }
            
            print(f"📦 Retornando dict com resultado de {len(resultado_dict['resultado'])} chars")
            
            return resultado_dict
            
        except Exception as e:
            tempo_processamento = datetime.now() - inicio
            
            return {
                'resultado': '',
                'tokens_usados': 0,
                'custo_estimado': 0,
                'tempo_processamento': tempo_processamento,
                'modelo_ia': modelo,
                'status': 'erro',
                'mensagem_erro': str(e)
            }




import requests
import json
