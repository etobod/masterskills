@rem Installs or updates the OpenCode version of masterskills: upgrades OpenCode itself with winget, pulls this repository, then builds into the OpenCode config directory.
@setlocal
@cd /d "%~dp0"
@rem No winget, no newer version or a running OpenCode holding the file: the plugin is installed anyway.
@where winget >nul 2>nul && winget upgrade --id SST.opencode -e --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
@git pull --ff-only
@if errorlevel 1 (
  @echo masterskills: git pull failed, nothing installed.
  @exit /b 1
)
@where python >nul 2>nul && (set "PY=python") || (set "PY=py -3")
@%PY% -B opencode\build.py --install
@exit /b %ERRORLEVEL%
