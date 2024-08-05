$lastRunFile = "last_run_date.txt"

function Get-CurrentDate {
    return (Get-Date).ToString("yyyy-MM-dd")
}

function Get-YesterdayDate {
    return (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
}

function Run-Script {
    Write-Output "Running python -m src"
    python -m src
}

function Update-LastRunDate {
    param ($date)
    Set-Content -Path $lastRunFile -Value $date
}

function Main {
    while ($true) {
        $currentDate = Get-CurrentDate
        $yesterdayDate = Get-YesterdayDate
        $currentHour = (Get-Date).Hour

        Write-Output "Current Date: $currentDate"
        Write-Output "Yesterday's Date: $yesterdayDate"        
	Write-Output "Current Hour: $currentHour"

        if (Test-Path $lastRunFile) {
            $lastRunDate = Get-Content $lastRunFile
            Write-Output "Last Run Date: $lastRunDate"
        } else {
            Write-Output "No last run date file found, creating new file."
            $lastRunDate = ""
            Set-Content -Path $lastRunFile -Value $lastRunDate
        }

        if ($currentHour -ge 13) {
            if ($lastRunDate -ne $currentDate) {
                if ($lastRunDate -eq $yesterdayDate) {
                    Run-Script
                    Update-LastRunDate -date $currentDate
                    Write-Output "Updated last run date to: $currentDate"
                } else {
                    Write-Output "Last run date is not yesterday."
                }
            } else {
                Write-Output "Last run date is today or not set."
            }
        } else {
            Write-Output "It is not yet 1 PM."
        }

        Start-Sleep -Seconds 3600
    }
}

Main
