# Get the current directory of the script
$scriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent

# Define the command to change directory and run the Python script
$command = "cd $scriptDirectory; python -m src"

# Print the command that will be queued
Write-Output "The following command will be queued:"
Write-Output $command

# Define the task action to run the command
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$command`""

# Define the task trigger to run every day at 1 PM
$trigger = New-ScheduledTaskTrigger -Daily -At 1:00PM

# Define task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Define the task principal to run with highest privileges
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the scheduled task
Register-ScheduledTask -TaskName "DailyKleinanzeigenScraper" -Action $action -Trigger $trigger -Settings $settings -Principal $principal

Write-Output "Scheduled task 'DailyKleinanzeigenScraper' has been created to run daily at 1 PM."
