# Running PyTracerLab Locally

PyTracerLab can be run locally as a Python application — no standalone `.exe` installer required. This is useful if your IT policy restricts unsigned executables, if you are on a non-Windows platform, or if you simply prefer working from a Python environment.

The steps below walk you through installing [Anaconda](https://www.anaconda.com/download) as a Python distribution, creating a dedicated environment, and launching the GUI. The whole process takes about 10–15 minutes.

```{tip}
**On Windows and only interested in the GUI?** The standalone application is quicker — it needs no
Python at all. See [Get PyTracerLab Running on Your Machine](#get-running) for a
click-by-click walkthrough.
```

---

## Step 1 — Install Anaconda

[Anaconda](https://www.anaconda.com/download) is a free Python distribution bundled with the `conda` package and environment manager. It is the recommended way to manage Python environments for scientific software like PyTracerLab.

1. Open [https://www.anaconda.com/download](https://www.anaconda.com/download) in your browser and download the **Anaconda Individual Edition** installer for your operating system (Windows, macOS, or Linux).

2. Run the installer and follow the on-screen instructions. The default settings work fine. On Windows, you may be asked whether to *add Anaconda to your PATH* — keeping the default (not adding to PATH) and using the dedicated **Anaconda Prompt** application is the safest choice.

3. After installation, open a terminal:
   - **Windows** — search for **Anaconda Prompt** (or **Anaconda PowerShell Prompt**) in the Start menu and open it.
   - **macOS / Linux** — open a regular **Terminal** (conda is initialised in your shell automatically).

4. Verify the installation by running:

   ```bash
   conda --version
   ```

   You should see output such as `conda 24.x.x`. If you get a `command not found` error on Windows, make sure you are using the **Anaconda Prompt** that was installed alongside Anaconda (searchable via the Windows Start menu) rather than a regular Command Prompt or PowerShell window.

---

## Step 2 — Create a Conda Environment

It is best practice to install PyTracerLab into its own isolated environment so that its dependencies do not interfere with other Python projects on your machine.

An `environment.yml` file is provided in the [PyTracerLab repository](https://github.com/iGW-TU-Dresden/PyTracerLab) that sets up a minimal environment with the correct Python version. Download it (or copy its contents into a file named `environment.yml`) and then run:

```bash
conda env create -f environment.yml
```

This creates a conda environment named `pytracerlab`. When the command finishes you will see a message confirming that the environment was created.

```{tip}
The environment only needs to be *created* once. On subsequent sessions you only need to *activate* it (Step 3).
```

### Manual setup (alternative)

If you prefer not to use the `environment.yml` file, create the environment in one command:

```bash
conda create -n pytracerlab python=3.11
```

---

## Step 3 — Activate the Environment

Before installing or running PyTracerLab, activate the environment:

```bash
conda activate pytracerlab
```

Your terminal prompt will change to show `(pytracerlab)` at the beginning, confirming that the environment is active.

```{warning}
You need to activate the environment **every time** you open a new terminal window. Commands run without the environment active will use a different Python installation and will fail with import errors.
```

---

## Step 4 — Install PyTracerLab

With the `pytracerlab` environment active, install PyTracerLab from [PyPI](https://pypi.org/project/PyTracerLab/) using pip. This automatically installs PyTracerLab and all of its dependencies (NumPy, SciPy, Matplotlib, PyQt5):

```bash
pip install PyTracerLab
```

You should see output ending with:

```
Successfully installed PyTracerLab-x.x.x
```

---

## Step 5 — Launch the GUI

With the environment still active, start the graphical user interface using one of the following commands.

**On all platforms (shows a background console window):**

```bash
PyTracerLab
```

**On Windows (no console window):**

```bash
PyTracerLab-gui
```

The PyTracerLab main window should now open. Refer to the [GUI usage guide](usage.md) for a description of the individual tabs and the typical workflow.

---

## Updating PyTracerLab

To update to the latest version at any time, activate the environment and run:

```bash
pip install --upgrade PyTracerLab
```

---

## Running from Source (Advanced)

If you want to run the very latest development version — or if you want to modify the source code — you can clone the repository and install from source instead of from PyPI.

### 1. Get the source code

**Clone with Git (recommended):**

```bash
git clone https://github.com/iGW-TU-Dresden/PyTracerLab.git
cd PyTracerLab
```

**Download as a ZIP archive:**

1. Go to [https://github.com/iGW-TU-Dresden/PyTracerLab](https://github.com/iGW-TU-Dresden/PyTracerLab).
2. Click the green **Code** button, then choose **Download ZIP**.
3. Extract the ZIP to a folder of your choice and navigate into it in your terminal.

### 2. Install from source

Follow Steps 1–3 above to install Anaconda and create + activate the `pytracerlab` environment. Then, from inside the repository folder (the one containing `pyproject.toml`), run:

```bash
pip install -e .
```

The `-e` flag (*editable mode*) makes Python load the package directly from the source files, so any changes you make to the code are reflected immediately without reinstalling.

### 3. Launch

```bash
python src/PyTracerLab/__main__.py
```

Or, using the entry point registered by `pip install -e .`:

```bash
PyTracerLab-gui
```

---

## Troubleshooting

### `conda: command not found` or `conda is not recognized`

On Windows, open **Anaconda Prompt** from the Start menu instead of a regular Command Prompt or PowerShell. On macOS/Linux, close and reopen your terminal after the Anaconda installation so that the shell initialisation takes effect.

### `ModuleNotFoundError: No module named 'PyQt5'`

This usually means the `pytracerlab` environment is not active. Run `conda activate pytracerlab` and try again. If the error persists after activation, reinstall PyTracerLab:

```bash
pip install --force-reinstall PyTracerLab
```

### `ModuleNotFoundError: No module named 'PyTracerLab'`

The package is not installed in the active environment. Run `pip install PyTracerLab` (or `pip install -e .` for a source installation) with the environment active.

### The GUI window does not appear on Linux

Qt requires a graphical display server. If you are on a headless Linux server (no desktop environment), the GUI cannot be shown. In this case, use PyTracerLab as a Python package in a script or Jupyter notebook instead.
