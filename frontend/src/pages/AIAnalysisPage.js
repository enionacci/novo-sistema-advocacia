import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid
} from '@mui/material';
import {
  Psychology as AIIcon,
  Visibility as VisibilityIcon,
  Send as SendIcon,
  Description as DocumentIcon
} from '@mui/icons-material';
import axios from '../utils/axiosInstance';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const TIPOS_ANALISE = [
  { value: 'resumo', label: 'Resumo Executivo', description: 'Resumo conciso do documento' },
  { value: 'extracao_dados', label: 'Extração de Dados', description: 'Extrai informações estruturadas em JSON' },
  { value: 'juridico', label: 'Análise Jurídica', description: 'Análise sob perspectiva jurídica' },
  { value: 'contrato', label: 'Análise de Contrato', description: 'Cláusulas, riscos e obrigações' },
  { value: 'risco', label: 'Análise de Risco', description: 'Identifica riscos e alertas' },
  { value: 'peticao', label: 'Análise de Petição', description: 'Analisa petições judiciais' },
  { value: 'decisao', label: 'Análise de Decisão Judicial', description: 'Analisa sentenças e decisões' },
  { value: 'personalizado', label: 'Personalizado', description: 'Análise com prompt customizado' }
];

// Modelos GPT principais para análise de documentos
const MODELOS_GPT = [
  { 
    id: 'gpt-5-nano-2025-08-07', 
    name: 'GPT-5 Nano', 
    category: 'GPT-5',
    cost_level: 'baixo',
    speed: 'muito rápida',
    description: 'Ideal para documentos pequenos (até 3 páginas ou resumos)'
  },
  { 
    id: 'gpt-5-mini-2025-08-07', 
    name: 'GPT-5 Mini', 
    category: 'GPT-5',
    cost_level: 'Médio',
    speed: 'rápida',
    description: 'Bom para documentos curtos (até 5 páginas)'
  },
  { 
    id: 'gpt-5-2025-08-07', 
    name: 'GPT-5', 
    category: 'GPT-5',
    cost_level: 'Alto',
    speed: 'média',
    description: 'Para documentos médios (até 7 páginas)'
  },
  { 
    id: 'gpt-4.1-nano-2025-04-14', 
    name: 'GPT-4.1 Nano', 
    category: 'GPT-4.1',
    cost_level: 'baixo',
    speed: 'muito rápida',
    description: '⭐ RECOMENDADO para documentos a partir de 8 páginas - 1M tokens'
  },
  { 
    id: 'gpt-4.1-mini-2025-04-14', 
    name: 'GPT-4.1 Mini', 
    category: 'GPT-4.1',
    cost_level: 'Médio',
    speed: 'rápida',
    description: '⭐ Melhor custo-benefício para petições e contratos extensos - 1M tokens'
  },
  { 
    id: 'gpt-4.1-2025-04-14', 
    name: 'GPT-4.1', 
    category: 'GPT-4.1',
    cost_level: 'alto',
    speed: 'média',
    description: '⭐ Máxima precisão para processos completos e documentos complexos - 1M tokens'
  },
];

const AIAnalysisPage = () => {
  // Estados
  const [documentos, setDocumentos] = useState([]);
  const [modelosGPT] = useState(MODELOS_GPT);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [previewDialog, setPreviewDialog] = useState(false);
  const [analysisDialog, setAnalysisDialog] = useState(false);
  
  // Estados da análise
  const [tipoAnalise, setTipoAnalise] = useState('resumo');
  const [modeloGPT, setModeloGPT] = useState('');
  const [promptPersonalizado, setPromptPersonalizado] = useState('');

  // Carregar documentos e modelos
  useEffect(() => {
    loadDocuments();
  }, []);

  // Definir modelo padrão (GPT-5 Nano)
  useEffect(() => {
    if (!modeloGPT) {
      setModeloGPT(MODELOS_GPT[0].id); // GPT-5 Nano como padrão
    }
  }, [modeloGPT]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/documentos/');
      
      // Filtrar apenas documentos que têm texto extraído
      const documentsWithText = response.data.results?.filter(doc => 
        doc.texto_extraido && doc.texto_extraido.trim().length > 0
      ) || [];
      
      setDocumentos(documentsWithText);
    } catch (err) {
      console.error('Erro ao carregar documentos:', err);
      setError('Erro ao carregar documentos');
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewDocument = (documento) => {
    setSelectedDocument(documento);
    setPreviewDialog(true);
  };

  const handleAnalyzeDocument = (documento) => {
    setSelectedDocument(documento);
    setAnalysisDialog(true);
  };

  const processAnalysis = async () => {
    if (!selectedDocument) return;

    if (tipoAnalise === 'personalizado' && !promptPersonalizado.trim()) {
      setError('Por favor, forneça instruções personalizadas');
      return;
    }

    try {
      setProcessing(true);
      setError('');

      const payload = {
        texto: selectedDocument.texto_extraido,
        tipo_analise: tipoAnalise,
        modelo_ia: modeloGPT,
        prompt_personalizado: tipoAnalise === 'personalizado' ? promptPersonalizado : null,
        documento_id: selectedDocument.id
      };

      console.log('📤 Enviando análise:', payload);

      const response = await axios.post('/api/documentos/analises/', payload);
      
      setSuccess('Análise solicitada com sucesso! Você pode acompanhar o progresso na página de Análises Realizadas.');
      setAnalysisDialog(false);
      
      // Limpar formulário
      setPromptPersonalizado('');
      setTipoAnalise('resumo');
      // Resetar para o modelo padrão (GPT-5 Nano)
      setModeloGPT(MODELOS_GPT[0].id);
      
      setTimeout(() => setSuccess(''), 5000);
      
    } catch (err) {
      console.error('❌ Erro completo:', err);
      console.error('❌ Resposta do servidor:', err.response?.data);
      setError(err.response?.data?.error || 'Erro ao solicitar análise');
    } finally {
      setProcessing(false);
    }
  };

  const tipoAnaliseSelecionada = TIPOS_ANALISE.find(t => t.value === tipoAnalise);

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <AIIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" gutterBottom>
              Análise com Inteligência Artificial
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Selecione documentos para análise inteligente: resumos, análise jurídica, extração de dados e mais
            </Typography>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}

        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>💡 Importante:</strong> Os modelos <strong>GPT-5</strong> suportam até <strong>7 páginas</strong>. 
            Para documentos maiores (petições, contratos extensos, processos completos), 
            utilize obrigatoriamente os modelos <strong>GPT-4.1</strong> que suportam até <strong>1 milhão de tokens</strong> de contexto.
          </Typography>
        </Alert>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : documentos.length === 0 ? (
          <Alert severity="info">
            Nenhum documento com texto extraído encontrado para análise.
            Use o Scanner para processar documentos primeiro.
          </Alert>
        ) : (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Documentos Disponíveis para Análise
              </Typography>
              
              <List>
                {documentos.map((documento, index) => (
                  <React.Fragment key={documento.id}>
                    <ListItem>
                      <DocumentIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary={documento.titulo || `Documento ${documento.id}`}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Cliente: {documento.cliente_nome || 'N/A'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Criado: {documento.data_criacao ? format(new Date(documento.data_criacao), 'dd/MM/yyyy HH:mm', { locale: ptBR }) : 'Data não disponível'}
                            </Typography>
                            <Box sx={{ mt: 0.5 }}>
                              <Chip 
                                label="Texto Extraído" 
                                size="small" 
                                color="primary" 
                                sx={{ mr: 1 }}
                              />
                              {documento.anonimizado && (
                                <Chip 
                                  label="Anonimizado" 
                                  size="small" 
                                  color="warning" 
                                />
                              )}
                            </Box>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          onClick={() => handlePreviewDocument(documento)}
                          color="primary"
                          title="Visualizar Texto"
                        >
                          <VisibilityIcon />
                        </IconButton>
                        <Button
                          variant="contained"
                          color="primary"
                          onClick={() => handleAnalyzeDocument(documento)}
                          startIcon={<AIIcon />}
                          sx={{ ml: 1 }}
                        >
                          Analisar com IA
                        </Button>
                      </ListItemSecondaryAction>
                    </ListItem>
                    {index < documentos.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        )}
      </Paper>

      {/* Dialog de Preview */}
      <Dialog 
        open={previewDialog} 
        onClose={() => setPreviewDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Prévia do Documento
        </DialogTitle>
        <DialogContent>
          <Typography variant="subtitle1" gutterBottom>
            {selectedDocument?.titulo || `Documento ${selectedDocument?.id}`}
          </Typography>
          <TextField
            multiline
            rows={15}
            fullWidth
            value={selectedDocument?.texto_extraido || ''}
            InputProps={{
              readOnly: true,
            }}
            variant="outlined"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>
            Fechar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de Análise */}
      <Dialog 
        open={analysisDialog} 
        onClose={() => setAnalysisDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AIIcon sx={{ mr: 1, color: 'primary.main' }} />
            Configurar Análise com IA
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Documento: {selectedDocument?.titulo || `Documento ${selectedDocument?.id}`}
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                select
                fullWidth
                label="Tipo de Análise"
                value={tipoAnalise}
                onChange={(e) => setTipoAnalise(e.target.value)}
                helperText={tipoAnaliseSelecionada?.description}
              >
                {TIPOS_ANALISE.map((tipo) => (
                  <MenuItem key={tipo.value} value={tipo.value}>
                    {tipo.label}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            <Grid item xs={12}>
              <TextField
                select
                fullWidth
                label="Modelo GPT"
                value={modeloGPT}
                onChange={(e) => setModeloGPT(e.target.value)}
                helperText="⚠️ GPT-5 suporta até 7 páginas. Para documentos maiores, use GPT-4.1 (1M tokens)"
                disabled={processing}
              >
                {modelosGPT.map((modelo) => (
                  <MenuItem key={modelo.id} value={modelo.id}>
                    <Box>
                      <Typography variant="body1">
                        {modelo.name}
                        <Chip 
                          label={modelo.category} 
                          size="small" 
                          color="primary"
                          variant="outlined"
                          sx={{ ml: 1, height: 20 }}
                        />
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        {modelo.description}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Custo: {modelo.cost_level} • Velocidade: {modelo.speed}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            {tipoAnalise === 'personalizado' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Instruções Personalizadas"
                  value={promptPersonalizado}
                  onChange={(e) => setPromptPersonalizado(e.target.value)}
                  placeholder="Descreva o que você deseja que a IA analise no documento..."
                  helperText="Seja específico sobre o que você quer extrair ou analisar"
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalysisDialog(false)}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={processAnalysis}
            disabled={processing}
            startIcon={processing ? <CircularProgress size={20} /> : <SendIcon />}
          >
            {processing ? 'Enviando...' : 'Solicitar Análise IA'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIAnalysisPage;