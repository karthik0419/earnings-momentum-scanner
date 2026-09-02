<#
.SYNOPSIS
    Archive and clean up scanner result CSVs across all scanner projects.

.DESCRIPTION
    - Deletes *_all.csv files older than 7 days (huge full-universe dumps)
    - Archives remaining CSVs older than 30 days into monthly tar.gz files in results/archive/
    - Reports what was deleted and archived
    - Safe to run repeatedly. Does NOT touch CSVs newer than 30 days.

.NOTES
    Run manually or schedule via Task Scheduler:
      schtasks /Create /SC WEEKLY /D SUN /ST 02:00 /TN "ScannerCsvArchive" /TR "powershell -File F:\projects\claude\archive_scanner_csvs.ps1"
    Remove: schtasks /Delete /TN "ScannerCsvArchive" /F
#>

[CmdletBinding()]
param(
    [int]$AllCsvMaxDays    = 7,
    [int]$ArchiveAfterDays = 30,
    [switch]$DryRun,
    [switch]$WhatIf
)

if ($WhatIf) { $DryRun = $true }

$WorkspaceRoot = 'F:\projects\claude'
$ScannerProjects = @('scanner-v3', 'scanner-v2', 'scanner', 'earnings-momentum-scanner')

$cutoffAll     = (Get-Date).AddDays(-$AllCsvMaxDays)
$cutoffArchive = (Get-Date).AddDays(-$ArchiveAfterDays)

$mode = if ($DryRun) { '[DRY RUN] ' } else { '' }
Write-Host ($mode + 'Scanner CSV Archive - ' + (Get-Date -Format 'yyyy-MM-dd HH:mm')) -ForegroundColor Cyan
Write-Host ('  _all.csv older than ' + $AllCsvMaxDays + ' days  -> delete (before ' + $cutoffAll + ')')
Write-Host ('  other CSVs older than ' + $ArchiveAfterDays + ' days -> archive to tar.gz (before ' + $cutoffArchive + ')')
Write-Host ''

$totalDeleted = 0
$totalDeletedKB = 0
$totalArchived = 0
$totalArchivedKB = 0

foreach ($proj in $ScannerProjects) {
    $resultsDir = Join-Path $WorkspaceRoot ($proj + '\results')
    if (-not (Test-Path $resultsDir)) {
        Write-Host ('  [' + $proj + '] no results/ folder - skipped') -ForegroundColor DarkGray
        continue
    }

    $archiveDir = Join-Path $resultsDir 'archive'
    if (-not $DryRun -and -not (Test-Path $archiveDir)) {
        New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    }

    $allCsvs = Get-ChildItem $resultsDir -File -Filter '*.csv' -ErrorAction SilentlyContinue
    if (-not $allCsvs) {
        Write-Host ('  [' + $proj + '] no CSVs - skipped') -ForegroundColor DarkGray
        continue
    }

    Write-Host ('  [' + $proj + '] ' + $allCsvs.Count + ' CSVs found') -ForegroundColor White

    # --- Step 1: Delete _all.csv older than $AllCsvMaxDays ---
    $allFiles = $allCsvs | Where-Object {
        $_.Name -like '*_all.csv' -and $_.LastWriteTime -lt $cutoffAll
    }
    foreach ($f in $allFiles) {
        $kb = [Math]::Round($f.Length / 1KB, 1)
        $dateStr = $f.LastWriteTime.ToString('yyyy-MM-dd')
        Write-Host ('    DELETE  ' + $f.Name + '  (' + $kb + ' KB, ' + $dateStr + ')') -ForegroundColor Yellow
        if (-not $DryRun) { Remove-Item $f.FullName -Force }
        $totalDeleted++
        $totalDeletedKB += $kb
    }

    # --- Step 2: Archive CSVs older than $ArchiveAfterDays ---
    $toArchive = $allCsvs | Where-Object {
        $_.LastWriteTime -lt $cutoffArchive -and
        -not ($_.Name -like '*_all.csv' -and $_.LastWriteTime -lt $cutoffAll)
    }

    if ($toArchive) {
        $byMonth = $toArchive | Group-Object { $_.LastWriteTime.ToString('yyyy-MM') }

        foreach ($group in $byMonth) {
            $month = $group.Name
            $tarName = $proj + '_' + $month + '.tar.gz'
            $tarPath = Join-Path $archiveDir $tarName

            $monthBytes = ($group.Group | Measure-Object -Property Length -Sum).Sum
            $monthKB = [Math]::Round($monthBytes / 1KB, 1)
            $fileList = $group.Group.Name -join ', '
            Write-Host ('    ARCHIVE ' + $month + ' -> ' + $tarName + '  (' + $group.Count + ' files, ' + $monthKB + ' KB)') -ForegroundColor Green
            Write-Host ('             files: ' + $fileList) -ForegroundColor DarkGray

            if (-not $DryRun) {
                Push-Location $resultsDir
                try {
                    $fileNames = $group.Group.Name
                    & tar -czf $tarPath $fileNames 2>$null
                    if ($LASTEXITCODE -eq 0 -and (Test-Path $tarPath)) {
                        $tarSize = (Get-Item $tarPath).Length
                        if ($tarSize -gt 0) {
                            foreach ($f in $group.Group) {
                                Remove-Item $f.FullName -Force
                            }
                            $totalArchived += $group.Count
                            $totalArchivedKB += $monthKB
                        } else {
                            Write-Host '      ERROR: archive empty, originals kept' -ForegroundColor Red
                        }
                    } else {
                        Write-Host ('      ERROR: tar failed (exit ' + $LASTEXITCODE + '), originals kept') -ForegroundColor Red
                    }
                } finally {
                    Pop-Location
                }
            } else {
                $totalArchived += $group.Count
                $totalArchivedKB += $monthKB
            }
        }
    }

    # --- Report remaining ---
    $remaining = (Get-ChildItem $resultsDir -File -Filter '*.csv' -ErrorAction SilentlyContinue).Count
    $archiveCount = 0
    if (Test-Path $archiveDir) {
        $archiveCount = (Get-ChildItem $archiveDir -File -Filter '*.tar.gz' -ErrorAction SilentlyContinue).Count
    }
    Write-Host ('    Remaining: ' + $remaining + ' CSVs, ' + $archiveCount + ' tar.gz archives') -ForegroundColor DarkGray
    Write-Host ''
}

# --- Summary ---
Write-Host '=== Summary ===' -ForegroundColor Cyan
$delMB = [Math]::Round($totalDeletedKB / 1024, 2)
$archMB = [Math]::Round($totalArchivedKB / 1024, 2)
Write-Host ('  Deleted _all.csv:   ' + $totalDeleted + ' files (' + $delMB + ' MB)')
Write-Host ('  Archived to tar.gz: ' + $totalArchived + ' files (' + $archMB + ' MB)')
if ($DryRun) {
    Write-Host ''
    Write-Host '  [DRY RUN] No files were actually modified. Run without -DryRun to execute.' -ForegroundColor Yellow
}
Write-Host ''
Write-Host 'Archives stored in each project results/archive/ folder.' -ForegroundColor DarkGray
Write-Host 'To extract:  tar -xzf results\archive\scanner-v3_2026-05.tar.gz -C results\' -ForegroundColor DarkGray
