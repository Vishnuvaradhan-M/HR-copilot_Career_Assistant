# Start Streamlit reliably on port 8530
# Stops orphaned python processes that may hold the port, then starts streamlit.
# Usage: .\start_streamlit.ps1

$port = 8530
$log = "streamlit.log"
$status = "streamlit_status.json"

Write-Host "Checking for processes listening on port $port..."
# Windows: find process using the port (netstat -> findstr -> get-process)
$net = netstat -a -n -o | Select-String ":$port "
if ($net) {
    foreach ($line in $net) {
        $parts = $line -split '\s+'
        $port_pid = $parts[-1]
        if ($port_pid -and $port_pid -ne $PID) {
            Write-Host "Killing process $port_pid that may be using port $port"
            Stop-Process -Id $port_pid -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Starting Streamlit on 127.0.0.1:$port; logs -> $log"
# Start streamlit as a background process
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "python"
$psi.Arguments = "-m streamlit run streamlit_app.py --server.port=$port --server.address=127.0.0.1"
$psi.WorkingDirectory = (Get-Location).Path
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$proc.Start() | Out-Null

# Redirect output to log
$stdout = $proc.StandardOutput
$stderr = $proc.StandardError
Start-Job -ScriptBlock {
    param($out,$err,$log)
    while (-not $out.EndOfStream) { $line = $out.ReadLine(); Add-Content -Path $log -Value $line }
} -ArgumentList $stdout,$stderr,$log | Out-Null

Write-Host "Streamlit started with PID $($proc.Id). Waiting for status file..."
# Wait up to 30s for streamlit_status.json
$wait = 0
while (-not (Test-Path $status) -and $wait -lt 30) {
    Start-Sleep -Seconds 1
    $wait += 1
}
if (Test-Path $status) {
    Write-Host "Status file created:" (Get-Content $status | ConvertFrom-Json)
} else {
    Write-Host "Warning: status file not found after 30s. Check $log"
}

Write-Host "Start script finished. Streamlit PID: $($proc.Id)"
