from traffic_env import TrafficEnv
import random

sumo_config = "../sumo-files/YYY.sumocfg"

env = TrafficEnv(sumo_config)

env.start_simulation()

for step in range(50):
    state = env.get_state()
    action = random.choice([0, 1])
    env.apply_action(action)
    env.step_simulation()
    reward = env.get_reward()

    print("Step:", step)
    print("State:", state)
    print("Reward:", reward)
    print("------------------")

env.close()
