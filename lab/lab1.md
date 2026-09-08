\# Lab 1 - Git/DVC and Data Preparation



\## Question 1

Observe the files created, what do you think they contain?



\### Answer

Running `uv init` created the initial Python project files:



\- `.python-version`: specifies the Python version used by the project.

\- `main.py`: contains a basic Python entry point that can be used to run the project.

\- `pyproject.toml`: contains the project configuration, including the project name, version, required Python version, and dependencies.

\- `README.md`: contains documentation and information about the project.



At the time of initialization, `pyproject.toml` specified:

\- project name: `mlops-lab-1`

\- version: `0.1.0`

\- required Python version: `>=3.12`

\- no dependencies yet



After running `uv add pillow`, `uv` created a virtual environment in `.venv`, added Pillow to the project dependencies, and created `uv.lock` to lock the exact dependency versions.



These files provide the basic structure of a Python project managed by `uv`.



\## Question 2

What are the created files? What do you think they are used for? And which ones should be pushed to git?



\### Answer

Running `dvc init` created the DVC configuration files for the project.



\- `.dvc/`: contains DVC project configuration and internal metadata.

\- `.dvc/config`: stores project-level DVC configuration, such as remote storage settings. It is currently empty because no remote has been configured yet.

\- `.dvc/.gitignore`: tells Git to ignore DVC internal files such as cache or temporary files that should not be versioned.

\- `.dvcignore`: tells DVC which files or folders it should ignore when scanning and tracking data.



The DVC configuration files that describe the project should be pushed to Git so that other developers can reproduce the same DVC setup. Internal cache files and temporary files should not be pushed to Git.

