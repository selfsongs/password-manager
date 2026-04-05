@echo off

REM 设置 cmd 窗口编码为 UTF-8
chcp 65001 > nul

REM 打包自动化脚本
REM 功能：激活虚拟环境，安装依赖，执行打包，添加配置文件，创建运行脚本
REM 使用方法：build.bat [--uv]  # 使用uv安装依赖

@REM PYTHONUTF8=1 环境变量的作用是强制 Python 使用 UTF-8 编码进行所有的文件 I/O 操作
@REM Python 会使用系统默认编码（如 GBK）读取 requirements.txt 文件
@REM 如果 requirements.txt 文件使用 UTF-8 编码保存，就会出现 UnicodeDecodeError
@REM 设置 PYTHONUTF8=1 后，Python 会强制使用 UTF-8 编码读取文件，避免这个错误
set PYTHONUTF8=1

echo 开始打包流程...

REM 检查是否使用uv
set USE_UV=0
if "%1"=="--uv" set USE_UV=1

REM 如果使用uv，检查是否安装了uv
if %USE_UV%==1 (
    echo 检查uv是否安装...
    uv --version > nul 2>&1
    if errorlevel 1 (
        echo uv未安装，正在安装...
        pip install uv
        if errorlevel 1 (
            echo 安装uv失败
            pause
            exit /b 1
        )
        echo uv安装成功
    ) else (
        echo uv已安装
    )
)

REM 检查虚拟环境是否存在
if not exist ".venv" (
    echo 虚拟环境不存在，正在创建...
    if %USE_UV%==1 (
        echo 使用uv创建虚拟环境...
        uv venv
        if errorlevel 1 (
            echo 创建虚拟环境失败
            pause
            exit /b 1
        )
    ) else (
        echo 使用python创建虚拟环境...
        python -m venv .venv
        if errorlevel 1 (
            echo 创建虚拟环境失败，请检查Python安装
            pause
            exit /b 1
        )
    )
    echo 虚拟环境创建成功
)

REM 激活虚拟环境
echo 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo 激活虚拟环境失败
    pause
    exit /b 1
)
echo 虚拟环境激活成功

REM 安装依赖
echo 安装依赖...
if %USE_UV%==1 (
    echo 使用uv安装依赖...
    uv pip install -r requirements.txt
    if errorlevel 1 (
        echo 安装依赖失败
        pause
        exit /b 1
    )
) else (
    echo 使用pip安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 安装依赖失败
        pause
        exit /b 1
    )
)
echo 依赖安装成功

REM 安装PyInstaller
echo 安装PyInstaller...
if %USE_UV%==1 (
    echo 使用uv安装PyInstaller...
    uv pip install pyinstaller
    if errorlevel 1 (
        echo 安装PyInstaller失败
        pause
        exit /b 1
    )
) else (
    echo 使用pip安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 安装PyInstaller失败
        pause
        exit /b 1
    )
)
echo PyInstaller安装成功

REM 执行打包
echo 执行打包...
pyinstaller --name password_manager src/main.py
if errorlevel 1 (
    echo 打包失败
    pause
    exit /b 1
)
echo 打包成功

REM 复制db_config.json到打包后的目录
echo 复制配置文件...
if exist "db_config.json" (
    copy "db_config.json" "dist\password_manager\" /y
    if errorlevel 1 (
        echo 复制配置文件失败
        pause
        exit /b 1
    )
    echo 配置文件复制成功
) else (
    echo 配置文件不存在，使用默认配置
)

REM 创建run_with_log.bat文件
echo 创建运行脚本...
(
    echo @echo off
    echo chcp 65001 ^> nul
    echo password_manager.exe ^> log.txt 2^>^&1
    echo pause
) > "dist\password_manager\run_with_log.bat"
if errorlevel 1 (
    echo 创建运行脚本失败
    pause
    exit /b 1
)
echo 运行脚本创建成功

echo 打包流程完成！
echo 可执行文件位于：dist\password_manager\password_manager.exe
echo 配置文件已复制到：dist\password_manager\db_config.json
echo 运行脚本已创建：dist\password_manager\run_with_log.bat

REM 创建压缩包用于分发
echo 创建压缩包用于分发...
set "ZIP_FILE=dist\password_manager.zip"
echo 压缩包路径：%ZIP_FILE%
echo 开始压缩...
powershell -Command "try { Compress-Archive -Path 'dist\password_manager' -DestinationPath '%ZIP_FILE%' -Force; Write-Host '压缩成功' } catch { Write-Host '压缩失败: ' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo 创建压缩包失败
    pause
    exit /b 1
)
echo 压缩包创建成功：%ZIP_FILE%

echo.
echo 打包流程完成！
echo 可执行文件位于：dist\password_manager\password_manager.exe
echo 配置文件已复制到：dist\password_manager\db_config.json
echo 运行脚本已创建：dist\password_manager\run_with_log.bat
echo 压缩包已创建：%ZIP_FILE%

echo.
echo 按任意键退出...
pause > nul
exit /b 0