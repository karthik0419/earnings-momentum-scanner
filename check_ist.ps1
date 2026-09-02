$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('India Standard Time')
$ist = [System.TimeZoneInfo]::ConvertTimeFromUtc((Get-Date).ToUniversalTime(), $tz)
Write-Host ('IST now: ' + $ist.ToString('yyyy-MM-dd HH:mm:ss dddd'))
$tod = $ist.TimeOfDay
if ($tod -ge [TimeSpan]'09:00:00' -and $tod -lt [TimeSpan]'09:15:00') {
    $state = 'PRE-OPEN'
} elseif ($tod -ge [TimeSpan]'09:15:00' -and $tod -lt [TimeSpan]'15:30:00') {
    $state = 'OPEN'
} elseif ($tod -lt [TimeSpan]'09:00:00') {
    $state = 'PRE-MARKET (closed)'
} else {
    $state = 'CLOSED'
}
Write-Host ('Market state: ' + $state)
