function MetricsCard({ title, value }) {

  const formattedValue =
    typeof value === "number"
      ? value.toFixed(2)
      : value || 0;

  return (
    <div
      style={{
        background: "linear-gradient(145deg, #1e293b, #0f172a)",
        padding: "25px",
        borderRadius: "15px",
        textAlign: "center",
        boxShadow: "0 0 15px rgba(0,255,136,0.2)",
      }}
    >
      <h3 style={{ color: "#94a3b8" }}>{title}</h3>
      <h2 style={{ fontSize: "28px", color: "#00ff88" }}>
        {formattedValue}
      </h2>
    </div>
  );
}

export default MetricsCard;
