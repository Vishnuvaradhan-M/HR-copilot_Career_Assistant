# Stop Streamlit reliably using recorded PID in streamlit_status.json
# Usage: .\stop_streamlit.ps1

$status = "streamlit_status.json"

if (Test-Path $status) {
    try {
        $j = Get-Content $status | ConvertFrom-Json
        if ($j.pid) {
            $stream_pid = $j.pid
            Write-Host "Stopping Streamlit PID $stream_pid"
            Stop-Process -Id $stream_pid -Force -ErrorAction SilentlyContinue
            Remove-Item $status -ErrorAction SilentlyContinue
            Write-Host "Stopped and removed status file."
            Exit 0
        }
    } catch {
        Write-Host "Could not parse status file, falling back to killing python processes"
    }
}

# Fallback: kill python processes that look like streamlit
$py = Get-Process python* -ErrorAction SilentlyContinue
if ($py) {
    foreach ($p in $py) {
        try {
            if ($p.Path -and ($p.Path -match "python")) {
                Write-Host "Stopping process $($p.Id) $($p.Path)"
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            }
        } catch {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Stopped python processes (fallback)."
} else {
    Write-Host "No python processes found."
}
