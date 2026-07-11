"""
Ferramentas de manipulação de PDF
- Juntar PDFs (Merge)
- Dividir PDF (Split)
- Compactar PDF
- Converter Imagem para PDF

Todas as funções usam bibliotecas já instaladas (pypdf, PyMuPDF, Pillow).
"""
import io
import zipfile
from typing import List, Tuple
from pypdf import PdfReader, PdfWriter
from PIL import Image


def merge_pdfs(arquivos_bytes: List[bytes]) -> bytes:
    """
    Junta múltiplos PDFs em um único arquivo.

    Args:
        arquivos_bytes: Lista de bytes de cada PDF

    Returns:
        Bytes do PDF mesclado
    """
    merger = PdfWriter()

    for pdf_bytes in arquivos_bytes:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        merger.append(reader)

    output = io.BytesIO()
    merger.write(output)
    merger.close()

    return output.getvalue()


def split_pdf(pdf_bytes: bytes, page_ranges: List[Tuple[int, int]]) -> List[bytes]:
    """
    Divide um PDF em múltiplos arquivos baseado em intervalos de páginas.

    Args:
        pdf_bytes: Bytes do PDF original
        page_ranges: Lista de tuplas (inicio, fim) - páginas são 1-indexed

    Returns:
        Lista de bytes, um para cada intervalo
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    resultados = []

    for start, end in page_ranges:
        # Valida intervalo
        start = max(1, min(start, total_pages))
        end = max(start, min(end, total_pages))

        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])

        output = io.BytesIO()
        writer.write(output)
        writer.close()
        resultados.append(output.getvalue())

    return resultados


def split_pdf_to_zip(pdf_bytes: bytes, page_ranges: List[Tuple[int, int]], filenames: List[str] = None) -> bytes:
    """
    Divide um PDF e retorna um ZIP com os arquivos.

    Args:
        pdf_bytes: Bytes do PDF original
        page_ranges: Lista de tuplas (inicio, fim)
        filenames: Lista de nomes para cada arquivo (opcional)

    Returns:
        Bytes do arquivo ZIP
    """
    partes = split_pdf(pdf_bytes, page_ranges)
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, parte in enumerate(partes):
            nome = filenames[i] if filenames and i < len(filenames) else f'parte_{i+1}.pdf'
            if not nome.endswith('.pdf'):
                nome += '.pdf'
            zf.writestr(nome, parte)
    
    return zip_buffer.getvalue()


def compress_pdf(pdf_bytes: bytes, quality: str = 'medium') -> bytes:
    """
    Compacta um PDF reduzindo o tamanho do arquivo.

    Args:
        pdf_bytes: Bytes do PDF original
        quality: 'low', 'medium', 'high'

    Returns:
        Bytes do PDF compactado
    """
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Configurações de compressão
    quality_settings = {
        'low': {'garbage': 4, 'deflate': True, 'clean': True},
        'medium': {'garbage': 3, 'deflate': True, 'clean': True},
        'high': {'garbage': 1, 'deflate': True},
    }

    settings = quality_settings.get(quality, quality_settings['medium'])

    output = io.BytesIO()
    doc.save(output, **settings)
    doc.close()

    return output.getvalue()


def images_to_pdf(imagens_bytes: List[bytes]) -> bytes:
    """
    Converte uma ou mais imagens em um PDF.

    Args:
        imagens_bytes: Lista de bytes de imagens (jpg, png, etc.)

    Returns:
        Bytes do PDF gerado
    """
    imagens = []
    for img_bytes in imagens_bytes:
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        imagens.append(img)

    output = io.BytesIO()
    if len(imagens) == 1:
        imagens[0].save(output, format='PDF')
    else:
        imagens[0].save(output, format='PDF', save_all=True, append_images=imagens[1:])

    return output.getvalue()


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[bytes]:
    """
    Converte cada página de um PDF em imagens PNG.

    Args:
        pdf_bytes: Bytes do PDF
        dpi: Resolução das imagens (padrão: 200)

    Returns:
        Lista de bytes de imagens PNG, uma por página
    """
    from pdf2image import convert_from_bytes
    from PIL import Image

    images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='png')
    resultados = []

    for img in images:
        output = io.BytesIO()
        img.save(output, format='PNG')
        resultados.append(output.getvalue())

    return resultados


def extract_pages(pdf_bytes: bytes, pages: List[int]) -> bytes:
    """
    Extrai páginas específicas de um PDF.

    Args:
        pdf_bytes: Bytes do PDF original
        pages: Lista de números de página (1-indexed) a extrair

    Returns:
        Bytes do novo PDF com apenas as páginas selecionadas
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total = len(reader.pages)
    writer = PdfWriter()

    for page_num in pages:
        if 1 <= page_num <= total:
            writer.add_page(reader.pages[page_num - 1])

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    return output.getvalue()


def insert_blank_page(pdf_bytes: bytes, position: int = None) -> bytes:
    """
    Insere uma página em branco no final (ou em posição específica) do PDF.

    Args:
        pdf_bytes: Bytes do PDF original
        position: Posição para inserir (1-indexed). Se None, insere no final.

    Returns:
        Bytes do PDF com a página em branco
    """
    from pypdf import PageObject

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    # Copia todas as páginas existentes
    for page in reader.pages:
        writer.add_page(page)

    # Cria página em branco (tamanho A4)
    blank_page = PageObject.create_blank_page(
        width=595.28,  # A4 width in points
        height=841.89  # A4 height in points
    )

    if position and 1 <= position <= len(reader.pages) + 1:
        # Insere na posição específica
        writer.pages.insert(position - 1, blank_page)
    else:
        # Adiciona no final
        writer.add_page(blank_page)

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    return output.getvalue()


def rotate_pdf_pages(pdf_bytes: bytes, rotation: int = 90, pages: List[int] = None) -> bytes:
    """
    Rotaciona páginas de um PDF.

    Args:
        pdf_bytes: Bytes do PDF original
        rotation: Graus de rotação (90, 180, 270)
        pages: Lista de páginas para rotacionar (1-indexed).
               Se None, rotaciona todas as páginas.

    Returns:
        Bytes do PDF com páginas rotacionadas
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        page_num = i + 1
        if pages is None or page_num in pages:
            page.rotate(rotation)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    return output.getvalue()
