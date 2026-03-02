import Dashboard from "./components/Dashboard";

function App() {
  return (
    <div style={{ background: "#121212", minHeight: "100vh", color: "white" }}>
      <h1 style={{ textAlign: "center", padding: "20px" }}>
        Smart Traffic Control Dashboard
      </h1>
      <Dashboard />
    </div>
  );
}

export default App;