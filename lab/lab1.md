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

