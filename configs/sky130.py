#!/usr/bin/env python3

import os
from pathlib import Path


PDK_ROOT = Path(
    os.environ.get("PDK_ROOT", "")
)

LIB_ROOT = (
    PDK_ROOT
    / "share"
    / "pdk"
    / "sky130A"
    / "libs.ref"
)


LIBRARIES = {
    "hs": "sky130_fd_sc_hs",
    "hd": "sky130_fd_sc_hd",
    "hdll": "sky130_fd_sc_hdll",
    "ms": "sky130_fd_sc_ms",
    "ls": "sky130_fd_sc_ls",
    "lp": "sky130_fd_sc_lp",
}


PROCESSES = {
    "tt": ["hs", "hd", "hdll", "ms", "ls"],
    "ss": ["hs", "hd", "hdll", "ms", "ls", "lp"],
    "ff": ["hs", "hd", "hdll", "ms", "ls", "lp"],
}


def build_corners():

    corners = {}

    for process, library_types in PROCESSES.items():

        for library_type in library_types:

            library = LIBRARIES[library_type]

            corner_name = f"{library_type}_{process}"

            matches = sorted(
                LIB_ROOT.rglob(
                    f"*{library}__{process}_*.lib"
                )
            )

            liberty = (
                matches[0]
                if matches
                else None
            )

            corners[corner_name] = {
                "library": library,
                "process": process,
                "liberty": liberty,
            }

    return corners


CORNERS = build_corners()
