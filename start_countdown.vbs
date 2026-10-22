Option Explicit

Dim shell, fileSystem, scriptPath, folderPath, command
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

scriptPath = fileSystem.BuildPath(fileSystem.GetParentFolderName(WScript.ScriptFullName), "countdown.py")
folderPath = fileSystem.GetParentFolderName(scriptPath)
command = "pythonw.exe """ & scriptPath & """"

shell.CurrentDirectory = folderPath
shell.Run command, 0, False
