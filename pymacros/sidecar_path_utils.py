# --------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2025-2026 Martin Jan Köhler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later
#--------------------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import *

from klayout_plugin_utils.debugging import debug, Debugging


@dataclass
class SidecarInfo:
    """A sidecar file's path and its compound suffix."""
    path: Path
    suffix: str   # e.g. ".klay.klib"


class SidecarPathUtils:
    # ---------------------------------------------------------------------------
    # Sidecar file mapping
    # ---------------------------------------------------------------------------
    # Maps a compound main-file suffix to a list of companion (sidecar) suffixes
    # that must be backed up alongside it.  All suffixes are compared
    # case-insensitively.  The dict is ordered longest-suffix-first so that
    # e.g. ".klay.gds.gz" is matched before ".gds.gz".
    #
    # Sources:  https://github.com/iic-jku/klayout-library-manager
    #
    SIDECAR_SUFFIX_MAP: Dict[str, List[str]] = {
        # KLayout Library-Manager compound formats
        '.klay.gds':    ['.klay.klib'],
        '.klay.gds.gz': ['.klay.klib'],
        '.klay.oas':    ['.klay.klib'],
        '.klay.oas.gz': ['.klay.klib'],
        '.klay.txt':    ['.klay.klib'],   # GDS-II text format
        '.klay.txt.gz': ['.klay.klib'],
    }
    
    # Pre-sorted by descending suffix length so greedy matching works correctly.
    _SIDECAR_SUFFIXES_SORTED: List[Tuple[str, List[str]]] = sorted(
        SIDECAR_SUFFIX_MAP.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    
    @staticmethod
    def _match_compound_suffix(path: Path) -> Optional[Tuple[str, str, List[str]]]:
        """Try to match *path* against the sidecar suffix map.
    
        Returns ``(stem, matched_suffix, sidecar_suffixes)`` on success,
        or ``None`` if the file name does not match any known compound suffix.
        """
        name_lower = path.name.lower()
        for main_suffix, sidecar_suffixes in SidecarPathUtils._SIDECAR_SUFFIXES_SORTED:
            if name_lower.endswith(main_suffix):
                stem = path.name[: len(path.name) - len(main_suffix)]
                return stem, main_suffix, sidecar_suffixes
        return None
    
    @staticmethod
    def get_sidecar_paths(layout_path: Path) -> List[SidecarInfo]:
        """Return sidecar paths and their suffixes for *layout_path*.
    
        Returns an empty list when the file format has no known sidecars.
        """
        match = SidecarPathUtils._match_compound_suffix(layout_path)
        if match is None:
            return []
        stem, _main_suffix, sidecar_suffixes = match
        parent = layout_path.parent
        return [
            SidecarInfo(path=parent / (stem + s), suffix=s)
            for s in sidecar_suffixes
        ]
    
    @staticmethod
    def compound_stem(path: Path) -> str:
        """Return the file stem with compound suffixes (like ``.klay.gds``) stripped.
    
        Falls back to splitting on the first dot for unknown formats.
        """
        match = SidecarPathUtils._match_compound_suffix(path)
        if match is not None:
            return match[0]
        return path.name.split('.')[0]
