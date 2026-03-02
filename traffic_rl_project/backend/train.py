import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
import traci
import matplotlib.pyplot as plt
import csv
from collections import deque

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rl_agent.model import DQN

# ==============================
# CONFIG
# ==============================
sumoBinary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
sumoConfig = os.path.join("sumo_config", "simulation.sumocfg")

TLS_ID = "B1"
EPISODES = 60
MIN_GREEN = 15

GAMMA = 0.99
LR = 0.0003
BATCH_SIZE = 64
MEMORY_SIZE = 10000

EPSILON_START = 1.0
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.97

TARGET_UPDATE = 1000
MAX_STEPS = 3000

REWARD_SCALE = 0.005
SWITCH_PENALTY = -0.5


def get_sumo_cmd(seed):
    return [
        sumoBinary,
        "-c", sumoConfig,
        "--start",
        "--quit-on-end",
        "--seed", str(seed)
    ]


def train(update_callback=None, stop_flag=None):

    memory = deque(maxlen=MEMORY_SIZE)
    reward_history = []
    

    if traci.isLoaded():
        traci.close()
    traci.start(get_sumo_cmd(1))
    

    lanes = traci.trafficlight.getControlledLanes(TLS_ID)
    lanes = list(dict.fromkeys(lanes))
    logic = traci.trafficlight.getAllProgramLogics(TLS_ID)[0]
    action_size = len(logic.getPhases())
    traci.close()

    state_size = len(lanes) * 2 + 1

    online_net = DQN(state_size, action_size)
    target_net = DQN(state_size, action_size)
    target_net.load_state_dict(online_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(online_net.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    epsilon = EPSILON_START
    step_counter = 0
    best_reward = -float("inf")

    for episode in range(EPISODES):

        if stop_flag and stop_flag():
            print("Training Stopped by User")
            break

        traci.start(get_sumo_cmd(episode + 1))

        total_reward = 0
        total_waiting_time = 0      # ✅ FIXED
        total_queue_length = 0      # ✅ FIXED

        time_since_last_change = 0
        steps = 0

        while traci.simulation.getMinExpectedNumber() > 0 and steps < MAX_STEPS:

            steps += 1

            vehicle_counts = [
                traci.lane.getLastStepVehicleNumber(lane)
                for lane in lanes
            ]

            waiting_times = [
                traci.lane.getWaitingTime(lane)
                for lane in lanes
            ]

            current_phase = traci.trafficlight.getPhase(TLS_ID)

            vehicle_counts = [v / 20.0 for v in vehicle_counts]  # assume max 20 vehicles
            waiting_times = [w / 10000.0 for w in waiting_times]  # scale down
            phase_norm = current_phase / action_size

            state = np.array(
            vehicle_counts + waiting_times + [phase_norm],
            dtype=np.float32
            )

            state_tensor = torch.FloatTensor(state).unsqueeze(0)

            # Epsilon-greedy
            if random.random() < epsilon:
                action = random.randrange(action_size)
            else:
                with torch.no_grad():
                    action = torch.argmax(online_net(state_tensor)).item()

            switched = False
            if action != current_phase and time_since_last_change >= MIN_GREEN:
                traci.trafficlight.setPhase(TLS_ID, action)
                time_since_last_change = 0
                switched = True

            traci.simulationStep()
            time_since_last_change += 1

            # 🔥 Reward calculation
            raw_wait = sum(
                traci.lane.getWaitingTime(lane) for lane in lanes
            )

            reward = -raw_wait * REWARD_SCALE

            if switched:
                reward += SWITCH_PENALTY

            total_reward += reward

            # ✅ Accumulate episode metrics
            total_waiting_time += raw_wait
            total_queue_length += sum(vehicle_counts)

            # Next state
            vehicle_counts_next = [
                traci.lane.getLastStepVehicleNumber(lane)
                for lane in lanes
            ]

            waiting_times_next = [
                traci.lane.getWaitingTime(lane)
                for lane in lanes
            ]

            current_phase_next = traci.trafficlight.getPhase(TLS_ID)

            next_state = np.array(
                vehicle_counts_next + waiting_times_next + [current_phase_next],
                dtype=np.float32
            )

            done = (steps >= MAX_STEPS or
                    traci.simulation.getMinExpectedNumber() <= 0)

            memory.append((state, action, reward, next_state, done))
            step_counter += 1

            # Training step
            if len(memory) >= BATCH_SIZE:

                batch = random.sample(memory, BATCH_SIZE)

                states = torch.FloatTensor([b[0] for b in batch])
                actions = torch.LongTensor([b[1] for b in batch])
                rewards = torch.FloatTensor([b[2] for b in batch])
                next_states = torch.FloatTensor([b[3] for b in batch])
                dones = torch.FloatTensor([b[4] for b in batch])

                q_values = online_net(states)
                next_q_online = online_net(next_states)
                next_q_target = target_net(next_states)

                target = q_values.clone()

                for i in range(BATCH_SIZE):
                    best_action = torch.argmax(next_q_online[i])
                    target_val = rewards[i] + GAMMA * next_q_target[i][best_action] * (1 - dones[i])
                    target[i][actions[i]] = target_val

                loss = loss_fn(q_values, target.detach())

                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(online_net.parameters(), 1.0)
                optimizer.step()

                if step_counter % TARGET_UPDATE == 0:
                    target_net.load_state_dict(online_net.state_dict())

        traci.close()

        epsilon = max(EPSILON_MIN, epsilon * EPSILON_DECAY)
        reward_history.append(total_reward)

        print(f"Episode {episode+1}/{EPISODES} | "
              f"Reward: {total_reward:.2f} | "
              f"Waiting: {total_waiting_time:.2f} | "
              f"Queue: {total_queue_length:.2f} | "
              f"Epsilon: {epsilon:.3f}")

        # ✅ Send FULL episode metrics to dashboard
        if update_callback:
            update_callback({
                "episode": episode + 1,
                "reward": float(total_reward),
                "waiting_time": float(total_waiting_time),
                "queue_length": float(total_queue_length),
            })

        # Save best model
        if total_reward > best_reward:
            best_reward = total_reward
            os.makedirs("models", exist_ok=True)
            torch.save(online_net.state_dict(),
                       "models/traffic_dqn_model.pth")

    os.makedirs("results", exist_ok=True)

    plt.plot(reward_history)
    plt.title("Stable Double DQN Training")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.savefig("results/training_curve.png")
    plt.close()

    print("\nTraining Complete. Stable Model Saved.")