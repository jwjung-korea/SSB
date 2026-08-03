"""Run 216 s staggered Abaqus/BV/UMAT coupling blocks.

The workflow is:

1. Generate an initial ``cdot_map.csv``.
2. Run the first Abaqus block for ``--block-seconds``.
3. Extract interface data from the resulting ODB.
4. Generate a new Butler-Volmer ``cdot_map.csv``.
5. Restart Abaqus from the previous block and repeat.

This script writes all generated files into ``--workdir``. It assumes Abaqus is
available as ``abaqus`` or via the path given by ``--abaqus-cmd``.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BV_SCRIPT = HERE / "generate_bv_cdot_map.py"
EXTRACT_SCRIPT = HERE / "extract_interface_for_coupling.py"


def run(cmd: list[str], cwd: Path, dry_run: bool = False) -> None:
    print("+ " + " ".join(str(part) for part in cmd))
    if dry_run:
        return
    try:
        subprocess.run(cmd, cwd=str(cwd), check=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Could not find command '{cmd[0]}'. If Abaqus is installed but "
            "not on PATH, pass --abaqus-cmd C:\\SIMULIA\\Commands\\abaqus.bat"
        ) from exc


def find_abaqus_command(requested: str | None) -> str:
    if requested:
        return requested

    for name in ("abaqus", "abq2017"):
        found = shutil.which(name)
        if found:
            return found

    common = Path(r"C:\SIMULIA\Commands\abaqus.bat")
    if common.exists():
        return str(common)

    return "abaqus"


def cleanup_job_files(workdir: Path, job_prefix: str, completed_block: int,
                      keep_blocks: int, cleanup_old_jobs: bool,
                      cleanup_csv: bool, dry_run: bool) -> None:
    if not cleanup_old_jobs:
        return
    delete_through = completed_block - keep_blocks
    if delete_through < 1:
        return

    heavy_exts = {
        ".odb", ".sim", ".msg", ".sta", ".dat", ".prt", ".res", ".stt",
        ".com", ".log", ".023", ".ipm", ".mdl", ".dmp",
    }
    for block in range(1, delete_through + 1):
        job = f"{job_prefix}_b{block:03d}"
        for path in workdir.iterdir():
            if not path.is_file():
                continue
            should_delete = path.stem == job and path.suffix.lower() in heavy_exts
            if cleanup_csv:
                should_delete = should_delete or fnmatch.fnmatch(
                    path.name, f"interface_b{block:03d}.csv"
                )
                should_delete = should_delete or fnmatch.fnmatch(
                    path.name, f"bv_current_b{block:03d}.csv"
                )
            if should_delete:
                print("cleanup: " + str(path))
                if not dry_run:
                    path.unlink()


def delete_intermediate_job_files(workdir: Path, job_prefix: str, nblocks: int,
                                  keep_csv: bool, keep_restart: bool,
                                  dry_run: bool) -> None:
    removable_exts = {
        ".odb", ".sim", ".msg", ".sta", ".dat", ".prt", ".com", ".log",
        ".023", ".ipm", ".mdl", ".dmp",
    }
    if not keep_restart:
        removable_exts.update({".res", ".stt"})

    for block in range(1, nblocks + 1):
        job = f"{job_prefix}_b{block:03d}"
        for path in workdir.iterdir():
            if not path.is_file():
                continue
            should_delete = path.stem == job and path.suffix.lower() in removable_exts
            if not keep_csv:
                should_delete = should_delete or path.name == f"interface_b{block:03d}.csv"
                should_delete = should_delete or path.name == f"bv_current_b{block:03d}.csv"
            if should_delete:
                print("delete-after-join: " + str(path))
                if not dry_run:
                    path.unlink()


def join_odb_history(abaqus_cmd: str, workdir: Path, job_prefix: str,
                     nblocks: int, joined_name: str, include_history: bool,
                     compress: bool, dry_run: bool) -> Path:
    if nblocks < 1:
        raise ValueError("nblocks must be positive")

    joined = workdir / joined_name
    if joined.suffix.lower() != ".odb":
        joined = joined.with_suffix(".odb")
    first_odb = workdir / f"{job_prefix}_b001.odb"

    print(f"join-odb: {first_odb} -> {joined}")
    if not dry_run:
        if not first_odb.exists():
            raise FileNotFoundError(first_odb)
        if joined.exists():
            joined.unlink()
        shutil.copy2(first_odb, joined)

    extra_flags = []
    if include_history:
        extra_flags.append("history")
    if compress:
        extra_flags.append("compressresult")

    for block in range(2, nblocks + 1):
        restart_odb = workdir / f"{job_prefix}_b{block:03d}.odb"
        run([
            abaqus_cmd, "restartjoin",
            f"originalodb={joined}",
            f"restartodb={restart_odb}",
            *extra_flags,
        ], cwd=workdir, dry_run=dry_run)

    return joined


def read_text(path: Path) -> list[str]:
    return path.read_text(errors="ignore").splitlines(keepends=True)


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines))


def make_first_block_input(base_inp: Path, out_inp: Path,
                           block_seconds: float) -> None:
    lines = read_text(base_inp)
    new_lines: list[str] = []
    pending_dynamic = False
    for line in lines:
        if pending_dynamic:
            parts = [p.strip() for p in line.split(",")]
            while len(parts) < 4:
                parts.append("")
            parts[1] = f"{block_seconds:g}"
            new_lines.append(",".join(parts) + "\n")
            pending_dynamic = False
            continue
        if line.lstrip().lower().startswith("*dynamic"):
            new_lines.append(line)
            pending_dynamic = True
            continue
        if line.lstrip().lower().startswith("*restart, write"):
            new_lines.append("*Restart, write, frequency=1, overlay\n")
            continue
        new_lines.append(line)
    write_text(out_inp, new_lines)


def step_body_from_input(inp: Path) -> list[str]:
    lines = read_text(inp)
    start = None
    end = None
    for idx, line in enumerate(lines):
        lower = line.lstrip().lower()
        if lower.startswith("*step"):
            start = idx
        if lower.startswith("*end step") and start is not None:
            end = idx
            break
    if start is None or end is None:
        raise RuntimeError(f"Could not find step body in {inp}")
    return lines[start + 1:end]


def make_restart_input(first_block_inp: Path, out_inp: Path,
                       block_seconds: float, step_name: str) -> None:
    body = step_body_from_input(first_block_inp)
    out: list[str] = [
        "*Heading\n",
        f"Restart block {step_name}\n",
        "*Restart, read\n",
        f"*Step, name={step_name}, nlgeom=YES, amplitude=STEP, inc=100000\n",
    ]
    pending_dynamic = False
    for line in body:
        lower = line.lstrip().lower()
        if lower.startswith("*step") or lower.startswith("*end step"):
            continue
        if pending_dynamic:
            parts = [p.strip() for p in line.split(",")]
            while len(parts) < 4:
                parts.append("")
            parts[1] = f"{block_seconds:g}"
            out.append(",".join(parts) + "\n")
            pending_dynamic = False
            continue
        if lower.startswith("*dynamic"):
            out.append(line)
            pending_dynamic = True
            continue
        if lower.startswith("*restart, write"):
            out.append("*Restart, write, frequency=1, overlay\n")
            continue
        out.append(line)
    out.append("*End Step\n")
    write_text(out_inp, out)


def write_initial_interface_csv(path: Path, width: float, dx: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = int(round(width / dx))
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["X_coordinate", "S22_Stress", "U2_Displacement"])
        for i in range(count + 1):
            writer.writerow([f"{i * dx:.8g}", "", ""])


def generate_map(python_cmd: str, interface_csv: Path, cdot_map: Path,
                 current_csv: Path, mode: str, eta: float, j0: float,
                 base_cdot: float, dry_run: bool) -> None:
    run([
        python_cmd, str(BV_SCRIPT), str(interface_csv),
        "-o", str(cdot_map),
        "--current-output", str(current_csv),
        "--mode", mode,
        "--eta", str(eta),
        "--j0", str(j0),
        "--base-cdot", str(base_cdot),
    ], cwd=cdot_map.parent, dry_run=dry_run)


def extract_interface(abaqus_cmd: str, odb: Path, out_csv: Path,
                      target_time: float, dry_run: bool) -> None:
    run([
        abaqus_cmd, "cae", f"noGUI={EXTRACT_SCRIPT}", "--",
        "--odb", str(odb),
        "--output", str(out_csv),
        "--target-time", str(target_time),
    ], cwd=out_csv.parent, dry_run=dry_run)


def mode_for_block(mode: str, block: int, block_seconds: float,
                   cycle_seconds: float) -> str:
    if mode != "cycling":
        return mode
    block_start = (block - 1) * block_seconds
    cycle_index = int(block_start // cycle_seconds)
    return "plating" if cycle_index % 2 == 0 else "stripping"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-inp", type=Path, required=True)
    parser.add_argument("--umat", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--job-prefix", default="bv216")
    parser.add_argument("--block-seconds", type=float, default=216.0)
    parser.add_argument("--total-seconds", type=float, default=21600.0)
    parser.add_argument("--abaqus-cmd", default=None)
    parser.add_argument("--python-cmd", default=sys.executable)
    parser.add_argument("--mode", choices=("plating", "stripping", "cycling"),
                        default="cycling")
    parser.add_argument("--cycle-seconds", type=float, default=2160.0)
    parser.add_argument("--eta", type=float, default=-0.05)
    parser.add_argument("--j0", type=float, default=1.0)
    parser.add_argument("--base-cdot", type=float, default=103.643)
    parser.add_argument("--interface-width", type=float, default=20.0)
    parser.add_argument("--initial-dx", type=float, default=0.1)
    parser.add_argument("--cleanup-old-jobs", action="store_true")
    parser.add_argument("--keep-blocks", type=int, default=1)
    parser.add_argument("--cleanup-csv", action="store_true")
    parser.add_argument("--join-odb", action="store_true")
    parser.add_argument("--joined-odb", default=None)
    parser.add_argument("--join-history", action="store_true")
    parser.add_argument("--no-join-compress", action="store_true")
    parser.add_argument("--delete-after-join", action="store_true")
    parser.add_argument("--delete-csv-after-join", action="store_true")
    parser.add_argument("--delete-restart-after-join", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.abaqus_cmd = find_abaqus_command(args.abaqus_cmd)

    args.workdir.mkdir(parents=True, exist_ok=True)
    umat = args.workdir / args.umat.name
    if not args.dry_run:
        shutil.copy2(args.umat, umat)

    nblocks = int(round(args.total_seconds / args.block_seconds))
    if nblocks < 1:
        raise ValueError("total-seconds must be at least one block")

    initial_interface = args.workdir / "interface_initial.csv"
    if not args.dry_run:
        write_initial_interface_csv(initial_interface, args.interface_width,
                                    args.initial_dx)
    generate_map(args.python_cmd, initial_interface, args.workdir / "cdot_map.csv",
                 args.workdir / "bv_current_b001.csv",
                 mode_for_block(args.mode, 1, args.block_seconds,
                                args.cycle_seconds),
                 args.eta, args.j0, args.base_cdot, args.dry_run)

    first_job = f"{args.job_prefix}_b001"
    first_inp = args.workdir / f"{first_job}.inp"
    if not args.dry_run:
        make_first_block_input(args.base_inp, first_inp, args.block_seconds)
    run([
        args.abaqus_cmd, f"job={first_job}", f"input={first_inp}",
        f"user={umat}", "double=both", "cpus=4", "interactive"
    ], cwd=args.workdir, dry_run=args.dry_run)

    previous_job = first_job
    template_inp = first_inp
    for block in range(2, nblocks + 1):
        prev_time = (block - 1) * args.block_seconds
        interface_csv = args.workdir / f"interface_b{block - 1:03d}.csv"
        extract_interface(args.abaqus_cmd, args.workdir / f"{previous_job}.odb",
                          interface_csv, prev_time, args.dry_run)
        generate_map(args.python_cmd, interface_csv,
                     args.workdir / "cdot_map.csv",
                     args.workdir / f"bv_current_b{block:03d}.csv",
                     mode_for_block(args.mode, block, args.block_seconds,
                                    args.cycle_seconds),
                     args.eta, args.j0, args.base_cdot,
                     args.dry_run)

        job = f"{args.job_prefix}_b{block:03d}"
        inp = args.workdir / f"{job}.inp"
        if not args.dry_run:
            make_restart_input(template_inp, inp, args.block_seconds,
                               f"Step-{block}")
        run([
            args.abaqus_cmd, f"job={job}", f"oldjob={previous_job}",
            f"input={inp}", f"user={umat}", "double=both", "cpus=4",
            "interactive"
        ], cwd=args.workdir, dry_run=args.dry_run)
        cleanup_job_files(args.workdir, args.job_prefix, block - 1,
                          args.keep_blocks, args.cleanup_old_jobs,
                          args.cleanup_csv, args.dry_run)
        previous_job = job

    if args.join_odb:
        joined_name = args.joined_odb or f"{args.job_prefix}_joined.odb"
        joined = join_odb_history(
            args.abaqus_cmd, args.workdir, args.job_prefix, nblocks,
            joined_name, args.join_history, not args.no_join_compress,
            args.dry_run,
        )
        print("joined-odb: " + str(joined))
        if args.delete_after_join:
            delete_intermediate_job_files(
                args.workdir, args.job_prefix, nblocks,
                keep_csv=not args.delete_csv_after_join,
                keep_restart=not args.delete_restart_after_join,
                dry_run=args.dry_run,
            )


if __name__ == "__main__":
    main()
