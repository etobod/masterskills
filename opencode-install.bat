@rem Installs or updates the OpenCode version of masterskills: pulls this repository, then builds into the OpenCode config directory.
@setlocal
@cd /d "%~dp0"
@git pull --ff-only
@if errorlevel 1 (
  @echo masterskills: git pull failed, nothing installed.
  @exit /b 1
)
@where python >nul 2>nul && (set "PY=python") || (set "PY=py -3")
@%PY% -B opencode\build.py --install
@exit /b %ERRORLEVEL%
