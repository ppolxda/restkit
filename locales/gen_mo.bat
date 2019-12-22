echo off

cd %~dp0

for /r %%a in (*.po) do (
    echo 'Translating %%a'
    if /i not "%%~na"=="filename" (
        msgfmt -cv -o "%%~pa%%~na.mo" "%%a"
    )
)