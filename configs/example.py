#!/usr/bin/env python3

from pathlib import Path


# ============================================================
# STANDARD-CELL LIBRARY CONFIGURATION
# ============================================================
#
# Replace these paths with the Liberty files from your library.
#
# The timing flow does NOT require any particular directory
# structure or filename convention.
#
# You can define as many corners as you need.
# ============================================================


CORNERS = {

    "typical": {
        "library": "my_library",
        "process": "tt",
        "liberty": Path(
            "/path/to/typical.lib"
        ),
    },

    "slow": {
        "library": "my_library",
        "process": "ss",
        "liberty": Path(
            "/path/to/slow.lib"
        ),
    },

    "fast": {
        "library": "my_library",
        "process": "ff",
        "liberty": Path(
            "/path/to/fast.lib"
        ),
    },

}
