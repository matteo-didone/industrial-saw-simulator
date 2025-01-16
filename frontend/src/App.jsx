// frontend/src/App.jsx
import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Container, Grid, Paper } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Componenti
import ControlPanel from './components/ControlPanel';
import MachineStatus from './components/MachineStatus';
import MetricsChart from './components/MetricsChart';
import AlertPanel from './components/AlertPanel';

// Crea il client per react-query
const queryClient = new QueryClient();

// Tema personalizzato
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ 
          display: 'flex',
          minHeight: '100vh',
          backgroundColor: 'background.default',
          padding: 3
        }}>
          <Container maxWidth="xl">
            <Grid container spacing={3}>
              {/* Pannello di Controllo */}
              <Grid item xs={12} md={4}>
                <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
                  <ControlPanel />
                </Paper>
              </Grid>

              {/* Stato Macchina */}
              <Grid item xs={12} md={8}>
                <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
                  <MachineStatus />
                </Paper>
              </Grid>

              {/* Grafici Metriche */}
              <Grid item xs={12}>
                <Paper elevation={3} sx={{ p: 2 }}>
                  <MetricsChart />
                </Paper>
              </Grid>

              {/* Pannello Allarmi */}
              <Grid item xs={12}>
                <Paper elevation={3} sx={{ p: 2 }}>
                  <AlertPanel />
                </Paper>
              </Grid>
            </Grid>
          </Container>
        </Box>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;