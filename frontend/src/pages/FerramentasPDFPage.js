import React, { useState, useRef } from 'react';
import {
  Box, Paper, Typography, Button, Alert,
  CircularProgress, List, ListItem, ListItemText,
  ListItemIcon, IconButton, Select, MenuItem, FormControl,
  InputLabel, TextField, Grid
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
  Add as AddIcon,
  PhotoLibrary as PhotoLibraryIcon,
  FileCopy as FileCopyIcon,
  PostAdd as PostAddIcon,
  RotateRight as RotateIcon,
  Description as DescriptionIcon,
  LooksOne as LooksOneIcon
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
// FERRAMENTA 5: PDF PARA IMAGEM
// ============================================
const PDFToImage = () => {
  const [arquivo, setArquivo] = useState(null);
  const [dpi, setDpi] = useState(200);
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

  const handleConvert = async () => {
    if (!arquivo) { setError('Selecione um arquivo PDF.'); return; }
    setLoading(true); setError('');

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      formData.append('dpi', dpi);

      const response = await axios.post('/api/documentos/pdf/to-images/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 120000
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'pdf_imagens.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao converter.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone onFilesSelected={handleFile} accept=".pdf" multiple={false}
          icon={<PhotoLibraryIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui" subtitle="Cada página virará uma imagem PNG" />
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
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Resolução (DPI)</InputLabel>
        <Select value={dpi} label="Resolução (DPI)" onChange={(e) => setDpi(e.target.value)}>
          <MenuItem value={150}>150 DPI (rascunho)</MenuItem>
          <MenuItem value={200}>200 DPI (recomendado)</MenuItem>
          <MenuItem value={300}>300 DPI (alta qualidade)</MenuItem>
        </Select>
      </FormControl>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Button variant="contained" fullWidth size="large" onClick={handleConvert}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <PhotoLibraryIcon />}>
        {loading ? 'Convertendo...' : 'Converter PDF para Imagens'}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 6: EXTRAIR PÁGINAS
// ============================================
const ExtractPages = () => {
  const [arquivo, setArquivo] = useState(null);
  const [paginas, setPaginas] = useState('');
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

  const handleExtract = async () => {
    if (!arquivo) { setError('Selecione um arquivo PDF.'); return; }

    const paginasArray = paginas.split(',')
      .map(p => parseInt(p.trim()))
      .filter(p => !isNaN(p) && p > 0);

    if (paginasArray.length === 0) {
      setError('Digite números de página válidos (ex: 1, 3, 5).');
      return;
    }

    setLoading(true); setError('');

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      formData.append('data', JSON.stringify({ paginas: paginasArray }));

      const response = await axios.post('/api/documentos/pdf/extract-pages/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 60000
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'paginas_extraidas.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao extrair páginas.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone onFilesSelected={handleFile} accept=".pdf" multiple={false}
          icon={<FileCopyIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui" subtitle="Depois escolha quais páginas extrair" />
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
      <TextField
        fullWidth label="Páginas para extrair" placeholder="Ex: 1, 3, 5-8, 10"
        value={paginas} onChange={(e) => setPaginas(e.target.value)}
        helperText="Separe por vírgulas. Use hífen para intervalos (ex: 1-5)"
        sx={{ mb: 2 }}
      />
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Button variant="contained" fullWidth size="large" onClick={handleExtract}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <FileCopyIcon />}>
        {loading ? 'Extraindo...' : 'Extrair Páginas'}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 7: INSERIR PÁGINA EM BRANCO
// ============================================
const InsertBlank = () => {
  const [arquivo, setArquivo] = useState(null);
  const [position, setPosition] = useState('');
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

  const handleInsert = async () => {
    if (!arquivo) { setError('Selecione um arquivo PDF.'); return; }
    setLoading(true); setError('');

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      if (position) formData.append('position', position);

      const response = await axios.post('/api/documentos/pdf/insert-blank/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 60000
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'pdf_com_pagina_branca.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao inserir página.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone onFilesSelected={handleFile} accept=".pdf" multiple={false}
          icon={<PostAddIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui" subtitle="Uma página em branco A4 será adicionada" />
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
      <TextField
        fullWidth label="Posição (opcional)" placeholder="Deixe em branco para inserir no final"
        value={position} onChange={(e) => setPosition(e.target.value)}
        helperText="Número da página onde inserir a página em branco"
        sx={{ mb: 2 }}
      />
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Button variant="contained" fullWidth size="large" onClick={handleInsert}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <PostAddIcon />}>
        {loading ? 'Inserindo...' : 'Inserir Página em Branco'}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 8: ROTACIONAR PÁGINAS
// ============================================
const RotatePDF = () => {
  const [arquivo, setArquivo] = useState(null);
  const [rotation, setRotation] = useState(90);
  const [paginas, setPaginas] = useState('');
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

  const handleRotate = async () => {
    if (!arquivo) { setError('Selecione um arquivo PDF.'); return; }
    setLoading(true); setError('');

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      formData.append('rotation', rotation);

      if (paginas.trim()) {
        const paginasArray = paginas.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p));
        formData.append('data', JSON.stringify({ paginas: paginasArray }));
      }

      const response = await axios.post('/api/documentos/pdf/rotate/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 60000
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'pdf_rotacionado.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao rotacionar.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone onFilesSelected={handleFile} accept=".pdf" multiple={false}
          icon={<RotateIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui" subtitle="Rotacione páginas específicas ou todas" />
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
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Rotação</InputLabel>
        <Select value={rotation} label="Rotação" onChange={(e) => setRotation(e.target.value)}>
          <MenuItem value={90}>90° (paisagem → retrato)</MenuItem>
          <MenuItem value={180}>180° (inverter)</MenuItem>
          <MenuItem value={270}>270° (retrato → paisagem)</MenuItem>
        </Select>
      </FormControl>
      <TextField
        fullWidth label="Páginas (opcional)" placeholder="Deixe em branco para rotacionar todas"
        value={paginas} onChange={(e) => setPaginas(e.target.value)}
        helperText="Ex: 1, 3, 5 (rotaciona apenas essas páginas)"
        sx={{ mb: 2 }}
      />
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Button variant="contained" fullWidth size="large" onClick={handleRotate}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <RotateIcon />}>
        {loading ? 'Rotacionando...' : 'Rotacionar PDF'}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 9: PDF PARA WORD
// ============================================
const PDFToDocx = () => {
  const [arquivo, setArquivo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFile = (files) => {
    if (files.length > 0 && files[0].name.toLowerCase().endsWith('.pdf')) {
      setArquivo(files[0]); setError('');
    } else { setError('Selecione um arquivo PDF.'); }
  };

  const handleConvert = async () => {
    if (!arquivo) { setError('Selecione um arquivo PDF.'); return; }
    setLoading(true); setError('');
    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      const response = await axios.post('/api/documentos/pdf/to-docx/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob', timeout: 120000
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url; link.setAttribute('download', 'documento_convertido.docx');
      document.body.appendChild(link); link.click(); link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) { setError(err.response?.data?.error || 'Erro ao converter.'); }
    finally { setLoading(false); }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone onFilesSelected={handleFile} accept=".pdf" multiple={false}
          icon={<DescriptionIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui" subtitle="Será convertido para Word (.docx)" />
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
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Button variant="contained" fullWidth size="large" onClick={handleConvert}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <DescriptionIcon />}>
        {loading ? 'Convertendo...' : 'Converter PDF para Word'}
      </Button>
    </Box>
  );
};

// ============================================
// FERRAMENTA 10: NUMERAR PÁGINAS
// ============================================
const AddPageNumbers = () => {
  const [arquivo, setArquivo] = useState(null);
  const [position, setPosition] = useState('bottom');
  const [startNumber, setStartNumber] = useState(1);
  const [prefix, setPrefix] = useState('');
  const [suffix, setSuffix] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFile = (files) => {
    if (files.length > 0 && files[0].name.toLowerCase().endsWith('.pdf')) {
      setArquivo(files[0]); setError('');
    } else { setError('Selecione um arquivo PDF.'); }
  };

  const handleAddNumbers = async () => {
    if (!arquivo) { setError('Selecione um arquivo PDF.'); return; }
    setLoading(true); setError('');
    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      formData.append('position', position);
      formData.append('start_number', startNumber);
      formData.append('prefix', prefix);
      formData.append('suffix', suffix);
      const response = await axios.post('/api/documentos/pdf/add-numbers/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob', timeout: 60000
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url; link.setAttribute('download', 'pdf_numerado.pdf');
      document.body.appendChild(link); link.click(); link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) { setError(err.response?.data?.error || 'Erro ao numerar.'); }
    finally { setLoading(false); }
  };

  return (
    <Box>
      {!arquivo ? (
        <FileDropZone onFilesSelected={handleFile} accept=".pdf" multiple={false}
          icon={<LooksOneIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />}
          title="Arraste um PDF aqui" subtitle="Adicione numeração às páginas" />
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
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Posição</InputLabel>
        <Select value={position} label="Posição" onChange={(e) => setPosition(e.target.value)}>
          <MenuItem value="bottom">Rodapé</MenuItem>
          <MenuItem value="top">Cabeçalho</MenuItem>
        </Select>
      </FormControl>
      <TextField fullWidth label="Número inicial" type="number" value={startNumber}
        onChange={(e) => setStartNumber(parseInt(e.target.value) || 1)} sx={{ mb: 2 }}
        inputProps={{ min: 1 }} />
      <TextField fullWidth label="Prefixo (opcional)" placeholder="Ex: Página "
        value={prefix} onChange={(e) => setPrefix(e.target.value)} sx={{ mb: 2 }} />
      <TextField fullWidth label="Sufixo (opcional)" placeholder="Ex: /10"
        value={suffix} onChange={(e) => setSuffix(e.target.value)} sx={{ mb: 2 }} />
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Button variant="contained" fullWidth size="large" onClick={handleAddNumbers}
        disabled={!arquivo || loading}
        startIcon={loading ? <CircularProgress size={20} /> : <LooksOneIcon />}>
        {loading ? 'Numerando...' : 'Numerar Páginas'}
      </Button>
    </Box>
  );
};

// ============================================
// PÁGINA PRINCIPAL
// ============================================
const FerramentasPDFPage = () => {
  const [tab, setTab] = useState(0);

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Ferramentas de PDF
      </Typography>

      {/* Grid de ferramentas */}
      <Grid container spacing={1} sx={{ mb: 3 }}>
        {[
          { icon: <MergeIcon />, label: 'Juntar', id: 0 },
          { icon: <SplitIcon />, label: 'Dividir', id: 1 },
          { icon: <CompressIcon />, label: 'Compactar', id: 2 },
          { icon: <ImageIcon />, label: 'Imagem→PDF', id: 3 },
          { icon: <PhotoLibraryIcon />, label: 'PDF→Imagem', id: 4 },
          { icon: <FileCopyIcon />, label: 'Extrair', id: 5 },
          { icon: <PostAddIcon />, label: 'Inserir', id: 6 },
          { icon: <RotateIcon />, label: 'Rotacionar', id: 7 },
          { icon: <DescriptionIcon />, label: 'PDF→Word', id: 8 },
          { icon: <LooksOneIcon />, label: 'Numerar', id: 9 },
        ].map((item) => (
          <Grid item xs={3} sm={3} md={1.5} key={item.id}>
            <Paper
              onClick={() => setTab(item.id)}
              sx={{
                p: 1,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: tab === item.id ? 'primary.main' : 'background.paper',
                color: tab === item.id ? 'white' : 'text.primary',
                '&:hover': { bgcolor: tab === item.id ? 'primary.dark' : 'action.hover' },
                transition: 'all 0.2s'
              }}
            >
              <Box sx={{ fontSize: 28 }}>{item.icon}</Box>
              <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                {item.label}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 3 }}>
        {tab === 0 && <MergePDF />}
        {tab === 1 && <SplitPDF />}
        {tab === 2 && <CompressPDF />}
        {tab === 3 && <ImageToPDF />}
        {tab === 4 && <PDFToImage />}
        {tab === 5 && <ExtractPages />}
        {tab === 6 && <InsertBlank />}
        {tab === 7 && <RotatePDF />}
        {tab === 8 && <PDFToDocx />}
        {tab === 9 && <AddPageNumbers />}
      </Paper>
    </Box>
  );
};

export default FerramentasPDFPage;
