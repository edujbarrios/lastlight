# Releasing LastLight to PyPI

LastLight is designed to publish through **PyPI Trusted Publishing** from GitHub Actions. No long-lived PyPI API token is stored in the repository.

## One-time setup

Before the first release, configure both GitHub and PyPI.

### 1. Create the GitHub environment

In `edujbarrios/lastlight`:

1. Open **Settings → Environments**.
2. Create an environment named exactly `pypi`.
3. Prefer adding a required reviewer before deployments are allowed.

The release workflow refers to this environment by name.

### 2. Register the PyPI Trusted Publisher

If the `lastlight` project does not exist yet on PyPI, use a **pending publisher** from your PyPI account's Publishing page. Use these exact values:

| Field | Value |
| --- | --- |
| PyPI project name | `lastlight` |
| GitHub owner | `edujbarrios` |
| GitHub repository | `lastlight` |
| Workflow filename | `release.yml` |
| Environment | `pypi` |

The distribution name must match the `name = "lastlight"` metadata in `pyproject.toml`.

A pending publisher does **not** reserve the package name before the first successful upload. Confirm the name again immediately before creating the first release.

If a `lastlight` PyPI project already exists under your control, add the same GitHub Actions publisher from that project's **Publishing** settings instead of creating a pending publisher.

## Preparing a release

Versions are currently declared in two places:

- `pyproject.toml` → `project.version`
- `src/lastlight/__init__.py` → `__version__`

They must match. CI enforces this with:

```bash
python tools/check_release.py
```

Before releasing, run the normal software-health checks and build the exact artifacts locally if desired:

```bash
python tools/check_core.py
python -m pip install --upgrade build twine
rm -rf dist
python -m build
python -m twine check dist/*
```

The normal `core` GitHub Actions workflow also builds the wheel and source distribution, runs `twine check`, installs the wheel in an isolated virtual environment, imports the public API, and executes the installed `lastlight` command.

## Publishing a release

The production publisher is `.github/workflows/release.yml`. It runs only when a GitHub Release is published.

1. Merge the version-change PR to `main` and wait for `core` CI to pass.
2. Create a GitHub Release from that exact `main` commit.
3. Use a tag exactly matching the package version with a `v` prefix. For version `0.1.0`, the tag must be `v0.1.0`.
4. Publish the GitHub Release.
5. Approve the `pypi` environment deployment if environment protection requires it.
6. Verify the new release on PyPI and install it in a clean environment.

The release workflow will fail before upload if the GitHub tag does not match the version declared by the package.

Example post-release verification:

```bash
python -m venv /tmp/lastlight-pypi
/tmp/lastlight-pypi/bin/python -m pip install --upgrade pip
/tmp/lastlight-pypi/bin/python -m pip install lastlight==0.1.0
/tmp/lastlight-pypi/bin/lastlight --help
```

## What the release workflow does

The workflow intentionally separates building from publishing:

1. checks that the tag and package versions match;
2. builds both a wheel and source distribution;
3. validates package metadata and README rendering with `twine check`;
4. installs the built wheel into a clean virtual environment and checks the public API and CLI;
5. stores the exact built artifacts as a GitHub Actions artifact;
6. gives only the final publishing job `id-token: write` permission;
7. downloads the already-built artifacts and publishes them with `pypa/gh-action-pypi-publish` using OIDC.

Do not add a `PYPI_TOKEN` secret unless the Trusted Publishing design is intentionally abandoned.

## Failed releases

PyPI release files are immutable: do not attempt to replace an already-published version. Fix the problem, bump the version, run CI again, and publish a new GitHub Release/tag.
