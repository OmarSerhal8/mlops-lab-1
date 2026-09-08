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

&#x20;

\## Question 3

Where are the credentials stored? What are the options other than `--global`? Should the credentials be pushed to GitHub?



\### Answer

DVC configuration can be stored at different levels.



In this project, the DagsHub credentials were configured using the `--local` option, so they are stored in `.dvc/config.local`. This file is machine-specific and should not be committed to Git.



The main configuration levels are:

\- project: stored in `.dvc/config`

\- local: stored in `.dvc/config.local`

\- global: stored in the user's global DVC configuration

\- system: applies system-wide



Credentials such as usernames, passwords, and access tokens should never be pushed to GitHub. Only non-secret configuration, such as the DVC remote URL and the default remote name, should be committed.



