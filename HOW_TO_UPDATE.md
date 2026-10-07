# How to Update

This guide covers both publishing code changes and installing those changes.

## Publish code changes

1. Create a feature branch from the branch you intend to update (`dev` or `main`).
2. Make the code or documentation changes. For Python server changes, run the tests:

   ```bash
   python -m pip install -e '.[test]'
   python -m pytest
   ```

   For VS Code extension changes, compile it:

   ```bash
   cd vscode-extension
   npm ci
   npm run compile
   cd ..
   ```

3. Commit and push the feature branch, then open a pull request into `dev` or `main`.
4. Before publishing a new version, update the root `VERSION` file to the next `MAJOR.MINOR.PATCH` version. The release workflow rejects a version whose tag already exists.
5. Merge the change into the target branch:
   - A push to `dev` creates a prerelease with the version and commit ID, such as `v0.1.0-abc123d`.
   - A push to `main` creates a production release such as `v0.1.0`.
6. Check the **Release** workflow under GitHub Actions. When it succeeds, download the VSIX and Python wheel from the generated GitHub Release.

The workflow runs the Python tests, builds the Python wheel and VS Code extension, and attaches both artifacts to the release. It retains only the newest published release across `dev` and `main`, so download the artifacts you need before publishing another release.

## Install an update

The VS Code extension and Python MCP server are separate installations. Update both if both components changed:

1. Download the new `.vsix` and `.whl` assets from the same GitHub Release.
2. In VS Code, run **Extensions: Install from VSIX...** and select the downloaded `.vsix`. Reload VS Code if prompted.
3. Update the MCP server in the virtual environment configured for your MCP client. For the default macOS installation:

   ```bash
   ~/.local/share/aws-resource-optimization/venv/bin/python -m pip install --upgrade /path/to/downloaded/aws_resource_optimization_mcp-<version>-py3-none-any.whl
   ```

4. Restart the MCP server from the VS Code MCP view. Its configured executable path should remain the same. If the server cannot be found, set `awsResourceOptimization.binaryPath` to the full path of `aws-resource-optimization-mcp`.
5. Verify the installed server with **AWS Resource Optimization: Show Version**. Use the MCP `aws_account_summary` tool if you also want to verify the AWS profile connection.

Installing a new VSIX does not update the Python wheel, and updating the wheel does not update the VSIX.

## Update a development checkout

If you run the project from a local Git checkout instead of release artifacts:

```bash
git switch dev
git pull --ff-only origin dev
python3 -m pip install -e '.[test]'
python3 -m pytest
```

For extension changes, rebuild it as well:

```bash
cd vscode-extension
npm ci
npm run compile
```
