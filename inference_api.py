from flask import Flask, request, jsonify
import mlflow.pytorch
import torch
import numpy as np
import pickle
from flask_cors import CORS 

# Load mappings (ensure these files are saved during training)
with open("user_id_map.pkl", "rb") as f:
    user_id_map = pickle.load(f)
with open("item_id_map.pkl", "rb") as f:
    item_id_map = pickle.load(f)
rev_item_id_map = {v: k for k, v in item_id_map.items()}

# Load the trained model from MLflow
model_path = "mlartifacts/159987644700385176/a0fa8e795e7b4d53bdf0b694f50b7216/artifacts/model"
model = mlflow.pytorch.load_model(model_path)

# Flask app initialization
app = Flask(__name__)
CORS(app)

# Wrapper class for the recommendation model
class RecommendationModel:
    def __init__(self, model, n_items):
        self.model = model
        self.n_items = n_items

    def get_recommendations(self, user_idx, n_recommendations=10):
        # Generate predictions for all items
        user_tensor = torch.LongTensor([user_idx] * self.n_items)
        item_tensor = torch.LongTensor(range(self.n_items))

        with torch.no_grad():
            predictions = self.model(user_tensor, item_tensor)

        # Get top N recommendations
        top_indices = torch.topk(predictions, n_recommendations).indices.numpy()
        top_scores = predictions[top_indices].numpy()

        return list(zip(top_indices, top_scores))

# Initialize the recommendation model
wrapped_model = RecommendationModel(model, n_items=len(item_id_map))

@app.route("/users", methods=["GET"])
def list_users():
    """Endpoint to list all users in the user_id_map"""
    try:
        # Convert the user_id_map to a list of user objects
        users = [
            {"user_id": user_id, "internal_index": internal_idx}
            for user_id, internal_idx in user_id_map.items()
        ]
        
        # Add summary information
        response = {
            "total_users": len(users),
            "users": users
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"Failed to list users: {str(e)}"}), 500

@app.route("/users/count", methods=["GET"])
def user_count():
    """Endpoint to get just the count of users"""
    try:
        return jsonify({"total_users": len(user_id_map)})
    except Exception as e:
        return jsonify({"error": f"Failed to get user count: {str(e)}"}), 500

@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    """Endpoint to check if a specific user exists"""
    try:
        if user_id in user_id_map:
            return jsonify({
                "exists": True,
                "user_id": user_id,
                "internal_index": user_id_map[user_id]
            })
        else:
            return jsonify({
                "exists": False,
                "user_id": user_id,
                "message": "User not found in mapping"
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
        
        # Check if the user exists in the mapping
        if user_id not in user_id_map:
            return jsonify({"error": f"Unknown user: {user_id}"}), 404
        
        user_idx = user_id_map[user_id]
        recommendations = wrapped_model.get_recommendations(user_idx)

        # Format the results
        results = [
            {"item_idx": int(item_idx), "score": float(score)}
            for item_idx, score in recommendations
        ]

        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5001)