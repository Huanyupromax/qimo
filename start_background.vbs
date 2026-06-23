CreateObject("WScript.Shell").Run "cmd /c cd /d " & CreateObject("Scripting.FileSystemObject").GetAbsolutePathName(".") & " && .\venv\Scripts\python.exe -X utf8 app.py", 0, False
