import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  AlertTitle,
  Divider
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Scanner as ScannerIcon,
  Clear as ClearIcon,
  Save as SaveIcon,
  CheckCircle as CheckCircleIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Description as DocumentIcon
} from '@mui/icons-material';
import axios from '../utils/axiosInstance';

const ScannerPage = () => {
  const [arquivo, setArquivo] = useState(null);
  const [textoExtraido, setTextoExtraido] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Estados para salvar documento
  const [saveDialog, setSaveDialog] = useState(false);
  const [documentTitle, setDocumentTitle] = useState('');
  const [clienteId, setClienteId] = useState('');
  const [clientes, setClientes] = useState([]);
  const [saving, setSaving] = useState(false);

  // Carregar clientes ao montar
  useEffect(() => {
    loadClientes();
  }, []);

  const loadClientes = async () => {
    try {
      const response = await axios.get('/api/clientes/');
      setClientes(response.data.results || []);
    } catch (err) {
      console.error('Erro ao carregar clientes:', err);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setArquivo(file);
      setError('');
      setTextoExtraido('');
      setSuccess('');
    }
  };

  const handleRemoveFile = () => {
    setArquivo(null);
    setTextoExtraido('');
    setSuccess('');
    setError('');
    setDocumentTitle('');
    setClienteId('');
    setSaveDialog(false);
  };

  // ===================================
  // EXTRAÇÃO DE TEXTO - ASSÍNCRONA COM POLLING
  // ===================================

  const handleExtrairTexto = async () => {
    if (!arquivo) return;

    // Valida se é PDF
    if (arquivo.type !== 'application/pdf' && !arquivo.name.toLowerCase().endsWith('.pdf')) {
      setError('Formato não suportado. Envie apenas arquivos PDF.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);

      // Tenta primeiro extração rápida (pypdf - para PDFs digitais)
      try {
        const response = await axios.post('/api/documentos/extrair-texto/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 15000 // 15s timeout (pypdf é instantâneo)
        });

        if (response.data.success) {
          const texto = response.data.texto || '';
          setTextoExtraido(texto);

          if (texto.trim()) {
            setSuccess(response.data.mensagem || 'Texto extraído com sucesso!');
            generateAutoTitle();
            setLoading(false);
            return;
          }
        }
      } catch (fastError) {
        console.log('Extração rápida falhou, tentando OCR assíncrono:', fastError.message);
      }

      // Se extração rápida falhou ou não retornou texto, usa OCR assíncrono
      setSuccess('Iniciando OCR em background. Aguarde...');

      // 1. Envia o arquivo para processamento assíncrono
      const asyncResponse = await axios.post('/api/documentos/ocr-async/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      });

      if (!asyncResponse.data.success) {
        setError(asyncResponse.data.error || 'Erro ao iniciar OCR.');
        setLoading(false);
        return;
      }

      const taskId = asyncResponse.data.task_id;
      console.log('📋 OCR Task ID:', taskId);

      // 2. Polling: consulta o progresso a cada 2 segundos
      const pollInterval = setInterval(async () => {
        try {
          const progressResponse = await axios.get(`/api/documentos/ocr-progress/${taskId}/`, {
            timeout: 10000
          });

          const data = progressResponse.data;
          console.log(`📊 Progresso: ${data.percentage}% - ${data.status}`);

          if (data.status === 'concluido' && data.resultado) {
            clearInterval(pollInterval);
            const texto = data.resultado.texto || '';
            setTextoExtraido(texto);

            if (texto.trim()) {
              setSuccess('OCR concluído com sucesso!');
              generateAutoTitle();
            } else {
              setError('OCR não encontrou texto no documento.');
            }
            setLoading(false);

          } else if (data.status === 'erro') {
            clearInterval(pollInterval);
            setError(data.message || 'Erro no processamento OCR.');
            setLoading(false);

          } else if (data.status === 'not_found') {
            clearInterval(pollInterval);
            setError('Tarefa expirou. Tente novamente.');
            setLoading(false);
          }

          // Atualiza mensagem de progresso
          if (data.status === 'processando' || data.status === 'iniciando') {
            setSuccess(`Processando OCR: ${Math.round(data.percentage)}% - ${data.message}`);
          }

        } catch (pollError) {
          console.error('Erro no polling:', pollError);
          // Não para o polling em caso de erro temporário
        }
      }, 2000);

      // Timeout de segurança: para o polling após 10 minutos
      setTimeout(() => {
        clearInterval(pollInterval);
        if (loading) {
          setError('Tempo limite excedido. O processamento pode estar demorando mais que o esperado.');
          setLoading(false);
        }
      }, 600000);

    } catch (err) {
      const errorMsg = err.response?.data?.error ||
                       (err.code === 'ECONNABORTED' ? 'Tempo limite excedido.' : 'Erro ao processar o PDF.');
      setError(errorMsg);
      console.error('Erro na extração:', err);
      setLoading(false);
    }
  };

  // ===================================
  // SALVAR DOCUMENTO
  // ===================================

  const generateAutoTitle = () => {
    if (arquivo) {
      const baseName = arquivo.name.replace(/\.[^/.]+$/, "");
      const now = new Date();
      const dateTime = now.toLocaleDateString('pt-BR') + ' ' + now.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
      });
      setDocumentTitle(`${baseName} - Digitalizado em ${dateTime}`);
    }
  };

  const handleOpenSaveDialog = () => {
    if (!textoExtraido.trim()) {
      setError('Nenhum texto extraído para salvar. Processe um documento primeiro.');
      return;
    }
    if (!documentTitle) {
      generateAutoTitle();
    }
    setSaveDialog(true);
  };

  const handleSaveDocument = async () => {
    if (!documentTitle.trim()) {
      setError('Por favor, insira um título para o documento.');
      return;
    }

    try {
      setSaving(true);
      setError('');

      const documentData = {
        titulo: documentTitle.trim(),
        texto_extraido: textoExtraido.trim(),
        cliente_id: clienteId ? parseInt(clienteId) : null,
        nome_arquivo_original: arquivo?.name || ''
      };

      const response = await axios.post('/api/documentos/salvar-scanner/', documentData);

      if (response.data.success) {
        setSuccess(`✅ Documento "${documentTitle}" salvo com sucesso! ID: ${response.data.id}`);
        setSaveDialog(false);

        setTimeout(() => {
          if (window.confirm('Documento salvo com sucesso!\n\nDeseja escanear outro documento?')) {
            handleRemoveFile();
          }
        }, 1500);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.details || 'Erro ao salvar documento';
      setError(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <ScannerIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" gutterBottom>
              Scanner de Documentos
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Faça upload de um PDF para extrair o texto automaticamente.
              O sistema extrai o texto de PDFs digitais de forma instantânea.
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

        {/* PASSO 1: UPLOAD */}
        {!textoExtraido && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                1. Selecione o PDF
              </Typography>

              {!arquivo ? (
                <Button variant="contained" component="label" startIcon={<UploadIcon />} size="large">
                  Selecionar Arquivo PDF
                  <input type="file" hidden accept=".pdf" onChange={handleFileChange} />
                </Button>
              ) : (
                <Box>
                  <Chip
                    label={arquivo.name}
                    onDelete={handleRemoveFile}
                    deleteIcon={<ClearIcon />}
                    color="primary"
                    sx={{ maxWidth: 400, mb: 2 }}
                  />
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      size="large"
                      onClick={handleExtrairTexto}
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} /> : <ScannerIcon />}
                    >
                      {loading ? 'Extraindo texto...' : 'Extrair Texto'}
                    </Button>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* LOADING */}
        {loading && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Extraindo texto...
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Processando o PDF. Isso leva apenas alguns segundos.
              </Typography>
            </CardContent>
          </Card>
        )}

        {/* PASSO 2: RESULTADO */}
        {textoExtraido && !loading && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📄 Texto Extraído
              </Typography>

              <TextField
                fullWidth
                multiline
                rows={15}
                value={textoExtraido}
                onChange={(e) => setTextoExtraido(e.target.value)}
                variant="outlined"
                sx={{ my: 2, backgroundColor: 'grey.50' }}
                placeholder="Texto extraído aparecerá aqui..."
              />

              {/* Estatísticas */}
              <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`${textoExtraido.length} caracteres`} color="primary" size="small" />
                <Chip label={`${textoExtraido.split(/\s+/).filter(w => w.length > 0).length} palavras`} color="secondary" size="small" />
                <Chip label={`${textoExtraido.split('\n').length} linhas`} color="info" size="small" />
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Botões */}
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between' }}>
                <Button variant="outlined" onClick={handleRemoveFile} startIcon={<ClearIcon />}>
                  Novo Documento
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  size="large"
                  onClick={handleOpenSaveDialog}
                  startIcon={<SaveIcon />}
                  disabled={!textoExtraido.trim()}
                  sx={{ minWidth: 200, fontSize: '1.1rem', fontWeight: 'bold' }}
                >
                  💾 Salvar no Sistema
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}
      </Paper>

      {/* DIALOG DE SALVAR */}
      <Dialog open={saveDialog} onClose={() => setSaveDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SaveIcon sx={{ mr: 1, color: 'success.main' }} />
            Salvar Documento no Sistema
          </Box>
        </DialogTitle>

        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <AlertTitle>💾 Salvar no Banco de Dados</AlertTitle>
              O documento será salvo apenas no banco de dados do sistema.
              O arquivo físico não será armazenado, apenas o texto extraído.
            </Alert>

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Título do Documento *"
                  value={documentTitle}
                  onChange={(e) => setDocumentTitle(e.target.value)}
                  variant="outlined"
                  required
                  placeholder="Ex: Contrato de Locação - João Silva"
                  helperText="Digite um título descritivo para o documento"
                  InputProps={{
                    startAdornment: <DocumentIcon sx={{ mr: 1, color: 'action.active' }} />
                  }}
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Cliente (Opcional)</InputLabel>
                  <Select
                    value={clienteId}
                    onChange={(e) => setClienteId(e.target.value)}
                    label="Cliente (Opcional)"
                  >
                    <MenuItem value="">
                      <em>Nenhum cliente - Documento geral</em>
                    </MenuItem>
                    {clientes.map((cliente) => (
                      <MenuItem key={cliente.id} value={cliente.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                          {cliente.tipo_cliente === 'pessoa_fisica' ?
                            <PersonIcon sx={{ mr: 1, fontSize: 18, color: 'primary.main' }} /> :
                            <BusinessIcon sx={{ mr: 1, fontSize: 18, color: 'secondary.main' }} />
                          }
                          <Box>
                            <Typography variant="body1">{cliente.nome}</Typography>
                            {cliente.cpf && <Typography variant="caption" color="text.secondary">CPF: {cliente.cpf}</Typography>}
                            {cliente.cnpj && <Typography variant="caption" color="text.secondary">CNPJ: {cliente.cnpj}</Typography>}
                          </Box>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  📋 Preview do Texto Extraído:
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflow: 'auto', bgcolor: 'grey.50' }}>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {textoExtraido.substring(0, 500)}
                    {textoExtraido.length > 500 && '...'}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setSaveDialog(false)} disabled={saving}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleSaveDocument}
            disabled={saving || !documentTitle.trim()}
            startIcon={saving ? <CircularProgress size={20} /> : <CheckCircleIcon />}
            sx={{ minWidth: 150 }}
          >
            {saving ? 'Salvando...' : '💾 Salvar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ScannerPage;
