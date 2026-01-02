# 简历拷打面试官 - Resume Roaster 🔥

一个基于 RAG（检索增强生成）技术的智能模拟面试系统，让 AI 扮演刁钻的面试官，根据你的简历内容进行深度技术面试。

## ✨ 项目特色

- 🎯 **精准提问**：基于简历内容的针对性技术问题，不是泛泛而谈
- 🧠 **智能检索**：使用 RAG 技术，AI 能准确引用简历中的具体项目和技术栈
- 💬 **连续对话**：支持多轮对话，面试官会根据你的回答继续追问
- 🔧 **多模型支持**：支持 DeepSeek 和 Google Gemini API
- 🆓 **本地 Embedding**：可使用免费的本地 Embedding 模型，无需额外 API 费用
- 🚀 **一键运行**：提供批处理脚本，自动配置环境和依赖

## 🎬 使用场景

### 面试准备
- 上传你的简历 PDF，让 AI 面试官根据你的项目经历提出技术问题
- 练习回答诸如"你在简历中提到使用了 Redis，请具体说说你是如何处理缓存穿透的？"这类深度问题

### 简历优化
- 通过 AI 面试官的提问，发现简历中可能被质疑的技术点
- 提前准备相关技术细节的解释

## 🛠️ 技术架构

### 核心技术栈
- **框架**：LangChain - 大模型应用开发框架
- **向量数据库**：ChromaDB - 本地向量存储
- **文档处理**：PyPDF - PDF 简历解析
- **Embedding**：HuggingFace Transformers - 多语言文本向量化
- **大模型**：DeepSeek API / Google Gemini API

### RAG 工作流程
1. **文档加载**：解析 PDF 简历文件
2. **文本分割**：将简历内容切分为语义块
3. **向量化存储**：使用 Embedding 模型将文本转换为向量并存储
4. **检索增强**：根据用户输入检索相关简历内容
5. **生成回答**：结合检索到的内容和对话历史生成面试问题

## 📦 安装与配置

### 环境要求
- Python 3.8+
- Windows 系统（提供批处理脚本）

### 快速开始

1. **克隆项目**
```bash
git clone <项目地址>
cd ResumeRoaster
```

2. **配置 API Key**
首先复制配置模板文件：
```bash
cp config.ini.template config.ini
```

然后编辑 `config.ini` 文件，配置你的 API 密钥：

```ini
[DEFAULT]
# 选择 API 提供商: deepseek 或 google
provider = deepseek

[deepseek]
# DeepSeek API 配置 (推荐，性价比高)
api_key = your-deepseek-api-key
base_url = https://api.deepseek.com/v1
model = deepseek-chat

[google]
# Google Gemini API 配置
api_key = your-google-api-key
model = gemini-2.0-flash
```

**API 申请地址：**
- DeepSeek: https://platform.deepseek.com/api_keys
- Google Gemini: https://aistudio.google.com/apikey

3. **一键运行**
双击 `run.bat` 文件，脚本会自动：
- 创建 Python 虚拟环境
- 安装所有依赖包
- 启动面试程序

### 手动安装（可选）

如果你更喜欢手动控制安装过程：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

## 🎮 使用方法

1. **启动程序**：运行 `run.bat` 或 `python main.py`

2. **上传简历**：程序会提示你输入简历 PDF 文件路径
   - 可以直接拖拽 PDF 文件到命令行窗口
   - 支持中文路径和文件名

3. **开始面试**：
   - 程序会自动加载简历并初始化 AI 面试官
   - 面试官会先自我介绍，然后开始提问
   - 你可以正常回答，面试官会根据你的回答继续追问

4. **结束面试**：输入 `quit`、`exit`、`退出` 或 `结束` 来结束面试

### 示例对话

```
[面试官]：你好，我是今天的面试官。我已经仔细阅读了你的简历，
看到你有丰富的后端开发经验。让我们从你最近的项目开始吧。
我注意到你在简历中提到负责了一个高并发的电商系统，
请详细介绍一下你是如何设计和优化这个系统的架构的？

[你]：我们使用了微服务架构，通过 Redis 做缓存...

[面试官]：很好，你提到了 Redis 缓存。那么在高并发场景下，
你是如何处理缓存穿透、缓存击穿和缓存雪崩这三个经典问题的？
能具体说说你的解决方案吗？
```

## ⚙️ 配置说明

### Embedding 配置

项目支持两种 Embedding 方式：

1. **本地模型（推荐）**：
```ini
[embedding]
type = local
model = sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```
- ✅ 完全免费
- ✅ 支持中文
- ⚠️ 首次运行需下载约 400MB 模型

2. **DeepSeek API**：
```ini
[embedding]
type = deepseek
model = text-embedding-3-small
```
- ⚠️ 需要额外 API 费用
- ⚠️ 目前 DeepSeek 暂不支持 Embedding API

### 模型选择

- **DeepSeek**：性价比最高的国产大模型，推荐使用
- **Google Gemini**：Google 最新模型，效果优秀但可能需要科学上网

## 📁 项目结构

```
ResumeRoaster/
├── main.py              # 主程序文件
├── config.ini.template  # 配置文件模板（安全，可上传 GitHub）
├── config.ini           # 实际配置文件（包含 API Key，不要上传）
├── requirements.txt     # Python 依赖
├── run.bat             # Windows 一键启动脚本
├── test_api.py         # API 连接测试脚本
├── README.md           # 项目说明文档
├── RAG简历拷问官.md     # 项目设计思路和教程
├── .gitignore          # Git 忽略文件（保护敏感信息）
└── venv/               # Python 虚拟环境（自动创建）
```

## 🔒 安全说明

**重要**：项目已配置 `.gitignore` 文件来保护您的 API Key 安全：

- ✅ `config.ini.template` - 安全的配置模板，可以上传到 GitHub
- ❌ `config.ini` - 包含真实 API Key，已被 `.gitignore` 排除，不会上传
- ✅ 虚拟环境和临时文件也已被忽略

**首次使用步骤**：
1. 克隆项目后，复制 `config.ini.template` 为 `config.ini`
2. 在 `config.ini` 中填入你的真实 API Key
3. 开始使用项目

## 🔧 故障排除

### 常见问题

1. **配置文件不存在**
   - 如果提示找不到 `config.ini`，请先复制模板文件：`cp config.ini.template config.ini`
   - 然后编辑 `config.ini` 填入你的 API Key

2. **API Key 错误**
   - 检查 `config.ini` 中的 API Key 是否正确
   - 确认 API Key 有足够的余额

3. **PDF 读取失败**
   - 确保 PDF 文件没有密码保护
   - 尝试重新保存 PDF 文件

4. **依赖安装失败**
   - 使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
   - 检查 Python 版本是否为 3.8+

5. **模型下载慢**
   - 首次使用本地 Embedding 需要下载模型，请耐心等待
   - 可以配置 HuggingFace 镜像源加速下载

### 测试 API 连接

运行 `test_api.py` 来测试你的 API 配置是否正确：

```bash
python test_api.py
```

## 🚀 扩展功能

### 未来计划
- [ ] 支持 Word 格式简历
- [ ] 添加面试评分功能
- [ ] 支持多轮面试记录
- [ ] Web 界面版本
- [ ] 支持更多大模型 API

### 自定义面试官风格

你可以修改 `main.py` 中的 `system_template` 来自定义面试官的风格：

```python
system_template = """你是一位经验丰富且极其刁钻的技术面试官。
# 在这里修改面试官的人设和提问风格
"""
```

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如果你在使用过程中遇到问题，或者有功能建议，欢迎：
- 提交 GitHub Issue
- 发送邮件到：278886678@qq.com

---

**祝你面试顺利！🎉**