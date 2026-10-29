#!/usr/bin/env python3
"""Write hardware/kicad/th_sensor_h2.kicad_pro: JLCPCB 2-layer standard-process design rules,
net classes and ERC settings. Values: JLCPCB capabilities page (checked 2026-10-29):
min trace/space 0.127/0.127 mm, min via 0.3 mm hole / 0.6 mm pad (2-layer standard),
board edge to copper 0.3 mm, silkscreen line >= 0.15 mm, text height >= 1.0 mm."""
import json
import os

import design as D
from kicad_sexpr import new_uuid

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "kicad", D.PROJECT + ".kicad_pro"))

POWER_NETS = ["VBAT1", "VBAT2", "VBAT1_L", "VBAT2_L", "VIN1", "VIN2", "VOUT1", "VOUT2", "3V3_PWR", "+3V3", "GND",
              "LX1_1", "LX2_1", "LX1_2", "LX2_2"]


def netclass(name, track, clearance, via_d=0.6, via_drill=0.3, priority=0):
    return {"name": name, "clearance": clearance, "track_width": track, "via_diameter": via_d,
            "via_drill": via_drill, "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2,
            "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)",
            "priority": priority}


pro = {
    "board": {
        "3dviewports": [],
        "design_settings": {
            "defaults": {
                "board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "other_line_width": 0.15,
                "silk_line_width": 0.15, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
                "silk_text_thickness": 0.15,
                "pads": {"drill": 0.0, "height": 1.0, "width": 1.0},
                "zones": {"min_clearance": 0.25},
            },
            "rules": {
                "min_clearance": 0.127, "min_connection": 0.127, "min_copper_edge_clearance": 0.3,
                "min_hole_clearance": 0.25, "min_hole_to_hole": 0.5, "min_microvia_diameter": 0.2,
                "min_microvia_drill": 0.1, "min_resolved_spokes": 1, "min_silk_clearance": 0.0,
                "min_text_height": 0.8, "min_text_thickness": 0.15, "min_through_hole_diameter": 0.3,
                "min_track_width": 0.127, "min_via_annular_width": 0.15, "min_via_diameter": 0.6,
                "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True,
            },
            "track_widths": [0.0, 0.2, 0.3, 0.4, 0.6],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
            "rule_severities": {"silk_overlap": "warning", "silk_edge_clearance": "warning",
                                "lib_footprint_issues": "warning", "lib_footprint_mismatch": "warning"},
        },
        "layer_presets": [], "viewports": [],
    },
    "boards": [],
    "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [],
            "rule_severities": {"lib_symbol_issues": "warning", "lib_symbol_mismatch": "warning",
                                "footprint_link_issues": "warning", "simulation_model_issue": "ignore"}},
    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    "meta": {"filename": D.PROJECT + ".kicad_pro", "version": 3},
    "net_settings": {
        "classes": [netclass("Default", 0.2, 0.15), netclass("Power", 0.4, 0.2, priority=1)],
        "meta": {"version": 4},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in POWER_NETS],
    },
    "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [[new_uuid("root-sheet"), "Root"]],
    "text_variables": {"REV": D.REV, "DATE": D.DATE},
}

with open(OUT, "w") as f:
    json.dump(pro, f, indent=2)
print("wrote", OUT)
