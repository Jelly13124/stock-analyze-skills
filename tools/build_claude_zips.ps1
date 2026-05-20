param(
    [string]$OutputDir = "claude_web_zips"
)

$ErrorActionPreference = "Stop"

# Manually create each entry with forward-slash paths.
# CreateFromDirectory on some Windows .NET versions writes backslashes (a known
# bug), which makes Claude.ai web reject the ZIP with
# "Zip file contains path with invalid characters".
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$RepoRoot   = Resolve-Path (Join-Path $PSScriptRoot "..")
$OutputPath = Join-Path $RepoRoot $OutputDir
$TempRoot   = Join-Path ([System.IO.Path]::GetTempPath()) ("stock-analyze-suite-" + [System.Guid]::NewGuid().ToString("N"))
$SkillName  = "stock-analysis"

New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
Get-ChildItem -Path $OutputPath -Filter "*.zip" -File -ErrorAction SilentlyContinue | Remove-Item -Force
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

try {
    $staged = Join-Path $TempRoot $SkillName
    Copy-Item -Path (Join-Path $RepoRoot $SkillName) -Destination $staged -Recurse -Force

    # Strip transient + sensitive files from the staged copy.
    Get-ChildItem -Path $staged -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Path $staged -Recurse -Force -File -Include "*.pyc", ".DS_Store", "key.txt", "keys.txt", "api_keys.txt", ".env" | Remove-Item -Force
    Get-ChildItem -Path $staged -Recurse -Force -File | Where-Object { $_.Name -like ".env.*" -or $_.Name -like "*.pem" -or $_.Name -like "*.key" } | Remove-Item -Force

    $zip = Join-Path $OutputPath ($SkillName + ".zip")
    if (Test-Path $zip) { Remove-Item -Path $zip -Force }

    # Manually create the ZIP, one entry at a time, with explicit forward-slash paths.
    $fs = [System.IO.File]::Create($zip)
    try {
        $archive = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
        try {
            $stagedParent = Split-Path -Parent $staged
            $files = Get-ChildItem -Path $staged -Recurse -Force -File
            foreach ($file in $files) {
                # Build a relative path under the staged dir, then prepend the
                # skill name so entries look like "stock-analysis/SKILL.md".
                $relative = $file.FullName.Substring($stagedParent.Length).TrimStart('\','/')
                $entryName = $relative -replace '\\','/'
                $entry = $archive.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
                $entryStream = $entry.Open()
                try {
                    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
                    $entryStream.Write($bytes, 0, $bytes.Length)
                } finally {
                    $entryStream.Dispose()
                }
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $fs.Dispose()
    }

    $built = Get-ChildItem -Path $OutputPath -Filter "*.zip" -File
    Write-Host ("Built {0} in {1}" -f (Split-Path $zip -Leaf), $OutputPath)
    $built | Select-Object Name, Length

    # Self-check: print first 5 entries and verify forward slashes.
    $zipObj = [System.IO.Compression.ZipFile]::OpenRead($zip)
    try {
        Write-Host ""
        Write-Host "First 5 entries in the ZIP:"
        $zipObj.Entries | Select-Object -First 5 -ExpandProperty FullName | ForEach-Object { Write-Host "  $_" }
        $bad = $zipObj.Entries | Where-Object { $_.FullName -match '\\' }
        if ($bad) {
            Write-Warning ("ZIP still contains {0} backslash paths. Claude.ai upload will fail." -f $bad.Count)
        } else {
            Write-Host ""
            Write-Host "OK: all paths use forward slashes."
        }
    } finally {
        $zipObj.Dispose()
    }
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Path $TempRoot -Recurse -Force
    }
}
