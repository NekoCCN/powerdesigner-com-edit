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
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

# Model Type GUIDs & Integer Identifiers in PowerDesigner
CLS_OOM = "{4BA9FBC0-D824-11D1-A1DF-0020AF12A261}"  # Object-Oriented Model
CLS_PDM = "{CDE44E21-3017-11D2-8A2D-00609756FE6C}"  # Physical Data Model
CLS_CDM = "{9C84FDF4-9E0C-11D1-A1DE-0020AF12A261}"  # Conceptual Data Model
CLS_BPM = "{8F7D0DF1-7C65-11D3-B437-0060976527C0}"  # Business Process Model

# Native Model Kind Constants (for CreateModel integer call)
MODEL_OOM = 403775584
MODEL_CDM = 509178224

# Native Object Kind Constants in PowerDesigner OOM
KIND_CLASS = 403775587
KIND_INTERFACE = 403775588
KIND_ATTRIBUTE = 403775589
KIND_OPERATION = 403775590
KIND_GENERALIZATION = 403775592
KIND_DEPENDENCY = 403775593
KIND_CLASS_ASSOC = 403775594
KIND_ACTOR = 403775745
KIND_USECASE = 403775746
KIND_USECASE_ASSOC = 403775603
KIND_INTERACTION_FRAGMENT = -168517650

def rgb(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) to Windows COLORREF integer."""
    return int(r) + (int(g) << 8) + (int(b) << 16)


def ensure_dynamic(obj):
    """
    Ensure a COM object uses late-bound dynamic dispatch.
    This prevents early-binding BaseObject wrapper issues where derived properties
    (like Name, Position, Object1, etc.) are stripped by makepy/gencache.
    """
    if hasattr(obj, "_oleobj_") and win32com is not None:
        try:
            return win32com.client.dynamic.Dispatch(obj._oleobj_)
        except Exception:
            pass
    return obj


def attach_link_symbol(diagram, link_obj):
    """
    Safely attach a link/connector symbol (Association, Generalization, Dependency, Reference)
    to a PowerDesigner diagram.

    In PowerDesigner COM, 2D symbols use `AttachObject` while 1D line connectors MUST use
    `AttachLinkObject`. Under pywin32, calling AttachLinkObject directly on dynamic dispatch
    can encounter COM argument type coercion issues; invoking via IDispatch safely resolves this.
    """
    if hasattr(diagram, "_oleobj_") and pythoncom is not None:
        try:
            dispid = diagram._oleobj_.GetIDsOfNames("AttachLinkObject")
            ole_link = link_obj._oleobj_ if hasattr(link_obj, "_oleobj_") else link_obj
            res = diagram._oleobj_.Invoke(dispid, 0, pythoncom.DISPATCH_METHOD, True, ole_link)
            if win32com:
                return win32com.client.dynamic.Dispatch(res)
            return res
        except Exception:
            pass

    if hasattr(diagram, "AttachLinkObject"):
        try:
            return diagram.AttachLinkObject(link_obj)
        except Exception:
            pass

    if hasattr(diagram, "AttachObject"):
        try:
            return diagram.AttachObject(link_obj)
        except Exception:
            pass

    return None


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
                try:
                    self.app.Visible = self.visible
                except Exception:
                    pass
                return
            except Exception as e:
                last_error = e
                time.sleep(1)
        raise RuntimeError(f"Failed to connect to PowerDesigner.Application: {last_error}")

    def start(self, visible: Optional[bool] = None):
        """Start or re-verify connection to PowerDesigner Application."""
        if visible is not None:
            self.visible = visible
        if self.app is None:
            self._connect()
        elif visible is not None:
            try:
                self.app.Visible = visible
            except Exception:
                pass

    def create_oom_model(self, name: str = "NewOOM", language: str = "Java"):
        """Create a new Object-Oriented Model (OOM)."""
        opts = f"|Language={language}|"
        try:
            model = self.app.CreateModel(MODEL_OOM, opts, 0)
        except Exception:
            model = self.app.CreateModel(CLS_OOM, opts)

        if hasattr(model, "_oleobj_") and win32com:
            try:
                model = win32com.client.dynamic.Dispatch(model._oleobj_)
            except Exception:
                pass

        if name:
            try:
                model.SetName(name)
            except Exception:
                try:
                    model.Name = name
                except Exception:
                    pass
        return model

    create_oom = create_oom_model

    def create_pdm_model(self, name: str = "NewPDM", dbms: str = "PostgreSQL 15"):
        """Create a new Physical Data Model (PDM)."""
        model = self.app.CreateModel(CLS_PDM, f"|DBMS={dbms}|")
        if name:
            model.SetName(name)
        return model

    create_pdm = create_pdm_model

    def create_cdm_model(self, name: str = "NewCDM"):
        """Create a new Conceptual Data Model (CDM)."""
        model = self.app.CreateModel(CLS_CDM, "")
        if name:
            model.SetName(name)
        return model

    create_cdm = create_cdm_model

    def open_model(self, path: str):
        """Open an existing .oom, .cdm, or .pdm file."""
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        m = self.app.OpenModel(path)
        if hasattr(m, "_oleobj_") and win32com:
            try:
                m = win32com.client.dynamic.Dispatch(m._oleobj_)
            except Exception:
                pass
        return m

    def save_model(self, model, path: str):
        """Save a model to specified target file path."""
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            model.SaveAs(path)
        except Exception:
            try:
                model.Save(path)
            except Exception:
                model.Save()

    def close_model(self, model, save_changes: bool = False):
        """Close an individual model safely."""
        try:
            m = ensure_dynamic(model)
            if save_changes:
                m.Save()
            else:
                try:
                    m.Modified = False
                except Exception:
                    pass
            try:
                m.Close(False)
            except Exception:
                m.Close()
        except Exception:
            pass

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
                    m = ensure_dynamic(self.app.Models.Item(0))
                    if save_changes:
                        m.Save()
                    else:
                        try:
                            m.Modified = False
                        except Exception:
                            pass
                    try:
                        m.Close(False)
                    except Exception:
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
