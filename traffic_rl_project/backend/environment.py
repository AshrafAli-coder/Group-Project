import traci
import numpy as np
import time


class TrafficEnv:

    def __init__(self, sumoCmd):
        self.sumoCmd = sumoCmd
        self.tls_id = "B1"
        self.lanes = None

    def start(self):
        traci.start(self.sumoCmd)

    def reset(self):
        traci.simulationStep()

        self.lanes = traci.trafficlight.getControlledLanes(self.tls_id)
        self.lanes = list(dict.fromkeys(self.lanes))

        return self.get_state()

    def get_state(self):
        state = []
        for lane in self.lanes:
            vehicle_count = traci.lane.getLastStepVehicleNumber(lane)
            state.append(vehicle_count)

        return np.array(state, dtype=np.float32)

    def step(self, action):

        current_phase = traci.trafficlight.getPhase(self.tls_id)

        # Phase 0 = NS green
        # Phase 2 = EW green

        if action == 0 and current_phase != 0:
            traci.trafficlight.setPhase(self.tls_id, 0)

        elif action == 1 and current_phase != 2:
            traci.trafficlight.setPhase(self.tls_id, 2)

        # Run few simulation steps slowly (visible)
        for _ in range(5):
            traci.simulationStep()

        next_state = self.get_state()

        # Reward = negative total waiting time
        total_wait = 0
        for lane in self.lanes:
            total_wait += traci.lane.getWaitingTime(lane)

        reward = -total_wait

        done = False
        if traci.simulation.getMinExpectedNumber() <= 0:
            done = True

        return next_state, reward, done

    def close(self):
        traci.close()