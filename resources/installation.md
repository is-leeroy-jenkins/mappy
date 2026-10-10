# Mappy Windows Installation

Mappy opens in a dedicated Microsoft Edge WebView2 window without browser tabs or an address bar. Its mapping, geospatial, environmental, astronomical, retrieval, processing, and vector controls remain available. Closing the window stops the local Streamlit server.

## Requirements

- Windows x64.
- Microsoft [Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).
- Disk space for the bundled scientific and machine-learning dependencies.
- Internet connectivity and your own provider credentials for online services, model downloads, and model downloads.

A built installer includes Python and the application dependencies. A separate Python installation is required only when building from source. No administrator privileges are required for the default per-user installation.

## Install from PyPI

After publication:

```powershell
python -m pip install mappy-py
mappy
```

`mappy` is the default tabless Windows command and requires WebView2. On other
platforms, or for standard browser mode, use `mappy-browser`.
Python 3.11 or later is required for pip installation.
Optional GGUF embedding support uses `python -m pip install "mappy-py[local]"`.
Provider API keys and user model files are supplied separately.
See [PyPI publication steps](pypi-release.md) for the initial release.

## Build and download from GitHub

1. Open [Mappy Actions](https://github.com/is-leeroy-jenkins/mappy/actions/workflows/windows-installer.yml).
2. Select **Build Mappy Windows desktop installer**, then **Run workflow** and the branch to build. The workflow becomes available on the default branch after the installer changes are merged.
3. Wait for all build steps to succeed.
4. Download **Mappy-Windows-Installer** from the run's **Artifacts** section and extract the ZIP.
5. Locate `Mappy-Setup-0.2.0.exe`.

The workflow builds on Windows using Python 3.11, PyInstaller, and Inno Setup 6. It runs manually and uploads an installer artifact; it does not automatically publish a GitHub Release. The source configuration is supplied here; a successful Windows build and a Windows installation test are still required before treating the installer as validated.

## Install and launch

1. Run the Setup executable downloaded from your intended workflow run. Builds are unsigned unless signing is configured separately; verify the source before accepting any Windows warning.
2. Confirm the installation directory, normally `%LOCALAPPDATA%\Programs\Mappy`.
3. Choose whether to create a desktop shortcut.
4. Finish the wizard and select **Launch Mappy**, or use the Start Menu shortcut.
5. Allow startup to complete. The launcher waits up to approximately two minutes for the local server.

The application window displays Mappy's existing Streamlit interface. “Tabless” refers to the desktop browser window; Mappy's internal workflow tabs remain available. The server binds only to `127.0.0.1` on an available port.

## Data and configuration

Writable resources, configuration, SQLite/vector data, and logs use:

```text
%LOCALAPPDATA%\Mappy
```

Bundled resources and Streamlit theme settings are copied only when a destination file does not exist. Existing user files are preserved across launches and upgrades. Development databases, logs, and `.streamlit/secrets.toml` are excluded from the executable build.

Provider credentials can be supplied using the environment variables defined in `config.py`, or through `%LOCALAPPDATA%\Mappy\.streamlit\secrets.toml` for features that read Streamlit secrets. Restart Mappy after changing environment variables. API keys are not supplied by the installer.

Sentence-transformer and optional local GGUF models require their own downloads. The Windows installer bundles Playwright Chromium. For a pip installation, run `python -m playwright install chromium` before using the Playwright renderer. Cartopy may download map datasets on first use. The installer is not a fully offline model bundle. Back up `%LOCALAPPDATA%\Mappy` before upgrades or resets.

## Build locally

Install Git, Python 3.11 x64, and [Inno Setup 6](https://jrsoftware.org/isinfo.php). In PowerShell:

```powershell
git clone https://github.com/is-leeroy-jenkins/mappy.git
cd mappy
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-desktop.txt
python -m playwright install chromium
python desktop.py
```

Close the test window, then build:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "$pwd/playwright-browsers"
python -m playwright install chromium
python -m PyInstaller --noconfirm --clean mappy.spec
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer\mappy.iss"
```

The executable directory is `dist\Mappy`; distribute the Setup executable at `dist-installer\Mappy-Setup-0.2.0.exe`. Build on Windows, since PyInstaller does not cross-compile Windows executables from Linux.

## Troubleshooting

| Symptom | Action |
|---|---|
| Missing installer artifact | Inspect the failed workflow step; an artifact is uploaded only when the Setup executable exists. |
| Window fails to open | Install WebView2 Runtime and check `%LOCALAPPDATA%\Mappy\desktop.log`. |
| Startup server exits or times out | Inspect `desktop.log` for import errors or missing native dependencies. |
| Provider request fails | Check the applicable credentials and internet connection. |
| NLP or local model fails | Check that the selected corpus or model has been downloaded and is accessible. |
| Database or log write fails | Confirm `%LOCALAPPDATA%\Mappy` is writable. |

Before distributing a build, test startup, representative loading/processing/embedding/vector operations, persistence after restart, window-close cleanup, and uninstall on a clean Windows x64 machine with WebView2 installed.

## Upgrade and uninstall

Close Mappy, back up its user data, and run the newer Setup executable to upgrade. Uninstall through **Windows Settings → Apps → Mappy → Uninstall**. User data under `%LOCALAPPDATA%\Mappy` remains; delete it separately only if you intend to remove your documents, credentials, and databases.

[Return to README](../README.md)
