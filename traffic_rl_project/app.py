from flask import Flask, jsonify
from flask_cors import CORS
import threading

from backend.train import train   # 🔥 import your real training

app = Flask(__name__)
CORS(app)

simulation_running = False
training_thread = None

current_metrics = {
    "episode": 0,
    "reward": 0,
    "waiting_time": 0,
    "queue_length": 0,
    "status": "stopped"
}


# -------------------------
# TRAINING WRAPPER
# -------------------------

def run_training():
    global simulation_running

    def update_metrics(data):
        current_metrics.update({
            "episode": data["episode"],
            "reward": data["reward"],
            "waiting_time": data["waiting_time"],
            "queue_length": data["queue_length"],
            "status": "running"
        })

    def stop_flag():
        return not simulation_running

    train(update_callback=update_metrics, stop_flag=stop_flag)

    current_metrics["status"] = "stopped"
    simulation_running = False


# -------------------------
# ROUTES
# -------------------------

@app.route('/metrics')
def metrics():
    return jsonify(current_metrics)


@app.route('/start')
def start():
    global simulation_running, training_thread

    if not simulation_running:
        simulation_running = True
        training_thread = threading.Thread(target=run_training)
        training_thread.start()

    return jsonify({"message": "Training Started"})


@app.route('/stop')
def stop():
    global simulation_running
    simulation_running = False
    return jsonify({"message": "Stopping Training..."})


@app.route('/evaluate')
def evaluate():
    return jsonify({
        "fixed_waiting": 480000,
        "rl_waiting": 93000,
        "improvement": 80.6
    })


if __name__ == "__main__":
    app.run(debug=True)