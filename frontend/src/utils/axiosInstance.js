// src/utils/axiosInstance.js
import axios from 'axios';

// Usa a variável de ambiente ou localhost como fallback
let baseURL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

// Se o frontend estiver em HTTPS, força o backend também usar HTTPS
if (window.location.protocol === 'https:' && baseURL.startsWith('http://')) {
    baseURL = baseURL.replace('http://', 'https://');
    console.log('🔒 Forçando HTTPS para API:', baseURL);
}

// Função para pegar o cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const axiosInstance = axios.create({
    baseURL: baseURL,
    timeout: 600000, // 10 minutos para operações de OCR
    headers: {
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }
});

// Aqui está o interceptor
axiosInstance.interceptors.request.use(
    config => {
        const accessToken = localStorage.getItem('access_token');
        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`;
        }

        // Adiciona o token CSRF a cada requisição
        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }

        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

export default axiosInstance;