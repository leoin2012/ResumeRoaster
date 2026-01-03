@echo off
chcp 65001
echo ========================================
echo    彻底清理并修复依赖
echo ========================================
echo.
echo [问题] 你的环境中有不需要的包导致冲突：
echo   - tensorflow 2.20.0 (不需要)
echo   - grpcio-status (不需要)
echo   - tensorboard (不需要)
echo.
echo [解决] 此脚本将：
echo   1. 卸载所有冲突的包
echo   2. 清理缓存
echo   3. 只安装项目需要的依赖
echo.

pause

echo.
echo ========================================
echo [步骤1] 卸载不需要的包
echo ========================================
echo.

echo [1.1] 卸载 tensorflow（项目不需要）...
pip uninstall -y tensorflow tensorflow-intel tensorflow-io-gcs-filesystem
echo.

echo [1.2] 卸载 tensorboard（项目不需要）...
pip uninstall -y tensorboard tensorboard-data-server
echo.

echo [1.3] 卸载 grpcio 相关包（项目不需要）...
pip uninstall -y grpcio grpcio-status grpcio-tools
echo.

echo [1.4] 卸载 opentelemetry 相关包（项目不需要）...
pip uninstall -y opentelemetry-exporter-otlp-proto-grpc opentelemetry-api opentelemetry-sdk
echo.

echo [1.5] 卸载 protobuf（准备重装）...
pip uninstall -y protobuf
pip uninstall -y protobuf
pip uninstall -y protobuf
echo.

echo [1.6] 卸载 chromadb（准备重装）...
pip uninstall -y chromadb
echo.

echo [1.7] 清理 pip 缓存...
pip cache purge
echo.

echo ========================================
echo [步骤2] 安装项目需要的依赖
echo ========================================
echo.

echo [2.1] 安装 protobuf 3.20.3...
pip install --no-cache-dir protobuf==3.20.3
if errorlevel 1 (
    echo [警告] 安装失败，尝试使用镜像源...
    pip install --no-cache-dir protobuf==3.20.3 -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo.

echo [2.2] 验证 protobuf 版本...
python -c "import google.protobuf; print('Protobuf 版本:', google.protobuf.__version__)"
if errorlevel 1 (
    echo [错误] protobuf 安装失败
    pause
    exit /b 1
)
echo.

echo [2.3] 安装 chromadb 0.4.24...
pip install --no-cache-dir chromadb==0.4.24
if errorlevel 1 (
    echo [警告] 安装失败，尝试使用镜像源...
    pip install --no-cache-dir chromadb==0.4.24 -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo.

echo [2.4] 安装其他核心依赖...
pip install --no-cache-dir sentence-transformers==2.7.0
pip install --no-cache-dir langchain==0.2.16
pip install --no-cache-dir langchain-community==0.2.17
pip install --no-cache-dir langchain-google-genai==1.0.10
pip install --no-cache-dir langchain-openai==0.1.25
pip install --no-cache-dir langchain-text-splitters==0.2.4
pip install --no-cache-dir langchain-huggingface==0.0.3
pip install --no-cache-dir pypdf==4.3.1
pip install --no-cache-dir python-dotenv==1.0.1
pip install --no-cache-dir flask==3.0.0
pip install --no-cache-dir flask-cors==4.0.0
echo.

echo [2.5] 强制降级 protobuf（防止被其他包升级）...
echo [重要] 某些依赖可能会自动升级 protobuf，现在强制降回 3.20.3
pip uninstall -y protobuf
pip install --no-cache-dir protobuf==3.20.3
echo.

echo [2.6] 再次验证 protobuf 版本...
python -c "import google.protobuf; print('Protobuf 最终版本:', google.protobuf.__version__)"
echo.

echo ========================================
echo [步骤3] 最终验证
echo ========================================
echo.

echo [3.1] 检查 protobuf 版本...
python -c "import google.protobuf; v=google.protobuf.__version__; print('Protobuf:', v); exit(0 if v.startswith('3.20') else 1)"
if errorlevel 1 (
    echo [错误] protobuf 版本不对！
    pause
    exit /b 1
)
echo ✓ Protobuf 版本正确
echo.

echo [3.2] 检查 chromadb...
python -c "import chromadb; print('✓ ChromaDB:', chromadb.__version__)"
if errorlevel 1 (
    echo [错误] ChromaDB 未正确安装
    pause
    exit /b 1
)
echo.

echo [3.3] 检查 HuggingFaceEmbeddings...
python -c "from langchain_huggingface import HuggingFaceEmbeddings; print('✓ HuggingFaceEmbeddings 可用')"
if errorlevel 1 (
    echo [错误] HuggingFaceEmbeddings 未正确安装
    pause
    exit /b 1
)
echo.

echo [3.4] 检查是否还有冲突...
pip check
echo.

echo ========================================
echo    修复成功！
echo ========================================
echo.
echo ✓ 已卸载不需要的包（tensorflow、grpcio 等）
echo ✓ protobuf 3.20.3 已安装
echo ✓ chromadb 0.4.24 已安装
echo ✓ 所有项目依赖已安装
echo.
echo 现在可以运行 run.bat 测试了！
echo.

pause
