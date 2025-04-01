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
    # copy export.xlsx to C:\Users\berti\OneDrive\Docs\export.xlsx
    Copy-Item -Path "export.xlsx" -Destination "C:\Users\berti\OneDrive\Docs\export.xlsx"
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
            Write-Output "No last run date file found, therefore running the script."
            $lastRunDate = ""
        }

        if ($currentHour -ge 13) {
            if ($lastRunDate -ne $currentDate) {
                Run-Script
                Update-LastRunDate -date $currentDate
                Write-Output "Updated last run date to: $currentDate"
            } else {
                Write-Output "Last run date is today."
            }
        } else {
            Write-Output "It is not yet 1 PM."
        }

        Start-Sleep -Seconds 3600
    }
}

Main
