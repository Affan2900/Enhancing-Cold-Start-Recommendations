import os
import pickle
import sys

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import mlflow.pytorch
import torch

load_dotenv()


def _die(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


DEFAULT_MODEL_URI = (
    "mlartifacts/159987644700385176/a0fa8e795e7b4d53bdf0b694f50b7216/artifacts/model"
)

user_map_path = os.getenv("USER_ID_MAP_PATH", "user_id_map.pkl")
item_map_path = os.getenv("ITEM_ID_MAP_PATH", "item_id_map.pkl")
model_uri = os.getenv("MLFLOW_MODEL_URI", DEFAULT_MODEL_URI)

if not os.path.isfile(user_map_path):
    _die(
        f"Missing user id map file: {user_map_path!r} "
        f"(set USER_ID_MAP_PATH or run training to create it)"
    )
if not os.path.isfile(item_map_path):
    _die(
        f"Missing item id map file: {item_map_path!r} "
        f"(set ITEM_ID_MAP_PATH or run training to create it)"
    )

# Local MLflow model dirs must contain MLmodel; registry URIs do not use the filesystem
is_registry = model_uri.startswith("models:") or model_uri.startswith("runs:")
if not is_registry:
    mlmodel = os.path.join(model_uri, "MLmodel")
    if not os.path.isdir(model_uri) or not os.path.isfile(mlmodel):
        _die(
            f"Model path not found or not an MLflow model directory: {model_uri!r} "
            f"(set MLFLOW_MODEL_URI to a directory with MLmodel, or use runs:/... / models:/...)"
        )

with open(user_map_path, "rb") as f:
    user_id_map = pickle.load(f)
with open(item_map_path, "rb") as f:
    item_id_map = pickle.load(f)
rev_item_id_map = {v: k for k, v in item_id_map.items()}

model = mlflow.pytorch.load_model(model_uri)

app = Flask(__name__)
CORS(app)


class RecommendationModel:
    def __init__(self, model, n_items):
        self.model = model
        self.n_items = n_items

    def get_recommendations(self, user_idx, n_recommendations=10):
        user_tensor = torch.LongTensor([user_idx] * self.n_items)
        item_tensor = torch.LongTensor(range(self.n_items))

        with torch.no_grad():
            predictions = self.model(user_tensor, item_tensor)
            predictions = torch.clamp(predictions, 1.0, 5.0)

        top_indices = torch.topk(predictions, n_recommendations).indices.numpy()
        top_scores = predictions[top_indices].numpy()

        return list(zip(top_indices, top_scores))


wrapped_model = RecommendationModel(model, n_items=len(item_id_map))


@app.route("/users", methods=["GET"])
def list_users():
    try:
        users = [
            {"user_id": user_id, "internal_index": internal_idx}
            for user_id, internal_idx in user_id_map.items()
        ]
        return jsonify({"total_users": len(users), "users": users})
    except Exception as e:
        return jsonify({"error": f"Failed to list users: {str(e)}"}), 500


@app.route("/users/count", methods=["GET"])
def user_count():
    try:
        return jsonify({"total_users": len(user_id_map)})
    except Exception as e:
        return jsonify({"error": f"Failed to get user count: {str(e)}"}), 500


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        if user_id in user_id_map:
            return jsonify({
                "exists": True,
                "user_id": user_id,
                "internal_index": user_id_map[user_id],
            })
        return jsonify({
            "exists": False,
            "user_id": user_id,
            "message": "User not found in mapping",
        }), 404
    except Exception as e:
        return jsonify({"error": f"Failed to check user: {str(e)}"}), 500


@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400

        user_id = data.get("user_id")
        if user_id is None:
            return jsonify({"error": "Missing user_id field"}), 400

        if user_id not in user_id_map:
            return jsonify({"error": f"Unknown user: {user_id}"}), 404

        user_idx = user_id_map[user_id]
        recommendations = wrapped_model.get_recommendations(user_idx)

        results = []
        for item_idx, score in recommendations:
            ext_item_id = rev_item_id_map.get(int(item_idx), None)
            row = {
                "item_idx": int(item_idx),
                "score": float(score),
                "item_id": ext_item_id,
            }
            results.append(row)

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5001)
