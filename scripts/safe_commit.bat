git commit -m %1
if ERRORLEVEL 2 (
    exit %ERRORLEVEL%
) else (
    exit 0
)