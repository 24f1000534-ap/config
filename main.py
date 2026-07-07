import os
import yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values

app = FastAPI()

# CORS: lets a browser on any website call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- LAYER 1: defaults ----------
DEFAULTS = {
    "port": "8000",
    "workers": "1",
    "debug": "false",
    "log_level": "info",
    "api_key": "default-secret-000",
}

# ---------- LAYER 2: yaml ----------
def load_yaml_layer(env_name="development"):
    path = f"config.{env_name}.yaml"
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        # yaml gives real types (int/bool) — turn everything to strings
        # so all layers are the same "shape" before we coerce at the end
        return {k: str(v) for k, v in data.items()}
    return {}

# ---------- LAYER 3: .env ----------
def load_dotenv_layer():
    raw = dotenv_values(".env")   # reads .env file without touching real OS env
    result = {}
    for k, v in raw.items():
        key = k.lower()
        if key == "num_workers":       # <-- the alias rule
            key = "workers"
        elif key.startswith("app_"):
            key = key[len("app_"):]
        result[key] = v
    return result

# ---------- LAYER 4: OS environment vars (APP_ prefix) ----------
def load_os_env_layer():
    result = {}
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            key = k[len("APP_"):].lower()
            result[key] = v
    return result

# ---------- Type coercion ----------
def coerce(config: dict) -> dict:
    out = {}
    for key, value in config.items():
        if key in ("port", "workers"):
            out[key] = int(value)
        elif key == "debug":
            out[key] = str(value).strip().lower() in ("true", "1", "yes", "on")
        else:
            out[key] = str(value)
    return out

@app.get("/effective-config")
def effective_config(request: Request):
    merged = {}
    merged.update(DEFAULTS)
    merged.update(load_yaml_layer())
    merged.update(load_dotenv_layer())
    merged.update(load_os_env_layer())

    # ---------- Layer 5: CLI overrides via ?set=key=value ----------
    overrides = request.query_params.getlist("set")
    for item in overrides:
        if "=" in item:
            k, v = item.split("=", 1)
            merged[k.strip()] = v.strip()

    result = coerce(merged)
    result["api_key"] = "****"   # always mask, no matter what layer set it
    return result