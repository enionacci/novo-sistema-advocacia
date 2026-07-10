// src/pages/EscritorioPage.js
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../utils/axiosInstance';
import {
    Container, Typography, Box, Paper, TextField, Button, CircularProgress,
    List, ListItem, ListItemText, ListItemAvatar, Avatar, IconButton, ListItemSecondaryAction, Grid
} from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AssessmentIcon from '@mui/icons-material/Assessment';
import { useAuth } from '../context/AuthContext';
import PapelDialog from '../components/PapelDialog';
import UserRolesDialog from '../components/UserRolesDialog';

function EscritorioPage() {
    const [escritorio, setEscritorio] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [nomeEdit, setNomeEdit] = useState('');
    const [apiKey, setApiKey] = useState('');
    const [isEditing, setIsEditing] = useState(false);
    const [inviteEmail, setInviteEmail] = useState('');
    const [isInviting, setIsInviting] = useState(false);
    const [logoFile, setLogoFile] = useState(null);
    const [address, setAddress] = useState({
        logradouro: '',
        numero: '',
        complemento: '',
        bairro: '',
        cidade: '',
        estado: '',
        cep: '',
    });
    const [papeis, setPapeis] = useState([]);
    const [permissoes, setPermissoes] = useState([]);
    const [showPapeis, setShowPapeis] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingPapel, setEditingPapel] = useState(null);
    const [isNewPapel, setIsNewPapel] = useState(false);
    const [userRolesDialogOpen, setUserRolesDialogOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const navigate = useNavigate();
    const { user } = useAuth(); // Pega o usuário logado

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const response = await axiosInstance.get('/api/meu-escritorio/');
            setEscritorio(response.data);
            setNomeEdit(response.data.nome);
            setAddress({
                logradouro: response.data.logradouro || '',
                numero: response.data.numero || '',
                complemento: response.data.complemento || '',
                bairro: response.data.bairro || '',
                cidade: response.data.cidade || '',
                estado: response.data.estado || '',
                cep: response.data.cep || '',
            });
            setError('');

            const [papeisRes, permissoesRes] = await Promise.all([
                axiosInstance.get('/api/papeis/'),
                axiosInstance.get('/api/permissoes/')
            ]);
            setPapeis(papeisRes.data);
            setPermissoes(permissoesRes.data);
        } catch (err) {
            setError('Não foi possível carregar os dados do escritório.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [setLoading, setEscritorio, setNomeEdit, setError]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleUpdateEscritorio = async (e) => {
        e.preventDefault();
        setIsEditing(true);

        const formData = new FormData();
        formData.append('nome', nomeEdit);
        formData.append('logradouro', address.logradouro);
        formData.append('numero', address.numero);
        formData.append('complemento', address.complemento);
        formData.append('bairro', address.bairro);
        formData.append('cidade', address.cidade);
        formData.append('estado', address.estado);
        formData.append('cep', address.cep);

        if (apiKey) {
            formData.append('openai_api_key', apiKey);
        }

        if (logoFile) {
            formData.append('logo', logoFile);
        }

        try {
            const response = await axiosInstance.patch('/api/meu-escritorio/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setEscritorio(response.data);
            setApiKey('');
            setLogoFile(null);
            alert('Dados do escritório atualizados com sucesso!');
        } catch (err) {
            alert('Não foi possível atualizar os dados do escritório.');
            console.error(err);
        } finally {
            setIsEditing(false);
        }
    };

    const handleSendInvite = async (e) => {
        e.preventDefault();
        setIsInviting(true);
        try {
            await axiosInstance.post('/api/meu-escritorio/convidar/', { email: inviteEmail });
            alert(`Convite enviado para ${inviteEmail}. O e-mail com as instruções será impresso no console do servidor backend.`);
            setInviteEmail('');
        } catch (err) {
            alert('Não foi possível enviar o convite. Verifique se o e-mail já não é um membro.');
            console.error(err);
        } finally {
            setIsInviting(false);
        }
    };

    const handleDeleteMember = async (perfilId) => {
        if (window.confirm('Tem certeza que deseja remover este membro do escritório?')) {
            try {
                await axiosInstance.delete(`/api/meu-escritorio/membros/${perfilId}/`);
                alert('Membro removido com sucesso.');
                fetchData(); // Re-busca os dados para atualizar a lista
            } catch (err) {
                alert('Não foi possível remover o membro.');
                console.error(err);
            }
        }
    };

    const handleOpenDialog = (papel = null) => {
        setIsNewPapel(!papel);
        setEditingPapel(papel);
        setDialogOpen(true);
    };

    const handleCloseDialog = () => {
        setDialogOpen(false);
        setEditingPapel(null);
    };

    const handleSavePapel = async (papelData) => {
        const payload = {
            nome: papelData.nome,
            permissoes: papelData.permissoes,
        };

        try {
            if (isNewPapel) {
                await axiosInstance.post('/api/papeis/', payload);
                alert('Papel criado com sucesso!');
            } else {
                await axiosInstance.put(`/api/papeis/${papelData.id}/`, payload);
                alert('Papel atualizado com sucesso!');
            }
            fetchData(); // Re-busca os dados para atualizar a lista
            handleCloseDialog();
        } catch (err) {
            alert('Não foi possível salvar o papel.');
            console.error(err);
        }
    };

    const handleDeletePapel = async (papelId) => {
        if (window.confirm('Tem certeza que deseja remover este papel? Esta ação não pode ser desfeita.')) {
            try {
                await axiosInstance.delete(`/api/papeis/${papelId}/`);
                alert('Papel removido com sucesso.');
                fetchData(); // Re-busca os dados para atualizar a lista
            } catch (err) {
                alert('Não foi possível remover o papel.');
                console.error(err);
            }
        }
    };

    const handleOpenUserRolesDialog = (user) => {
        setEditingUser(user);
        setUserRolesDialogOpen(true);
    };

    const handleCloseUserRolesDialog = () => {
        setUserRolesDialogOpen(false);
        setEditingUser(null);
    };

    const handleSaveUserRoles = async (perfilId, papeis) => {
        try {
            await axiosInstance.patch(`/api/membros/${perfilId}/papeis/`, { papeis });
            alert('Papéis do usuário atualizados com sucesso!');
            fetchData(); // Re-busca os dados para atualizar a lista
            handleCloseUserRolesDialog();
        } catch (err) {
            alert('Não foi possível atualizar os papéis do usuário.');
            console.error(err);
        }
    };

    if (loading) {        return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
    }

    if (error) {
        return <Typography color="error" sx={{ mt: 4, textAlign: 'center' }}>{error}</Typography>;
    }

    if (!escritorio) {
        return null; // Ou uma mensagem de 'nenhum escritório encontrado'
    }

    return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mb: 2 }}>
                Voltar para Clientes
            </Button>
            <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Gerenciar Meu Escritório
                </Typography>
                
                <Box component="form" onSubmit={handleUpdateEscritorio} sx={{ mt: 2 }}>
                    <TextField
                        fullWidth
                        label="Nome do Escritório"
                        variant="outlined"
                        value={nomeEdit}
                        onChange={(e) => setNomeEdit(e.target.value)}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        fullWidth
                        type="password"
                        label="Chave de API da OpenAI"
                        variant="outlined"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        sx={{ mb: 2 }}
                        placeholder="Deixe em branco para não alterar"
                        helperText="A chave é armazenada de forma criptografada e não será exibida novamente."
                    />

                    <Button variant="contained" component="label" sx={{ mt: 2, mb: 2 }}>
                        Upload Logotipo
                        <input type="file" hidden accept="image/*" onChange={(e) => setLogoFile(e.target.files[0])} />
                    </Button>
                    {logoFile && <Typography variant="body2">{logoFile.name}</Typography>}
                    {escritorio.logo_url && (
                        <Box sx={{ mt: 2, mb: 2 }}>
                            <Typography variant="subtitle1">Logotipo Atual:</Typography>
                            <img src={escritorio.logo_url} alt="Logotipo" style={{ maxWidth: '200px', marginTop: '10px' }} />
                        </Box>
                    )}

                    <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 4 }}>
                        Endereço
                    </Typography>

                    <Grid container spacing={2}>
                        <Grid item size={6}xs={12}>
                            <TextField fullWidth label="Logradouro" variant="outlined" value={address.logradouro} onChange={(e) => setAddress({ ...address, logradouro: e.target.value })} />
                        </Grid>
                        <Grid item size={2} xs={4}>
                            <TextField fullWidth label="Número" variant="outlined" value={address.numero} onChange={(e) => setAddress({ ...address, numero: e.target.value })} />
                        </Grid>
                        <Grid item xs={8}>
                            <TextField fullWidth label="Complemento" variant="outlined" value={address.complemento} onChange={(e) => setAddress({ ...address, complemento: e.target.value })} />
                        </Grid>
                        <Grid item xs={6}>
                            <TextField fullWidth label="Bairro" variant="outlined" value={address.bairro} onChange={(e) => setAddress({ ...address, bairro: e.target.value })} />
                        </Grid>
                        <Grid item xs={6}>
                            <TextField fullWidth label="Cidade" variant="outlined" value={address.cidade} onChange={(e) => setAddress({ ...address, cidade: e.target.value })} />
                        </Grid>
                        <Grid item xs={4}>
                            <TextField fullWidth label="Estado" variant="outlined" value={address.estado} onChange={(e) => setAddress({ ...address, estado: e.target.value })} />
                        </Grid>
                        <Grid item xs={8}>
                            <TextField fullWidth label="CEP" variant="outlined" value={address.cep} onChange={(e) => setAddress({ ...address, cep: e.target.value })} />
                        </Grid>
                    </Grid>
                    

                    <Button type="submit" variant="contained" disabled={isEditing} sx={{ mt: 2 }}>
                        {isEditing ? 'Salvando...' : 'Salvar Alterações'}
                    </Button>

                    <Button 
                        variant="outlined" 
                        onClick={() => setShowPapeis(!showPapeis)} 
                        sx={{ mt: 2, ml: 2 }}
                    >
                        {showPapeis ? 'Ocultar Gerenciamento de Papéis' : 'Gerenciar Papéis'}
                    </Button>

                    <Button 
                        variant="outlined" 
                        startIcon={<AssessmentIcon />}
                        onClick={() => navigate('/audit-logs')} 
                        sx={{ mt: 2, ml: 2 }}
                    >
                        Auditoria
                    </Button>
                </Box>
            </Paper>

            {showPapeis && (
                <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
                    <Typography variant="h5" component="h2" gutterBottom>
                        Gerenciamento de Papéis
                    </Typography>
                    <Button variant="contained" onClick={() => handleOpenDialog()} sx={{ mb: 2 }}>
                        Novo Papel
                    </Button>
                    <List>
                        {papeis.map(papel => (
                            <ListItem key={papel.id}>
                                <ListItemText 
                                    primary={papel.nome}
                                    secondary={`Permissões: ${papel.permissoes.length}`}
                                />
                                <ListItemSecondaryAction>
                                    <IconButton edge="end" aria-label="edit" onClick={() => handleOpenDialog(papel)}>
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton edge="end" aria-label="delete" onClick={() => handleDeletePapel(papel.id)}>
                                        <DeleteIcon />
                                    </IconButton>
                                </ListItemSecondaryAction>
                            </ListItem>
                        ))}
                    </List>
                </Paper>
            )}

            <PapelDialog 
                open={dialogOpen} 
                onClose={handleCloseDialog} 
                onSave={handleSavePapel} 
                papel={editingPapel}
                permissoes={permissoes}
            />

            <UserRolesDialog
                open={userRolesDialogOpen}
                onClose={handleCloseUserRolesDialog}
                onSave={handleSaveUserRoles}
                user={editingUser}
                papeis={papeis}
            />

            <Paper elevation={3} sx={{ p: 4 }}>
                <Typography variant="h5" component="h2" gutterBottom>
                    Membros do Escritório
                </Typography>
                <List>
                    {escritorio.membros.map(perfil => (
                        <ListItem key={perfil.id}>
                            <ListItemAvatar>
                                <Avatar>
                                    <AccountCircleIcon />
                                </Avatar>
                            </ListItemAvatar>
                            <ListItemText 
                                primary={`${perfil.user.first_name} ${perfil.user.last_name}`.trim() || perfil.user.username}
                                secondary={perfil.papeis.join(', ')}
                            />
                            {user && user.id !== perfil.user.id && (
                                <ListItemSecondaryAction>
                                    <IconButton edge="end" aria-label="edit-roles" onClick={() => handleOpenUserRolesDialog(perfil)}>
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteMember(perfil.id)}>
                                        <DeleteIcon />
                                    </IconButton>
                                </ListItemSecondaryAction>
                            )}
                        </ListItem>
                    ))}
                </List>
            </Paper>

            <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
                <Typography variant="h5" component="h2" gutterBottom>
                    Convidar Novo Membro
                </Typography>
                <Box component="form" onSubmit={handleSendInvite} sx={{ mt: 2 }}>
                    <TextField
                        fullWidth
                        type="email"
                        label="E-mail do Convidado"
                        variant="outlined"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        sx={{ mb: 2 }}
                        required
                    />
                    <Button type="submit" variant="contained" disabled={isInviting}>
                        {isInviting ? 'Enviando...' : 'Enviar Convite'}
                    </Button>
                </Box>
            </Paper>
        </Container>
    );
}

export default EscritorioPage;
