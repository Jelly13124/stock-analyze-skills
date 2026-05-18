param(
    [string]$OutputDir = "claude_web_zips"
)

$ErrorActionPreference = "Stop"

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

    Get-ChildItem -Path $staged -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Path $staged -Recurse -Force -File -Include "*.pyc", ".DS_Store", "key.txt", "keys.txt", "api_keys.txt", ".env" | Remove-Item -Force
    Get-ChildItem -Path $staged -Recurse -Force -File | Where-Object { $_.Name -like ".env.*" -or $_.Name -like "*.pem" -or $_.Name -like "*.key" } | Remove-Item -Force

    $zip = Join-Path $OutputPath ($SkillName + ".zip")
    Compress-Archive -Path $staged -DestinationPath $zip -Force

    $built = Get-ChildItem -Path $OutputPath -Filter "*.zip" -File
    Write-Host ("Built {0} in {1}" -f (Split-Path $zip -Leaf), $OutputPath)
    $built | Select-Object Name, Length
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Path $TempRoot -Recurse -Force
    }
}
