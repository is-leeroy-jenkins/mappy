# PyPI release

Distribution: **mappy-py**. Import: **mappy**. Initial version: **0.2.0**.

## First publication — complete these steps in order

1. Merge the PyPI packaging pull request into `master`.
2. Open GitHub **Settings → Environments**, create an environment named `pypi`.
3. Sign in to [PyPI Publishing](https://pypi.org/manage/account/publishing/) and add a pending GitHub publisher using these exact values:

   | Field | Value |
   |---|---|
   | PyPI project name | `mappy-py` |
   | Owner | `is-leeroy-jenkins` |
   | Repository | `mappy` |
   | Workflow filename | `publish-to-pypi.yml` |
   | Environment | `pypi` |

4. After the publisher is registered, open GitHub **Actions → Publish to PyPI → Run workflow**, select `master`, and run it.
5. Confirm both **build** and **publish** succeed. Check [the project page](https://pypi.org/project/mappy-py/) and install in a fresh virtual environment:

   ```powershell
   python -m pip install mappy-py
   mappy
   ```

A pending publisher does not reserve the package name. The first successful upload creates the project. No API token is needed with Trusted Publishing. Do not create a GitHub release before configuring the publisher. A release is optional for the first upload because the workflow supports manual publication.

## Launch commands

`mappy` opens the tabless Windows window. `mappy-browser` opens the standard browser UI.

```powershell
python -m pip install mappy-py
mappy
```

The desktop command requires Windows and Edge WebView2. The standalone Setup executable remains a separate build documented in [installation.md](installation.md).

## Subsequent releases

Update `pyproject.toml` and `__version__` in `__init__.py` to the same new version. Merge the changes, then publish a GitHub release with a matching tag, for example `v0.2.1`. The release triggers **Publish to PyPI**. PyPI versions cannot be overwritten; a failed upload after partial publication may require a new version.

## Package contents

The wheel contains the application modules, PNG/ICO interface assets, celestial-map assets, and Streamlit theme configuration. Runtime dependencies are read from `requirements-runtime.txt`. Documentation/build dependencies and optional local llama.cpp inference are excluded from the base dependency list. Install `mappy-py[local]` when using local GGUF embedding models. Development databases, logs, secrets, GIF demos, and local model weights are excluded.

Application data uses `%LOCALAPPDATA%\Mappy` on Windows and `~/AppData/Local/Mappy` when `LOCALAPPDATA` is absent. Existing user resources are preserved. Provider credentials, external loader services, downloaded models, and Playwright Chromium require their normal configuration.

Avoid installing the unrelated `mappy` distribution alongside `mappy-py`; both use the `mappy` import namespace.
