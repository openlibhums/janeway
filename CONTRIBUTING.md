Thanks for considering contributing to Janeway!

- To report a bug please provide as much information as possible on the action you were undertaking. It would be preferable if we could have the stack trace for the error supplied.
- To suggest a new feature please describe it as in depth as possible, it will be considered and may be added to a future release of Janeway.
- To maintain a consistent and readable codebase, we require all Python code to be automatically formatted with Black and linted with [Ruff](https://docs.astral.sh/ruff/formatter/). These tools help ensure code style uniformity and catch potential issues early. Once you have installed the development dependencies, you can run `ruff format .`. We strongly recommend adding our hooks to your repository config (`git config --local core.hooksPath .git-hooks`) to avoid committing unformatted code.
- When writing a commit message, we adhere to the [conventional commits specification](https://www.conventionalcommits.org/en/v1.0.0/). We also add a reference in the commit message (e.g `fix: #123 fixed a bug where [...]`)
- When a PR is expected to resolve an issue you can flag it as `closes #123` and the issue will be closed once the PR is merged into the main branch
4
