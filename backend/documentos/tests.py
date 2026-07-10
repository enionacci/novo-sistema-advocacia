from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from .models import Documento
from escritorios.models import Escritorio
from clientes.models import Cliente
from unittest.mock import patch, MagicMock
import io
import fitz

User = get_user_model()

class DocumentoCompressionTests(TestCase):
    def setUp(self):
        # Setup básico
        self.user = User.objects.create_user(username='testuser', password='password')
        self.escritorio = Escritorio.objects.create(nome='Escritório Teste')
        self.cliente = Cliente.objects.create(
            escritorio=self.escritorio,
            nome_completo='Cliente Teste',
            email='cliente@teste.com'
        )

    def create_dummy_pdf(self, size_bytes=1000):
        """Cria um PDF válido com tamanho aproximado"""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Teste de Compressão " * 10)
        
        # Para aumentar o tamanho, podemos adicionar metadados ou streams, 
        # mas para o teste de trigger, vamos usar o tamanho do arquivo reportado pelo Django
        # e um conteúdo PDF válido mínimo.
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Se precisarmos de um arquivo "fisicamente" grande mas válido, seria custoso gerar.
        # Vamos confiar no mock para o teste de trigger baseando-se no size do FieldFile.
        return pdf_bytes

    @patch('documentos.utils.compress_pdf')
    def test_compression_trigger_large_pdf(self, mock_compress):
        """Testa se a compressão é chamada para PDFs > 5MB"""
        
        # Configura o mock para retornar um arquivo simulado
        mock_return = SimpleUploadedFile("compressed.pdf", b"%PDF-1.4 compressed", content_type="application/pdf")
        mock_compress.return_value = mock_return

        # Cria um arquivo que o Django vai achar que tem 6MB
        large_content = b"%PDF-1.4 " + b"0" * (5 * 1024 * 1024 + 100) # > 5MB
        uploaded_file = SimpleUploadedFile(
            "large_doc.pdf",
            large_content,
            content_type="application/pdf"
        )

        doc = Documento(
            escritorio=self.escritorio,
            cliente=self.cliente,
            titulo="Documento Grande",
            arquivo=uploaded_file,
            usuario_upload=self.user
        )
        
        # Salva
        doc.save()
        
        # Verifica se compress_pdf foi chamado
        mock_compress.assert_called_once()

    @patch('documentos.utils.compress_pdf')
    def test_no_compression_small_pdf(self, mock_compress):
        """Testa se a compressão NÃO é chamada para PDFs < 5MB"""
        
        small_content = b"%PDF-1.4 " + b"0" * 1000 # Pequeno
        uploaded_file = SimpleUploadedFile(
            "small_doc.pdf",
            small_content,
            content_type="application/pdf"
        )

        doc = Documento(
            escritorio=self.escritorio,
            cliente=self.cliente,
            titulo="Documento Pequeno",
            arquivo=uploaded_file,
            usuario_upload=self.user
        )
        
        doc.save()
        
        mock_compress.assert_not_called()

    @patch('documentos.utils.compress_pdf')
    def test_no_compression_non_pdf(self, mock_compress):
        """Testa se a compressão NÃO é chamada para arquivos não-PDF mesmo grandes"""
        
        large_content = b"TEXT " + b"0" * (6 * 1024 * 1024) # > 6MB
        uploaded_file = SimpleUploadedFile(
            "large_doc.txt",
            large_content,
            content_type="text/plain"
        )

        doc = Documento(
            escritorio=self.escritorio,
            cliente=self.cliente,
            titulo="Texto Grande",
            arquivo=uploaded_file,
            usuario_upload=self.user
        )
        
        doc.save()
        
        mock_compress.assert_not_called()

    def test_utils_compress_pdf_validity(self):
        """Testa se a função utilitária consegue processar um PDF real sem erro"""
        from .utils import compress_pdf
        
        # Cria um PDF real pequeno
        pdf_content = self.create_dummy_pdf()
        uploaded_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        # Chama a função real
        compressed = compress_pdf(uploaded_file)
        
        # Verifica se retornou um ContentFile
        self.assertTrue(hasattr(compressed, 'read'))
        
        # Verifica se o conteúdo resultante é um PDF válido
        compressed_content = compressed.read()
        self.assertTrue(compressed_content.startswith(b'%PDF'))
        
        # Tenta abrir com fitz para garantir integridade
        try:
            doc = fitz.open(stream=compressed_content, filetype="pdf")
            doc.close()
        except Exception as e:
            self.fail(f"PDF comprimido inválido: {e}")
