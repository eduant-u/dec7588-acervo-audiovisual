@echo off
cd /d "%~dp0"
python -B -c "from preparar_banco import binaries; from config import LOCAL; import subprocess; subprocess.run([str(binaries()/'pg_ctl.exe'),'-D',str(LOCAL/'pgdata'),'-m','fast','-w','stop'])"
pause

