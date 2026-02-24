param(
  [Parameter(Mandatory = $true)]
  [string]$JobFolder
)

$JobFolder = (Resolve-Path $JobFolder).Path
$out = Join-Path $JobFolder "combined_report.txt"

function Add-Section([string]$title, [string]$fileName) {
  $path = Join-Path $JobFolder $fileName

  Add-Content -Path $out -Value ""
  Add-Content -Path $out -Value "=================================================="
  Add-Content -Path $out -Value $title
  Add-Content -Path $out -Value "FILE: $fileName"
  Add-Content -Path $out -Value "=================================================="

  if (Test-Path $path) {
    Get-Content $path -Raw | Add-Content -Path $out
  } else {
    Add-Content -Path $out -Value "(MISSING)"
  }
}

"SMART TRAPPER COMBINED REPORT" | Set-Content $out
"Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content $out
"Folder: $JobFolder" | Add-Content $out

# These match your current TrapJobs filenames (no extensions)
Add-Section "IMPORT DEBUG LOG" "import_debug_log"
Add-Section "TRAPPER LOG"       "trapper_log"
Add-Section "JOB JSON"          "job"
Add-Section "TRAPS JSON"        "traps"
Add-Section "ERROR LEVEL"       "errorlevel"

Write-Host "Combined report created:"
Write-Host $out
