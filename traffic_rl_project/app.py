from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/metrics')
def metrics():
    return jsonify({
        "waiting_time": random.randint(10, 100),
        "reward": random.randint(-50, 10),
        "episode": random.randint(1, 50)
    })

if __name__ == "__main__":
    app.run(debug=True)