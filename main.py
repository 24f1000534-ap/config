import os
import yaml

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Defaults
# -----------------------

config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# -----------------------
# YAML
# -----------------------

with open("config.development.yaml", "r") as f:
    yaml_config = yaml.safe_load(f)

config.update(yaml_config)

# -----------------------
# .env
# -----------------------

env_mapping = {
    "APP_PORT": "port",
    "APP_WORKERS": "workers",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
    "NUM_WORKERS": "workers",
}

for env_key, config_key in env_mapping.items():
    value = os.getenv(env_key)

    if value is not None:
        config[config_key] = value

# -----------------------
# OS Environment
# -----------------------

# (load_dotenv does not overwrite existing OS env vars,
# so OS variables automatically take precedence.)

def convert_value(key, value):

    if key in ["port", "workers"]:
        return int(value)

    if key == "debug":
        return str(value).lower() in ["true", "1", "yes", "on"]

    return str(value)


@app.get("/effective-config")
def effective_config(
    set: list[str] | None = Query(default=None)
):

    final = {}

    for k, v in config.items():
        final[k] = convert_value(k, v)

    if set:
        for item in set:
            if "=" not in item:
                continue

            key, value = item.split("=", 1)

            final[key] = convert_value(key, value)

    final["api_key"] = "****"

    return final