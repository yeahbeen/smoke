@echo off
REM echo 当前盘符：%~d0
REM echo 当前盘符和路径：%~dp0
REM echo 当前盘符和路径的短文件名格式：%~sdp0
REM echo 当前批处理全路径：%~f0
REM echo 当前CMD默认目录：%cd%




%~d0
cd %~dp0
echo 当前CMD目录：%cd%

C:\Python34\python.exe smoke.py 