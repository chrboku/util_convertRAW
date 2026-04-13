import sys
import shutil
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths relative to this script
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.parent.parent.resolve()
print(f"Script directory: {SCRIPT_DIR}")

MSCONVERT = SCRIPT_DIR / "sw" / "pwiz-bin-windows-x86_64-vc143-release-3_0_23163_09bc765" / "msconvert.exe"
THERMOCONVERT = SCRIPT_DIR / "sw" / "ThermoRawFileParser1.4.2" / "ThermoRawFileParser.exe"

# Import correction helper directly (same project)
from .fixMSMSPrecursor import correctWrongPrecursorInfo  # noqa: E402

SEP = "-" * 79


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ask(default: str) -> str:
    """Prompt with a default value; return default when user hits Enter."""
    answer = input(f"  [default: {default}] > ").strip()
    return answer if answer else default


def _ask_choice(choices: list[str], default: str) -> str:
    """Prompt for one of a fixed set of choice strings; default returned on Enter or invalid input."""
    answer = input(f"  [{'/'.join(choices)}] > ").strip()
    return answer if answer in choices else default


def collect_raw_files(source_folder: Path, recursive: bool) -> list[Path]:
    pattern = "**/*.raw" if recursive else "*.raw"
    return sorted(source_folder.glob(pattern))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def output_dir_for(raw_file: Path, source_folder: Path, output_base: Path, mode_subdir: str) -> Path:
    """Mirror the relative sub-path of *raw_file* under *output_base/mode_subdir*."""
    rel_parent = raw_file.relative_to(source_folder).parent
    return output_base / mode_subdir / rel_parent


def convert_thermo(raw_file: Path, out_dir: Path) -> None:
    ensure_dir(out_dir)
    cmd = [
        str(THERMOCONVERT),
        "-f",
        "1",
        "-a",
        "-e",
        "-x",
        "-i",
        str(raw_file),
        "-o",
        str(out_dir),
    ]
    print(f"  Converting (ThermoRawFileParser): {raw_file.name}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  WARNING: Converter returned exit code {result.returncode} for '{raw_file.name}'")


def convert_msconvert(raw_file: Path, out_dir: Path, polarity_filter: str | None = None) -> None:
    ensure_dir(out_dir)
    cmd = [
        str(MSCONVERT),
        str(raw_file),
        "--mzML",
        "--zlib",
        "-v",
        "--filter",
        "peakPicking true 1-",
    ]
    if polarity_filter:
        cmd += ["--filter", f"polarity {polarity_filter}"]
    cmd += ["-o", str(out_dir), "--ignoreUnknownInstrumentError"]
    print(f"  Converting (MSConvert): {raw_file.name}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  WARNING: Converter returned exit code {result.returncode} for '{raw_file.name}'")


def fix_msms(mzml_file: Path, new_file_suffix: str, ppm_dev: float) -> None:
    if not mzml_file.exists():
        print(f"  WARNING: Expected output file not found, skipping MSMS fix: {mzml_file}")
        return
    print(f"  Fixing MSMS precursors: {mzml_file.name}")
    suffix = "" if new_file_suffix == "::SAME" else new_file_suffix
    try:
        correctWrongPrecursorInfo(str(mzml_file), new_file_suffix=suffix, ppm_dev=ppm_dev)
    except Exception as exc:
        print(f"  WARNING: MSMS fix failed for '{mzml_file.name}': {exc}")


def get_version() -> str:
    # Get version from TOML file
    try:
        import toml

        version_info = toml.load(SCRIPT_DIR / "pyproject.toml")["project"]["version"]
        return version_info
    except Exception as exc:
        print(f"Error retrieving version: {exc}")
        return "unknown"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # --- Welcome message ---
    print("Welcome to the Thermo Raw File Converter!")
    print(" This utility helps you convert Thermo raw files to mzML format, with options to fix MSMS precursor information and separate polarity modes.")
    print(f"Version: {get_version()}")
    print()

    # check for tools
    missing_tool = False
    if not THERMOCONVERT.exists():
        print(f"ERROR: ThermoRawFileParser not found at expected location: {THERMOCONVERT}")
        print("Please ensure the converter is downloaded and placed in the 'sw' subfolder.")
        missing_tool = True
    else:
        print(f"Found ThermoRawFileParser: {THERMOCONVERT}")

    if not MSCONVERT.exists():
        print(f"ERROR: MSConvert not found at expected location: {MSCONVERT}")
        print("Please ensure the converter is downloaded and placed in the 'sw' subfolder.")
        missing_tool = True
    else:
        print(f"Found MSConvert: {MSCONVERT}")

    if missing_tool:
        sys.exit(1)

    print("\n\n")
    print(SEP)
    print(" This script converts Thermo raw files to the mzML format.")
    print(" It can correct incorrect MSMS precursor m/z values and separate")
    print(" FPS data into positive and negative mode files.")
    print(SEP)
    print("\n\n")

    # --- Source folder ---
    print(SEP)
    print("Which folder contains the raw data files?")
    raw_data_folder = Path(_ask("..\\"))
    print()

    # --- Output folder ---
    print(SEP)
    print("Where should the converted mzML files be saved?")
    output_folder = Path(_ask("..\\mzMLs"))
    print()

    # --- Recurse subfolders ---
    print(SEP)
    print("Should raw files in subfolders of the source folder also be converted?")
    print("  The subfolder structure will be mirrored in the output directory.")
    print("   y - Yes, recurse into all subfolders  [DEFAULT]")
    print("   n - No, convert only top-level raw files")
    recursive = _ask_choice(["y", "n"], "y") == "y"
    print()

    # --- Converter ---
    print(SEP)
    print("Which converter do you want to use for file conversion?")
    print("   1 - ThermoRawFileParser (generates only FPS data)  [DEFAULT]")
    print("   2 - MSConvert (can generate FPS, positive, and negative mode datasets)")
    progc = _ask_choice(["1", "2"], "1")
    print()

    # --- Fix MSMS ---
    print(SEP)
    print("Do you want to fix the MSMS precursor information?")
    print("   1 - Yes, fix the MSMS information  [DEFAULT]")
    print("   2 - No, do not fix")
    fix = _ask_choice(["1", "2"], "1") == "1"
    print()

    # --- New extension for fixed files ---
    newext = "::SAME"
    if fix:
        print(SEP)
        print("What file extension should be used for the MSMS-corrected files?")
        print("   ::SAME - Overwrite original files  [DEFAULT]")
        print("   <string> - Any A-z0-9_ string: append as new file extension")
        newext_input = _ask("::SAME")
        newext = newext_input if newext_input != "::SAME" or newext_input else "::SAME"
        print()

    # --- MSConvert mode selection ---
    exp_fps, exp_pos, exp_neg = True, False, False
    if progc == "2":
        print(SEP)
        print("Do you want to export the FPS data (all scans, no polarity separation)?")
        print("   1 - Yes, export FPS data  [DEFAULT]")
        print("   2 - No, do not export FPS data")
        exp_fps = _ask_choice(["1", "2"], "1") == "1"
        print()

        print(SEP)
        print("Do you want to export the positive mode data?")
        print("   2 - No, do not export positive mode data  [DEFAULT]")
        print("   1 - Yes, export positive mode data")
        exp_pos = _ask_choice(["2", "1"], "2") == "1"
        print()

        print(SEP)
        print("Do you want to export the negative mode data?")
        print("   2 - No, do not export negative mode data  [DEFAULT]")
        print("   1 - Yes, export negative mode data")
        exp_neg = _ask_choice(["2", "1"], "2") == "1"
        print()

    # --- Collect files ---
    raw_data_folder = raw_data_folder.resolve()
    if not raw_data_folder.exists():
        print(f"ERROR: Source folder '{raw_data_folder}' does not exist.")
        sys.exit(1)

    output_folder = output_folder.resolve()

    # --- Output folder existence check ---
    if output_folder.exists():
        print(SEP)
        print("WARNING: The output folder already exists:")
        print(f"  {output_folder}")
        print("  Continuing may mix old and new files.")
        print("   y - Delete the existing output folder and continue  [DEFAULT]")
        print("   n - Abort")
        delete_choice = _ask_choice(["y", "n"], "y")
        print()
        if delete_choice == "y":
            shutil.rmtree(output_folder)
        else:
            print("Aborted. Please remove the output folder manually or choose a different output folder when re-running the tool.")
            input("\nPress Enter to exit.")
            sys.exit(0)

    ppm_dev = 1.0

    raw_files = collect_raw_files(raw_data_folder, recursive)
    if not raw_files:
        suffix_note = " (including subfolders)" if recursive else ""
        print(f"No .raw files found in '{raw_data_folder}'{suffix_note}.")
        input("\nPress Enter to continue.")
        sys.exit(0)

    recurse_note = " (including subfolders)" if recursive else ""
    print(f"\nFound {len(raw_files)} .raw file(s) in '{raw_data_folder}'{recurse_note}.\n")

    # --- Convert ---
    if progc == "1":
        # ThermoRawFileParser — FPS only
        print("\n\n")
        print("Converting FPS data")
        print("#" * 73)
        for raw_file in raw_files:
            out_dir = output_dir_for(raw_file, raw_data_folder, output_folder, "FPS")
            convert_thermo(raw_file, out_dir)
            if fix:
                mzml_file = out_dir / (raw_file.stem + ".mzML")
                print("  Fixing wrong MSMS precursor information")
                fix_msms(mzml_file, newext, ppm_dev)

        print("\nAll done. If you need separate pos/neg mode data files, consider using the MSConvert option.")

    else:
        # MSConvert
        if exp_fps:
            print("\n\n")
            print("Converting FPS data")
            print("#" * 73)
            for raw_file in raw_files:
                out_dir = output_dir_for(raw_file, raw_data_folder, output_folder, "FPS")
                convert_msconvert(raw_file, out_dir, polarity_filter=None)
                if fix:
                    mzml_file = out_dir / (raw_file.stem + ".mzML")
                    print("  Fixing wrong MSMS precursor information")
                    fix_msms(mzml_file, newext, ppm_dev)

        if exp_pos:
            print("\n\n")
            print("Converting positive mode data")
            print("#" * 73)
            for raw_file in raw_files:
                out_dir = output_dir_for(raw_file, raw_data_folder, output_folder, "pos")
                convert_msconvert(raw_file, out_dir, polarity_filter="positive")
                if fix:
                    mzml_file = out_dir / (raw_file.stem + ".mzML")
                    print("  Fixing wrong MSMS precursor information")
                    fix_msms(mzml_file, newext, ppm_dev)

        if exp_neg:
            print("\n\n")
            print("Converting negative mode data")
            print("#" * 73)
            for raw_file in raw_files:
                out_dir = output_dir_for(raw_file, raw_data_folder, output_folder, "neg")
                convert_msconvert(raw_file, out_dir, polarity_filter="negative")
                if fix:
                    mzml_file = out_dir / (raw_file.stem + ".mzML")
                    print("  Fixing wrong MSMS precursor information")
                    fix_msms(mzml_file, newext, ppm_dev)

        print("\nAll done.")

    input("\nPress Enter to continue.")


if __name__ == "__main__":
    main()
