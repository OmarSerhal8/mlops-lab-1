# Lab 4 — Docker Compose

## Overview

This lab extends the Food-11 MLOps project from Labs 1–3 by orchestrating three services with Docker Compose:

- **MLflow** (`mlflow`): experiment tracking and model registry, exposed to the host on port 5000.
- **Inference** (`inference`): FastAPI serving a ResNet18 Food-11 classifier on internal port 8000.
- **Frontend** (`frontend`): Streamlit image-upload interface, exposed to the host on port 8501.

The frontend calls `http://inference:8000/predict`. At startup, the inference API resolves `models:/food11@champion` using `MLFLOW_TRACKING_URI=http://mlflow:5000`. MLflow uses a named volume, `mlflow-data`, for its SQLite database and artifact storage. The existing Lab 3 MLflow database and proxied artifacts were copied into that volume to preserve the trained model.

## Question 1 — What happens when MLflow runs without a volume and its container is removed?

Without a mounted volume, files written to `/mlflow-data` reside in that container's writable layer. Stopping and restarting **the same** container preserves those files, but removing the container and creating a new one discards them.

**Test:** We started an MLflow test container without a volume on host port 5001, created an experiment named `volume-test`, removed that container, and created a new one from the same image. The new MLflow UI showed only `Default`; `volume-test` was gone. This verified the loss of container-local state after removal.

## Question 2 — Why use a named volume rather than a bind mount? Would a bind mount work?

A Docker named volume is managed by Docker, persists independently of container lifecycle, and avoids depending on a particular host directory path. It is convenient for MLflow's database and artifacts.

A bind mount would also work, for example `./mlflow-data:/mlflow-data`, and would make the data easy to inspect from the host. However, it requires managing the host path and permissions, and can introduce platform-specific filesystem behavior.

## Question 3 — Why use `mlflow` as the host name instead of `host.docker.internal`?

Docker Compose puts services on a shared network with internal DNS. Other services can resolve `mlflow` by its Compose service name, so inference uses `http://mlflow:5000`.

In Lab 3, MLflow ran on Windows outside the container network. The inference container therefore connected to the host using `host.docker.internal:5000`. In Lab 4, both services run inside Compose, so the service name is the correct address.

## Question 4 — Why configure `INFERENCE_URL` as an environment variable? What if the frontend runs outside Compose?

The environment variable makes the frontend reusable across environments without editing code or rebuilding its image. Inside the Compose network, `INFERENCE_URL=http://inference:8000` reaches FastAPI by service name.

A frontend container launched independently on a different Docker network cannot automatically resolve `inference`. It must join the same network or use another reachable API address. If Streamlit runs directly on Windows, the inference API also needs a published host port or another accessible endpoint.

## Question 5 — Why is the inference port not published to the host?

The frontend is the user-facing service and can reach inference over the internal Compose network. The inference service listens on container port 8000 but does not need a host port mapping. Keeping it internal also reduces unnecessary exposure. Publishing port 8000 would be useful only if host-side clients needed direct API access.

## Question 6 — Does `depends_on` guarantee MLflow is ready when inference starts?

No. Short-form `depends_on` controls startup order, not application readiness. Inference loads `food11@champion` at startup; if MLflow is not accepting requests yet, or if its registry/model artifacts are missing, inference can fail. A robust setup would add an MLflow health check and an inference dependency with `condition: service_healthy`, and/or implement retries when loading the model.

## Question 7 — Which services publish ports? What did `docker compose ps` show?

The verified Compose output showed all three services running:

| Service | Host-visible port mapping | Docker Compose `ps` output |
|---|---|---|
| `mlflow` | `5000:5000` | `0.0.0.0:5000->5000/tcp` |
| `inference` | None | `8000/tcp` (internal only) |
| `frontend` | `8501:8501` | `0.0.0.0:8501->8501/tcp` |

We opened the Streamlit interface at `http://127.0.0.1:8501`. An uploaded egg image was predicted as **Egg (94.6%)**, confirming a successful end-to-end frontend-to-inference prediction. Earlier, the MLflow-backed inference logs showed that all six model artifacts were downloaded and Uvicorn started successfully.

## Question 8 — What happens after promoting another model version? Does running inference update automatically?

We registered the same existing logged ResNet18 model again as `food11` **Version 3**, without retraining, and moved the `champion` alias from Version 2 to Version 3.

The running inference service does **not** automatically reload a different model when the alias changes: its Python process retains the model loaded during startup. We tested the frontend before restarting; it still predicted **Egg (94.6%)** for the egg image. Because Versions 2 and 3 use the same model weights, identical predictions alone cannot identify which version was loaded.

MLflow 3 uses model aliases such as `champion`; the older Staging model stage is deprecated. The lab's promotion operation was therefore demonstrated by moving the `champion` alias.

## Question 9 — Why can restarting inference load the promoted model without rebuilding its Docker image?

The Docker image packages FastAPI application code and dependencies, while the model is retrieved from MLflow when the application starts. After changing the alias, we ran `docker compose restart inference`. The logs showed a clean shutdown followed by `Downloading artifacts: 100% (6/6)`, `Application startup complete`, and Uvicorn listening on port 8000. No image rebuild or model retraining was required.

The restart is consistent with resolving the newly promoted `champion` alias, although the identical model weights mean the prediction did not change.

## Question 10 — What is the difference between `docker compose down` and `docker compose down -v`?

**Without `-v`:** We ran `docker compose down` and then `docker compose up -d`. The containers and network were recreated, but the named volume remained. The MLflow UI still contained Versions 1, 2, and 3, with `champion` pointing to Version 3. This verified persistence.

**With `-v`:** We ran `docker compose down -v` followed by `docker compose up -d`. Docker explicitly removed and recreated `mlops-lab-1_mlflow-data`. The MLflow registry was empty, and inference failed with `RESOURCE_DOES_NOT_EXIST: Registered Model with name=food11 not found`.

We subsequently restored the original Lab 3 `mlflow.db` and `mlartifacts/` from local copies into the new volume, then restarted the services. Inference logs later confirmed a successful model download and startup. The restored Lab 3 database originally had Versions 1 and 2; Version 3 was recreated through the registry workflow afterward. A later backup was copied outside the repository to `..\mlflow-lab4-backup` and verified to contain `mlflow.db` and `mlartifacts/`. The final backup's exact registry alias/version contents were not independently inspected in the provided command outputs.

**Safety note:** `down -v` is destructive for volume-only data. Backups should be verified before using it.

## Question 11 — What would be needed to scale inference across multiple machines with high availability?

Docker Compose is primarily a single-host orchestration tool. It does not by itself provide cross-machine scheduling, automatic recovery after a host failure, or a multi-host load-balancing control plane.

A multi-machine production design could use Kubernetes (or another cluster orchestrator) with multiple inference replicas, a Service/load balancer, readiness and liveness probes, rolling updates, and appropriate resource limits. MLflow would need a reachable shared artifact store (for example object storage) and a durable external database with a suitable high-availability and backup strategy. Networking, authentication, TLS, monitoring, and secret management would also be required.

## Deliverables and verification summary

- `mlflow/Dockerfile`: containerized MLflow configured with SQLite and proxied artifacts.
- `frontend/app.py` and `frontend/Dockerfile`: Streamlit upload interface.
- `docker-compose.yml`: MLflow, inference, frontend and persistent named volume.
- The Lab 3 inference implementation and ResNet18 weights were reused; no retraining was performed.
- Both model promotion/restart behavior and volume persistence/deletion behavior were tested.
- The images and services were built and started locally; publishing images to a remote Docker registry was not part of these verified results.

