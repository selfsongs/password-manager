@echo off

REM 设置 cmd 窗口编码为 UTF-8
chcp 65001 > nul

REM 打包自动化脚本
REM 功能：激活虚拟环境，安装依赖，执行打包，添加配置文件，创建运行脚本
REM 使用方法：
REM   build.bat                # 默认 Debug 构建（带源码 + debugpy，支持远程调试）
REM   build.bat --release      # Release 构建（不带源码和 debugpy，体积更小更安全）
REM   build.bat --uv           # 使用 uv 安装依赖（Debug 模式）
REM   build.bat --uv --release # 使用 uv 安装依赖（Release 模式）

@REM PYTHONUTF8=1 环境变量的作用是强制 Python 使用 UTF-8 编码进行所有的文件 I/O 操作
@REM Python 会使用系统默认编码（如 GBK）读取 requirements.txt 文件
@REM 如果 requirements.txt 文件使用 UTF-8 编码保存，就会出现 UnicodeDecodeError
@REM 设置 PYTHONUTF8=1 后，Python 会强制使用 UTF-8 编码读取文件，避免这个错误
set PYTHONUTF8=1

REM 解析参数
set USE_UV=0
set BUILD_MODE=debug

:parse_args
if "%1"=="" goto args_done
if "%1"=="--uv" set USE_UV=1
if "%1"=="--release" set BUILD_MODE=release
shift
goto parse_args
:args_done

if "%BUILD_MODE%"=="release" (
    echo ============================================
    echo   Release 构建模式（不含调试功能和源码）
    echo ============================================
) else (
    echo ============================================
    echo   Debug 构建模式（含调试功能和源码）
    echo ============================================
)
echo.
echo 开始打包流程...

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

REM 根据构建模式设置 PyInstaller 参数
set "PYINSTALLER_ARGS=--name password_manager --onedir --noupx"

if "%BUILD_MODE%"=="debug" (
    echo [Debug] 包含 debugpy 调试支持和源码...
    set "PYINSTALLER_ARGS=%PYINSTALLER_ARGS% --additional-hooks-dir=hooks --add-data "src/*.py;.""
) else (
    echo [Release] 排除 debugpy，不包含源码...
    set "PYINSTALLER_ARGS=%PYINSTALLER_ARGS% --exclude-module debugpy --exclude-module pydevd"
)

REM 执行打包
echo 执行打包...
if "%BUILD_MODE%"=="debug" (
    echo [Debug] 包含 debugpy 调试支持、源码...
    pyinstaller --name password_manager --onedir --noupx --additional-hooks-dir=hooks --add-data "src/*.py;." src/main.py
) else (
    pyinstaller --name password_manager --onedir --noupx --exclude-module debugpy --exclude-module pydevd src/main.py
)
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
    echo password_manager.exe %%* ^> log.txt 2^>^&1
    echo pause
) > "dist\password_manager\run_with_log.bat"
if errorlevel 1 (
    echo 创建运行脚本失败
    pause
    exit /b 1
)

REM Debug 模式下额外创建调试启动脚本
if "%BUILD_MODE%"=="debug" (
    echo 创建带调试模式的运行脚本...
    (
        echo @echo off
        echo chcp 65001 ^> nul
        echo call run_with_log.bat --debug
    ) > "dist\password_manager\run_with_log_with_debug.bat"
    if errorlevel 1 (
        echo 创建带调试模式的运行脚本失败
        pause
        exit /b 1
    )
)
echo 运行脚本创建成功

echo.
if "%BUILD_MODE%"=="debug" (
    echo 打包流程完成！[Debug 版本]
    echo 可执行文件位于：dist\password_manager\password_manager.exe
    echo 配置文件已复制到：dist\password_manager\db_config.json
    echo 运行脚本已创建：dist\password_manager\run_with_log.bat
    echo 调试脚本已创建：dist\password_manager\run_with_log_with_debug.bat
    echo.
    echo 调试用法：
    echo   1. 运行 run_with_log_with_debug.bat 启动 exe
    echo   2. 在 VSCode 中选择 "Attach 到打包后的 EXE" 进行调试
) else (
    echo 打包流程完成！[Release 版本]
    echo 可执行文件位于：dist\password_manager\password_manager.exe
    echo 配置文件已复制到：dist\password_manager\db_config.json
    echo 运行脚本已创建：dist\password_manager\run_with_log.bat
    echo.
    echo 注意：Release 版本不包含调试功能和源码
)


REM 创建压缩包用于分发
echo.
echo 创建压缩包用于分发...
set "ZIP_FILE=dist\password_manager.zip"
echo 压缩包路径：%ZIP_FILE%

REM 等待 2 秒，让系统释放文件
echo 等待系统释放文件...
timeout /t 2 /nobreak > nul

echo 开始压缩...
powershell -Command "try { Compress-Archive -Path 'dist\password_manager' -DestinationPath '%ZIP_FILE%' -Force; Write-Host '压缩成功' } catch { Write-Host '压缩失败: ' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo 创建压缩包失败
    pause
    exit /b 1
)
echo 压缩包创建成功：%ZIP_FILE%

echo.
echo 按任意键退出...
pause > nul
exit /b 0