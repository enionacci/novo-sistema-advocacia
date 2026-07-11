/**
 * Layout Principal com Menu Lateral (Drawer)
 * 
 * Funcionalidades:
 * - Menu lateral permanente (desktop)
 * - Menu colapsável (mobile)
 * - Controle de permissões para exibir itens
 * - Avatar com submenu
 * - Breadcrumbs
 */

import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  Collapse,
  Tooltip,
  useTheme,
  useMediaQuery,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Description as DocumentIcon,
  Assessment as AuditIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  ExpandLess,
  ExpandMore,
  Add as AddIcon,
  List as ListIcon,
  Category as CategoryIcon,
  BarChart as StatsIcon,
  Scanner as ScannerIcon,
  Psychology as AIIcon,
  Security as SecurityIcon,
  Gavel as GavelIcon,
  Build as BuildIcon,
} from '@mui/icons-material';

const drawerWidth = 260;

const Layout = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logoutAction, escritorio, hasPermission } = useAuth();

  // Estados
  const [drawerOpen, setDrawerOpen] = useState(!isMobile);
  const [anchorElUser, setAnchorElUser] = useState(null);
  const [clientesOpen, setClientesOpen] = useState(false);
  const [auditoriaOpen, setAuditoriaOpen] = useState(false);
  const [arquivosOpen, setArquivosOpen] = useState(false);
  const [processosOpen, setProcessosOpen] = useState(false);

  // Handlers
  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleUserMenuOpen = (event) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorElUser(null);
  };

  const handleLogout = () => {
    handleUserMenuClose();
    logoutAction();
  };

  const handleNavigate = (path) => {
    navigate(path);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  // Verifica se rota está ativa
  const isActive = (path) => {
    return location.pathname === path;
  };

  const isParentActive = (paths) => {
    return paths.some(path => location.pathname.startsWith(path));
  };

  // Estrutura do menu com permissões
  const menuItems = [
    {
      id: 'clientes',
      label: 'Clientes',
      icon: <PeopleIcon />,
      permission: 'ver_cliente',
      submenu: [
        {
          id: 'clientes-listar',
          label: 'Listar Clientes',
          icon: <ListIcon />,
          path: '/',
          permission: 'ver_cliente',
        },
        {
          id: 'clientes-novo',
          label: 'Novo Cliente',
          icon: <AddIcon />,
          path: '/clientes/novo',
          permission: 'criar_cliente',
        },
      ],
    },
    {
      id: 'processos',
      label: 'Processos',
      icon: <GavelIcon />,
      permission: 'ver_cliente', // Usa mesma permissão de clientes por enquanto
      submenu: [
        {
          id: 'processos-listar',
          label: 'Listar Processos',
          icon: <ListIcon />,
          path: '/processos',
          permission: 'ver_cliente',
        },
        {
          id: 'processos-novo',
          label: 'Novo Processo',
          icon: <AddIcon />,
          path: '/processos/novo',
          permission: 'criar_cliente',
        },
      ],
    },
    {
      id: 'arquivos',
      label: 'Arquivos',
      icon: <DocumentIcon />,
      permission: 'ver_arquivos',
      submenu: [
        {
          id: 'scanner',
          label: 'Escanear Arquivo',
          icon: <ScannerIcon />,
          path: '/scanner',
          permission: 'escanear_arquivo',
        },
        {
          id: 'anonimizar',
          label: 'Anonimizar Dados',
          icon: <SecurityIcon />,
          path: '/anonimizar',
          permission: 'anonimizar_arquivo',
        },
        {
          id: 'analise-ia',
          label: 'Análise com IA',
          icon: <AIIcon />,
          path: '/analise-ia',
          permission: 'analisar_arquivo_ia',
        },
        {
          id: 'ferramentas-pdf',
          label: 'Ferramentas PDF',
          icon: <BuildIcon />,
          path: '/ferramentas-pdf',
          permission: 'ver_arquivos',
        },
        {
          id: 'documentos-listar',
          label: 'Arquivos Salvos',
          icon: <ListIcon />,
          path: '/documentos',
          permission: 'ver_arquivos',
        },
        {
          id: 'analises-listar',
          label: 'Análises Realizadas',
          icon: <AIIcon />,
          path: '/analises',
          permission: 'ver_arquivos',
        },
      ],
    },
    {
      id: 'auditoria',
      label: 'Auditoria',
      icon: <AuditIcon />,
      permission: 'ver_auditoria',
      submenu: [
        {
          id: 'auditoria-logs',
          label: 'Logs de Auditoria',
          icon: <ListIcon />,
          path: '/audit-logs',
          permission: 'ver_auditoria',
        },
        {
          id: 'auditoria-stats',
          label: 'Estatísticas',
          icon: <StatsIcon />,
          path: '/audit-logs/stats',
          permission: 'ver_auditoria',
        },
      ],
    },
    {
      id: 'configuracoes',
      label: 'Configurações',
      icon: <SettingsIcon />,
      path: '/meu-escritorio',
      permission: 'gerenciar_escritorio',
    },
  ];

  // Filtra itens do menu baseado em permissões
  const filterMenuByPermission = (items) => {
    return items.filter(item => {
      // Se não tem permissão definida, sempre exibe
      if (!item.permission) return true;
      
      // Verifica permissão
      if (!hasPermission(item.permission)) return false;
      
      // Se tem submenu, filtra recursivamente
      if (item.submenu) {
        item.submenu = filterMenuByPermission(item.submenu);
        // Se após filtrar não sobrou nenhum item, não exibe o pai
        return item.submenu.length > 0;
      }
      
      return true;
    });
  };

  const visibleMenuItems = filterMenuByPermission([...menuItems]);

  return (
    <Box sx={{ display: 'flex' }}>
      {/* AppBar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: 'primary.main',
        }}
      >
        <Toolbar>
          {/* Menu Icon (Mobile) */}
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {/* Título */}
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {location.pathname === '/' && 'Clientes'}
            {location.pathname === '/clientes/novo' && 'Novo Cliente'}
            {location.pathname === '/processos' && 'Processos'}
            {location.pathname === '/processos/novo' && 'Novo Processo'}
            {location.pathname.startsWith('/processos/') && !location.pathname.includes('/novo') && 'Detalhes do Processo'}
            {location.pathname === '/scanner' && 'Arquivos - Escanear'}
            {location.pathname === '/anonimizar' && 'Arquivos - Anonimizar'}
            {location.pathname === '/analise-ia' && 'Arquivos - Análise IA'}
            {location.pathname === '/documentos' && 'Arquivos - Salvos'}
            {location.pathname === '/analises' && 'Arquivos - Análises'}
            {location.pathname.startsWith('/audit-logs') && 'Auditoria'}
            {location.pathname === '/meu-escritorio' && 'Meu Escritório'}
          </Typography>

          {/* User Menu */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {user?.perfil?.papel_principal && (
              <Chip
                label={user.perfil.papel_principal}
                size="small"
                color="secondary"
                sx={{ display: { xs: 'none', sm: 'flex' } }}
              />
            )}
            <Tooltip title="Menu do Usuário">
              <IconButton onClick={handleUserMenuOpen} sx={{ p: 0 }}>
                <Avatar
                  alt={user?.username || 'User'}
                  sx={{ bgcolor: 'secondary.main' }}
                >
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </Avatar>
              </IconButton>
            </Tooltip>
          </Box>

          {/* User Dropdown Menu */}
          <Menu
            anchorEl={anchorElUser}
            open={Boolean(anchorElUser)}
            onClose={handleUserMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem disabled>
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  {user?.username}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.email}
                </Typography>
              </Box>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { handleNavigate('/meu-escritorio'); handleUserMenuClose(); }}>
              <ListItemIcon>
                <BusinessIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Meu Escritório</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Sair</ListItemText>
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={drawerOpen}
        onClose={handleDrawerToggle}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Box>
          {/* Espaçador para AppBar */}
          <Toolbar />
          
          {/* Header do Drawer */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              px: 2,
              py: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {escritorio?.logo_url && (
                <img
                  src={escritorio.logo_url}
                  alt="Logo"
                  style={{ height: 35, width: 'auto' }}
                />
              )}
              <Typography variant="h6" noWrap component="div">
                {escritorio?.nome || 'Sistema'}
              </Typography>
            </Box>
            {!isMobile && (
              <IconButton onClick={handleDrawerToggle}>
                <ChevronLeftIcon />
              </IconButton>
            )}
          </Box>

          <Divider />

          {/* Menu Items */}
          <List sx={{ px: 1 }}>
            {visibleMenuItems.map((item) => (
              <React.Fragment key={item.id}>
                {item.submenu ? (
                  // Item com submenu
                  <>
                    <ListItemButton
                      onClick={() => {
                        if (item.id === 'clientes') setClientesOpen(!clientesOpen);
                        if (item.id === 'processos') setProcessosOpen(!processosOpen);
                        if (item.id === 'arquivos') setArquivosOpen(!arquivosOpen);
                        if (item.id === 'auditoria') setAuditoriaOpen(!auditoriaOpen);
                      }}
                      selected={isParentActive(item.submenu.map(sub => sub.path))}
                      sx={{
                        borderRadius: 1,
                        mb: 0.5,
                      }}
                    >
                      <ListItemIcon>{item.icon}</ListItemIcon>
                      <ListItemText primary={item.label} />
                      {(item.id === 'clientes' && clientesOpen) ||
                       (item.id === 'processos' && processosOpen) ||
                       (item.id === 'arquivos' && arquivosOpen) ||
                       (item.id === 'auditoria' && auditoriaOpen) ? (
                        <ExpandLess />
                      ) : (
                        <ExpandMore />
                      )}
                    </ListItemButton>

                    <Collapse
                      in={
                        (item.id === 'clientes' && clientesOpen) ||
                        (item.id === 'processos' && processosOpen) ||
                        (item.id === 'arquivos' && arquivosOpen) ||
                        (item.id === 'auditoria' && auditoriaOpen)
                      }
                      timeout="auto"
                      unmountOnExit
                    >
                      <List component="div" disablePadding>
                        {item.submenu.map((subitem) => (
                          <ListItemButton
                            key={subitem.id}
                            onClick={() => handleNavigate(subitem.path)}
                            selected={isActive(subitem.path)}
                            sx={{
                              pl: 4,
                              borderRadius: 1,
                              mb: 0.5,
                            }}
                          >
                            <ListItemIcon>{subitem.icon}</ListItemIcon>
                            <ListItemText primary={subitem.label} />
                          </ListItemButton>
                        ))}
                      </List>
                    </Collapse>
                  </>
                ) : (
                  // Item simples sem submenu
                  <ListItemButton
                    onClick={() => handleNavigate(item.path)}
                    selected={isActive(item.path)}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                    }}
                  >
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label} />
                  </ListItemButton>
                )}
              </React.Fragment>
            ))}
          </List>

          {/* Footer do Drawer */}
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Sistema para Advocacia
            </Typography>
            <br />
            <Typography variant="caption" color="text.secondary">
              v1.0.0
            </Typography>
          </Box>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout;
