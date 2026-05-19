# -*- coding: utf-8 -*-
"""在未激活 venv 时，将 scripts/.venv 的 site-packages 加入 sys.path。"""

from __future__ import annotations

import sys
from pathlib import Path


def prepend_scripts_venv_site_packages() -> bool:
    """
    若当前解释器未装可选依赖，尝试使用与本模块同目录的 .venv。

    Returns:
        是否向 sys.path 注入了至少一个 site-packages 目录。
    """
    scripts_dir = Path(__file__).resolve().parent
    venv_lib = scripts_dir / ".venv" / "lib"
    if not venv_lib.is_dir():
        return False

    added = False
    for site in sorted(venv_lib.glob("python*/site-packages"), reverse=True):
        site_str = str(site)
        if site_str not in sys.path:
            sys.path.insert(0, site_str)
            added = True
    return added
