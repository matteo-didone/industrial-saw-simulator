// frontend/src/components/ControlPanel.jsx
import React from "react";
import {
  Box,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Alert,
  Snackbar,
} from "@mui/material";
import {
  PlayArrow,
  Stop,
  Pause,
  Security,
  Warning,
  Refresh,
} from "@mui/icons-material";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { sendCommand, getMachineState } from "../services/api";

function ControlPanel() {
  const [errorMessage, setErrorMessage] = React.useState("");
  const queryClient = useQueryClient();

  // Query per lo stato della macchina
  const { data: machineState } = useQuery({
    queryKey: ["machineState"],
    queryFn: getMachineState,
    refetchInterval: 1000,
  });

  // Mutation per i comandi con gestione errori
  const commandMutation = useMutation({
    mutationFn: async ({ command, parameters }) => {
      try {
        const response = await sendCommand({ command, parameters });
        return response;
      } catch (error) {
        console.error("Error sending command:", error);
        throw new Error(error.message || "Errore nell'invio del comando");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["machineState"] });
    },
    onError: (error) => {
      setErrorMessage(error.message);
    },
  });

  const handleCommand = async (command, parameters = {}) => {
    try {
      await commandMutation.mutateAsync({ command, parameters });
    } catch (error) {
      console.error("Command error:", error);
    }
  };

  const state = machineState?.data?.state || "unknown";
  const isAlarm = state === "alarm";
  const isError = state === "error";
  const isRunning = state === "running";
  const isPaused = state === "paused";
  const isInactive = state === "inactive";
  const safetyBarrier = machineState?.data?.safety_barrier;
  const currentMaterial = machineState?.data?.current_material?.toLowerCase();

  // Helper per determinare la severità dell'Alert di stato
  const getStateSeverity = () => {
    switch (state) {
      case "running":
        return "success";
      case "paused":
        return "warning";
      case "alarm":
      case "error":
        return "error";
      case "inactive":
        return "info";
      default:
        return "info";
    }
  };

  // Helper per il testo dello stato
  const getStateMessage = () => {
    switch (state) {
      case "alarm":
        return "La macchina è in stato di allarme - Reset richiesto";
      case "error":
        return "La macchina è in errore - Reset richiesto";
      case "running":
        return "La macchina è in funzione";
      case "paused":
        return "La macchina è in pausa";
      case "inactive":
        return "La macchina è inattiva";
      default:
        return "Stato sconosciuto";
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Controllo Segatrice
      </Typography>

      <Stack spacing={2}>
        {/* Stato corrente */}
        <Alert
          severity={getStateSeverity()}
          sx={{ mb: 2 }}
          action={
            (isAlarm || isError) && (
              <Button
                color="inherit"
                size="small"
                onClick={() => handleCommand("reset")}
                startIcon={<Refresh />}
              >
                Reset
              </Button>
            )
          }
        >
          {getStateMessage()}
        </Alert>

        {/* Controlli principali */}
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            color="success"
            startIcon={<PlayArrow />}
            onClick={() => handleCommand("start")}
            disabled={isRunning || isAlarm || isError}
            fullWidth
          >
            Avvia
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<Stop />}
            onClick={() => handleCommand("stop")}
            disabled={(!isRunning && !isPaused) || isAlarm || isError}
            fullWidth
          >
            Ferma
          </Button>
          <Button
            variant="contained"
            color="warning"
            startIcon={<Pause />}
            onClick={() => handleCommand("pause")}
            disabled={!isRunning || isAlarm || isError}
            fullWidth
          >
            Pausa
          </Button>
        </Stack>

        {/* Barriera di sicurezza */}
        <Button
          variant="outlined"
          startIcon={<Security />}
          onClick={() => handleCommand("toggle_barrier")}
          color={safetyBarrier ? "success" : "error"}
          disabled={isAlarm || isError}
          fullWidth
        >
          Barriera: {safetyBarrier ? "Chiusa" : "Aperta"}
        </Button>

        {/* Selezione materiale */}
        <FormControl fullWidth>
          <InputLabel>Materiale</InputLabel>
          <Select
            value={currentMaterial || ""}
            label="Materiale"
            onChange={(e) => {
              handleCommand("set_material", { material: e.target.value });
            }}
            disabled={isAlarm || isError}
          >
            <MenuItem value="steel">Acciaio</MenuItem>
            <MenuItem value="aluminum">Alluminio</MenuItem>
            <MenuItem value="wood">Legno</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {/* Error Snackbar */}
      <Snackbar
        open={!!errorMessage}
        autoHideDuration={6000}
        onClose={() => setErrorMessage("")}
      >
        <Alert severity="error" onClose={() => setErrorMessage("")}>
          {errorMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default ControlPanel;
