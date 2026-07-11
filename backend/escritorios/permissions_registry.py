# escritorios/permissions_registry.py
"""
Sistema centralizado de registro de permissões.
Todas as permissões do sistema devem ser declaradas aqui.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PermissionDefinition:
    """Define uma permissão do sistema."""
    codename: str
    nome: str
    categoria: str
    descricao: str = ""


class PermissionsRegistry:
    """
    Registro centralizado de todas as permissões do sistema.
    
    Benefícios:
    1. Todas as permissões em um único lugar
    2. Fácil de auditar e documentar
    3. Auto-sincronização com banco de dados
    4. Categorização por módulo
    5. Validação automática
    """
    
    # ==================== CLIENTES ====================
    CLIENTES = [
        PermissionDefinition(
            codename='ver_cliente',
            nome='Ver Cliente',
            categoria='Clientes',
            descricao='Permite visualizar dados de clientes'
        ),
        PermissionDefinition(
            codename='criar_cliente',
            nome='Criar Cliente',
            categoria='Clientes',
            descricao='Permite criar novos clientes'
        ),
        PermissionDefinition(
            codename='editar_cliente',
            nome='Editar Cliente',
            categoria='Clientes',
            descricao='Permite editar dados de clientes existentes'
        ),
        PermissionDefinition(
            codename='deletar_cliente',
            nome='Deletar Cliente',
            categoria='Clientes',
            descricao='Permite remover clientes do sistema'
        ),
        PermissionDefinition(
            codename='exportar_clientes',
            nome='Exportar Clientes',
            categoria='Clientes',
            descricao='Permite exportar lista de clientes'
        ),
    ]
    
    # ==================== CONSULTAS ====================
    CONSULTAS = [
        PermissionDefinition(
            codename='ver_consulta',
            nome='Ver Consulta',
            categoria='Consultas',
            descricao='Permite visualizar consultas'
        ),
        PermissionDefinition(
            codename='criar_consulta',
            nome='Criar Consulta',
            categoria='Consultas',
            descricao='Permite criar novas consultas'
        ),
        PermissionDefinition(
            codename='editar_consulta',
            nome='Editar Consulta',
            categoria='Consultas',
            descricao='Permite editar consultas existentes'
        ),
        PermissionDefinition(
            codename='deletar_consulta',
            nome='Deletar Consulta',
            categoria='Consultas',
            descricao='Permite remover consultas'
        ),
    ]
    
    # ==================== ANÁLISES ====================
    ANALISES = [
        PermissionDefinition(
            codename='ver_analise',
            nome='Ver Análise',
            categoria='Análises',
            descricao='Permite visualizar análises jurídicas'
        ),
        PermissionDefinition(
            codename='criar_analise',
            nome='Criar Análise',
            categoria='Análises',
            descricao='Permite criar novas análises'
        ),
        PermissionDefinition(
            codename='editar_analise',
            nome='Editar Análise',
            categoria='Análises',
            descricao='Permite editar análises existentes'
        ),
        PermissionDefinition(
            codename='deletar_analise',
            nome='Deletar Análise',
            categoria='Análises',
            descricao='Permite remover análises'
        ),
    ]
    
    # ==================== GERENCIAMENTO ====================
    GERENCIAMENTO = [
        PermissionDefinition(
            codename='gerenciar_papeis',
            nome='Gerenciar Papéis',
            categoria='Gerenciamento',
            descricao='Permite criar, editar e deletar papéis e suas permissões'
        ),
        PermissionDefinition(
            codename='gerenciar_membros',
            nome='Gerenciar Membros',
            categoria='Gerenciamento',
            descricao='Permite convidar, remover e editar membros do escritório'
        ),
        PermissionDefinition(
            codename='gerenciar_escritorio',
            nome='Gerenciar Escritório',
            categoria='Gerenciamento',
            descricao='Permite editar dados do escritório'
        ),
        PermissionDefinition(
            codename='ver_relatorios',
            nome='Ver Relatórios',
            categoria='Gerenciamento',
            descricao='Permite visualizar relatórios e estatísticas'
        ),
        PermissionDefinition(
            codename='ver_auditoria',
            nome='Ver Auditoria',
            categoria='Gerenciamento',
            descricao='Permite visualizar logs de auditoria do sistema (restrito a administradores)'
        ),
    ]
    
    # ==================== FINANCEIRO ====================
    FINANCEIRO = [
        PermissionDefinition(
            codename='ver_financeiro',
            nome='Ver Financeiro',
            categoria='Financeiro',
            descricao='Permite visualizar dados financeiros'
        ),
        PermissionDefinition(
            codename='criar_lancamento',
            nome='Criar Lançamento',
            categoria='Financeiro',
            descricao='Permite criar lançamentos financeiros'
        ),
        PermissionDefinition(
            codename='editar_lancamento',
            nome='Editar Lançamento',
            categoria='Financeiro',
            descricao='Permite editar lançamentos financeiros'
        ),
        PermissionDefinition(
            codename='deletar_lancamento',
            nome='Deletar Lançamento',
            categoria='Financeiro',
            descricao='Permite remover lançamentos financeiros'
        ),
    ]
    
    # ==================== PROCESSOS ====================
    PROCESSOS = [
        PermissionDefinition(
            codename='ver_processo',
            nome='Ver Processo',
            categoria='Processos',
            descricao='Permite visualizar processos'
        ),
        PermissionDefinition(
            codename='criar_processo',
            nome='Criar Processo',
            categoria='Processos',
            descricao='Permite criar novos processos'
        ),
        PermissionDefinition(
            codename='editar_processo',
            nome='Editar Processo',
            categoria='Processos',
            descricao='Permite editar processos existentes'
        ),
        PermissionDefinition(
            codename='deletar_processo',
            nome='Deletar Processo',
            categoria='Processos',
            descricao='Permite remover processos'
        ),
    ]
    
    # ==================== DOCUMENTOS (Cliente) ====================
    DOCUMENTOS = [
        PermissionDefinition(
            codename='ver_documento',
            nome='Ver Documentos do Cliente',
            categoria='Documentos',
            descricao='Permite visualizar documentos vinculados a clientes'
        ),
        PermissionDefinition(
            codename='criar_documento',
            nome='Criar Documentos para Cliente',
            categoria='Documentos',
            descricao='Permite fazer upload de novos documentos para clientes'
        ),
        PermissionDefinition(
            codename='editar_documento',
            nome='Editar Documentos do Cliente',
            categoria='Documentos',
            descricao='Permite editar metadados de documentos de clientes'
        ),
        PermissionDefinition(
            codename='deletar_documento',
            nome='Deletar Documentos do Cliente',
            categoria='Documentos',
            descricao='Permite remover documentos de clientes'
        ),
        PermissionDefinition(
            codename='download_documento',
            nome='Download de Documento do Cliente',
            categoria='Documentos',
            descricao='Permite fazer download de documentos de clientes'
        ),
        PermissionDefinition(
            codename='gerenciar_categorias',
            nome='Gerenciar Categorias de Documentos',
            categoria='Documentos',
            descricao='Permite criar, editar e deletar categorias de documentos'
        ),
        PermissionDefinition(
            codename='gerenciar_tags',
            nome='Gerenciar Tags de Documentos',
            categoria='Documentos',
            descricao='Permite criar, editar e deletar tags de documentos'
        ),
    ]
    
    # ==================== ARQUIVOS (Geral) ====================
    ARQUIVOS = [
        PermissionDefinition(
            codename='ver_arquivos',
            nome='Ver Arquivos Gerais',
            categoria='Arquivos',
            descricao='Permite visualizar o módulo de arquivos gerais e análises'
        ),
        PermissionDefinition(
            codename='criar_arquivo',
            nome='Criar Arquivo Geral',
            categoria='Arquivos',
            descricao='Permite fazer upload de novos arquivos no módulo geral'
        ),
        PermissionDefinition(
            codename='editar_arquivo',
            nome='Editar Arquivo Geral',
            categoria='Arquivos',
            descricao='Permite editar metadados de arquivos gerais'
        ),
        PermissionDefinition(
            codename='deletar_arquivo',
            nome='Deletar Arquivo Geral',
            categoria='Arquivos',
            descricao='Permite remover arquivos gerais do sistema'
        ),
        PermissionDefinition(
            codename='download_arquivo',
            nome='Download de Arquivo Geral',
            categoria='Arquivos',
            descricao='Permite fazer download de arquivos gerais'
        ),
        PermissionDefinition(
            codename='escanear_arquivo',
            nome='Escanear Novo Arquivo',
            categoria='Arquivos',
            descricao='Permite usar a função de OCR para extrair texto de arquivos'
        ),
        PermissionDefinition(
            codename='anonimizar_arquivo',
            nome='Anonimizar Arquivos',
            categoria='Arquivos',
            descricao='Permite acessar e gerenciar a anonimização de dados em arquivos'
        ),
        PermissionDefinition(
            codename='analisar_arquivo_ia',
            nome='Analisar Arquivo com IA',
            categoria='Arquivos',
            descricao='Permite solicitar e visualizar análises de arquivos por IA'
        ),
        PermissionDefinition(
            codename='deletar_analise_arquivo',
            nome='Deletar Análise de Arquivo',
            categoria='Arquivos',
            descricao='Permite remover análises de IA de arquivos'
        ),
        PermissionDefinition(
            codename='usar_ferramentas_pdf',
            nome='Usar Ferramentas de PDF',
            categoria='Arquivos',
            descricao='Permite usar ferramentas de manipulação de PDF (juntar, dividir, compactar, converter, etc.)'
        ),
    ]
    
    @classmethod
    def get_all_permissions(cls) -> List[PermissionDefinition]:
        """Retorna todas as permissões do sistema."""
        return (
            cls.CLIENTES +
            cls.CONSULTAS +
            cls.ANALISES +
            cls.GERENCIAMENTO +
            cls.FINANCEIRO +
            cls.PROCESSOS +
            cls.DOCUMENTOS +
            cls.ARQUIVOS
        )
    
    @classmethod
    def get_permissions_by_category(cls) -> Dict[str, List[PermissionDefinition]]:
        """Retorna permissões agrupadas por categoria."""
        return {
            'Clientes': cls.CLIENTES,
            'Consultas': cls.CONSULTAS,
            'Análises': cls.ANALISES,
            'Gerenciamento': cls.GERENCIAMENTO,
            'Financeiro': cls.FINANCEIRO,
            'Processos': cls.PROCESSOS,
            'Documentos': cls.DOCUMENTOS,
            'Arquivos': cls.ARQUIVOS,
        }
    
    @classmethod
    def get_permission_by_codename(cls, codename: str) -> PermissionDefinition:
        """Busca uma permissão pelo codename."""
        for perm in cls.get_all_permissions():
            if perm.codename == codename:
                return perm
        raise ValueError(f"Permissão '{codename}' não encontrada no registro")
    
    @classmethod
    def validate_permission(cls, codename: str) -> bool:
        """Valida se uma permissão existe no registro."""
        try:
            cls.get_permission_by_codename(codename)
            return True
        except ValueError:
            return False
    
    @classmethod
    def sync_to_database(cls):
        """
        Sincroniza as permissões do registro com o banco de dados.
        Cria novas permissões e marca obsoletas como inativas.
        """
        from .models import Permissao
        
        all_permissions = cls.get_all_permissions()
        existing_codenames = set(Permissao.objects.values_list('codename', flat=True))
        registry_codenames = {perm.codename for perm in all_permissions}
        
        # Criar ou atualizar permissões
        created_count = 0
        updated_count = 0
        
        for perm_def in all_permissions:
            perm, created = Permissao.objects.get_or_create(
                codename=perm_def.codename,
                defaults={'nome': perm_def.nome}
            )
            
            if created:
                created_count += 1
                print(f"Permissão criada: {perm_def.codename} - {perm_def.nome}")
            else:
                # Atualiza o nome se mudou
                if perm.nome != perm_def.nome:
                    perm.nome = perm_def.nome
                    perm.save()
                    updated_count += 1
                    print(f"Permissão atualizada: {perm_def.codename}")
        
        # Identificar permissões obsoletas
        obsolete_codenames = existing_codenames - registry_codenames
        if obsolete_codenames:
            print(f"\nPermissões obsoletas encontradas (não estão no registro):")
            for codename in obsolete_codenames:
                print(f"   - {codename}")
        
        print(f"\nResumo da sincronização:")
        print(f"   - Permissões criadas: {created_count}")
        print(f"   - Permissões atualizadas: {updated_count}")
        print(f"   - Permissões obsoletas: {len(obsolete_codenames)}")
        print(f"   - Total no registro: {len(all_permissions)}")
    
    @classmethod
    def get_default_role_permissions(cls) -> Dict[str, List[str]]:
        """
        Define as permissões padrão para cada papel.
        Retorna um dicionário com nome do papel e lista de codenames.
        """
        return {
            'Administrador': [perm.codename for perm in cls.get_all_permissions()],
            'Advogado': [
                'ver_cliente', 'criar_cliente', 'editar_cliente',
                'ver_consulta', 'criar_consulta', 'editar_consulta',
                'ver_analise', 'criar_analise', 'editar_analise',
                'ver_processo', 'criar_processo', 'editar_processo',
                'ver_documento', 'criar_documento', 'editar_documento', 'deletar_documento', 'download_documento',
                'ver_arquivos', 'criar_arquivo', 'editar_arquivo', 'deletar_arquivo', 'download_arquivo',
                'escanear_arquivo', 'anonimizar_arquivo', 'analisar_arquivo_ia', 'deletar_analise_arquivo',
                'usar_ferramentas_pdf',
                'ver_relatorios',
            ],
            'Secretária': [
                'ver_cliente', 'criar_cliente', 'editar_cliente',
                'ver_consulta', 'criar_consulta',
                'ver_processo', 'criar_processo',
                'ver_documento', 'criar_documento', 'editar_documento', 'download_documento',
                'ver_arquivos', 'criar_arquivo', 'editar_arquivo', 'download_arquivo', 'escanear_arquivo',
                'usar_ferramentas_pdf',
            ],
            'Assistente': [
                'ver_cliente',
                'ver_consulta',
                'ver_processo',
                'ver_documento', 'download_documento',
                'ver_arquivos', 'download_arquivo',
            ],
            'Financeiro': [
                'ver_cliente',
                'ver_financeiro', 'criar_lancamento', 'editar_lancamento',
                'ver_relatorios',
            ],
        }


# Atalho para facilitar importação
PERMISSIONS = PermissionsRegistry
