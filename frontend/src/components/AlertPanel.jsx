import React from "react";
import { useQuery } from "@tanstack/react-query";
import { getAlerts } from "../services/api";
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Chip,
  Divider,
  Stack,
} from "@mui/material";
import { Warning, Error, Info, CheckCircle } from "@mui/icons-material";

const AlertItem = ({ alert }) => {
  const severityConfig = {
    critical: {
      icon: <Error color="error" />,
      color: "error",
    },
    warning: {
      icon: <Warning color="warning" />,
      color: "warning",
    },
    info: {
      icon: <Info color="info" />,
      color: "info",
    },
  };

  const config = severityConfig[alert.severity] || severityConfig.info;

  return (
    <>
      <ListItem
        sx={{
          bgcolor: `${config.color}.lighter`,
          borderRadius: 1,
          mb: 1,
          flexDirection: "column",
          alignItems: "flex-start",
        }}
      >
        <Box sx={{ display: "flex", width: "100%", alignItems: "flex-start" }}>
          <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
            {config.icon}
          </ListItemIcon>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body1">{alert.message}</Typography>
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{ mt: 1 }}
            >
              <Chip
                label={alert.type}
                size="small"
                color={config.color}
                variant="outlined"
              />
              <Typography variant="caption" color="text.secondary">
                {new Date(alert.timestamp).toLocaleString()}
              </Typography>
            </Stack>
          </Box>
          {alert.active && (
            <Chip
              label="Attivo"
              color={config.color}
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </Box>
      </ListItem>
      <Divider sx={{ my: 1 }} />
    </>
  );
};

function AlertPanel() {
  const { data: alertsData } = useQuery({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    refetchInterval: 1000,
  });

  const alerts = alertsData?.data || [];
  const activeAlerts = alerts.filter((alert) => alert.active);
  const hasActiveAlerts = activeAlerts.length > 0;

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h6">Allarmi e Notifiche</Typography>
        <Chip
          icon={hasActiveAlerts ? <Warning /> : <CheckCircle />}
          label={
            hasActiveAlerts
              ? `${activeAlerts.length} allarmi attivi`
              : "Nessun allarme attivo"
          }
          color={hasActiveAlerts ? "error" : "success"}
        />
      </Box>

      <Paper sx={{ maxHeight: 400, overflow: "auto", p: 2 }}>
        {alerts.length > 0 ? (
          <List>
            {alerts.map((alert, index) => (
              <AlertItem key={`${alert.type}-${index}`} alert={alert} />
            ))}
          </List>
        ) : (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              p: 3,
            }}
          >
            <Typography color="text.secondary">
              Nessun allarme da mostrare
            </Typography>
          </Box>
        )}
      </Paper>

      <Box sx={{ mt: 2, display: "flex", gap: 2 }}>
        <Chip
          size="small"
          icon={<Error fontSize="small" />}
          label="Critico"
          color="error"
          variant="outlined"
        />
        <Chip
          size="small"
          icon={<Warning fontSize="small" />}
          label="Avviso"
          color="warning"
          variant="outlined"
        />
        <Chip
          size="small"
          icon={<Info fontSize="small" />}
          label="Informazione"
          color="info"
          variant="outlined"
        />
      </Box>
    </Box>
  );
}

export default AlertPanel;
