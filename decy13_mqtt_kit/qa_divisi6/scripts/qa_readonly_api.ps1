<#
QA Divisi 6: sampling GET /api/status tanpa MQTT publish, aktuator, atau GPIO.
Windows PowerShell 5.1. Contoh:
  .\qa_readonly_api.ps1 -Samples 30
  .\qa_readonly_api.ps1 -Samples 300 -Uri http://127.0.0.1:1880/api/status
#>
param(
    [ValidateRange(1,10000)][int]$Samples = 30,
    [string]$Uri = 'http://127.0.0.1:1880/api/status',
    [string]$OutputCsv = ''
)

if ([string]::IsNullOrWhiteSpace($OutputCsv)) {
    $OutputCsv = Join-Path (Get-Location) ("DECY13_QA_{0}_samples_{1}.csv" -f $Samples,(Get-Date -Format 'yyyyMMdd_HHmmss'))
}
$rows = New-Object System.Collections.Generic.List[object]
Write-Host "DECY-13 QA read-only: $Samples sampel dari $Uri"
for ($i = 1; $i -le $Samples; $i++) {
    $now = Get-Date
    try {
        $s = Invoke-RestMethod -Uri $Uri -TimeoutSec 5 -ErrorAction Stop
        $missing = 0
        if ($null -ne $s.link.missing) { $missing = @($s.link.missing).Count }
        $rows.Add([PSCustomObject]@{
            Waktu = $now.ToString('yyyy-MM-dd HH:mm:ss.fff')
            Sample = $i
            RequestOK = $true
            Online = [bool]$s.link.online
            Hz = [double]$s.link.hz
            Packets = [long]$s.link.packets
            Bad = [long]$s.link.bad
            Missing = $missing
            AgeMs = [double]$s.link.ageMs
            Stage = [string]$s.stage
            Mode = [string]$s.mode
            Error = ''
        })
    } catch {
        $rows.Add([PSCustomObject]@{
            Waktu=$now.ToString('yyyy-MM-dd HH:mm:ss.fff'); Sample=$i
            RequestOK=$false; Online=$false; Hz=$null; Packets=$null
            Bad=$null; Missing=$null; AgeMs=$null; Stage=$null
            Mode='API_ERROR'; Error=$_.Exception.Message
        })
    }
    if ($i -lt $Samples) { Start-Sleep -Seconds 1 }
}
$rows | Export-Csv -Path $OutputCsv -NoTypeInformation -Encoding UTF8
$valid = @($rows | Where-Object { $_.RequestOK })
$online = @($valid | Where-Object { $_.Online })
$invalid = @($valid | Where-Object { $_.Missing -gt 0 })
Write-Host "HASIL QA: valid $($valid.Count)/$Samples | ONLINE $($online.Count) | OFFLINE/API_ERROR $($Samples-$online.Count)"
if ($valid.Count -gt 0) {
    $stats = $valid | Measure-Object -Property Hz -Average -Minimum -Maximum
    Write-Host ("Hz rata-rata={0:N2} minimum={1:N2} maksimum={2:N2}" -f $stats.Average, $stats.Minimum, $stats.Maximum)
    Write-Host "Sampel field hilang: $($invalid.Count)"
}
if ($valid.Count -ge 2) {
    $first = $valid[0]; $last = $valid[-1]
    Write-Host "Delta paket: $($last.Packets - $first.Packets) | Delta invalid: $($last.Bad - $first.Bad)"
}
Write-Host "CSV: $OutputCsv"
if ($valid.Count -eq $Samples -and $online.Count -eq $Samples -and $invalid.Count -eq 0 -and
    (($valid.Count -lt 2) -or (($valid[-1].Bad - $valid[0].Bad) -eq 0))) {
    Write-Host 'STATUS: PASS untuk validitas API/ONLINE/field/invalid pada sampel yang diuji'
} else {
    Write-Host 'STATUS: REVIEW / FAIL (periksa data CSV dan koneksi)'
}
