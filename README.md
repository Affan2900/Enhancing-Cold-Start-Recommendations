# machine-learning

Repository for the machine learning semester project: a cold-start recommendation system (notebook training + MLflow), a Flask inference API, and a React UI.

## Setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Train or obtain `user_id_map.pkl` and `item_id_map.pkl` (produced by the notebook’s `load_data`), and an MLflow-exported PyTorch model directory (or use the model registry).

## Environment variables (inference API)

The API loads config from the process environment. Optional: create a `.env` file in the project root (`python-dotenv` is used by [inference_api.py](inference_api.py)).

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `USER_ID_MAP_PATH` | `user_id_map.pkl` | Path to the pickled user id → index map |
| `ITEM_ID_MAP_PATH` | `item_id_map.pkl` | Path to the pickled item id → index map |
| `MLFLOW_MODEL_URI` | `mlartifacts/.../model` (see [inference_api.py](inference_api.py)) | Local path to an MLflow model folder (contains `MLmodel`), or a URI such as `models:/ModelName/Stage` or `runs:/<run_id>/model` when using MLflow tracking/registry |

If map files are missing or a local model directory is invalid, the API exits at startup with an error message.

## Run the API

From the repository root (so pickle paths resolve):

```bash
python inference_api.py
```

Default listening port: **5001**.

## Run the frontend (development)

```bash
cd recommendation-frontend
npm install
npm start
```

The dev server proxies **`/api`** to `http://localhost:5001` ([setupProxy.js](recommendation-frontend/src/setupProxy.js)). The React app calls `/api/...` by default.

Optional: set **`REACT_APP_API_BASE`** (e.g. `http://localhost:5001`) if you need an absolute API origin instead of same-origin `/api`.
