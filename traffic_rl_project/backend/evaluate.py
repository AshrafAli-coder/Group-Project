import os
import sys
import torch
import traci
import numpy as np
import statistics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rl_agent.model import DQN

sumoBinary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
sumoConfig = os.path.join("sumo_config", "simulation.sumocfg")

TLS_ID = "B1"
RUNS = 5


def get_sumo_cmd(seed):
    return [
        sumoBinary,
        "-c", sumoConfig,
        "--start",
        "--quit-on-end",
        "--seed", str(seed)
    ]


def evaluate_controller(seed, use_rl=False):

    traci.start(get_sumo_cmd(seed))

    lanes = traci.trafficlight.getControlledLanes(TLS_ID)
    lanes = list(dict.fromkeys(lanes))

    if use_rl:
        state_size = len(lanes) * 2 + 1
        logic = traci.trafficlight.getAllProgramLogics(TLS_ID)[0]
        action_size = len(logic.getPhases())

        model = DQN(state_size, action_size)
        model.load_state_dict(torch.load("models/traffic_dqn_model.pth"))
        model.eval()

    total_wait = 0
    total_queue = 0
    max_queue = 0
    steps = 0

    while traci.simulation.getMinExpectedNumber() > 0:

        if use_rl:
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
            action = torch.argmax(model(state_tensor)).item()
            traci.trafficlight.setPhase(TLS_ID, action)

        traci.simulationStep()
        steps += 1

        queue_now = sum(
            traci.lane.getLastStepHaltingNumber(lane)
            for lane in lanes
        )

        total_queue += queue_now
        max_queue = max(max_queue, queue_now)

        total_wait += sum(
            traci.lane.getWaitingTime(lane)
            for lane in lanes
        )

    throughput = traci.simulation.getArrivedNumber()

    traci.close()

    return {
        "total_wait": total_wait,
        "avg_queue": total_queue / steps,
        "max_queue": max_queue,
        "throughput": throughput
    }


if __name__ == "__main__":

    print("\nRunning Advanced Evaluation...\n")

    fixed_results = []
    rl_results = []

    for seed in range(1, RUNS + 1):

        print(f"Run {seed}/{RUNS}")

        fixed = evaluate_controller(seed, use_rl=False)
        rl = evaluate_controller(seed, use_rl=True)

        fixed_results.append(fixed)
        rl_results.append(rl)

    def avg(metric, results):
        return statistics.mean([r[metric] for r in results])

    print("\n==============================")
    print("AVERAGE RESULTS OVER", RUNS, "RUNS")
    print("==============================\n")

    print("Fixed-Time Controller")
    print("Total Waiting:", avg("total_wait", fixed_results))
    print("Avg Queue:", avg("avg_queue", fixed_results))
    print("Max Queue:", avg("max_queue", fixed_results))
    print("Throughput:", avg("throughput", fixed_results))

    print("\nRL Controller")
    print("Total Waiting:", avg("total_wait", rl_results))
    print("Avg Queue:", avg("avg_queue", rl_results))
    print("Max Queue:", avg("max_queue", rl_results))
    print("Throughput:", avg("throughput", rl_results))

    improvement = (
        (avg("total_wait", fixed_results) -
         avg("total_wait", rl_results))
        / avg("total_wait", fixed_results)
    ) * 100

    print("\nOverall Waiting Time Improvement: {:.2f}%".format(improvement))