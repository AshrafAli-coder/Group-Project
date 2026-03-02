import { useEffect, useState } from "react";
import MetricsCard from "./MetricsCard";
import RewardChart from "./RewardChart";

function Dashboard() {
  const [metrics, setMetrics] = useState({});
  const [rewardHistory, setRewardHistory] = useState([]);
  const [evaluation, setEvaluation] = useState(null);

  useEffect(() => {
    const interval = setInterval(() => {
      fetch("http://127.0.0.1:5000/metrics")
        .then(res => res.json())
        .then(data => {
          setMetrics(data);
          if (data.reward !== undefined) {
            setRewardHistory(prev => [...prev.slice(-20), data.reward]);
          }
        });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const startSimulation = () => {
    fetch("http://127.0.0.1:5000/start");
  };

  const stopSimulation = () => {
    fetch("http://127.0.0.1:5000/stop");
  };

  const evaluateModel = () => {
    fetch("http://127.0.0.1:5000/evaluate")
      .then(res => res.json())
      .then(data => setEvaluation(data));
  };

  return (
    <div style={{
      padding: "40px",
      background: "#0f172a",
      minHeight: "100vh",
      color: "white"
    }}>
      <h1 style={{ textAlign: "center", marginBottom: "30px" }}>
        Smart Traffic Control Intelligence System
      </h1>

      <h3>
        Status:
        <span style={{
          marginLeft: "10px",
          color: metrics.status === "running" ? "#00ff88" : "red"
        }}>
          {metrics.status?.toUpperCase()}
        </span>
      </h3>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: "20px",
        marginTop: "20px"
      }}>
        <MetricsCard title="Episode" value={metrics.episode} />
        <MetricsCard title="Reward" value={metrics.reward} />
        <MetricsCard title="Waiting Time" value={metrics.waiting_time} />
        <MetricsCard title="Queue Length" value={metrics.queue_length} />
      </div>

      <div style={{ marginTop: "50px" }}>
        <RewardChart rewards={rewardHistory} />
      </div>

      <div style={{ marginTop: "50px" }}>
        <button onClick={startSimulation}>Start</button>
        <button onClick={stopSimulation} style={{ marginLeft: "20px" }}>
          Stop
        </button>
        <button onClick={evaluateModel} style={{ marginLeft: "20px" }}>
          Evaluate
        </button>
      </div>

      {evaluation && (
        <div style={{ marginTop: "40px" }}>
          <h2>Evaluation Results</h2>
          <p>Fixed Waiting: {evaluation.fixed_waiting}</p>
          <p>RL Waiting: {evaluation.rl_waiting}</p>
          <p>Improvement: {evaluation.improvement}%</p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;