REM To be used by Task Scheduler to start or reload NGINX

cd "C:\nginx-1.29.1"

REM Check if nginx.exe is running
tasklist /FI "IMAGENAME eq nginx.exe" | find /I "nginx.exe" >nul
if %ERRORLEVEL%==0 (
    REM NGINX is running, reload it
    "C:\nginx-1.29.1\nginx.exe" -s reload
) else (
    REM NGINX is not running, start it
    start "" /b "C:\nginx-1.29.1\nginx.exe"
)