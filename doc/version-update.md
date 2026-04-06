# 密码管理器版本更新功能技术方案

## 1. 项目背景

当前密码管理器为本地应用程序，用户无法及时获取最新版本的功能更新和安全修复。为提升用户体验和安全性，需要实现版本更新功能，使应用能够自动检查更新、下载并安装最新版本。

## 2. 功能概述

### 2.1 核心功能

- **自动检查更新**：应用启动时自动检查是否有新版本
- **手动检查更新**：提供手动检查更新的入口
- **版本对比**：比较本地版本与远程版本
- **更新提示**：当有新版本时显示更新提示
- **下载更新**：支持下载最新版本安装包
- **自动安装**：下载完成后自动安装更新
- **版本回滚**：更新失败时能够回滚到之前版本

### 2.2 非功能需求

- **安全性**：确保更新来源可信，防止恶意代码注入
- **可靠性**：处理网络异常、下载失败等情况
- **用户体验**：更新过程不影响用户正常使用
- **兼容性**：支持不同操作系统（Windows、macOS）

## 3. 技术方案

### 3.1 版本管理机制

#### 3.1.1 版本存储

- **本地版本**：
  - 在 `src/config.py` 中硬编码版本号
  - 格式：`VERSION = "1.0.0"`
  - 同时在 `pyproject.toml` 中保持版本号一致

- **远程版本**：
  - 在服务器上存储 `version.json` 文件
  - 示例格式：

    ```json
    {
      "latest_version": "1.1.0",
      "download_url": "https://example.com/password-manager-v1.1.0.exe",
      "changelog": [
        "新增：支持批量导入密码",
        "修复：登录界面崩溃问题",
        "优化：数据库性能"
      ],
      "md5_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    }
    ```

#### 3.1.2 版本号格式

- 使用语义化版本号（Semantic Versioning）：`主版本.次版本.修订号`
- 示例：`1.0.0`、`1.1.0`、`2.0.0`

### 3.2 更新检查流程

#### 3.2.1 自动检查

- 应用启动时，在后台线程中执行更新检查
- 检查频率：每次启动时检查一次
- 超时设置：网络请求超时时间为 5 秒

#### 3.2.2 手动检查

- 在设置页面添加“检查更新”按钮
- 点击后立即执行更新检查
- 显示检查状态和结果

#### 3.2.3 检查机制

1. **获取本地版本**：从 `src/config.py` 读取当前版本号
2. **获取远程版本**：从服务器下载 `version.json` 文件
3. **版本对比**：使用版本号比较算法判断是否有更新
4. **结果处理**：
   - 有更新：显示更新提示弹窗
   - 无更新：显示“已是最新版本”提示
   - 检查失败：记录错误，不影响程序运行

#### 3.2.4 版本比较算法

```python
def compare_versions(version1, version2):
    """比较两个版本号，返回 1（version1 > version2）、0（相等）或 -1（version1 < version2）"""
    v1_parts = list(map(int, version1.split('.')))
    v2_parts = list(map(int, version2.split('.')))
    
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1 = v1_parts[i] if i < len(v1_parts) else 0
        v2 = v2_parts[i] if i < len(v2_parts) else 0
        
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    
    return 0
```

### 3.3 下载和安装流程

#### 3.3.1 更新包格式

- **完整包**：包含整个程序的可执行文件和依赖
- **文件格式**：
  - Windows：`.exe` 安装包
  - macOS：`.dmg` 安装包

#### 3.3.2 下载机制

- 使用 `requests` 库下载更新包
- 显示下载进度条
- 支持断点续传
- 下载完成后验证文件完整性（使用 MD5 校验）

#### 3.3.3 安装机制

- **自更新实现**：
  1. 下载更新包到临时目录（`%TEMP%\password-manager-update`）
  2. 验证文件完整性
  3. 创建更新脚本（`updater.bat`）
  4. 退出主程序
  5. 运行更新脚本，替换旧文件
  6. 重启主程序

- **更新脚本示例**：

  ```batch
  @echo off
  timeout /t 2 > nul
  xcopy /y "update\*" "%~dp0"
  start "" "%~dp0password_manager.exe"
  del /f /q "updater.bat"
  rd /s /q "update"
  ```

#### 3.3.4 安全考虑

- 使用 HTTPS 下载更新包
- 验证更新包的 MD5 哈希值
- 防止中间人攻击
- 确保更新来源可信

### 3.4 用户交互设计

#### 3.4.1 更新提示弹窗

- 显示当前版本和最新版本
- 显示更新内容（从远程版本信息中获取）
- 提供“立即更新”、“稍后提醒”和“忽略此版本”按钮

#### 3.4.2 下载进度弹窗

- 显示下载进度条
- 显示下载速度和剩余时间
- 提供“取消下载”按钮
- 下载完成后自动开始安装

#### 3.4.3 安装完成提示

- 显示安装成功信息
- 提供“立即重启”和“稍后重启”按钮

#### 3.4.4 错误处理

- 网络错误：显示网络连接失败提示，提供重试选项
- 下载失败：显示下载失败提示，提供重试选项
- 安装失败：显示安装失败提示，提供回滚选项

### 3.5 实现架构

#### 3.5.1 模块设计

- **`src/update/checker.py`**：更新检查模块
- **`src/update/downloader.py`**：更新下载模块
- **`src/update/installer.py`**：更新安装模块
- **`src/update/ui.py`**：更新 UI 模块
- **`src/config.py`**：版本配置模块

#### 3.5.2 类设计

| 类名               | 职责     | 主要方法               |
| ------------------ | -------- | ---------------------- |
| `UpdateChecker`    | 检查更新 | `check_for_updates()`  |
| `UpdateDownloader` | 下载更新 | `download_update()`    |
| `UpdateInstaller`  | 安装更新 | `install_update()`     |
| `UpdateUI`         | 更新界面 | `show_update_dialog()` |

## 4. 实现步骤

### 4.1 准备工作

1. 创建版本管理服务器，部署 `version.json` 文件
2. 在 `src/config.py` 中添加版本号配置
3. 安装必要的依赖（`requests`）

### 4.2 核心功能实现

1. **版本检查模块**：
   - 实现 `UpdateChecker` 类
   - 实现网络请求和版本对比功能

2. **下载模块**：
   - 实现 `UpdateDownloader` 类
   - 实现下载进度和文件验证功能

3. **安装模块**：
   - 实现 `UpdateInstaller` 类
   - 实现文件替换和程序重启功能

4. **UI 模块**：
   - 实现 `UpdateUI` 类
   - 实现更新提示和进度弹窗

5. **集成到主程序**：
   - 在 `main.py` 中添加自动检查更新逻辑
   - 在设置页面添加手动检查更新按钮

### 4.3 测试和优化

1. 测试不同网络环境下的更新流程
2. 测试更新失败的回滚机制
3. 优化下载速度和用户体验
4. 测试不同操作系统的兼容性

## 5. 技术栈

| 技术/库       | 用途      | 版本要求  |
| ------------- | --------- | --------- |
| Python        | 开发语言  | >= 3.11   |
| customtkinter | UI 库     | >= 5.2.0  |
| requests      | 网络请求  | >= 2.31.0 |
| json          | JSON 处理 | 标准库    |
| os            | 文件操作  | 标准库    |
| shutil        | 文件复制  | 标准库    |
| threading     | 多线程    | 标准库    |
| hashlib       | 文件校验  | 标准库    |

## 6. 测试计划

### 6.1 功能测试

- **自动检查更新**：启动应用，验证是否自动检查更新
- **手动检查更新**：点击“检查更新”按钮，验证是否正确检查
- **版本对比**：测试不同版本号的比较结果
- **下载功能**：测试不同网络环境下的下载速度和稳定性
- **安装功能**：测试更新包的安装过程
- **错误处理**：测试网络异常、下载失败等情况的处理

### 6.2 安全测试

- **文件完整性**：验证下载的更新包 MD5 哈希值
- **更新来源**：确保更新包来自可信来源
- **权限管理**：测试不同权限下的安装过程

### 6.3 兼容性测试

- **Windows**：测试 Windows 10/11 环境
- **macOS**：测试 macOS 12/13 环境
- **不同 Python 版本**：测试 Python 3.11+ 版本

## 7. 风险分析

### 7.1 潜在风险

- **网络异常**：网络连接不稳定导致更新检查或下载失败
- **文件损坏**：下载的更新包损坏导致安装失败
- **权限不足**：程序没有足够权限写入安装目录
- **版本冲突**：更新过程中发生版本冲突
- **安全风险**：更新来源被篡改，注入恶意代码

### 7.2 风险缓解措施

- **网络异常**：实现重试机制，设置合理的超时时间
- **文件损坏**：使用 MD5 校验确保文件完整性
- **权限不足**：添加权限检查，提示用户以管理员身份运行
- **版本冲突**：实现版本回滚机制，确保更新失败时能恢复到之前版本
- **安全风险**：使用 HTTPS 下载，验证更新包的数字签名

## 8. CI/CD 集成

为了实现自动化的构建、测试和发布流程，建议将版本更新功能与 CI/CD 集成。

### 8.1 流程设计

#### 8.1.1 代码提交触发 Debug 构建

- **触发条件**：每次向主分支（如 `main` 或 `develop`）提交代码时
- **构建内容**：
  - 安装依赖
  - 运行测试
  - 构建 Debug 版本的可执行文件
  - 上传构建产物到 artifact 存储

#### 8.1.2 创建 Tag 触发 Release 构建

- **触发条件**：当创建新的 Git Tag（如 `v1.1.0`）时
- **构建内容**：
  - 安装依赖
  - 运行测试
  - 构建 Release 版本的可执行文件
  - 自动更新版本号
  - 生成更新包
  - 更新 `version.json` 文件
  - 发布到 GitHub Releases 或其他分发平台

### 8.2 版本号管理

- **版本格式**：遵循语义化版本号（`主版本.次版本.修订号`）
- **版本更新规则**：
  - 补丁版本（如 `1.0.0 → 1.0.1`）：修复 bug
  - 次版本（如 `1.0.0 → 1.1.0`）：添加新功能
  - 主版本（如 `1.0.0 → 2.0.0`）：不兼容的重大变更
- **自动版本更新**：
  - 基于 Git Tag 自动更新版本号
  - 更新 `src/config.py` 和 `pyproject.toml` 中的版本号
  - 更新 `version.json` 文件中的版本信息

### 8.3 实现示例

#### GitHub Actions 配置示例（`.github/workflows/ci-cd.yml`）

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
    tags: [ v*.*.* ]

jobs:
  # Debug 构建（代码提交时）
  debug-build:
    if: startsWith(github.ref, 'refs/heads/')
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build Debug version
        run: |
          pyinstaller --name password_manager_debug --onedir src/main.py
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: password-manager-debug
          path: dist/

  # Release 构建（创建 Tag 时）
  release-build:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Extract version from tag
        id: get-version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_ENV
      - name: Update version files
        run: |
          # 更新 src/config.py
          (Get-Content src/config.py) -replace 'VERSION = ".*"', "VERSION = `"$env:VERSION`"" | Set-Content src/config.py
          # 更新 pyproject.toml
          (Get-Content pyproject.toml) -replace 'version = ".*"', "version = `"$env:VERSION`"" | Set-Content pyproject.toml
          # 更新 version.json
          $versionInfo = @{
            latest_version = $env:VERSION
            download_url = "https://github.com/yourusername/password-manager/releases/download/v$env:VERSION/password_manager.exe"
            changelog = @("Auto-generated release")
            md5_hash = ""
          } | ConvertTo-Json
          $versionInfo | Set-Content version.json
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build Release version
        run: |
          pyinstaller --name password_manager --onedir src/main.py
      - name: Calculate MD5 hash
        id: calculate-hash
        run: |
          $hash = Get-FileHash dist/password_manager/password_manager.exe -Algorithm MD5 | Select-Object -ExpandProperty Hash
          echo "MD5_HASH=$hash" >> $env:GITHUB_ENV
      - name: Update version.json with MD5
        run: |
          $versionInfo = Get-Content version.json | ConvertFrom-Json
          $versionInfo.md5_hash = "$env:MD5_HASH"
          $versionInfo | ConvertTo-Json | Set-Content version.json
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/password_manager/password_manager.exe
            version.json
          body: "Release version ${{ env.VERSION }}"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 8.4 优势和注意事项

#### 优势

- **自动化**：减少人工干预，提高开发效率
- **一致性**：确保每次构建的版本号和产物一致
- **可靠性**：通过 CI/CD 流程确保代码质量
- **可追溯性**：每个版本都有对应的 Git Tag 和 Release 记录

#### 注意事项

- **密钥管理**：确保 CI/CD 流程中的密钥（如 GitHub Token）安全存储
- **构建环境**：确保构建环境与目标环境一致
- **测试覆盖**：添加足够的测试用例，确保构建产物的质量
- **版本号规范**：严格遵循语义化版本号规范，避免版本冲突

## 9. 结论

通过实现版本更新功能，密码管理器将能够及时为用户提供最新的功能和安全修复，提升用户体验和安全性。本技术方案详细设计了版本管理、更新检查、下载安装、用户交互和 CI/CD 集成等方面的实现细节，确保更新过程安全、可靠、用户友好。

在实施过程中，需要注意安全风险的防范，确保更新来源可信，同时优化用户体验，确保更新过程不影响用户正常使用。通过严格的测试和 CI/CD 集成，可以确保版本更新功能的稳定性和可靠性，实现自动化的构建、测试和发布流程。
