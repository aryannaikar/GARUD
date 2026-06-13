# Garud Startup Launcher — waits for system to be fully ready before launching
Start-Sleep -Seconds 20  # Wait for audio drivers and mic to initialize

# Use WMI to create a truly independent process (escapes Windows Job Objects)
$wmi = [wmiclass]"Win32_Process"
$wmi.Create('"C:\Users\Aryan Naikar\OneDrive\Desktop\vs\Garud\dist\Garud.exe"', "C:\Users\Aryan Naikar\OneDrive\Desktop\vs\Garud") | Out-Null
