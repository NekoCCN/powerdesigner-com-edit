#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Skill Installer for powerdesigner-com-edit
Installs the skill into Claude Code, Google Antigravity, or local workspace skill directories.
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def get_default_skill_targets():
    home = Path.home()
    targets = []

    gemini_skills = home / ".gemini" / "skills"
    if gemini_skills.parent.exists():
        targets.append(("Antigravity (Gemini)", gemini_skills / "powerdesigner-com-edit"))

    claude_skills = home / ".claude" / "skills"
    if claude_skills.parent.exists():
        targets.append(("Claude Code", claude_skills / "powerdesigner-com-edit"))

    return targets


def copy_skill(source_dir: Path, target_dir: Path):
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        shutil.rmtree(target_dir)

    ignore = shutil.ignore_patterns(
        ".git", "__pycache__", "*.pyc", "build", "dist", "*.egg-info", ".vscode"
    )
    shutil.copytree(source_dir, target_dir, ignore=ignore)
    print(f"Successfully installed skill to: {target_dir}")


def main():
    parser = argparse.ArgumentParser(description="Install powerdesigner-com-edit as an Agent Skill")
    parser.add_argument(
        "--target",
        choices=["all", "gemini", "claude", "local"],
        default="all",
        help="Target platform to install the skill for (default: all detected)"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Custom destination directory to install the skill into"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent

    if args.path:
        dest = Path(args.path) / "powerdesigner-com-edit"
        copy_skill(repo_root, dest)
        return

    home = Path.home()
    installed = False

    if args.target in ["all", "gemini"]:
        dest = home / ".gemini" / "skills" / "powerdesigner-com-edit"
        copy_skill(repo_root, dest)
        installed = True

    if args.target in ["all", "claude"]:
        dest = home / ".claude" / "skills" / "powerdesigner-com-edit"
        copy_skill(repo_root, dest)
        installed = True

    if args.target == "local":
        dest = Path.cwd() / ".agents" / "skills" / "powerdesigner-com-edit"
        copy_skill(repo_root, dest)
        installed = True

    if not installed:
        print("No target agent directories found. Use --path <directory> to specify custom installation path.")
    else:
        print("\nInstallation complete! AI agents can now use 'powerdesigner-com-edit'.")
        print("Test prompt: 'Use powerdesigner-com-edit to create a sequence diagram with activation bars.'")


if __name__ == "__main__":
    main()
