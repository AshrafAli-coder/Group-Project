import os
import sys
import traci
import numpy as np

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare SUMO_HOME environment variable")


class TrafficEnv:
    def __init__(self, sumo_config):
        self.sumo_config = sumo_config
        self.sumo_cmd = ["sumo", "-c", self.sumo_config]
        self.traffic_light_id = None

    def start_simulation(self):
        traci.start(self.sumo_cmd)

        tls_ids = traci.trafficlight.getIDList()
        if len(tls_ids) == 0:
            raise Exception("No traffic lights found")
        self.traffic_light_id = tls_ids[0]

        print("Connected to SUMO")
        print("Traffic Light ID:", self.traffic_light_id)

    def step_simulation(self):
        traci.simulationStep()

    def get_state(self):
        lanes = traci.lane.getIDList()
        state = []
        for lane in lanes:
            state.append(traci.lane.getLastStepVehicleNumber(lane))
        return np.array(state)

    def apply_action(self, action):
        if action == 0:
            traci.trafficlight.setPhase(self.traffic_light_id, 0)
        elif action == 1:
            traci.trafficlight.setPhase(self.traffic_light_id, 1)
        else:
            raise ValueError("Invalid action")

    def get_reward(self):
        lanes = traci.lane.getIDList()
        total_wait = 0
        for lane in lanes:
            total_wait += traci.lane.getWaitingTime(lane)
        return -total_wait

    def reset(self):
        traci.load(["-c", self.sumo_config])
        return self.get_state()

    def close(self):
        traci.close()
        print("Simulation closed")
