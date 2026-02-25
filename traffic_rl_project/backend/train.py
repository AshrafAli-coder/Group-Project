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
EPISODES = 150
MIN_GREEN = 15

GAMMA = 0.99
LR = 0.0003
BATCH_SIZE = 64
MEMORY_SIZE = 10000

EPSILON_START = 1.0
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.990

TARGET_UPDATE = 1000
MAX_STEPS = 3000

REWARD_SCALE = 0.001
SWITCH_PENALTY = -0.5


def get_sumo_cmd(seed):
    return [
        sumoBinary,
        "-c", sumoConfig,
        "--start",
        "--quit-on-end",
        "--seed", str(seed)
    ]


def train():

    memory = deque(maxlen=MEMORY_SIZE)
    reward_history = []

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

        traci.start(get_sumo_cmd(episode + 1))
        total_reward = 0
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

            state = np.array(
                vehicle_counts + waiting_times + [current_phase],
                dtype=np.float32
            )

            state_tensor = torch.FloatTensor(state).unsqueeze(0)

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

            raw_wait = sum(
                traci.lane.getWaitingTime(lane) for lane in lanes
            )

            reward = -raw_wait * REWARD_SCALE

            if switched:
                reward += SWITCH_PENALTY

            total_reward += reward

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

            done = steps >= MAX_STEPS

            memory.append((state, action, reward, next_state, done))
            step_counter += 1

            if len(memory) > BATCH_SIZE:

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

        print(f"Episode {episode+1}/{EPISODES} | Reward: {total_reward:.2f} | Epsilon: {epsilon:.3f}")

        if total_reward > best_reward:
            best_reward = total_reward
            os.makedirs("models", exist_ok=True)
            torch.save(online_net.state_dict(), "models/traffic_dqn_model.pth")

    os.makedirs("results", exist_ok=True)

    plt.plot(reward_history)
    plt.title("Stable Double DQN Training")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.savefig("results/training_curve.png")
    plt.close()

    print("\nTraining Complete. Stable Model Saved.")


if __name__ == "__main__":
    train()