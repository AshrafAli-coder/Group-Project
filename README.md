# Traffic Signal Control using Reinforcement Learning (SUMO)

This is a group project focused on simulating and optimizing traffic signal control using **Reinforcement Learning (RL)** with the **SUMO (Simulation of Urban MObility)** traffic simulator.

The project aims to reduce traffic congestion by learning optimal traffic light phases based on real-time traffic conditions.

---

## 📁 Project Files

| File Name | Description |
|---------|------------|
| `YYY.net.xml` | Road network definition |
| `YYY.rou.xml` | Vehicle routes and traffic flow |
| `YYY.add.xml` | Additional elements (traffic lights, detectors, etc.) |
| `YYY.sumocfg` | SUMO configuration file |

---

## 🛠 Tools & Technologies

- **SUMO** (Traffic Simulation)
- **Python**
- **TraCI API**
- **Reinforcement Learning**
- **Git & GitHub**

---

## 🎯 Project Objectives

- Simulate a traffic junction using SUMO
- Define state, action, and reward for RL agent
- Optimize traffic signal timing
- Minimize vehicle waiting time and congestion

---

## ▶️ How to Run the Simulation

1. Install SUMO  
   https://www.eclipse.org/sumo/

2. Open terminal and run:
   ```bash
   sumo-gui -c YYY.sumocfg
