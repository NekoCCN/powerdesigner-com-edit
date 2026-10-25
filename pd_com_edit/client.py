#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerDesigner COM Application Client & Lifecycle Management
"""

import os
import sys
import subprocess
import time
from typing import Optional

try:
    import win32com.client
except ImportError:
    win32com = None

# Model Type GUIDs in PowerDesigner
CLS_OOM = "{4BA9FBC0-D824-11D1-A1DF-0020AF12A261}"  # Object-Oriented Model
CLS_PDM = "{CDE44E21-3017-11D2-8A2D-00609756FE6C}"  # Physical Data Model
CLS_CDM = "{9C84FDF4-9E0C-11D1-A1DE-0020AF12A261}"  # Conceptual Data Model
CLS_BPM = "{8F7D0DF1-7C65-11D3-B437-0060976527C0}"  # Business Process Model

def rgb(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) to Windows COLORREF integer."""
    return int(r) + (int(g) << 8) + (int(b) << 16)


class PowerDesignerClient:
    """Manages connection, model lifecycle, and process safety for PowerDesigner."""

    def __init__(self, visible: bool = False, timeout_sec: int = 15):
        if win32com is None:
            raise RuntimeError("pywin32 is required. Install via: pip install pywin32")
        self.visible = visible
        self.timeout_sec = timeout_sec
        self.app = None
        self._connect()

    def _connect(self):
        start_time = time.time()
        last_error = None
        while time.time() - start_time < self.timeout_sec:
            try:
                self.app = win32com.client.Dispatch("PowerDesigner.Application")
                self.app.Visible = self.visible
                return
            except Exception as e:
                last_error = e
                time.sleep(1)
        raise RuntimeError(f"Failed to connect to PowerDesigner.Application: {last_error}")

    def create_oom_model(self, name: str = "NewOOM", language: str = "Java"):
        """Create a new Object-Oriented Model (OOM)."""
        model = self.app.CreateModel(CLS_OOM, f"|Language={language}|")
        if name:
            model.SetName(name)
        return model

    def create_pdm_model(self, name: str = "NewPDM", dbms: str = "PostgreSQL 15"):
        """Create a new Physical Data Model (PDM)."""
        model = self.app.CreateModel(CLS_PDM, f"|DBMS={dbms}|")
        if name:
            model.SetName(name)
        return model

    def create_cdm_model(self, name: str = "NewCDM"):
        """Create a new Conceptual Data Model (CDM)."""
        model = self.app.CreateModel(CLS_CDM, "")
        if name:
            model.SetName(name)
        return model

    def open_model(self, path: str):
        """Open an existing .oom, .cdm, or .pdm file."""
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        return self.app.OpenModel(path)

    def open_workspace(self, path: str):
        """Open a PowerDesigner workspace (.pbw)."""
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Workspace file not found: {path}")
        return self.app.OpenWorkspace(path)

    def close_all_safely(self, save_changes: bool = False):
        """Safely close open models and release the COM server handle."""
        try:
            if self.app:
                while self.app.Models.Count > 0:
                    m = self.app.Models.Item(0)
                    if save_changes:
                        m.Save()
                    m.Close()
        except Exception:
            pass
        self.app = None

    @staticmethod
    def kill_lingering_processes():
        """Force-kill any hung or lingering pdshell16.exe processes."""
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "pdshell16.exe"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
