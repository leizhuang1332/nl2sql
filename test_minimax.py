"""
MiniMax M2.5 API 测试文件

基于 Anthropic API 兼容接口: https://platform.minimaxi.com/docs/api-reference/text-anthropic-api

支持模型:
- MiniMax-M2.5 (上下文窗口: 204,800, 约 60 TPS)
- MiniMax-M2.5-highspeed (约 100 TPS)
- MiniMax-M2.1
- MiniMax-M2.1-highspeed
- MiniMax-M2
"""

import os
from dotenv import load_dotenv

import anthropic

# 加载 .env 文件
load_dotenv()

# ============================================================
# 配置区域 - 从 .env 文件加载
# ============================================================
# 在 .env 文件中设置以下变量:
# MINIMAX_API_KEY=your_api_key_here
# MINIMAX_BASE_URL=https://api.minimaxi.com/anthropic (可选)
#
# 或在 .env.local 中覆盖默认配置
API_KEY = os.getenv("MINIMAX_API_KEY", "your_api_key_here")
BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic")

# 模型选择
MODEL = "MiniMax-M2.5"  # 可选: MiniMax-M2.5, MiniMax-M2.5-highspeed, MiniMax-M2.1, MiniMax-M2


# ============================================================
# 客户端初始化
# ============================================================

def get_client():
    """获取 Anthropic 客户端实例"""
    return anthropic.Anthropic(
        api_key=API_KEY,
        base_url=BASE_URL,
    )


# ============================================================
# 输入规范
# ============================================================

"""
【输入参数说明】

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| model | 是 | string | 模型名称: MiniMax-M2.5, MiniMax-M2.5-highspeed, MiniMax-M2.1 等 |
| messages | 是 | array | 消息列表 |
| max_tokens | 是 | int | 最大生成 token 数 |
| system | 否 | string | 系统提示词 |
| temperature | 否 | float | 随机性控制, 范围 (0.0, 1.0], 推荐 1.0 |
| top_p | 否 | float | 核采样参数 |
| stream | 否 | bool | 是否使用流式响应, 默认 false |
| tools | 否 | array | 工具定义列表 |
| tool_choice | 否 | object | 工具选择策略 |
| metadata | 否 | object | 元信息 |

【messages 消息格式】

每条消息包含:
- role: "user" | "assistant" | "system"
- content: 内容块列表

内容块类型:
- {"type": "text", "text": "文本内容"}
- {"type": "tool_use", "id": "xxx", "name": "tool_name", "input": {...}}
- {"type": "tool_result", "tool_use_id": "xxx", "content": "结果"}
- {"type": "thinking", "thinking": "推理内容"}  # 仅输出

【注意】
- temperature 推荐使用 1.0, 超出范围会返回错误
- 不支持图像和文档输入 (type="image", type="document")
- 多轮对话必须保留完整的 assistant 消息内容 (包含 thinking/text/tool_use)
"""


# ============================================================
# 输出规范
# ============================================================

"""
【输出格式】

响应是一个 Message 对象, 包含:
- id: 消息 ID
- type: "message"
- role: "assistant"
- content: 内容块列表
- model: 使用的模型
- stop_reason: 结束原因: "end_turn" | "max_tokens" | "stop_sequence"
- usage: {"input_tokens": x, "output_tokens": y}

【内容块类型 (content block)】

1. Text Block (type="text")
   {"type": "text", "text": "文本内容"}

2. Thinking Block (type="thinking")
   {"type": "thinking", "thinking": "推理过程内容"}

3. Tool Use Block (type="tool_use")
   {
     "type": "tool_use",
     "id": "toolu_xxx",
     "name": "tool_name",
     "input": {"param": "value"}
   }

【流式响应 chunk 类型】

- content_block_start: 内容块开始
- content_block_delta: 内容块增量更新
  - delta.type = "thinking_delta": 推理过程流
  - delta.type = "text_delta": 文本内容流
- content_block_stop: 内容块结束
- message_start / message_delta / message_stop: 消息级别
"""


# ============================================================
# 示例 1: 基础对话 (非流式)
# ============================================================

def basic_chat():
    """基础对话示例"""
    client = get_client()
    
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="你是一个有帮助的AI助手。",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "你好，请介绍一下你自己"}
                ]
            }
        ]
    )
    
    # 处理响应
    print("=" * 60)
    print("【响应内容】")
    print("=" * 60)
    
    for block in response.content:
        if block.type == "thinking":
            print(f"【思考过程】\n{block.thinking}\n")
        elif block.type == "text":
            print(f"【回复文本】\n{block.text}\n")
        elif block.type == "tool_use":
            print(f"【工具调用】{block.name}: {block.input}")
    
    print(f"【使用统计】输入: {response.usage.input_tokens} tokens, 输出: {response.usage.output_tokens} tokens")
    print(f"【结束原因】{response.stop_reason}")
    
    return response


# ============================================================
# 示例 2: 流式响应
# ============================================================

def stream_chat():
    """流式响应示例"""
    client = get_client()
    
    stream = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="你是一个有帮助的AI助手。",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "用三句话介绍Python语言的特点"}
                ]
            }
        ],
        stream=True,
    )
    
    print("=" * 60)
    print("【流式响应】")
    print("=" * 60)
    
    thinking_buffer = ""
    text_buffer = ""
    
    for chunk in stream:
        if chunk.type == "content_block_delta":
            if hasattr(chunk, "delta") and chunk.delta:
                if chunk.delta.type == "thinking_delta":
                    # 推理过程流式输出
                    new_thinking = chunk.delta.thinking
                    if new_thinking:
                        print(new_thinking, end="", flush=True)
                        thinking_buffer += new_thinking
                elif chunk.delta.type == "text_delta":
                    # 文本内容流式输出
                    new_text = chunk.delta.text
                    if new_text:
                        print(new_text, end="", flush=True)
                        text_buffer += new_text
    
    print("\n")
    return thinking_buffer, text_buffer


# ============================================================
# 示例 3: 带工具调用的对话
# ============================================================

def tool_chat():
    """工具调用示例"""
    client = get_client()
    
    # 定义工具
    tools = [
        {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如北京、上海、东京"
                    }
                },
                "required": ["city"]
            }
        }
    ]
    
    # 第一轮: 用户提问，模型可能调用工具
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="你是一个有帮助的助手，可以使用工具来回答问题。",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "北京今天的天气怎么样？"}
                ]
            }
        ],
        tools=tools,
    )
    
    print("=" * 60)
    print("【第一轮响应】")
    print("=" * 60)
    
    assistant_message_content = []
    
    for block in response.content:
        assistant_message_content.append(block)
        if block.type == "thinking":
            print(f"【思考】{block.thinking}")
        elif block.type == "text":
            print(f"【文本】{block.text}")
        elif block.type == "tool_use":
            print(f"【工具调用】{block.name}, 参数: {block.input}")
    
    # 检查是否需要调用工具
    tool_calls = [block for block in response.content if block.type == "tool_use"]
    
    if tool_calls:
        # 模拟工具执行
        tool_results = []
        for tool_call in tool_calls:
            if tool_call.name == "get_weather":
                # 实际应该调用天气API，这里模拟返回
                result_content = f"北京今天天气: 晴, 温度 15-25°C"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result_content
                })
        
        # 第二轮: 将工具结果返回给模型
        messages = [
            {"role": "user", "content": [{"type": "text", "text": "北京今天的天气怎么样？"}]}
        ]
        # 添加助手消息（包含完整的 content）
        messages.append({
            "role": "assistant",
            "content": assistant_message_content
        })
        # 添加工具结果
        messages.append({
            "role": "user",
            "content": tool_results
        })
        
        response2 = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=messages,
            tools=tools,
        )
        
        print("\n" + "=" * 60)
        print("【第二轮响应】")
        print("=" * 60)
        
        for block in response2.content:
            if block.type == "thinking":
                print(f"【思考】{block.thinking}")
            elif block.type == "text":
                print(f"【文本】{block.text}")


# ============================================================
# 示例 4: 多轮对话
# ============================================================

def multi_turn_chat():
    """多轮对话示例 - 必须保留完整的 assistant 消息"""
    client = get_client()
    
    # 对话历史
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "什么是机器学习？"}]
        }
    ]
    
    # 第一轮
    response1 = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=messages,
    )
    
    print("=" * 60)
    print("【第一轮】什么是机器学习？")
    print("=" * 60)
    
    assistant_content = []
    for block in response1.content:
        assistant_content.append(block)
        if block.type == "text":
            print(block.text[:200] + "..." if len(block.text) > 200 else block.text)
    
    # 【重要】将完整的 assistant 消息添加到历史
    messages.append({
        "role": "assistant",
        "content": assistant_content  # 必须包含完整的 content 列表
    })
    
    # 第二轮追问
    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": "它和深度学习有什么区别？"}]
    })
    
    response2 = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=messages,
    )
    
    print("\n" + "=" * 60)
    print("【第二轮】和深度学习的区别？")
    print("=" * 60)
    
    for block in response2.content:
        if block.type == "text":
            print(block.text)


# ============================================================
# 主函数
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MiniMax M2.5 API 测试")
    print("=" * 60)
    print(f"模型: {MODEL}")
    print(f"API地址: {BASE_URL}")
    print(f"API Key: {'✓ 已设置' if API_KEY and API_KEY != 'your_api_key_here' else '✗ 未设置'}")
    print()
    
    # 检查 API Key
    if not API_KEY or API_KEY == "your_api_key_here":
        print("⚠️  请先在 .env 文件中设置 MINIMAX_API_KEY!")
        print("   参考 .env.example 添加配置")
        exit(1)
    
    # 选择要运行的示例
    print("请选择要运行的示例:")
    print("1. 基础对话 (非流式)")
    print("2. 流式响应")
    print("3. 工具调用")
    print("4. 多轮对话")
    print("5. 全部运行")
    print()
    
    choice = input("请输入选项 (1-5): ").strip()
    
    if choice == "1":
        basic_chat()
    elif choice == "2":
        stream_chat()
    elif choice == "3":
        tool_chat()
    elif choice == "4":
        multi_turn_chat()
    elif choice == "5":
        print("\n>>> 运行示例1: 基础对话 <<<")
        basic_chat()
        print("\n>>> 运行示例2: 流式响应 <<<")
        stream_chat()
        print("\n>>> 运行示例3: 工具调用 <<<")
        tool_chat()
        print("\n>>> 运行示例4: 多轮对话 <<<")
        multi_turn_chat()
    else:
        print("无效选项")
