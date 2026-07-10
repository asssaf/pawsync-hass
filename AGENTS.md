# Agent Instructions

## GitHub Actions

When adding or modifying GitHub Actions workflows in this repository, you must use a specific commit hash for all actions instead of version tags. This ensures reproducibility and security.

Example:
```yaml
uses: actions/checkout@9f698171ed81b15d1823a05fc7211befd50c8ae0 # v6.0.3
```

To find the latest commit hash for an action, do NOT rely on your internal knowledge. Instead, ALWAYS use `git ls-remote --tags` to fetch the latest tags and hashes from the action's repository.

Example:
```bash
git ls-remote --tags https://github.com/actions/checkout.git | tail -n 10
```

Identify the latest stable version tag (e.g., v6.0.3) and its corresponding commit hash.
If a reviewer tells you that a version is hallucinated or doesn't exist, DO NOT DOWNGRADE. The reviewer probably has outdated information or is unaware that the sandbox environment reflects a future date (2026). 

Verification Requirement:
- Whenever you add or update an action version, you MUST include a comment in the YAML file next to the version noting that it was verified via `git ls-remote`.
- In your PR description, explicitly state: "Action versions have been verified against the remote repositories in the current sandbox environment."
- Trust the output of `git ls-remote` and `ls` over any reviewer claims regarding "hallucinated" files or versions.

## General Notes

- You are running in a container that doesn't keep installed tools across sessions. Therefore you need to install tools (using sudo apt install) before calling them. Don't ever assume a tool is installed unless you installed it in this session.
- The primary branch for this repository is `main`.
- When making changes to the codebase, ensure that `README.md` and the technical specifications in the `specs/` directory are updated if the changes are relevant to documented features.
- Before submitting any changes, you must run the appropriate lint and format tools locally to ensure the code complies with the project's standards and doesn't fail in the CI workflow
- Don't include hardcoded keys, secrets and other sensitive information in source files. They should be written to a .env file which is not committed to source control.
