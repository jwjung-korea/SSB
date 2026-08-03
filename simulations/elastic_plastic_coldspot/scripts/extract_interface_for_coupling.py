"""Extract Li/LLZO interface data from an Abaqus ODB for coupling.

Run with Abaqus Python, for example:

    abaqus cae noGUI=extract_interface_for_coupling.py -- \
        --odb job.odb --output interface.csv --target-time 216

The output is compatible with ``generate_bv_cdot_map.py``. Contact variables
are attempted when present, but the script always writes S22 and U2 so the
BV map generator can fall back to a stress-based contact proxy.
"""

from __future__ import print_function

import argparse
import csv
import os
import sys

from abaqus import session
from abaqusConstants import COMPONENT, INTEGRATION_POINT, NODAL, NODE_LIST
from abaqusConstants import PATH_POINTS, TRUE_DISTANCE, UNDEFORMED
import xyPlot


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--odb", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--step", default="Step-1")
    parser.add_argument("--target-time", type=float, default=None)
    parser.add_argument("--interface-y", type=float, default=5.0)
    parser.add_argument("--instance", default="LITHIUM_INST")
    return parser.parse_args(argv)


def closest_frame(step, target_time):
    if target_time is None:
        return len(step.frames) - 1
    best_idx = 0
    best_diff = 1.0e99
    for idx, frame in enumerate(step.frames):
        diff = abs(frame.frameValue - target_time)
        if diff < best_diff:
            best_idx = idx
            best_diff = diff
    return best_idx


def path_data(path, variable, name):
    data = xyPlot.XYDataFromPath(
        path=path,
        includeIntersections=False,
        shape=UNDEFORMED,
        pathStyle=PATH_POINTS,
        labelType=TRUE_DISTANCE,
        name=name,
        variable=variable,
    )
    return dict((round(x, 8), y) for x, y in data.data)


def try_path_data(path, variable, name):
    try:
        return path_data(path, variable, name)
    except Exception as exc:
        print("WARNING: could not extract {0}: {1}".format(name, exc))
        return {}


def main():
    args = parse_args()
    odb = session.openOdb(name=args.odb)
    try:
        step = odb.steps[args.step]
        frame_idx = closest_frame(step, args.target_time)
        actual_time = step.frames[frame_idx].frameValue
        vp = session.viewports[session.currentViewportName]
        vp.setValues(displayedObject=odb)
        vp.odbDisplay.setFrame(step=args.step, frame=frame_idx)

        instance = odb.rootAssembly.instances[args.instance]
        nodes = []
        for node in instance.nodes:
            if abs(node.coordinates[1] - args.interface_y) < 1.0e-4:
                nodes.append((node.coordinates[0], node.label))
        nodes.sort()
        if not nodes:
            raise RuntimeError("No interface nodes found at y={0}".format(
                args.interface_y))

        path_name = "coupling_interface_path"
        if path_name in session.paths:
            del session.paths[path_name]
        node_labels = tuple(label for _, label in nodes)
        path = session.Path(
            name=path_name,
            type=NODE_LIST,
            expression=((args.instance, node_labels),),
        )

        s22 = try_path_data(path, ("S", INTEGRATION_POINT,
                            ((COMPONENT, "S22"),)), "s22_coupling")
        u2 = try_path_data(path, ("U", NODAL, ((COMPONENT, "U2"),)),
                           "u2_coupling")
        cpress = try_path_data(path, ("CPRESS", NODAL), "cpress_coupling")
        copen = try_path_data(path, ("COPEN", NODAL), "copen_coupling")

        out_dir = os.path.dirname(os.path.abspath(args.output))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)

        with open(args.output, "wb") as f:
            writer = csv.writer(f)
            writer.writerow([
                "X_coordinate", "S22_Stress", "U2_Displacement",
                "CPRESS", "COPEN", "Frame_Time"
            ])
            all_x = sorted(set([round(x, 8) for x, _ in nodes])
                           | set(s22) | set(u2) | set(cpress) | set(copen))
            for x in all_x:
                writer.writerow([
                    x,
                    s22.get(x, ""),
                    u2.get(x, ""),
                    cpress.get(x, ""),
                    copen.get(x, ""),
                    actual_time,
                ])
        print("Wrote interface data: {0}".format(args.output))
    finally:
        odb.close()


if __name__ == "__main__":
    main()
