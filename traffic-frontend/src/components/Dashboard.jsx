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
            setRewardHistory(prev => [...prev.slice(-40), data.reward]);
          }

        })
        .catch(err => console.error("Error fetching metrics:", err));

    }, 2000);

    return () => clearInterval(interval);

  }, []);


  const startSimulation = () => {
    fetch("http://127.0.0.1:5000/start")
      .catch(err => console.error("Start error:", err));
  };

  const stopSimulation = () => {
    fetch("http://127.0.0.1:5000/stop")
      .catch(err => console.error("Stop error:", err));
  };

  const evaluateModel = () => {
    fetch("http://127.0.0.1:5000/evaluate")
      .then(res => res.json())
      .then(data => setEvaluation(data))
      .catch(err => console.error("Evaluation error:", err));
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

      <div style={{ marginBottom: "20px" }}>
        <span
          style={{
            padding: "8px 20px",
            borderRadius: "20px",
            background:
              metrics.status === "running"
                ? "rgba(0,255,136,0.2)"
                : "rgba(255,0,0,0.2)",
            color:
              metrics.status === "running"
                ? "#00ff88"
                : "red",
            fontWeight: "bold",
          }}
        >
          {metrics.status?.toUpperCase() || "STOPPED"}
        </span>
      </div>

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

      <div style={{ marginTop: "50px", textAlign: "center" }}>

        <button
          onClick={startSimulation}
          style={{
            padding: "10px 25px",
            background: "#00ff88",
            border: "none",
            borderRadius: "8px",
            marginRight: "20px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Start
        </button>

        <button
          onClick={stopSimulation}
          style={{
            padding: "10px 25px",
            background: "red",
            border: "none",
            borderRadius: "8px",
            marginRight: "20px",
            cursor: "pointer",
            color: "white",
            fontWeight: "bold",
          }}
        >
          Stop
        </button>

        <button
          onClick={evaluateModel}
          style={{
            padding: "10px 25px",
            background: "#6366f1",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            color: "white",
            fontWeight: "bold",
          }}
        >
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
