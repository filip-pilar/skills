# Release a skill

Release checks do not grant permission to install, synchronize, commit, push, or publish. Perform only the distribution actions the user authorized.

Inspect the complete diff and preserve unrelated work. Run the repository's package checks and relevant tests, or this package's `scripts/validate_skill.py` when no repository validator exists. Check metadata, links, resource routing, executable permissions, and symlinks. Keep generated outputs, credentials, caches, and evaluation history out of the package. Reuse applicable validation results; run additional behavioral checks only where uncertainty warrants them.

For synchronization, compare source and installed copies and follow the authorized source of truth. Do not overwrite a divergent installation without resolving which changes to preserve.

Report material changes, completed validation, remaining limits, and the exact installation or publication state.
