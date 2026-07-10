import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Chip,
  Button,
  Tab,
  Tabs,
  Card,
  CardContent,
  IconButton,
  Divider,
  CircularProgress,
  Alert,
  Link as MuiLink,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  FormControlLabel
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent
} from '@mui/lab';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Gavel as GavelIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Event as EventIcon,
  Description as DescriptionIcon,
  OpenInNew as OpenInNewIcon,
  Psychology as PsychologyIcon,
  Add as AddIcon,
  ContentCopy as ContentCopyIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import axiosInstance from '../utils/axiosInstance';

const ProcessoDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [processo, setProcesso] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [atualizandoMovimentacoes, setAtualizandoMovimentacoes] = useState(false);
  
  // Estados para análise com IA
  const [iaDialogOpen, setIaDialogOpen] = useState(false);
  const [textoIntimacao, setTextoIntimacao] = useState('');
  const [dataIntimacao, setDataIntimacao] = useState('');
  const [analisandoIA, setAnalisandoIA] = useState(false);
  const [resultadoIA, setResultadoIA] = useState(null);
  const [movimentacaoEmAnaliseId, setMovimentacaoEmAnaliseId] = useState(null);
  
  // Estados para adicionar/editar Prazo
  const [prazoDialogOpen, setPrazoDialogOpen] = useState(false);
  const [prazoEditando, setPrazoEditando] = useState(null);
  const [prazoForm, setPrazoForm] = useState({
    descricao: '',
    data_inicio: new Date().toISOString().split('T')[0],
    prazo_dias: 15,
    prioridade: 'media',
    status: 'pendente'
  });
  
  // Estados para adicionar/editar Audiência
  const [audienciaDialogOpen, setAudienciaDialogOpen] = useState(false);
  const [audienciaEditando, setAudienciaEditando] = useState(null);
  const [audienciaForm, setAudienciaForm] = useState({
    tipo: 'conciliacao',
    data: '',
    hora: '',
    pauta: '',
    local: '',
    status: 'agendada',
    alertar: true
  });
  
  // Estados para adicionar/editar Parte
  const [parteDialogOpen, setParteDialogOpen] = useState(false);
  const [parteEditando, setParteEditando] = useState(null);
  const [parteForm, setParteForm] = useState({
    tipo_parte: 'autor',
    tipo_pessoa: 'fisica',
    nome: '',
    cpf_cnpj: '',
    email: '',
    telefone: '',
    endereco: '',
    representado_escritorio: false
  });
  
  // Estados para adicionar/editar Movimentação
  const [movimentacaoDialogOpen, setMovimentacaoDialogOpen] = useState(false);
  const [movimentacaoEditando, setMovimentacaoEditando] = useState(null);
  const [movimentacaoForm, setMovimentacaoForm] = useState({
    tipo: 'outro',
    data_movimentacao: new Date().toISOString().split('T')[0],
    descricao: '',
    importante: false,
    numero_protocolo: ''
  });

  useEffect(() => {
    fetchProcesso();
  }, [id]);

  const fetchProcesso = async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get(`/api/processos/processos/${id}/`);
      setProcesso(response.data);
      setError('');
    } catch (err) {
      console.error('Erro ao buscar processo:', err);
      setError('Erro ao carregar processo. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '-';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getStatusColor = (status) => {
    const colors = {
      'andamento': 'primary',
      'suspenso': 'warning',
      'arquivado': 'default',
      'sentenciado': 'success',
      'transito_julgado': 'success',
      'recurso': 'info',
      'execucao': 'secondary'
    };
    return colors[status] || 'default';
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      await axiosInstance.delete(`/api/processos/processos/${id}/`);
      setDeleteDialogOpen(false);
      navigate('/processos');
    } catch (err) {
      console.error('Erro ao deletar processo:', err);
      setError(err.response?.data?.detail || 'Erro ao deletar processo. Você pode não ter permissão.');
      setDeleteDialogOpen(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  const handleAnalisarMovimentacao = async (movimentacao) => {
    setTextoIntimacao(movimentacao.descricao);
    setDataIntimacao(movimentacao.data_movimentacao.split('T')[0]);
    setIaDialogOpen(true);
    
    // Armazena o ID da movimentação para enviar na análise
    setMovimentacaoEmAnaliseId(movimentacao.id);
  };

  const handleAnalisarComIA = async (movimentacaoId = null) => {
    if (!textoIntimacao.trim()) {
      alert('Digite o texto da intimação');
      return;
    }

    try {
      setAnalisandoIA(true);
      setResultadoIA(null);

      // Usa o ID da movimentação armazenado temporariamente ou o passado por parâmetro
      const movId = movimentacaoId || movimentacaoEmAnaliseId;

      const requestData = {
        texto: textoIntimacao,
        data_intimacao: dataIntimacao || new Date().toISOString().split('T')[0]
      };
      
      // Se for análise de uma movimentação específica, envia o ID
      if (movId) {
        requestData.movimentacao_id = movId;
      }

      const response = await axiosInstance.post('/api/processos/processos/analisar_intimacao_ia/', requestData);

      setResultadoIA(response.data);
      
      // Exibe mensagem de sucesso
      const mensagem = movId
        ? `✅ Análise concluída e salva na movimentação!\n\n📋 ${response.data.total_prazos} prazos encontrados\n🎤 ${response.data.total_audiencias} audiências encontradas`
        : `✅ Análise concluída!\n\n📋 ${response.data.total_prazos} prazos encontrados\n🎤 ${response.data.total_audiencias} audiências encontradas`;
      
      alert(mensagem);
      
      // Limpa o ID temporário
      if (movId) {
        setMovimentacaoEmAnaliseId(null);
        // Recarrega para atualizar o badge
        await fetchProcesso();
      }

    } catch (err) {
      console.error('Erro ao analisar com IA:', err);
      alert('Erro ao analisar intimação com IA: ' + (err.response?.data?.erro || err.message));
    } finally {
      setAnalisandoIA(false);
    }
  };

  const handleSalvarResultadosIA = async () => {
    if (!resultadoIA) return;

    try {
      // Salva prazos
      for (const prazo of resultadoIA.prazos) {
        await axiosInstance.post('/api/processos/prazos/', {
          ...prazo,
          processo: id
        });
      }

      // Salva audiências
      for (const audiencia of resultadoIA.audiencias) {
        await axiosInstance.post('/api/processos/audiencias/', {
          ...audiencia,
          processo: id
        });
      }

      alert(`✅ Dados salvos com sucesso!\n\n${resultadoIA.total_prazos} prazos e ${resultadoIA.total_audiencias} audiências foram cadastrados.`);
      
      // Limpa e fecha
      setIaDialogOpen(false);
      setTextoIntimacao('');
      setDataIntimacao('');
      setResultadoIA(null);
      
      // Recarrega processo para atualizar badge de "analisada_ia"
      await fetchProcesso();

    } catch (err) {
      console.error('Erro ao salvar resultados:', err);
      alert('Erro ao salvar: ' + (err.response?.data?.detail || err.message));
    }
  };

  // ========== FUNÇÕES PARA GERENCIAR PRAZOS ==========
  
  const handleAbrirDialogPrazo = (prazo = null) => {
    if (prazo) {
      // Editar prazo existente
      setPrazoEditando(prazo);
      setPrazoForm({
        descricao: prazo.descricao,
        data_inicio: prazo.data_inicio,
        prazo_dias: prazo.prazo_dias,
        prioridade: prazo.prioridade,
        status: prazo.status
      });
    } else {
      // Novo prazo
      setPrazoEditando(null);
      setPrazoForm({
        descricao: '',
        data_inicio: new Date().toISOString().split('T')[0],
        prazo_dias: 15,
        prioridade: 'media',
        status: 'pendente'
      });
    }
    setPrazoDialogOpen(true);
  };

  const handleSalvarPrazo = async () => {
    try {
      const prazoData = {
        ...prazoForm,
        processo: id
      };

      if (prazoEditando) {
        // Atualizar prazo existente
        await axiosInstance.put(`/api/processos/prazos/${prazoEditando.id}/`, prazoData);
        alert('✅ Prazo atualizado com sucesso!');
      } else {
        // Criar novo prazo
        await axiosInstance.post('/api/processos/prazos/', prazoData);
        alert('✅ Prazo criado com sucesso!');
      }

      setPrazoDialogOpen(false);
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao salvar prazo:', err);
      alert('Erro ao salvar prazo: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleExcluirPrazo = async (prazoId) => {
    if (!window.confirm('Tem certeza que deseja excluir este prazo?')) return;

    try {
      await axiosInstance.delete(`/api/processos/prazos/${prazoId}/`);
      alert('✅ Prazo excluído com sucesso!');
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao excluir prazo:', err);
      alert('Erro ao excluir prazo: ' + (err.response?.data?.detail || err.message));
    }
  };

  // ========== FUNÇÕES PARA GERENCIAR AUDIÊNCIAS ==========
  
  const handleAbrirDialogAudiencia = (audiencia = null) => {
    if (audiencia) {
      // Editar audiência existente
      setAudienciaEditando(audiencia);
      const dataHora = audiencia.data_hora ? new Date(audiencia.data_hora) : new Date();
      setAudienciaForm({
        tipo: audiencia.tipo,
        data: dataHora.toISOString().split('T')[0],
        hora: dataHora.toTimeString().substring(0, 5),
        pauta: audiencia.pauta || '',
        local: audiencia.local || '',
        status: audiencia.status,
        alertar: audiencia.alertar
      });
    } else {
      // Nova audiência
      setAudienciaEditando(null);
      setAudienciaForm({
        tipo: 'conciliacao',
        data: '',
        hora: '',
        pauta: '',
        local: '',
        status: 'agendada',
        alertar: true
      });
    }
    setAudienciaDialogOpen(true);
  };

  const handleSalvarAudiencia = async () => {
    try {
      const audienciaData = {
        processo: id,
        tipo: audienciaForm.tipo,
        data_hora: audienciaForm.data && audienciaForm.hora 
          ? `${audienciaForm.data}T${audienciaForm.hora}:00`
          : null,
        pauta: audienciaForm.pauta,
        local: audienciaForm.local,
        status: audienciaForm.status,
        alertar: audienciaForm.alertar
      };

      if (audienciaEditando) {
        // Atualizar audiência existente
        await axiosInstance.put(`/api/processos/audiencias/${audienciaEditando.id}/`, audienciaData);
        alert('✅ Audiência atualizada com sucesso!');
      } else {
        // Criar nova audiência
        await axiosInstance.post('/api/processos/audiencias/', audienciaData);
        alert('✅ Audiência criada com sucesso!');
      }

      setAudienciaDialogOpen(false);
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao salvar audiência:', err);
      alert('Erro ao salvar audiência: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleExcluirAudiencia = async (audienciaId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta audiência?')) return;

    try {
      await axiosInstance.delete(`/api/processos/audiencias/${audienciaId}/`);
      alert('✅ Audiência excluída com sucesso!');
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao excluir audiência:', err);
      alert('Erro ao excluir audiência: ' + (err.response?.data?.detail || err.message));
    }
  };

  // ========== FUNÇÕES PARA GERENCIAR PARTES ==========
  
  const handleAbrirDialogParte = (parte = null) => {
    if (parte) {
      // Editar parte existente
      setParteEditando(parte);
      setParteForm({
        tipo_parte: parte.tipo_parte,
        tipo_pessoa: parte.tipo_pessoa,
        nome: parte.nome,
        cpf_cnpj: parte.cpf_cnpj || '',
        email: parte.email || '',
        telefone: parte.telefone || '',
        endereco: parte.endereco || '',
        representado_escritorio: parte.representado_escritorio || false
      });
    } else {
      // Nova parte
      setParteEditando(null);
      setParteForm({
        tipo_parte: 'autor',
        tipo_pessoa: 'fisica',
        nome: '',
        cpf_cnpj: '',
        email: '',
        telefone: '',
        endereco: '',
        representado_escritorio: false
      });
    }
    setParteDialogOpen(true);
  };

  const handleSalvarParte = async () => {
    try {
      const parteData = {
        ...parteForm,
        processo: id
      };

      if (parteEditando) {
        // Atualizar parte existente
        await axiosInstance.put(`/api/processos/partes/${parteEditando.id}/`, parteData);
        alert('✅ Parte atualizada com sucesso!');
      } else {
        // Criar nova parte
        await axiosInstance.post('/api/processos/partes/', parteData);
        alert('✅ Parte criada com sucesso!');
      }

      setParteDialogOpen(false);
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao salvar parte:', err);
      alert('Erro ao salvar parte: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleExcluirParte = async (parteId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta parte?')) return;

    try {
      await axiosInstance.delete(`/api/processos/partes/${parteId}/`);
      alert('✅ Parte excluída com sucesso!');
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao excluir parte:', err);
      alert('Erro ao excluir parte: ' + (err.response?.data?.detail || err.message));
    }
  };

  // ========== FUNÇÕES PARA GERENCIAR MOVIMENTAÇÕES ==========
  
  const handleAbrirDialogMovimentacao = (movimentacao = null) => {
    if (movimentacao) {
      // Editar movimentação existente
      setMovimentacaoEditando(movimentacao);
      const dataMovStr = movimentacao.data_movimentacao ? 
        new Date(movimentacao.data_movimentacao).toISOString().split('T')[0] : 
        new Date().toISOString().split('T')[0];
      
      setMovimentacaoForm({
        tipo: movimentacao.tipo,
        data_movimentacao: dataMovStr,
        descricao: movimentacao.descricao,
        importante: movimentacao.importante || false,
        numero_protocolo: movimentacao.numero_protocolo || ''
      });
    } else {
      // Nova movimentação
      setMovimentacaoEditando(null);
      setMovimentacaoForm({
        tipo: 'outro',
        data_movimentacao: new Date().toISOString().split('T')[0],
        descricao: '',
        importante: false,
        numero_protocolo: ''
      });
    }
    setMovimentacaoDialogOpen(true);
  };

  const handleSalvarMovimentacao = async () => {
    try {
      const movimentacaoData = {
        ...movimentacaoForm,
        processo: id,
        lido: false
      };

      if (movimentacaoEditando) {
        // Atualizar movimentação existente
        await axiosInstance.put(`/api/processos/movimentacoes/${movimentacaoEditando.id}/`, movimentacaoData);
        alert('✅ Movimentação atualizada com sucesso!');
      } else {
        // Criar nova movimentação
        await axiosInstance.post('/api/processos/movimentacoes/', movimentacaoData);
        alert('✅ Movimentação criada com sucesso!');
      }

      setMovimentacaoDialogOpen(false);
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao salvar movimentação:', err);
      alert('Erro ao salvar movimentação: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleExcluirMovimentacao = async (movimentacaoId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta movimentação?')) return;

    try {
      await axiosInstance.delete(`/api/processos/movimentacoes/${movimentacaoId}/`);
      alert('✅ Movimentação excluída com sucesso!');
      fetchProcesso();
    } catch (err) {
      console.error('Erro ao excluir movimentação:', err);
      alert('Erro ao excluir movimentação: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCopiarTexto = (texto) => {
    navigator.clipboard.writeText(texto).then(() => {
      alert('✅ Texto copiado para a área de transferência!');
    }).catch(err => {
      console.error('Erro ao copiar texto:', err);
      alert('❌ Erro ao copiar texto');
    });
  };

  const handleAtualizarMovimentacoes = async () => {
    try {
      setAtualizandoMovimentacoes(true);
      
      // Buscar movimentações atualizadas do PJe usando o novo endpoint
      const response = await axiosInstance.post(
        `/api/processos/processos/${id}/atualizar_movimentacoes/`
      );
      
      const { novas, mensagem } = response.data;
      
      // Recarregar processo
      await fetchProcesso();
      
      if (novas === 0) {
        alert('✅ Processo está atualizado! Nenhuma nova movimentação encontrada.');
      } else {
        alert(`✅ ${mensagem}`);
      }
      
    } catch (err) {
      console.error('Erro ao atualizar movimentações:', err);
      alert('❌ Erro ao atualizar movimentações: ' + (err.response?.data?.erro || err.response?.data?.detail || err.message));
    } finally {
      setAtualizandoMovimentacoes(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !processo) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">{error || 'Processo não encontrado'}</Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/processos')}
          sx={{ mt: 2 }}
        >
          Voltar para Processos
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Cabeçalho */}
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/processos')}
          sx={{ mb: 2 }}
        >
          Voltar para Processos
        </Button>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Processo {processo.numero_processo}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <Chip
                label={processo.status_display}
                color={getStatusColor(processo.status)}
              />
              <Chip label={processo.tipo_display} />
              {processo.sigilo && <Chip label="SIGILO" color="error" />}
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={atualizandoMovimentacoes ? <CircularProgress size={20} /> : <RefreshIcon />}
              onClick={handleAtualizarMovimentacoes}
              disabled={atualizandoMovimentacoes}
              title="Atualizar movimentações do PJe"
            >
              {atualizandoMovimentacoes ? 'Atualizando...' : 'Atualizar'}
            </Button>
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/processos/${id}/editar`)}
            >
              Editar
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDeleteClick}
            >
              Excluir
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Abas */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Informações Gerais" />
          <Tab label="Partes" />
          <Tab label="Movimentações" />
          <Tab label="Prazos" />
          <Tab label="Audiências" />
        </Tabs>
      </Paper>

      {/* Conteúdo das Abas */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          {/* Dados do Cliente */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Cliente
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Nome:
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {processo.cliente_principal_detalhes?.nome_completo || 
                   processo.cliente_principal_detalhes?.razao_social}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Posição:
                </Typography>
                <Chip label={processo.posicao_cliente_display} size="small" />
              </CardContent>
            </Card>
          </Grid>

          {/* Dados do Processo */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <GavelIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Dados do Processo
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Classe:
                    </Typography>
                    <Typography variant="body1">{processo.classe}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Assunto:
                    </Typography>
                    <Typography variant="body1">{processo.assunto}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Tribunal:
                    </Typography>
                    <Typography variant="body1">{processo.tribunal}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Vara:
                    </Typography>
                    <Typography variant="body1">{processo.vara || '-'}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Datas */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <EventIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Datas Importantes
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Distribuição:
                    </Typography>
                    <Typography variant="body1">{formatDate(processo.data_distribuicao)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Citação:
                    </Typography>
                    <Typography variant="body1">{formatDate(processo.data_citacao)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Sentença:
                    </Typography>
                    <Typography variant="body1">{formatDate(processo.data_sentenca)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Trânsito em Julgado:
                    </Typography>
                    <Typography variant="body1">{formatDate(processo.data_transito_julgado)}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Valores */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Valores
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Valor da Causa:
                    </Typography>
                    <Typography variant="h6" color="primary">
                      {formatCurrency(processo.valor_causa)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Condenação:
                    </Typography>
                    <Typography variant="body1">{formatCurrency(processo.valor_condenacao)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Acordo:
                    </Typography>
                    <Typography variant="body1">{formatCurrency(processo.valor_acordo)}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Resumo e Estratégia */}
          {(processo.resumo || processo.estrategia_juridica || processo.observacoes) && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <DescriptionIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Resumo e Estratégia
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  {processo.resumo && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Resumo do Caso:
                      </Typography>
                      <Typography variant="body1" paragraph>
                        {processo.resumo}
                      </Typography>
                    </Box>
                  )}
                  
                  {processo.estrategia_juridica && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Estratégia Jurídica:
                      </Typography>
                      <Typography variant="body1" paragraph>
                        {processo.estrategia_juridica}
                      </Typography>
                    </Box>
                  )}
                  
                  {processo.observacoes && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Observações:
                      </Typography>
                      <Typography variant="body1">
                        {processo.observacoes}
                      </Typography>
                    </Box>
                  )}

                  {processo.link_consulta && (
                    <Box sx={{ mt: 2 }}>
                      <MuiLink
                        href={processo.link_consulta}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                      >
                        Consultar no e-SAJ/PJe
                        <OpenInNewIcon fontSize="small" />
                      </MuiLink>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Aba Partes */}
      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Partes do Processo
              </Typography>
              <Button
                variant="outlined"
                color="primary"
                startIcon={<AddIcon />}
                onClick={() => handleAbrirDialogParte()}
              >
                Adicionar Parte
              </Button>
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            {processo.partes && processo.partes.length > 0 ? (
              processo.partes.map((parte, index) => (
                <Box key={index} sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                        <Chip label={parte.tipo_parte_display} color="primary" size="small" />
                        <Chip label={parte.tipo_pessoa_display} size="small" />
                        {parte.representado_escritorio && (
                          <Chip label="Representado por Você" color="success" size="small" />
                        )}
                        {parte.cliente_vinculado && (
                          <Chip label="Cliente do Escritório" color="info" size="small" />
                        )}
                      </Box>
                      <Typography variant="h6">{parte.nome}</Typography>
                      {parte.cpf_cnpj && (
                        <Typography variant="body2" color="text.secondary">
                          CPF/CNPJ: {parte.cpf_cnpj}
                        </Typography>
                      )}
                      {parte.advogado_nome && (
                        <Typography variant="body2" color="text.secondary">
                          Advogado: {parte.advogado_nome} {parte.advogado_oab && `(OAB: ${parte.advogado_oab})`}
                        </Typography>
                      )}
                    </Box>
                    <Box>
                      <IconButton size="small" color="primary" onClick={() => handleAbrirDialogParte(parte)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => handleExcluirParte(parte.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                </Box>
              ))
            ) : (
              <Alert severity="info">
                Nenhuma parte cadastrada ainda.
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => handleAbrirDialogParte()}
                  sx={{ ml: 2 }}
                >
                  Adicionar Parte
                </Button>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Aba Movimentações */}
      {tabValue === 2 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Movimentações Processuais
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={() => handleAbrirDialogMovimentacao()}
                >
                  Adicionar Movimentação
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<PsychologyIcon />}
                  onClick={() => setIaDialogOpen(true)}
                >
                  Analisar com IA
                </Button>
              </Box>
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            {processo.movimentacoes && processo.movimentacoes.length > 0 ? (
              <Box sx={{ maxHeight: '600px', overflowY: 'auto', pr: 1 }}>
                <Timeline>
                  {processo.movimentacoes.map((mov) => (
                    <TimelineItem key={mov.id}>
                      <TimelineOppositeContent 
                        color="text.secondary"
                        sx={{ flex: 0.25, maxWidth: '25%' }}
                      >
                        {formatDateTime(mov.data_movimentacao)}
                      </TimelineOppositeContent>
                      <TimelineSeparator>
                        <TimelineDot color={mov.importante ? 'error' : 'primary'} />
                        <TimelineConnector />
                      </TimelineSeparator>
                      <TimelineContent sx={{ flex: 0.75 }}>
                        <Paper elevation={3} sx={{ p: 2, position: 'relative' }}>
                          <Box sx={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 0.5 }}>
                            <IconButton 
                              size="small" 
                              color="secondary" 
                              onClick={() => handleAnalisarMovimentacao(mov)}
                              title={mov.analisada_ia ? "Reanalisar com IA" : "Analisar com IA"}
                            >
                              <PsychologyIcon fontSize="small" />
                            </IconButton>
                            <IconButton 
                              size="small" 
                              color="success" 
                              onClick={() => handleCopiarTexto(mov.descricao)}
                              title="Copiar texto"
                            >
                              <ContentCopyIcon fontSize="small" />
                            </IconButton>
                            <IconButton size="small" color="primary" onClick={() => handleAbrirDialogMovimentacao(mov)}>
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton size="small" color="error" onClick={() => handleExcluirMovimentacao(mov.id)}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Box>
                          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                            <Chip label={mov.tipo_display} size="small" />
                            {mov.analisada_ia && (
                              <Chip 
                                label="✓ Analisada por IA" 
                                size="small" 
                                color="secondary"
                                title={`Analisada em ${formatDateTime(mov.data_analise_ia)} por ${mov.analisada_por_detalhes?.first_name || 'Usuário'}`}
                              />
                            )}
                          </Box>
                          <Typography 
                            variant="body1"
                            sx={{
                              maxHeight: '200px',
                              overflowY: 'auto',
                              pr: 1,
                              wordBreak: 'break-word'
                            }}
                          >
                            {mov.descricao}
                          </Typography>
                          {mov.numero_protocolo && (
                            <Typography variant="caption" color="text.secondary">
                              Protocolo: {mov.numero_protocolo}
                            </Typography>
                          )}
                        </Paper>
                      </TimelineContent>
                    </TimelineItem>
                  ))}
                </Timeline>
              </Box>
            ) : (
              <Alert severity="info">
                Nenhuma movimentação cadastrada ainda.
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => handleAbrirDialogMovimentacao()}
                  sx={{ ml: 2 }}
                >
                  Adicionar Movimentação
                </Button>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Aba Prazos */}
      {tabValue === 3 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Prazos Processuais
              </Typography>
              <Button
                variant="outlined"
                color="primary"
                startIcon={<AddIcon />}
                onClick={() => handleAbrirDialogPrazo()}
              >
                Adicionar Prazo
              </Button>
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            {processo.prazos && processo.prazos.length > 0 ? (
              processo.prazos.map((prazo) => (
                <Box key={prazo.id} sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6">{prazo.descricao}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Início: {formatDate(prazo.data_inicio)} | Limite: {formatDate(prazo.data_limite)} ({prazo.prazo_dias} dias)
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip label={prazo.prioridade_display} size="small" sx={{ mr: 1 }} />
                        <Chip label={prazo.status_display} size="small" color={prazo.status === 'pendente' ? 'warning' : 'success'} />
                      </Box>
                    </Box>
                    <Box>
                      <IconButton size="small" color="primary" onClick={() => handleAbrirDialogPrazo(prazo)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => handleExcluirPrazo(prazo.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                </Box>
              ))
            ) : (
              <Alert severity="info">
                Nenhum prazo cadastrado ainda.
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => handleAbrirDialogPrazo()}
                  sx={{ ml: 2 }}
                >
                  Adicionar Manualmente
                </Button>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Aba Audiências */}
      {tabValue === 4 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                <EventIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Audiências
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={() => handleAbrirDialogAudiencia()}
                >
                  Adicionar Audiência
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<PsychologyIcon />}
                  onClick={() => setIaDialogOpen(true)}
                >
                  Analisar com IA
                </Button>
              </Box>
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            {processo.audiencias && processo.audiencias.length > 0 ? (
              processo.audiencias.map((audiencia) => (
                <Box key={audiencia.id} sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6">{audiencia.tipo_display}</Typography>
                      <Typography variant="body1" gutterBottom>
                        📅 {formatDateTime(audiencia.data_hora)}
                      </Typography>
                      {audiencia.local && (
                        <Typography variant="body2" color="text.secondary">
                          📍 {audiencia.local}
                        </Typography>
                      )}
                      {audiencia.link_virtual && (
                        <MuiLink href={audiencia.link_virtual} target="_blank" rel="noopener noreferrer" sx={{ display: 'block', mt: 1 }}>
                          🔗 Link da audiência virtual
                        </MuiLink>
                      )}
                      {audiencia.pauta && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Pauta: {audiencia.pauta}
                        </Typography>
                      )}
                      <Chip label={audiencia.status_display} size="small" sx={{ mt: 1 }} />
                    </Box>
                    <Box>
                      <IconButton size="small" color="primary" onClick={() => handleAbrirDialogAudiencia(audiencia)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => handleExcluirAudiencia(audiencia.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                </Box>
              ))
            ) : (
              <Alert severity="info">
                Nenhuma audiência agendada.
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => handleAbrirDialogAudiencia()}
                  sx={{ ml: 2 }}
                >
                  Adicionar Manualmente
                </Button>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Dialog de confirmação de exclusão */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">
          Confirmar Exclusão do Processo
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Tem certeza que deseja excluir o processo <strong>{processo.numero_processo}</strong>?
            <br /><br />
            <strong>⚠️ ATENÇÃO:</strong> Esta ação é irreversível!
            <br /><br />
            Serão excluídos permanentemente:
            <ul>
              <li>Todas as partes do processo</li>
              <li>Todas as movimentações</li>
              <li>Todos os prazos</li>
              <li>Todas as audiências</li>
              <li>Dados do processo</li>
            </ul>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancelar
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained" autoFocus>
            Sim, Excluir Permanentemente
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para Adicionar/Editar Parte */}
      <Dialog open={parteDialogOpen} onClose={() => setParteDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {parteEditando ? 'Editar Parte' : 'Adicionar Parte'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Tipo de Parte</InputLabel>
              <Select
                value={parteForm.tipo_parte}
                onChange={(e) => setParteForm({...parteForm, tipo_parte: e.target.value})}
                label="Tipo de Parte"
              >
                <MenuItem value="autor">Autor/Requerente</MenuItem>
                <MenuItem value="reu">Réu/Requerido</MenuItem>
                <MenuItem value="terceiro">Terceiro Interessado</MenuItem>
                <MenuItem value="testemunha">Testemunha</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth>
              <InputLabel>Tipo de Pessoa</InputLabel>
              <Select
                value={parteForm.tipo_pessoa}
                onChange={(e) => setParteForm({...parteForm, tipo_pessoa: e.target.value})}
                label="Tipo de Pessoa"
              >
                <MenuItem value="fisica">Pessoa Física</MenuItem>
                <MenuItem value="juridica">Pessoa Jurídica</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Nome Completo / Razão Social"
              fullWidth
              value={parteForm.nome}
              onChange={(e) => setParteForm({...parteForm, nome: e.target.value})}
              required
            />
            
            <TextField
              label="CPF/CNPJ"
              fullWidth
              value={parteForm.cpf_cnpj}
              onChange={(e) => setParteForm({...parteForm, cpf_cnpj: e.target.value})}
            />
            
            <TextField
              label="E-mail"
              type="email"
              fullWidth
              value={parteForm.email}
              onChange={(e) => setParteForm({...parteForm, email: e.target.value})}
            />
            
            <TextField
              label="Telefone"
              fullWidth
              value={parteForm.telefone}
              onChange={(e) => setParteForm({...parteForm, telefone: e.target.value})}
            />
            
            <TextField
              label="Endereço"
              fullWidth
              multiline
              rows={2}
              value={parteForm.endereco}
              onChange={(e) => setParteForm({...parteForm, endereco: e.target.value})}
            />
            
            <FormControlLabel
              control={
                <Checkbox
                  checked={parteForm.representado_escritorio}
                  onChange={(e) => setParteForm({...parteForm, representado_escritorio: e.target.checked})}
                />
              }
              label="Representado pelo escritório"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setParteDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleSalvarParte} variant="contained" color="primary">
            {parteEditando ? 'Atualizar' : 'Salvar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para Adicionar/Editar Movimentação */}
      <Dialog open={movimentacaoDialogOpen} onClose={() => setMovimentacaoDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {movimentacaoEditando ? 'Editar Movimentação' : 'Adicionar Movimentação'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Tipo de Movimentação</InputLabel>
              <Select
                value={movimentacaoForm.tipo}
                onChange={(e) => setMovimentacaoForm({...movimentacaoForm, tipo: e.target.value})}
                label="Tipo de Movimentação"
              >
                <MenuItem value="peticao">Petição</MenuItem>
                <MenuItem value="despacho">Despacho</MenuItem>
                <MenuItem value="decisao">Decisão</MenuItem>
                <MenuItem value="sentenca">Sentença</MenuItem>
                <MenuItem value="acordao">Acórdão</MenuItem>
                <MenuItem value="intimacao">Intimação</MenuItem>
                <MenuItem value="juntada">Juntada</MenuItem>
                <MenuItem value="certidao">Certidão</MenuItem>
                <MenuItem value="outro">Outro</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Data da Movimentação"
              type="date"
              fullWidth
              value={movimentacaoForm.data_movimentacao}
              onChange={(e) => setMovimentacaoForm({...movimentacaoForm, data_movimentacao: e.target.value})}
              InputLabelProps={{ shrink: true }}
              required
            />
            
            <TextField
              label="Descrição"
              fullWidth
              multiline
              rows={4}
              value={movimentacaoForm.descricao}
              onChange={(e) => setMovimentacaoForm({...movimentacaoForm, descricao: e.target.value})}
              required
            />
            
            <TextField
              label="Número do Protocolo"
              fullWidth
              value={movimentacaoForm.numero_protocolo}
              onChange={(e) => setMovimentacaoForm({...movimentacaoForm, numero_protocolo: e.target.value})}
            />
            
            <FormControlLabel
              control={
                <Checkbox
                  checked={movimentacaoForm.importante}
                  onChange={(e) => setMovimentacaoForm({...movimentacaoForm, importante: e.target.checked})}
                />
              }
              label="Marcar como importante"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMovimentacaoDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleSalvarMovimentacao} variant="contained" color="primary">
            {movimentacaoEditando ? 'Atualizar' : 'Salvar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para Adicionar/Editar Prazo */}
      <Dialog open={prazoDialogOpen} onClose={() => setPrazoDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {prazoEditando ? 'Editar Prazo' : 'Adicionar Prazo'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Descrição do Prazo"
              fullWidth
              multiline
              rows={2}
              value={prazoForm.descricao}
              onChange={(e) => setPrazoForm({...prazoForm, descricao: e.target.value})}
              required
            />
            
            <TextField
              label="Data de Início"
              type="date"
              fullWidth
              value={prazoForm.data_inicio}
              onChange={(e) => setPrazoForm({...prazoForm, data_inicio: e.target.value})}
              InputLabelProps={{ shrink: true }}
              required
            />
            
            <TextField
              label="Prazo (em dias)"
              type="number"
              fullWidth
              value={prazoForm.prazo_dias}
              onChange={(e) => setPrazoForm({...prazoForm, prazo_dias: parseInt(e.target.value)})}
              required
            />
            
            <FormControl fullWidth>
              <InputLabel>Prioridade</InputLabel>
              <Select
                value={prazoForm.prioridade}
                onChange={(e) => setPrazoForm({...prazoForm, prioridade: e.target.value})}
                label="Prioridade"
              >
                <MenuItem value="baixa">Baixa</MenuItem>
                <MenuItem value="media">Média</MenuItem>
                <MenuItem value="alta">Alta</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={prazoForm.status}
                onChange={(e) => setPrazoForm({...prazoForm, status: e.target.value})}
                label="Status"
              >
                <MenuItem value="pendente">Pendente</MenuItem>
                <MenuItem value="cumprido">Cumprido</MenuItem>
                <MenuItem value="vencido">Vencido</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPrazoDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleSalvarPrazo} variant="contained" color="primary">
            {prazoEditando ? 'Atualizar' : 'Salvar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para Adicionar/Editar Audiência */}
      <Dialog open={audienciaDialogOpen} onClose={() => setAudienciaDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {audienciaEditando ? 'Editar Audiência' : 'Adicionar Audiência'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Tipo de Audiência</InputLabel>
              <Select
                value={audienciaForm.tipo}
                onChange={(e) => setAudienciaForm({...audienciaForm, tipo: e.target.value})}
                label="Tipo de Audiência"
              >
                <MenuItem value="conciliacao">Conciliação</MenuItem>
                <MenuItem value="instrucao">Instrução e Julgamento</MenuItem>
                <MenuItem value="inicial">Inicial</MenuItem>
                <MenuItem value="julgamento">Julgamento</MenuItem>
                <MenuItem value="outras">Outras</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Data"
              type="date"
              fullWidth
              value={audienciaForm.data}
              onChange={(e) => setAudienciaForm({...audienciaForm, data: e.target.value})}
              InputLabelProps={{ shrink: true }}
              required
            />
            
            <TextField
              label="Hora"
              type="time"
              fullWidth
              value={audienciaForm.hora}
              onChange={(e) => setAudienciaForm({...audienciaForm, hora: e.target.value})}
              InputLabelProps={{ shrink: true }}
              required
            />
            
            <TextField
              label="Pauta / Assunto"
              fullWidth
              multiline
              rows={2}
              value={audienciaForm.pauta}
              onChange={(e) => setAudienciaForm({...audienciaForm, pauta: e.target.value})}
            />
            
            <TextField
              label="Local"
              fullWidth
              value={audienciaForm.local}
              onChange={(e) => setAudienciaForm({...audienciaForm, local: e.target.value})}
            />
            
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={audienciaForm.status}
                onChange={(e) => setAudienciaForm({...audienciaForm, status: e.target.value})}
                label="Status"
              >
                <MenuItem value="agendada">Agendada</MenuItem>
                <MenuItem value="realizada">Realizada</MenuItem>
                <MenuItem value="cancelada">Cancelada</MenuItem>
                <MenuItem value="adiada">Adiada</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAudienciaDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleSalvarAudiencia} variant="contained" color="primary">
            {audienciaEditando ? 'Atualizar' : 'Salvar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo de Análise com IA */}
      <Dialog 
        open={iaDialogOpen} 
        onClose={() => !analisandoIA && setIaDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Analisar Intimação com IA
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Cole o texto da intimação/comunicação processual abaixo. A IA irá extrair automaticamente:
            <ul>
              <li>📋 Prazos processuais (manifestação, contestação, recurso, etc.)</li>
              <li>🎤 Audiências agendadas (tipo, data e horário)</li>
            </ul>
          </DialogContentText>

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Data da Intimação (opcional):
            </Typography>
            <input
              type="date"
              value={dataIntimacao}
              onChange={(e) => setDataIntimacao(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                fontSize: '14px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Texto da Intimação: *
            </Typography>
            <textarea
              value={textoIntimacao}
              onChange={(e) => setTextoIntimacao(e.target.value)}
              placeholder="Cole aqui o texto completo da intimação..."
              rows={12}
              style={{
                width: '100%',
                padding: '10px',
                fontSize: '14px',
                fontFamily: 'inherit',
                borderRadius: '4px',
                border: '1px solid #ccc',
                resize: 'vertical'
              }}
              disabled={analisandoIA}
            />
          </Box>

          {analisandoIA && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <CircularProgress size={24} />
              <Typography>Analisando com IA...</Typography>
            </Box>
          )}

          {resultadoIA && (
            <Alert severity="success" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                ✅ Análise concluída!
              </Typography>
              <Typography variant="body2">
                📋 {resultadoIA.total_prazos} prazo(s) encontrado(s)
                <br />
                🎤 {resultadoIA.total_audiencias} audiência(s) encontrada(s)
              </Typography>
              
              {resultadoIA.prazos.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Prazos:</Typography>
                  {resultadoIA.prazos.map((prazo, idx) => (
                    <Typography key={idx} variant="body2" sx={{ ml: 2 }}>
                      • {prazo.descricao} ({prazo.prazo_dias} dias)
                    </Typography>
                  ))}
                </Box>
              )}
              
              {resultadoIA.audiencias.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Audiências:</Typography>
                  {resultadoIA.audiencias.map((aud, idx) => (
                    <Typography key={idx} variant="body2" sx={{ ml: 2 }}>
                      • {aud.pauta} - {aud.data_hora ? new Date(aud.data_hora).toLocaleString('pt-BR') : 'Data não especificada'}
                    </Typography>
                  ))}
                </Box>
              )}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setIaDialogOpen(false);
              setTextoIntimacao('');
              setDataIntimacao('');
              setResultadoIA(null);
              setMovimentacaoEmAnaliseId(null);
            }} 
            disabled={analisandoIA}
          >
            Cancelar
          </Button>
          {!resultadoIA ? (
            <Button 
              onClick={() => handleAnalisarComIA()} 
              color="secondary" 
              variant="contained"
              disabled={analisandoIA || !textoIntimacao.trim()}
              startIcon={<PsychologyIcon />}
            >
              Analisar com IA
            </Button>
          ) : (
            <Button 
              onClick={handleSalvarResultadosIA} 
              color="primary" 
              variant="contained"
              startIcon={<AddIcon />}
            >
              Salvar Resultados
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProcessoDetailPage;
