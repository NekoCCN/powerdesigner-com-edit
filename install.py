#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Skill Installer for powerdesigner-com-edit
Supports:
1. Global User-Level Installation (~/.claude/skills, ~/.gemini/skills)
2. Project-Level Installation (.agents/skills, .claude/skills, .gemini/skills inside a workspace)
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def copy_or_link_skill(source_dir: Path, target_dir: Path, symlink: bool = False):
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        if target_dir.is_symlink():
            target_dir.unlink()
        else:
            shutil.rmtree(target_dir)

    if symlink:
        try:
            target_dir.symlink_to(source_dir, target_is_directory=True)
            print(f"Created symlink to skill at: {target_dir}")
            return
        except OSError:
            print("Symlink creation failed (permission denied). Falling back to direct copy...")

    ignore = shutil.ignore_patterns(
        ".git", "__pycache__", "*.pyc", "build", "dist", "*.egg-info", ".vscode",
        ".agents", ".claude", ".gemini", ".pytest_cache"
    )
    shutil.copytree(source_dir, target_dir, ignore=ignore)
    print(f"Installed skill to: {target_dir}")


def install_to_project(source_dir: Path, project_root: Path, symlink: bool = False):
    project_root = project_root.resolve()
    print(f"\nInstalling skill at Project Level: {project_root}")

    # Project-level locations for standard agents:
    # 1. .agents/skills (Universal / SpecKit standard)
    # 2. .claude/skills (Claude Code project directory)
    # 3. .gemini/skills (Antigravity project directory)
    destinations = [
        project_root / ".agents" / "skills" / "powerdesigner-com-edit",
        project_root / ".claude" / "skills" / "powerdesigner-com-edit",
        project_root / ".gemini" / "skills" / "powerdesigner-com-edit"
    ]

    for dest in destinations:
        copy_or_link_skill(source_dir, dest, symlink=symlink)

    print("\nProject-level installation successful!")
    print("Any AI agent opened inside this project repository will automatically detect 'powerdesigner-com-edit'.")


def main():
    parser = argparse.ArgumentParser(description="Install powerdesigner-com-edit as an Agent Skill")
    parser.add_argument(
        "--scope",
        choices=["global", "project", "both"],
        default="global",
        help="Installation scope: 'global' (user home), 'project' (current or target repo), or 'both'"
    )
    parser.add_argument(
        "--target",
        choices=["all", "gemini", "claude"],
        default="all",
        help="Target agent platform for global installation (default: all)"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Specify the target project directory for project-level installation (defaults to cwd)"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Explicit custom destination path to install the skill"
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="Create a symbolic link / junction instead of copying files"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent

    # 1. Custom explicit path
    if args.path:
        dest = Path(args.path) / "powerdesigner-com-edit"
        copy_or_link_skill(repo_root, dest, symlink=args.link)
        return

    # 2. Project-level installation
    if args.scope in ["project", "both"]:
        if args.project_dir:
            project_dir = Path(args.project_dir).resolve()
        else:
            cwd = Path.cwd().resolve()
            project_dir = repo_root.parent if cwd == repo_root else cwd
        install_to_project(repo_root, project_dir, symlink=args.link)
        if args.scope == "project":
            return

    # 3. Global user-level installation
    home = Path.home()
    print("\nInstalling skill at Global User Level (~/):")

    if args.target in ["all", "gemini"]:
        dest = home / ".gemini" / "skills" / "powerdesigner-com-edit"
        copy_or_link_skill(repo_root, dest, symlink=args.link)

    if args.target in ["all", "claude"]:
        dest = home / ".claude" / "skills" / "powerdesigner-com-edit"
        copy_or_link_skill(repo_root, dest, symlink=args.link)

    print("\nGlobal installation complete! Coding assistants can now use 'powerdesigner-com-edit'.")


if __name__ == "__main__":
    main()
