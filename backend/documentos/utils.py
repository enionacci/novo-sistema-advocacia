import io
import os
from django.core.files.base import ContentFile

def compress_pdf(file_input):
    """
    Comprime um arquivo PDF usando PyMuPDF (fitz).
    
    Args:
        file_input: O objeto de arquivo (FileField ou similar)
        
    Returns:
        ContentFile: O arquivo comprimido pronto para ser salvo no Django
    """
    try:
        import fitz  # PyMuPDF - Importação lazy para evitar crash no boot se falhar
        
        # Lê o conteúdo do arquivo para a memória
        file_content = file_input.read()
        
        # Abre o PDF com PyMuPDF
        doc = fitz.open(stream=file_content, filetype="pdf")
        
        # Cria um buffer para o arquivo comprimido
        output_buffer = io.BytesIO()
        
        # Salva com compressão (deflate=True, garbage=4 para máxima limpeza)
        doc.save(
            output_buffer,
            garbage=4,
            deflate=True,
            clean=True
        )
        
        # Obtém o conteúdo comprimido
        compressed_content = output_buffer.getvalue()
        
        # Fecha o documento
        doc.close()
        output_buffer.close()
        
        # Retorna como ContentFile do Django, mantendo o nome original
        return ContentFile(compressed_content, name=file_input.name)
        
    except ImportError:
        print("⚠️ PyMuPDF (fitz) não instalado ou com erro. Pulando compressão.")
        file_input.seek(0)
        return file_input
    except Exception as e:
        print(f"Erro ao comprimir PDF: {e}")
        # Em caso de erro, retorna o arquivo original (resetando o ponteiro)
        file_input.seek(0)
        return file_input
