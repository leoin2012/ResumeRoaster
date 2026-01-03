# -*- coding: utf-8 -*-
"""
简历拷打面试官 - Resume Roaster
基于 RAG 技术的模拟面试对话系统
支持 DeepSeek 和 Google Gemini API
"""

import os
import sys
import configparser
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate


def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent / "config.ini"
    
    if not config_path.exists():
        print("错误：找不到 config.ini 配置文件！")
        return None
    
    config.read(config_path, encoding='utf-8')
    return config


def print_banner(style='critical'):
    """打印欢迎横幅"""
    style_info = {
        'critical': '我是一位刁钻的面试官，准备好被拷问了吗？',
        'partner': '我是一位充满热情的面试官，让我们一起聊聊你的经历吧！',
        'guide': '我是一位善于引导的面试官，让我们一起探讨你的技术之路。'
    }
    
    print("\n" + "=" * 50)
    print("   简历拷打面试官 - Resume Roaster")
    print("=" * 50)
    print(f"   {style_info.get(style, style_info['critical'])}")
    print("=" * 50 + "\n")


def get_llm(config):
    """根据配置创建 LLM"""
    provider = config.get('DEFAULT', 'provider').lower()
    
    if provider == 'deepseek':
        from langchain_openai import ChatOpenAI
        api_key = config.get('deepseek', 'api_key')
        base_url = config.get('deepseek', 'base_url')
        model = config.get('deepseek', 'model')
        
        if api_key == 'your-deepseek-api-key':
            print("错误：请在 config.ini 中配置 DeepSeek API Key！")
            print("申请地址：https://platform.deepseek.com/api_keys")
            return None
        
        print(f"使用 DeepSeek API，模型：{model}")
        return ChatOpenAI(
            model_name=model,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7
        )
    
    elif provider == 'google':
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = config.get('google', 'api_key')
        model = config.get('google', 'model')
        
        if api_key == 'your-google-api-key':
            print("错误：请在 config.ini 中配置 Google API Key！")
            print("申请地址：https://aistudio.google.com/apikey")
            return None
        
        print(f"使用 Google Gemini API，模型：{model}")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
    
    else:
        print(f"错误：不支持的 API 提供商 '{provider}'")
        print("请在 config.ini 中设置 provider = deepseek 或 google")
        return None


def get_resume_path():
    """获取简历文件路径"""
    print("请输入简历 PDF 文件路径（可直接拖拽文件到此窗口）：")
    path = input("> ").strip().strip('"').strip("'")
    
    if not path:
        print("未输入文件路径")
        return None
    
    path = Path(path)
    if not path.exists():
        print(f"文件不存在：{path}")
        return None
    
    if path.suffix.lower() != ".pdf":
        print("请提供 PDF 格式的简历文件")
        return None
    
    return path


def load_resume(pdf_path: Path):
    """加载并处理简历"""
    print(f"\n正在加载简历：{pdf_path.name}")
    
    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()
    
    if not documents:
        print("无法读取简历内容")
        return None
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "；", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    print(f"简历已加载，共 {len(chunks)} 个文本块")
    return chunks


def get_interview_style_prompt(style: str) -> str:
    """根据风格返回对应的面试官提示词"""
    
    styles = {
        'critical': """你是一位经验丰富且极其刁钻的技术面试官。你的任务是根据候选人的简历内容，进行深入的技术面试。

面试风格：
1. 针对简历中的具体项目和技术栈提问，不要泛泛而谈
2. 追问细节，比如"你说用了Redis，那缓存穿透怎么处理的？"
3. 适当施压，但保持专业和尊重
4. 如果候选人回答模糊，继续追问直到得到具体答案
5. 偶尔给予肯定，但不要轻易放过

简历内容：
{context}

对话历史：
{chat_history}

候选人回答：{question}

请根据简历内容和对话历史，继续面试。如果是面试刚开始，请先简单介绍自己，然后根据简历提出第一个问题。""",
        
        'partner': """你是一位充满激情和共情能力的伙伴型面试官。你的任务是根据候选人的简历内容，进行有温度、有参与感的技术面试。

面试风格：
1. 以平等的伙伴姿态交流，营造轻松但专业的氛围
2. 对候选人的项目经历表现出真诚的兴趣和好奇，比如"哇，这个项目听起来很有挑战性！当时是怎么想到这个解决方案的？"
3. 善于捕捉候选人话语中的亮点，给予及时的肯定和鼓励
4. 用共情的方式理解候选人遇到的困难，比如"我能理解这种情况，当时压力一定很大吧？"
5. 通过分享自己的经验或见解，引发候选人更深入的思考和分享
6. 保持热情和参与感，让候选人感受到你真的在倾听和理解

简历内容：
{context}

对话历史：
{chat_history}

候选人回答：{question}

请根据简历内容和对话历史，继续面试。如果是面试刚开始，请先热情地介绍自己，然后以伙伴的姿态开始对话。""",
        
        'guide': """你是一位冷静理智、内心宽和的引导型面试官。你的任务是根据候选人的简历内容，通过巧妙的引导帮助候选人展现最佳状态。

面试风格：
1. 保持冷静、理智、审慎的专业态度，给人以可靠和值得信赖的感觉
2. 善于通过循序渐进的问题引导候选人深入思考，比如"我们先从整体架构聊起，然后再深入细节，你觉得如何？"
3. 当候选人回答不够清晰时，不是直接质疑，而是提供思路提示，比如"你可以从技术选型、实现难点、优化方案这几个角度来谈谈"
4. 用开放式问题激发候选人的思考，给予充分的表达空间
5. 内心宽和，对候选人的不足保持理解和包容，但会温和地指出改进方向
6. 善于总结和提炼候选人的观点，帮助其理清思路

简历内容：
{context}

对话历史：
{chat_history}

候选人回答：{question}

请根据简历内容和对话历史，继续面试。如果是面试刚开始，请先沉稳地介绍自己，然后以引导的方式开启对话。"""
    }
    
    return styles.get(style, styles['critical'])


def create_interview_chain(chunks, llm, config):
    """创建面试问答链"""
    print("正在初始化面试官大脑...")
    
    # 获取 Embedding 配置
    embedding_type = config.get('embedding', 'type', fallback='local')
    
    if embedding_type == 'deepseek':
        # 使用 DeepSeek 兼容的 Embedding（实际调用 OpenAI 兼容接口）
        from langchain_openai import OpenAIEmbeddings
        print("正在连接 DeepSeek Embedding API...")
        embeddings = OpenAIEmbeddings(
            model=config.get('embedding', 'model', fallback='text-embedding-3-small'),
            openai_api_key=config.get('deepseek', 'api_key'),
            openai_api_base=config.get('deepseek', 'base_url')
        )
    else:
        # 使用本地 Embedding 模型（免费，无需 API）
        print("正在加载本地 Embedding 模型（首次需下载约400MB）...")
        embeddings = HuggingFaceEmbeddings(
            model_name=config.get('embedding', 'model', fallback='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'),
            model_kwargs={'device': 'cpu'}
        )
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="resume"
    )
    
    # 对话记忆
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # 获取面试官风格
    interview_style = config.get('DEFAULT', 'interview_style', fallback='critical')
    style_names = {
        'critical': '刁钻型',
        'partner': '伙伴型',
        'guide': '引导型'
    }
    print(f"面试官风格：{style_names.get(interview_style, '刁钻型')}")
    
    # 获取对应风格的面试官系统提示
    system_template = get_interview_style_prompt(interview_style)

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        return_source_documents=False,
        combine_docs_chain_kwargs={
            "prompt": PromptTemplate(
                template=system_template,
                input_variables=["context", "chat_history", "question"]
            )
        }
    )
    
    print("面试官已就绪！\n")
    return chain


def run_interview(chain):
    """运行面试对话"""
    print("-" * 50)
    print("提示：输入 'quit' 或 'exit' 结束面试")
    print("-" * 50 + "\n")
    
    response = chain.invoke({"question": "请开始面试"})
    print(f"[面试官]：{response['answer']}\n")
    
    while True:
        user_input = input("[你]：").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ["quit", "exit", "退出", "结束"]:
            print("\n[面试官]：好的，今天的面试就到这里。感谢你的时间，我们会尽快给你反馈。再见！")
            break
        
        try:
            response = chain.invoke({"question": user_input})
            print(f"\n[面试官]：{response['answer']}\n")
        except Exception as e:
            print(f"\n出错了：{e}\n")


def main():
    """主函数"""
    # 加载配置
    config = load_config()
    if not config:
        return
    
    # 获取面试官风格
    interview_style = config.get('DEFAULT', 'interview_style', fallback='critical')
    
    # 打印横幅
    print_banner(interview_style)
    
    # 获取简历路径
    resume_path = get_resume_path()
    if not resume_path:
        return
    
    # 加载简历
    chunks = load_resume(resume_path)
    if not chunks:
        return
    
    # 创建 LLM
    llm = get_llm(config)
    if not llm:
        return
    
    # 创建面试链
    try:
        chain = create_interview_chain(chunks, llm, config)
    except Exception as e:
        print(f"初始化失败：{e}")
        return
    
    # 开始面试
    run_interview(chain)
    
    print("\n" + "=" * 50)
    print("   感谢使用简历拷打面试官！祝你面试顺利！")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
