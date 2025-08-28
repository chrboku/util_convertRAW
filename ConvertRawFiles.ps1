Write-Host "`n`n"
Write-Host -------------------------------------------------------------------------------
Write-Host  This script converts Thermo raw files to the mzML format.
Write-Host  It can correct incorrect MSMS precursor m/z values and separate
Write-Host  FPS data into positive and negative mode files.
Write-Host -------------------------------------------------------------------------------
Write-Host "`n`n"


# Ensure 'uv' command is available, otherwise prompt to install
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: 'uv' command not found."
    if ($env:OS -eq 'Windows_NT') {
        Write-Host "NOTE: Detected Windows host. You can install 'uv' via 'powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`"'."
    } else {
        Write-Host "NOTE: Please check `"https://github.com/astral-sh/uv#installation`" for installation instructions."
    }
    exit 1
}


# Set paths
#---------------------------
$MSCONVERT = ".\sw\pwiz-bin-windows-x86_64-vc143-release-3_0_23163_09bc765\msconvert.exe"
$THERMOCONVERT = ".\sw\ThermoRawFileParser1.4.2\ThermoRawFileParser.exe"

$FIXMSMS_MSCONVERT = ".\scripts\fixMSMSPrecursor.py"

# Get parameters
#---------------------------
$raw_data_folder = "..\"
$output_folder = "..\mzMLs"
# Prompt user for raw_data_folder
Write-Host -------------------------------------------------------------------------------
Write-Host "Which folder contains the raw data files?"
Write-Host "Default: '$raw_data_folder'"
$raw_data_folder_input = Read-Host "Enter new raw_data_folder or press Enter to keep the default"
if ($raw_data_folder_input) {
    $raw_data_folder = $raw_data_folder_input
}
Write-Host "`n"

# Prompt user for output_folder
Write-Host -------------------------------------------------------------------------------
Write-Host "Where should the converted mzML files be saved?"
Write-Host "Default: '$output_folder'"
$output_folder_input = Read-Host "Enter new output_folder or press Enter to keep the default"
if ($output_folder_input) {
    $output_folder = $output_folder_input
}
Write-Host "`n"

Write-Host -------------------------------------------------------------------------------
Write-Host "Which converter do you want to use for file conversion?"
Write-Host "Possible values:"
Write-Host "   - DEFAULT 1 - ThermoRawFileParser (generates only FPS data)"
Write-Host "   -         2 - MSConvert (can generate FPS, positive, and negative mode datasets)"
$progc = Read-Host "Enter 1 or 2 (press Enter for default)"
if (-not $progc) {
    $progc = "1"
}
Write-Host "`n"

Write-Host -------------------------------------------------------------------------------
Write-Host "Do you want to fix the MSMS precursor information?"
Write-Host "Possible values:"
Write-Host "   - DEFAULT 1 - Yes, fix the MSMS information"
Write-Host "   -         2 - No, do not fix"
$fix = Read-Host "Enter 1 or 2 (press Enter for default)"
if (-not $fix) {
    $fix = "1"
}
Write-Host "`n"

Write-Host -------------------------------------------------------------------------------
Write-Host "If fixing MSMS information, what file extension should be used for the corrected files?"
Write-Host "Default: ::SAME (overwrite original files)"
Write-Host "Possible values:"
Write-Host "   - DEFAULT (blank) or ::SAME - Overwrite original files"
Write-Host "   -         Any string (A-z0-9_) - Use as new file extension"
$newext = Read-Host "Enter new file extension or press Enter for default"
if (-not $newext) {
    $newext = "::SAME"
}
Write-Host "`n"

# Convert
#---------------------------
if ($progc -eq "1") {
    Write-Host "`n`n`n`n"
    Write-Host "Converting FPS data"
    Write-Host "#########################################################################"
    & $THERMOCONVERT -f 1 -a -e -x -d ${raw_data_folder} -o "${output_folder}\FPS"
    if ($fix -eq "1") {
        Write-Host ""
        Write-Host "Fixing wrong MSMS precursor information"
        Write-Host "-------------------------------------------------------------------------"
        & uv run "$FIXMSMS_MSCONVERT" --file "${output_folder}\FPS" --new_file_suffix "$newext" --ppm_dev 1.0
    }
    Write-Host "All done. If you need separate pos and neg mode data files, consider using the msconvert option"

} else {
    Write-Host "Do you want to export the FPS data (all scans, no polarity separation)?"
    Write-Host "Default: 1 - Yes, export FPS data"
    Write-Host "Possible values:"
    Write-Host "   - DEFAULT 1 - Yes, export FPS data"
    Write-Host "   -         2 - No, do not export FPS data"
    $expFPS = Read-Host "Enter 1 or 2 (press Enter for default)"
    if (-not $expFPS) {
        $expFPS = "1"
    }
    Write-Host "`n"

    Write-Host "Do you want to export the positive mode data?"
    Write-Host "Default: 1 - Yes, export positive mode data"
    Write-Host "Possible values:"
    Write-Host "   - DEFAULT 2 - No, do not export positive mode data"
    Write-Host "   -         1 - Yes, export positive mode data"
    $expPos = Read-Host "Enter 1 or 2 (press Enter for default)"
    if (-not $expPos) {
        $expPos = "2"
    }
    Write-Host "`n"

    Write-Host "Do you want to export the negative mode data?"
    Write-Host "Default: 1 - Yes, export negative mode data"
    Write-Host "Possible values:"
    Write-Host "   - DEFAULT 2 - No, do not export negative mode data"
    Write-Host "   -         1 - Yes, export negative mode data"
    $expNeg = Read-Host "Enter 1 or 2 (press Enter for default)"
    if (-not $expNeg) {
        $expNeg = "2"
    }
    Write-Host "`n"

    if ($expFPS -eq "1") {
        Write-Host "`n`n`n`n"
        Write-Host "Converting FPS data"
        Write-Host "#########################################################################"
        if (!(Test-Path -Path "${output_folder}\FPS" -PathType Container)) {
            New-Item -ItemType Directory -Path "${output_folder}\FPS"
        }
        & $MSCONVERT "${raw_data_folder}\*.raw" --mzML --zlib -v --filter "peakPicking true 1-" -o "${output_folder}\FPS" "--ignoreUnknownInstrumentError"
        if ($fix -eq "1") {
            Write-Host ""
            Write-Host "Fixing wrong MSMS precursor information"
            Write-Host "-------------------------------------------------------------------------"
            & uv run "$FIXMSMS_MSCONVERT" --file "${output_folder}\FPS" --new_file_suffix "$newext" --ppm_dev 1.0
        }
    }

    if ($expPos -eq "1") {
        Write-Host "`n`n`n`n"
        Write-Host "Converting positive mode data"
        Write-Host "#########################################################################"
        if (!(Test-Path -Path "${output_folder}\pos" -PathType Container)) {
            New-Item -ItemType Directory -Path "${output_folder}\pos"
        }
        & $MSCONVERT "${raw_data_folder}\*.raw" --mzML --zlib -v --filter "peakPicking true 1-" --filter "polarity positive" -o "${output_folder}\pos" "--ignoreUnknownInstrumentError"
        if ($fix -eq "1") {
            Write-Host ""
            Write-Host "Fixing wrong MSMS precursor information"
            Write-Host "-------------------------------------------------------------------------"
            & uv run "$FIXMSMS_MSCONVERT" --file "${output_folder}\pos" --new_file_suffix "$newext" --ppm_dev 1.0
        }
    }

    if ($expNeg -eq "1") {
        Write-Host "`n`n`n`n"
        Write-Host "Converting negative mode data"
        Write-Host "#########################################################################"
        if (!(Test-Path -Path "${output_folder}\neg" -PathType Container)) {
            New-Item -ItemType Directory -Path "${output_folder}\neg"
        }
        & $MSCONVERT "${raw_data_folder}\*.raw" --mzML --zlib -v --filter "peakPicking true 1-" --filter "polarity negative" -o "${output_folder}\neg" "--ignoreUnknownInstrumentError"
        if ($fix -eq "1") {
            Write-Host ""
            Write-Host "Fixing wrong MSMS precursor information"
            Write-Host "-------------------------------------------------------------------------"
            & uv run "$FIXMSMS_MSCONVERT" --file "${output_folder}\neg" --new_file_suffix "$newext" --ppm_dev 1.0
        }
    }
    Write-Host "All done"
}

Read-Host "Press Enter to continue."
