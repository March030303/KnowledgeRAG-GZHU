from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT / ".git" / "hooks"
HOOK_TEMPLATES = {
    "pre-commit": "#!/usr/bin/env sh\nrepo_root=\"$(git rev-parse --show-toplevel 2>/dev/null || pwd)\"\nsh \"$repo_root/.husky/pre-commit\" \"$@\"\n",
    "commit-msg": "#!/usr/bin/env sh\nrepo_root=\"$(git rev-parse --show-toplevel 2>/dev/null || pwd)\"\nsh \"$repo_root/.husky/commit-msg\" \"$@\"\n",
}


def main() -> int:
    if not HOOKS_DIR.exists():
        print("Skip local hook install: .git/hooks not found.")
        return 0

    HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    for hook_name, content in HOOK_TEMPLATES.items():
        target = HOOKS_DIR / hook_name
        target.write_text(content, encoding="utf-8", newline="\n")

    print("Installed local hook bridge for .husky scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
