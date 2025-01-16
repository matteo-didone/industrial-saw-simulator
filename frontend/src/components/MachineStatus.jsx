import React from "react";
import {
  Box,
  Grid,
  Typography,
  Card,
  CardContent,
  LinearProgress,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import {
  Speed,
  Timer,
  PowerSettingsNew,
  Thermostat,
  Build,
  Numbers,
} from "@mui/icons-material";
import { getMachineState } from "../services/api";

const MetricCard = ({
  title,
  value,
  unit,
  icon,
  progress,
  color = "primary",
}) => (
  <Card sx={{ height: "100%" }}>
    <CardContent>
      <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
        {icon}
        <Typography variant="subtitle1" color="textSecondary" sx={{ ml: 1 }}>
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" component="div" gutterBottom>
        {value !== undefined && value !== null ? value.toFixed(1) : "N/A"}{" "}
        {unit}
      </Typography>
      {progress !== undefined && progress !== null && (
        <LinearProgress
          variant="determinate"
          value={Math.min(Math.max(progress, 0), 100)}
          color={color}
          sx={{ mt: 1 }}
        />
      )}
    </CardContent>
  </Card>
);

function MachineStatus() {
  const { data: machineState } = useQuery({
    queryKey: ["machineState"],
    queryFn: getMachineState,
    refetchInterval: 1000,
  });

  const state = machineState?.data || {};

  // Helper per determinare il colore in base al valore e alle soglie
  const getProgressColor = (value, warningThreshold, errorThreshold) => {
    if (value >= errorThreshold) return "error";
    if (value >= warningThreshold) return "warning";
    return "primary";
  };

  // Helper per calcolare la percentuale normalizzata
  const normalizePercentage = (value, max) => {
    if (value === undefined || value === null) return null;
    return (value / max) * 100;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Stato Macchina
      </Typography>

      <Grid container spacing={3}>
        {/* Velocità di taglio */}
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Velocità di Taglio"
            value={state.cuttingspeed}
            unit="m/min"
            icon={<Speed color="primary" />}
            progress={normalizePercentage(state.cuttingspeed, 100)}
          />
        </Grid>

        {/* Pezzi tagliati */}
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Pezzi Tagliati"
            value={state.piecescut}
            unit="pezzi"
            icon={<Numbers color="primary" />}
          />
        </Grid>

        {/* Consumo energetico */}
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Consumo Energetico"
            value={state.powerconsumption}
            unit="kW"
            icon={<PowerSettingsNew color="primary" />}
            progress={normalizePercentage(state.powerconsumption, 15)}
            color={getProgressColor(state.powerconsumption, 8, 10)}
          />
        </Grid>

        {/* Temperatura */}
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Temperatura"
            value={state.temperature}
            unit="°C"
            icon={<Thermostat color="primary" />}
            progress={normalizePercentage(state.temperature, 100)}
            color={getProgressColor(state.temperature, 40, 50)}
          />
        </Grid>

        {/* Usura Lama */}
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Usura Lama"
            value={state.bladewear}
            unit="%"
            icon={<Build color="primary" />}
            progress={state.bladewear}
            color={getProgressColor(state.bladewear, 70, 90)}
          />
        </Grid>

        {/* Stato Attuale */}
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <Timer color="primary" />
                <Typography
                  variant="subtitle1"
                  color="textSecondary"
                  sx={{ ml: 1 }}
                >
                  Stato Attuale
                </Typography>
              </Box>
              <Typography variant="h4" component="div">
                {state.state || "N/A"}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default MachineStatus;
