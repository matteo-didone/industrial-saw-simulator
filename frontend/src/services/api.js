// frontend/src/services/api.js
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 5000, // timeout dopo 5 secondi
});

// Interceptor per le richieste
api.interceptors.request.use(
    (config) => {
        console.log('API Request:', {
            url: config.url,
            method: config.method,
            data: config.data,
        });
        return config;
    },
    (error) => {
        console.error('Request Error:', error);
        return Promise.reject(error);
    }
);

// Interceptor per le risposte
api.interceptors.response.use(
    (response) => {
        console.log('API Response:', {
            url: response.config.url,
            status: response.status,
            data: response.data,
        });
        return response;
    },
    (error) => {
        if (error.response) {
            // La richiesta è stata fatta e il server ha risposto con uno status code
            // che non rientra nel range 2xx
            console.error('Response Error:', {
                url: error.config.url,
                status: error.response.status,
                data: error.response.data,
            });

            // Se abbiamo un messaggio di errore dettagliato dal server, lo usiamo
            if (error.response.data?.detail) {
                throw new Error(error.response.data.detail);
            }
            throw new Error(`Errore del server: ${error.response.status}`);
        }

        if (error.request) {
            // La richiesta è stata fatta ma non è stata ricevuta alcuna risposta
            console.error('No Response Error:', error.request);
            throw new Error('Nessuna risposta dal server');
        }

        // Si è verificato un errore durante l'impostazione della richiesta
        console.error('Error:', error.message);
        throw new Error('Errore nella richiesta');
    }
);

export const getMachineState = async () => {
    try {
        const response = await api.get('/state');
        return response.data;
    } catch (error) {
        console.error('Error fetching machine state:', error);
        throw error;
    }
};

export const getMetrics = async () => {
    try {
        const response = await api.get('/metrics');
        return response.data;
    } catch (error) {
        console.error('Error fetching metrics:', error);
        throw error;
    }
};

export const getAlerts = async () => {
    try {
        const response = await api.get('/alerts');
        return response.data;
    } catch (error) {
        console.error('Error fetching alerts:', error);
        throw error;
    }
};

export const sendCommand = async ({ command, parameters = {} }) => {
    try {
        console.log('Sending command:', { command, parameters });
        const response = await api.post('/command', {
            command,
            parameters,
        });
        console.log('Command response:', response.data);  // Log della risposta
        return response.data;
    } catch (error) {
        console.error('Error details:', {
            status: error.response?.status,
            data: error.response?.data,
            message: error.message
        });
        throw error;
    }
};

export default api;