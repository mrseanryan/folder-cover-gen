REM Use Python under Program Files, to get around Application Control issue (Windows 11).

SET PYTHON_PATH=c:\Users\str_i\AppData\Local\Programs\Python\Python314\python.exe

uv run --python "%PYTHON_PATH%" -m folder_cover_gen.cli %1 %2 %3 %4 %5 %6 %7 %8 %9
