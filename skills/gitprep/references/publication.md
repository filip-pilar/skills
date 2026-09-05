# Separately authorized publication

Read only for a user request to publish existing local commits after Gitprep.
This reference does not authorize publication by itself.

Prefer local `git push` to preserve local commit history. Use the GitHub app for
remote metadata, pull requests, or useful independent verification; do not
reconstruct commits through per-file connector writes. Follow the user's target
and existing repository conventions. Do not force-push without explicit authority.

Use the actual host permission rules. If a sandbox prevents access to the host
credential helper, treat that authentication failure as inconclusive. When
supported, retry the same authentication check or authorized push through the host
approval flow before asking the user to log in. Do not escalate every push by
default or expose token values. A connector failure does not establish that local
Git authentication will fail.

After a successful push, verify the intended remote branch against the local
commit using fresh remote evidence. Local `HEAD`/`@{u}` equality alone is not an
independent remote check. Report the published commit and any remaining local
commits or uncertainty. If the push outcome is unclear, inspect remote state
before deciding whether a retry is needed.
