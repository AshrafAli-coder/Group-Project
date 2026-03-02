import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

function RewardChart({ rewards }) {

  if (!rewards || rewards.length === 0) {
    return <h3 style={{ textAlign: "center" }}>No Data Yet</h3>;
  }

  const data = {
    labels: rewards.map((_, index) => index + 1),
    datasets: [
      {
        label: "Reward Over Time",
        data: rewards,
        borderColor: "#00ff88",
        backgroundColor: "#00ff88",
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { labels: { color: "white" } },
    },
    scales: {
      x: { ticks: { color: "white" } },
      y: { ticks: { color: "white" } },
    },
  };

  return (
    <div style={{ width: "80%", margin: "auto" }}>
      <Line data={data} options={options} />
    </div>
  );
}

export default RewardChart;