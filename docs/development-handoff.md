# Development Handoff and Publication

GitHub is the durable handoff for Explore Studio development. A local checkout,
temporary Codex workspace, connected GitHub integration, and iPhone-operated
remote session do not share Git objects or credentials reliably. Do not treat
any of them as a durable source of completed work until its commit is published
to GitHub.

## Required completion boundary

Every completed implementation slice must cross this boundary before further
dependent work, independent review, or cross-environment continuation:

```
clean commit -> authenticated push -> GitHub branch/PR -> exact-head handoff
```

The implementer must:

1. Create a clean commit for the completed slice.
2. Push the branch to `github.com/tonyluo2000/explore-studio` immediately.
3. Confirm that the remote branch points at the same exact commit SHA.
4. Record the branch name, pushed exact-head SHA, and GitHub branch or pull
   request in the issue/handoff before an independent reviewer starts.

An unpushed completed commit is a blocker, not a handoff. Do not start work
that depends on it in another environment.

## Authentication and publication

Before using a Mac checkout as a publication host, configure GitHub CLI and
Git credential integration in that checkout's execution context:

```bash
gh auth login
gh auth setup-git
gh auth status
```

`gh auth status` only reports the CLI session; it is not proof that Git can
publish. Verify the setup with a real branch push to this repository, then
record its exact pushed SHA. Do not make an empty verification commit just for
this purpose: push the next legitimate completed slice or an existing branch
that needs publication.

If a push fails because authentication is unavailable, stop at the clean
commit. Repair authentication in that same execution context, then retry the
push. Do not move dependent work to another workspace meanwhile.

Never put credentials, tokens, or other authentication material in commits,
prompts, command output, documentation artifacts, or issue text.

## Remote and iPhone-operated work

The iPhone is an operator surface, not a durable Git store. A remote session
may operate the Mac, but the completed work is not handed off until GitHub has
the commit.

When a remote session cannot publish, it must report only:

- the exact local commit SHA;
- the current branch; and
- the authentication or publication blocker.

It must then stop before dependent work begins elsewhere.

## Handoff record

Use this compact record in the canonical GitHub issue or pull request:

```
Branch: <branch>
Pushed exact head: <40-character SHA>
GitHub handoff: <branch URL or PR URL>
Publication verified: <command/result, without credentials>
```

The GitHub branch/PR and associated issue are the canonical cross-environment
handoff; a local path, transient workspace, or chat summary is not.
