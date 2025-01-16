import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Card,
  CardContent,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { getMetrics } from "../services/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function MetricsChart() {
  const [historicalData, setHistoricalData] = useState({
    power: [],
    speed: [],
    temperature: [],
    timestamps: [],
  });

  const [selectedMetric, setSelectedMetric] = useState("all");

  const { data: metricsData } = useQuery({
    queryKey: ["metrics"],
    queryFn: getMetrics,
    refetchInterval: 1000,
  });

  useEffect(() => {
    if (metricsData?.data) {
      const now = new Date().toLocaleTimeString();

      setHistoricalData((prev) => {
        const maxPoints = 60;
        const power = [
          ...prev.power,
          metricsData.data.powerconsumption.current,
        ].slice(-maxPoints);
        const speed = [
          ...prev.speed,
          metricsData.data.cuttingspeed.current,
        ].slice(-maxPoints);
        const temperature = [
          ...prev.temperature,
          metricsData.data.temperature.current,
        ].slice(-maxPoints);
        const timestamps = [...prev.timestamps, now].slice(-maxPoints);

        return { power, speed, temperature, timestamps };
      });
    }
  }, [metricsData]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 0,
    },
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Andamento Metriche nel Tempo",
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: "Tempo",
        },
        ticks: {
          maxRotation: 45,
          minRotation: 45,
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: "Valore",
        },
        beginAtZero: true,
      },
    },
  };

  const chartData = {
    labels: historicalData.timestamps,
    datasets: [
      ...(selectedMetric === "all" || selectedMetric === "power"
        ? [
            {
              label: "Consumo Energetico (kW)",
              data: historicalData.power,
              borderColor: "rgb(255, 99, 132)",
              backgroundColor: "rgba(255, 99, 132, 0.5)",
              tension: 0.1,
              borderWidth: 2,
            },
          ]
        : []),
      ...(selectedMetric === "all" || selectedMetric === "speed"
        ? [
            {
              label: "Velocità di Taglio (m/min)",
              data: historicalData.speed,
              borderColor: "rgb(53, 162, 235)",
              backgroundColor: "rgba(53, 162, 235, 0.5)",
              tension: 0.1,
              borderWidth: 2,
            },
          ]
        : []),
      ...(selectedMetric === "all" || selectedMetric === "temperature"
        ? [
            {
              label: "Temperatura (°C)",
              data: historicalData.temperature,
              borderColor: "rgb(75, 192, 192)",
              backgroundColor: "rgba(75, 192, 192, 0.5)",
              tension: 0.1,
              borderWidth: 2,
            },
          ]
        : []),
    ],
  };

  return (
    <Box sx={{ width: "100%", height: "100%", minHeight: "500px" }}>
      <Box
        sx={{
          mb: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h6">Metriche in Tempo Reale</Typography>

        <ToggleButtonGroup
          value={selectedMetric}
          exclusive
          onChange={(e, value) => value && setSelectedMetric(value)}
          size="small"
        >
          <ToggleButton value="all">Tutte</ToggleButton>
          <ToggleButton value="power">Consumo</ToggleButton>
          <ToggleButton value="speed">Velocità</ToggleButton>
          <ToggleButton value="temperature">Temperatura</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Card sx={{ height: "calc(100% - 48px)" }}>
        <CardContent sx={{ height: "100%", p: 2 }}>
          <Box sx={{ width: "100%", height: "100%", minHeight: "400px" }}>
            <Line options={chartOptions} data={chartData} />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default MetricsChart;
