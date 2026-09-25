Q1 — What version number was your model given? What is the difference between a logged model artifact and a registered model?



The model was initially registered as Version 1 under the registered model name food11.







A logged model artifact is the model file and its metadata stored inside an MLflow run. A registered model is a model managed inside the MLflow Model Registry, where it receives a name and version number and can later be referenced using aliases.







During Docker serving, I created Version 2 from the same trained model because Version 1 used a local Windows file: artifact path that was not accessible from the Linux Docker container. No retraining was performed.



Q2 — What do aliases such as champion provide compared with model stages?



Aliases provide a flexible name that points to a specific model version. For example:







food11@champion → Version 2



The alias can later be moved to another version without changing the serving code.







Older MLflow workflows used fixed stages such as Staging, Production, and Archived. Aliases are more flexible because we can define names such as champion, challenger, or any other useful label.



Q3 — Why load the model using a registry URI instead of a local filesystem path? What happens when a new model becomes champion?



The serving application loads:







mlflow.pyfunc.load\_model("models:/food11@champion")



instead of loading a local model path.







This decouples the API from a specific filesystem location or model version. MLflow resolves the registered model and downloads the correct artifacts.







If a new model version becomes the champion, only the alias needs to be changed:







champion → new version



The FastAPI code does not need to change.



Q4 — Why copy pyproject.toml and uv.lock before copying the source code in the Dockerfile?



Docker builds images using cached layers.







By copying:







COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev



before:







COPY src/ ./src/



Docker can reuse the dependency layer when only the application source code changes.







Therefore, changing serve.py does not force Docker to reinstall all Python dependencies, which makes rebuilding much faster.



Q5 — Compare the naive single-stage image with the multi-stage image.



The actual results were:



ImageDisk UsageContent Size



Single-stage



9.84 GB



3.31 GB



Multi-stage



9.69 GB



3.28 GB



The multi-stage image reduced reported disk usage by approximately:







9.84 - 9.69 = 0.15 GB ≈ 150 MB



The reduction was relatively small because most of the image size comes from runtime dependencies such as PyTorch, torchvision, and MLflow, which are required in both images.







The naive image contained a dependency layer of approximately 6.33 GB, while the multi-stage runtime copied a .venv of approximately 6.28 GB.







The multi-stage build still helps by preventing builder-only tools and build-stage overhead from remaining in the final runtime image.



Q6 — Why is .dockerignore important? What would happen without it?



.dockerignore prevents unnecessary local files from being sent to the Docker build context.







In this project, directories such as:







.venv/

data/

mlruns/

mlartifacts/

.git/

\_\_pycache\_\_/



do not belong in the Docker build context.







Without .dockerignore, Docker would send much more data to the build daemon, making builds slower and potentially exposing unnecessary files.







A host .venv can also be problematic if it is copied because it may contain platform-specific files from Windows that are incompatible with the Linux container.







Other folders such as data, mlruns, and .git mainly cause unnecessary build-context size and may expose data or metadata.



Q7 — Why does the container use host.docker.internal instead of localhost to access MLflow?



Inside a Docker container:







localhost / 127.0.0.1



refers to the container itself, not the Windows host machine.







MLflow is running on the Windows host, so the container uses:







host.docker.internal



to reach the host machine.







Therefore, the container was started with:







docker run -p 8000:8000 -e MLFLOW\_TRACKING\_URI=http://host.docker.internal:5000 food11-api:latest



The MLflow server also had to listen on:







0.0.0.0:5000



instead of only 127.0.0.1, so that Docker could access it.



Q8 — Does the Docker image contain the model? What happened when you restarted the container?



The model is not baked into the Docker image.







The image contains:







Python

dependencies

FastAPI

Uvicorn

serve.py

preprocessing code



At container startup, the application resolves:







models:/food11@champion



and downloads the model artifacts from MLflow.







This was confirmed by the message:







Downloading artifacts: 100%



I stopped the first container and started a new container from the same food11-api:latest image without rebuilding it.







The second container successfully returned:







{"status":"ok"}



for /health, and:







{"category":"Fried food","confidence":0.4130365252494812}



for /predict.







This proves that the same Docker image can start a new container and retrieve the current champion model at runtime.



Q9 — What is still missing before this image could be used in CI/CD or Kubernetes?



The Docker image currently exists only on the local machine.







For CI/CD or Kubernetes, the image should be pushed to a container registry such as Docker Hub, GitHub Container Registry, or another private registry.







It should also use an immutable version tag or image digest instead of relying only on:







latest



For example:







food11-api:1.0



or an immutable image digest.







This allows CI/CD and Kubernetes to pull the exact same image that was built and tested instead of rebuilding it differently on another machine.

