import React, { useState, useRef } from 'react';
import {
  Box, Paper, Typography, Button, Tabs, Tab, Alert,
  CircularProgress, List, ListItem, ListItemText,
  ListItemIcon, IconButton, Select, MenuItem, FormControl,
  InputLabel, TextField, Chip, Grid, Divider, Card, CardContent,
  LinearProgress
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  PictureAsPdf as PdfIcon,
  Merge as MergeIcon,
  ContentCut as SplitIcon,
  Compress as CompressIcon,
  Image as ImageIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  Add as AddIcon
} from '@mui/icons-material';
import axios from '../utils/axiosInstance';

// ============================================
// COMPONENTE DE DRAG AND DROP
// ============================================
const FileDropZone = ({ onFilesSelected, accept, multiple, icon, title, subtitle }) => {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) onFilesSelected(files);
  };

  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) onFilesSelected(files);
    e.target.value = '';
  };

  return (
    <Box
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      sx={{
        border: '2px dashed',
        borderColor: dragging ? 'primary.main' : 'grey.400',
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        cursor: 'pointer',
        bgcolor: dragging ? 'action.hover' : 'background.paper',
        transition: 'all 0.2s',
        '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        hidden
        accept={accept}
        multiple={multiple}
        onChange={handleFileChange}
      />
      {icon}
      <Typography variant="h6" gutterBottom>{title}</Typography>
      <Typography variant="body2" color="text.secondary">{subtitle}</Typography>
    </Box>
  );
};

// ============================================
// COMPONENTE DE LISTA DE ARQUIVOS
// ============================================
const FileList = ({ files, onRemove, onMoveUp, onMoveDown }) => {
  if (files.length === 0) return null;

  return (
    <Paper variant="outlined" sx={{ mt: 2 }}>
      <List dense>
        {files.map((file, index) => (
          <ListItem key={`${file.name}-${index}`} divider>
            <ListItemIcon>
              <PdfIcon color="error" />
            </ListItemIcon>
            <ListItemText
              primary={file.name}
              secondary={`${(file.size / 1024).toFixed(1)} KB`}
            />
            {onMoveUp && index > 0 && (
              <IconButton size="small" onClick={() => onMoveUp(index)}>
                <ArrowUpIcon />
              </IconButton>
            )}
            {onMoveDown && index < files.length - 1 && (
              <IconButton size="small" onClick={() => onMoveDown(index)}>
                <ArrowDownIcon />
              </IconButton>
            )}
            {onRemove && (
              <IconButton size="small" color="error" onClick={() => onRemove(index)}>
                <DeleteIcon />
              </IconButton>
            )}
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

// ============================================
// FERRAMENTA 1: JUNTAR PDFs
// ============================================
const MergePDF = () => {
  const [arquivos, setArquivos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFiles = (files) => {
    const pdfs = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfs.length === 0) {
      setError('Selecione apenas arquivos PDF.');
      return;
    }
    setError('');
    setArquivos(prev => [...prev, ...pdfs]);
  };

  const handleRemove = (index) => {
    setArquivos(prev => prev.filter((_, i) => i !== index));
  };

  const handleMoveUp = (index) => {
    if (index === 0) return;
    setArquivos(prev => {
      const novo = [...prev];
      [novo[index - 1], novo[index]] = [novo[index], novo[index - 1]];
      return novo;
    });
  };

  const handleMoveDown = (index) => {
    setArquivos(prev => {
      if (index >= prev.length - 1) return prev;
      const novo = [...prev];
      [novo[index], novo[index + 1]] = [novo[index + 1], novo[index]];
      return novo;
    });
  };

  const handleMerge = async () => {
    if (arquivos.length < 2) {
      setError('Adicione pelo menos 2 PDFs.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      arquivos.forEach(f => formData.append('arquivos', f));

      const response = await axios.post('/api/documentos/pdf/merge/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 60000
      });

      // Download do arquivo
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'pdf_merged.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao juntar PDFs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <FileDropZone
        onFilesSelected={handleFiles}
        accept=".pdf"
        multiple={true}
        icon={<MergeIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
        title="Arraste PDFs aqui"
        subtitle="ou clique para selecionar. Use as setas para reordenar."
      />

      <FileList
        files={arquivos}
        onRemove={handleRemove}
        onMoveUp={handleMoveUp}
        onMoveDown={handleMoveDown}
      />

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

      <Button
        variant="contained"
        fullWidth
        size="large"
        onClick={handleMerge}
        disabled={arquivos.length < 2 || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <MergeIcon />}
        sx={{ mt: 2 }}
      >
        {loading ? 'Juntando...' : `Juntar ${arquivos.length} PDFs`}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 2: DIVIDIR PDF
// ============================================
const SplitPDF = () => {
  const [arquivo, setArquivo] = useState(null);
  const [intervalos, setIntervalos] = useState([{ inicio: 1, fim: 1, nome: '' }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFile = (files) => {
    if (files.length > 0 && files[0].name.toLowerCase().endsWith('.pdf')) {
      setArquivo(files[0]);
      setError('');
    } else {
      setError('Selecione um arquivo PDF.');
    }
  };

  const handleAddIntervalo = () => {
    const last = intervalos[intervalos.length - 1];
    setIntervalos([...intervalos, { inicio: (last.fim || 1) + 1, fim: (last.fim || 1) + 1, nome: '' }]);
  };

  const handleRemoveIntervalo = (index) => {
    if (intervalos.length <= 1) return;
    setIntervalos(intervalos.filter((_, i) => i !== index));
  };

  const handleIntervaloChange = (index, field, value) => {
    const novo = [...intervalos];
    novo[index][field] = value;
    setIntervalos(novo);
  };

  const handleSplit = async () => {
    if (!arquivo) {
      setError('Selecione um arquivo PDF.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      formData.append('data', JSON.stringify({
        intervalos: intervalos.map((r, i) => ({
          inicio: parseInt(r.inicio) || 1,
          fim: parseInt(r.fim) || 1,
          nome: r.nome || `parte_${i + 1}.pdf`
        }))
      }));

      const response = await axios.post('/api/documentos/pdf/split/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 60000
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'pdf_split.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao dividir PDF.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone
          onFilesSelected={handleFile}
          accept=".pdf"
          multiple={false}
          icon={<SplitIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui"
          subtitle="ou clique para selecionar"
        />
      ) : (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PdfIcon color="error" />
            <Typography>{arquivo.name}</Typography>
            <IconButton size="small" color="error" onClick={() => setArquivo(null)} sx={{ ml: 'auto' }}>
              <DeleteIcon />
            </IconButton>
          </Box>
        </Paper>
      )}

      <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
        Intervalos de Páginas:
      </Typography>

      {intervalos.map((intervalo, index) => (
        <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
          <TextField
            label="Início"
            type="number"
            size="small"
            value={intervalo.inicio}
            onChange={(e) => handleIntervaloChange(index, 'inicio', e.target.value)}
            sx={{ width: 100 }}
            inputProps={{ min: 1 }}
          />
          <Typography>até</Typography>
          <TextField
            label="Fim"
            type="number"
            size="small"
            value={intervalo.fim}
            onChange={(e) => handleIntervaloChange(index, 'fim', e.target.value)}
            sx={{ width: 100 }}
            inputProps={{ min: 1 }}
          />
          <TextField
            label="Nome (opcional)"
            size="small"
            value={intervalo.nome}
            onChange={(e) => handleIntervaloChange(index, 'nome', e.target.value)}
            sx={{ flex: 1 }}
          />
          {intervalos.length > 1 && (
            <IconButton size="small" color="error" onClick={() => handleRemoveIntervalo(index)}>
              <DeleteIcon />
            </IconButton>
          )}
        </Box>
      ))}

      <Button startIcon={<AddIcon />} onClick={handleAddIntervalo} sx={{ mb: 2 }}>
        Adicionar Intervalo
      </Button>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Button
        variant="contained"
        fullWidth
        size="large"
        onClick={handleSplit}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <SplitIcon />}
      >
        {loading ? 'Dividindo...' : 'Dividir PDF'}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 3: COMPACTAR PDF
// ============================================
const CompressPDF = () => {
  const [arquivo, setArquivo] = useState(null);
  const [quality, setQuality] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFile = (files) => {
    if (files.length > 0 && files[0].name.toLowerCase().endsWith('.pdf')) {
      setArquivo(files[0]);
      setError('');
    } else {
      setError('Selecione um arquivo PDF.');
    }
  };

  const handleCompress = async () => {
    if (!arquivo) {
      setError('Selecione um arquivo PDF.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      formData.append('quality', quality);

      const response = await axios.post('/api/documentos/pdf/compress/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 120000
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'pdf_compactado.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao compactar PDF.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone
          onFilesSelected={handleFile}
          accept=".pdf"
          multiple={false}
          icon={<CompressIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui"
          subtitle="ou clique para selecionar"
        />
      ) : (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PdfIcon color="error" />
            <Typography>{arquivo.name} ({(arquivo.size / 1024).toFixed(1)} KB)</Typography>
            <IconButton size="small" color="error" onClick={() => setArquivo(null)} sx={{ ml: 'auto' }}>
              <DeleteIcon />
            </IconButton>
          </Box>
        </Paper>
      )}

      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Nível de Compressão</InputLabel>
        <Select
          value={quality}
          label="Nível de Compressão"
          onChange={(e) => setQuality(e.target.value)}
        >
          <MenuItem value="low">Máxima compressão (menor tamanho)</MenuItem>
          <MenuItem value="medium">Compressão média (recomendado)</MenuItem>
          <MenuItem value="high">Compressão leve (melhor qualidade)</MenuItem>
        </Select>
      </FormControl>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Button
        variant="contained"
        fullWidth
        size="large"
        onClick={handleCompress}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <CompressIcon />}
      >
        {loading ? 'Compactando...' : 'Compactar PDF'}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 4: IMAGEM PARA PDF
// ============================================
const ImageToPDF = () => {
  const [imagens, setImagens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFiles = (files) => {
    const extValidas = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'];
    const validas = files.filter(f => {
      const ext = f.name.toLowerCase().split('.').pop();
      return extValidas.includes('.' + ext);
    });
    if (validas.length === 0) {
      setError('Selecione apenas imagens (JPG, PNG, GIF, BMP, TIFF, WEBP).');
      return;
    }
    setError('');
    setImagens(prev => [...prev, ...validas]);
  };

  const handleRemove = (index) => {
    setImagens(prev => prev.filter((_, i) => i !== index));
  };

  const handleMoveUp = (index) => {
    if (index === 0) return;
    setImagens(prev => {
      const novo = [...prev];
      [novo[index - 1], novo[index]] = [novo[index], novo[index - 1]];
      return novo;
    });
  };

  const handleMoveDown = (index) => {
    setImagens(prev => {
      if (index >= prev.length - 1) return prev;
      const novo = [...prev];
      [novo[index], novo[index + 1]] = [novo[index + 1], novo[index]];
      return novo;
    });
  };

  const handleConvert = async () => {
    if (imagens.length === 0) {
      setError('Adicione pelo menos uma imagem.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      imagens.forEach(f => formData.append('imagens', f));

      const response = await axios.post('/api/documentos/pdf/convert-image/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 60000
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'imagens_convertidas.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao converter imagens.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <FileDropZone
        onFilesSelected={handleFiles}
        accept=".jpg,.jpeg,.png,.gif,.bmp,.tiff,.webp"
        multiple={true}
        icon={<ImageIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
        title="Arraste imagens aqui"
        subtitle="ou clique para selecionar. Use as setas para reordenar."
      />

      {imagens.length > 0 && (
        <Paper variant="outlined" sx={{ mt: 2 }}>
          <List dense>
            {imagens.map((file, index) => (
              <ListItem key={`${file.name}-${index}`} divider>
                <ListItemIcon>
                  <ImageIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={`${(file.size / 1024).toFixed(1)} KB`}
                />
                {index > 0 && (
                  <IconButton size="small" onClick={() => handleMoveUp(index)}>
                    <ArrowUpIcon />
                  </IconButton>
                )}
                {index < imagens.length - 1 && (
                  <IconButton size="small" onClick={() => handleMoveDown(index)}>
                    <ArrowDownIcon />
                  </IconButton>
                )}
                <IconButton size="small" color="error" onClick={() => handleRemove(index)}>
                  <DeleteIcon />
                </IconButton>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

      <Button
        variant="contained"
        fullWidth
        size="large"
        onClick={handleConvert}
        disabled={imagens.length === 0 || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <ImageIcon />}
        sx={{ mt: 2 }}
      >
        {loading ? 'Convertendo...' : `Converter ${imagens.length} imagem(ns) para PDF`}
      </Button>
    </Box>
  );
};

// ============================================
// PÁGINA PRINCIPAL
// ============================================
const FerramentasPDFPage = () => {
  const [tab, setTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Ferramentas de PDF
      </Typography>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tab}
          onChange={handleTabChange}
          variant="fullWidth"
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab icon={<MergeIcon />} label="Juntar" />
          <Tab icon={<SplitIcon />} label="Dividir" />
          <Tab icon={<CompressIcon />} label="Compactar" />
          <Tab icon={<ImageIcon />} label="Imagem → PDF" />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        {tab === 0 && <MergePDF />}
        {tab === 1 && <SplitPDF />}
        {tab === 2 && <CompressPDF />}
        {tab === 3 && <ImageToPDF />}
      </Paper>
    </Box>
  );
};

export default FerramentasPDFPage;
