创建对话请求（OpenAI）
Creates a model response for the given chat conversation.

POST
/
chat
/
completions

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Body
application/json
LLM
VLM
​
model
enum<string>required
Corresponding Model Name. To better enhance service quality, we will make periodic changes to the models provided by this service, including but not limited to model on/offlining and adjustments to model service capabilities. We will notify you of such changes through appropriate means such as announcements or message pushes where feasible.

Available options: Pro/moonshotai/Kimi-K2-Thinking, moonshotai/Kimi-K2-Thinking, Kwaipilot/KAT-Dev, MiniMaxAI/MiniMax-M2, deepseek-ai/DeepSeek-V3.2-Exp, Pro/deepseek-ai/DeepSeek-V3.2-Exp, inclusionAI/Ling-1T, zai-org/GLM-4.6, moonshotai/Kimi-K2-Instruct-0905, Pro/deepseek-ai/DeepSeek-V3.1-Terminus, deepseek-ai/DeepSeek-V3.1-Terminus, Qwen/Qwen3-Next-80B-A3B-Instruct, Qwen/Qwen3-Next-80B-A3B-Thinking, inclusionAI/Ring-flash-2.0, inclusionAI/Ling-flash-2.0, inclusionAI/Ling-mini-2.0, ByteDance-Seed/Seed-OSS-36B-Instruct, stepfun-ai/step3, Qwen/Qwen3-Coder-30B-A3B-Instruct, Qwen/Qwen3-Coder-480B-A35B-Instruct, Qwen/Qwen3-30B-A3B-Thinking-2507, Qwen/Qwen3-30B-A3B-Instruct-2507, Qwen/Qwen3-235B-A22B-Thinking-2507, Qwen/Qwen3-235B-A22B-Instruct-2507, zai-org/GLM-4.5-Air, zai-org/GLM-4.5, baidu/ERNIE-4.5-300B-A47B, ascend-tribe/pangu-pro-moe, tencent/Hunyuan-A13B-Instruct, MiniMaxAI/MiniMax-M1-80k, Tongyi-Zhiwen/QwenLong-L1-32B, Qwen/Qwen3-30B-A3B, Qwen/Qwen3-32B, Qwen/Qwen3-14B, Qwen/Qwen3-8B, Qwen/Qwen3-235B-A22B, THUDM/GLM-Z1-32B-0414, THUDM/GLM-4-32B-0414, THUDM/GLM-Z1-Rumination-32B-0414, THUDM/GLM-4-9B-0414, THUDM/GLM-4-9B-0414, Qwen/QwQ-32B, Pro/deepseek-ai/DeepSeek-R1, Pro/deepseek-ai/DeepSeek-V3, deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-V3, deepseek-ai/DeepSeek-R1-0528-Qwen3-8B, deepseek-ai/DeepSeek-R1-Distill-Qwen-32B, deepseek-ai/DeepSeek-R1-Distill-Qwen-14B, deepseek-ai/DeepSeek-R1-Distill-Qwen-7B, Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B, deepseek-ai/DeepSeek-V2.5, Qwen/Qwen2.5-72B-Instruct-128K, Qwen/Qwen2.5-72B-Instruct, Qwen/Qwen2.5-32B-Instruct, Qwen/Qwen2.5-14B-Instruct, Qwen/Qwen2.5-7B-Instruct, Qwen/Qwen2.5-Coder-32B-Instruct, Qwen/Qwen2.5-Coder-7B-Instruct, Qwen/Qwen2-7B-Instruct, THUDM/glm-4-9b-chat, internlm/internlm2_5-7b-chat, Pro/Qwen/Qwen2.5-7B-Instruct, Pro/Qwen/Qwen2-7B-Instruct, Pro/THUDM/glm-4-9b-chat 
Example:
"Qwen/QwQ-32B"

​
messages
object[]required
A list of messages comprising the conversation so far.

Required array length: 1 - 10 elements
Show child attributes

​
stream
boolean
If set, tokens are returned as Server-Sent Events as they are made available. Stream terminates with data: [DONE]

Example:
false

​
max_tokens
integer
The maximum number of tokens to generate. Ensure that input tokens + max_tokens do not exceed the model’s context window. As some services are still being updated, avoid setting max_tokens to the window’s upper bound; reserve ~10k tokens as buffer for input and system overhead. See Models(https://cloud.siliconflow.cn/models) for details.

Example:
4096

​
enable_thinking
boolean
Switches between thinking and non-thinking modes. Default is True. This field supports the following models:

- zai-org/GLM-4.6
- Qwen/Qwen3-8B
- Qwen/Qwen3-14B
- Qwen/Qwen3-32B
- wen/Qwen3-30B-A3B
- Qwen/Qwen3-235B-A22B
- tencent/Hunyuan-A13B-Instruct
- zai-org/GLM-4.5V
- deepseek-ai/DeepSeek-V3.1-Terminus
- Pro/deepseek-ai/DeepSeek-V3.1-Terminus
If you want to use the function call feature for deepseek-ai/DeepSeek-V3.1 or Pro/deepseek-ai/DeepSeek-V3.1 , you need to set enable_thinking to false.

Example:
false

​
thinking_budget
integerdefault:4096
Maximum number of tokens for chain-of-thought output. This field applies to all Reasoning models.

Required range: 128 <= x <= 32768
Example:
4096

​
min_p
number<float>
Dynamic filtering threshold that adapts based on token probabilities.This field only applies to Qwen3.

Required range: 0 <= x <= 1
Example:
0.05

​
stop

string
Up to 4 sequences where the API will stop generating further tokens. The returned text will not contain the stop sequence.

Example:
null

​
temperature
number<float>
Determines the degree of randomness in the response.

Example:
0.7

​
top_p
number<float>default:0.7
The top_p (nucleus) parameter is used to dynamically adjust the number of choices for each predicted token based on the cumulative probabilities.

Example:
0.7

​
top_k
number<float>
Example:
50

​
frequency_penalty
number<float>
Example:
0.5

​
n
integer
Number of generations to return

Example:
1

​
response_format
object
An object specifying the format that the model must output.

Show child attributes

​
tools
object[]
A list of tools the model may call. Currently, only functions are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for. A max of 128 functions are supported.

Show child attributes

Response

200

application/json
200

​
id
string
​
choices
object[]
Show child attributes

​
usage
object
Show child attributes

​
created
integer
​
model
string
​
object
enum<string>
Available options: chat.completion 


curl --request POST \
  --url https://api.siliconflow.cn/v1/chat/completions \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "Qwen/Qwen2.5-VL-72B-Instruct",
  "messages": [
    {
      "role": "user",
      "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
    }
  ],
  "stream": false,
  "max_tokens": 4096,
  "enable_thinking": false,
  "thinking_budget": 4096,
  "min_p": 0.05,
  "stop": [],
  "temperature": 0.7,
  "top_p": 0.7,
  "top_k": 50,
  "frequency_penalty": 0.5,
  "n": 1,
  "response_format": {
    "type": "text"
  },
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "<string>",
        "description": "<string>",
        "parameters": {},
        "strict": false
      }
    }
  ]
}
'



创建对话请求（Anthropic）
Creates a model response for the given chat conversation.

POST
/
messages

Try it
Authorizations

bearerAuth
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Body
application/json
​
model
enum<string>required
Corresponding Model Name. To better enhance service quality, we will make periodic changes to the models provided by this service, including but not limited to model on/offlining and adjustments to model service capabilities. We will notify you of such changes through appropriate means such as announcements or message pushes where feasible.

Available options: Pro/deepseek-ai/DeepSeek-V3.1-Terminus, deepseek-ai/DeepSeek-V3.1, Pro/deepseek-ai/DeepSeek-V3.1, deepseek-ai/DeepSeek-V3, Pro/deepseek-ai/DeepSeek-V3, moonshotai/Kimi-K2-Instruct-0905, Pro/moonshotai/Kimi-K2-Instruct-0905, moonshotai/Kimi-Dev-72B, baidu/ERNIE-4.5-300B-A47B 
Example:
"deepseek-ai/DeepSeek-V3.1"

​
messages
object[]required
A list of messages comprising the conversation so far.

Required array length: 1 - 10 elements
Show child attributes

​
max_tokens
integerrequired
The maximum number of tokens to generate before stopping.

Note that our models may stop before reaching this maximum. This parameter only specifies the absolute maximum number of tokens to generate.

Different models have different maximum values for this parameter. See models for details.

Example:
8192

​
system

string
System prompt.

A system prompt is a way of providing context and instructions to llm, such as specifying a particular goal or role.

​
stop_sequences
string[]
Custom text sequences that will cause the model to stop generating.

Our models will normally stop when they have naturally completed their turn, which will result in a response stop_reason of "end_turn".

If you want the model to stop generating when it encounters custom strings of text, you can use the stop_sequences parameter. If the model encounters one of the custom sequences, the response stop_reason value will be "stop_sequence" and the response stop_sequence value will contain the matched stop sequence.

​
stream
boolean
If set, tokens are returned as Server-Sent Events as they are made available. Stream terminates with data: [DONE]

Example:
true

​
temperature
number<float>
Determines the degree of randomness in the response.

Required range: 0 <= x <= 2
Example:
0.7

​
top_p
number<float>
The top_p (nucleus) parameter is used to dynamically adjust the number of choices for each predicted token based on the cumulative probabilities.

Required range: 0.1 <= x <= 1
Example:
0.7

​
top_k
number<float>
Required range: 0 <= x <= 50
Example:
50

​
tools
object[]
Each tool definition includes:

name: Name of the tool.

description: Optional, but strongly-recommended
description of the tool.

input_schema: JSON
schema for the
tool input shape that the model will produce in
tool_use output content blocks.

Show child attributes

​
tool_choice
Auto · object
How the model should use the provided tools. The model can use a specific tool, any available tool, decide by itself, or not use tools at all.

Auto
Tool
None
Show child attributes

Response

200

application/json
200

​
id
string
​
type
enum<string>default:message
Object type.

For Messages, this is always "message".

Available options: message 
​
role
enum<string>default:assistant
Conversational role of the generated message.

This will always be "assistant".

Available options: assistant 
​
content
Tool use · object[]
Content generated by the model.

This is an array of content blocks, each of which has a type that determines its shape.

Example:

[{"type": "text", "text": "Hi"}]
If the request input messages ended with an assistant turn, then the response content will continue directly from that last turn. You can use this to constrain the model's output.

For example, if the input messages were:

[
  {"role": "user", "content": "What's the Greek name for Sun? (A) Sol (B) Helios (C) Sun"},
  {"role": "assistant", "content": "The best answer is ("}
]
Then the response content might be:

[{"type": "text", "text": "B)"}]
Show child attributes

​
model
string
The model that handled the request.

​
stop_reason
enum<string>
The reason that we stopped.

This may be one the following values:

"end_turn": the model reached a natural stopping point or one of your provided custom stop_sequences was generated
"max_tokens": we exceeded the requested max_tokens or the model's maximum
"tool_use": the model invoked one or more tools
"refusal": when streaming classifiers intervene to handle potential policy violations
In non-streaming mode this value is always non-null. In streaming mode, it is null in the message_start event and non-null otherwise.

Available options: end_turn, max_tokens, tool_use, refusal 
​
stop_sequence
string
Which custom stop sequence was generated, if any.

This value will be a non-null string if one of your custom stop sequences was generated.

​
usage
Usage · object
Billing and rate-limit usage.

Show child attributes

Example:
{
  "input_tokens": 2095,
  "output_tokens": 503
}


curl --request POST \
  --url https://api.siliconflow.cn/v1/messages \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "deepseek-ai/DeepSeek-V3.1",
  "messages": [
    {
      "role": "user",
      "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
    }
  ],
  "max_tokens": 8192,
  "system": "<string>",
  "stop_sequences": [
    "<string>"
  ],
  "stream": true,
  "temperature": 0.7,
  "top_p": 0.7,
  "top_k": 50,
  "tools": [
    {
      "name": "<string>",
      "input_schema": {
        "type": "object",
        "properties": {},
        "required": [
          "<string>"
        ]
      }
    }
  ],
  "tool_choice": {
    "type": "auto",
    "disable_parallel_tool_use": true
  }
}
'



批量处理
上传文件
Upload files

POST
/
files

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Body
multipart/form-data
​
purpose
enum<string>required
Available options: batch 
Example:
"batch"

​
file
filerequired
File to upload

Example:
"/path/to/abc.jsonl"

Response

200

application/json
Successful response

​
code
integer
Example:
20000

​
message
string
Example:
"Ok"

​
status
boolean
Example:
true

​
data
object
Show child attributes


curl --request POST \
  --url https://api.siliconflow.cn/v1/files \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: multipart/form-data' \
  --form purpose=batch \
  --form file='@example-file'



  批量处理
创建batch任务
Upload files

POST
/
batches

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Body
application/json
​
input_file_id
stringrequired
The ID of an uploaded file that contains requests for the new batch.

Example:
"file-jkvytbjtow"

​
endpoint
stringrequired
The endpoint to be used for all requests in the batch. Currently /v1/chat/completions is supported.

Example:
"/v1/chat/completions"

​
completion_window
stringrequired
The time frame within which the batch should be processed. The maximum value is 24 hours, and the minimum value is 336 hours.

Example:
"24h"

​
metadata
object
Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard.<\br>Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.

Show child attributes

​
replace
object
Show child attributes

Response

200

application/json
Successful response

​
id
string
Example:
"batch_rdyqgrcgjg"

​
object
string
Example:
"batch"

​
endpoint
string
Example:
"/v1/chat/completions"

​
errors
string[]
Example:
null

​
input_file_id
string
Example:
"file-jkvytbjtow"

​
completion_window
string
Example:
"24h"

​
status
string
Example:
"in_queue"

​
output_file_id
string
Example:
null

​
error_file_id
string
Example:
null

​
created_at
integer
Example:
1741685413

​
in_progress_at
integer
Example:
null

​
expires_at
integer
Example:
1741771813

​
finalizing_at
integer
Example:
null

​
completed_at
integer
Example:
null

​
failed_at
integer
Example:
null

​
expired_at
integer
Example:
null

​
cancelling_at
integer
Example:
null

​
cancelled_at
integer
Example:
null

​
request_counts
object
Example:
null

​
metadata
object
Show child attributes


curl --request POST \
  --url https://api.siliconflow.cn/v1/batches \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "input_file_id": "file-jkvytbjtow",
  "endpoint": "/v1/chat/completions",
  "completion_window": "24h",
  "metadata": {
    "description": "nightly eval job"
  },
  "replace": {
    "model": "deepseek-ai/DeepSeek-V3"
  }
}
'



批量处理
获取batch任务详情
Retrieves a batch.

GET
/
batches
/
{batch_id}

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Path Parameters
​
batch_id
stringrequired
The ID of the batch to retrieve.

Response

200

application/json
The Batch object matching the specified ID.

​
id
string
Example:
"batch_rdyqgrcgjg"

​
object
string
Example:
"batch"

​
endpoint
string
Example:
"/v1/chat/completions"

​
errors
string[]
Example:
[]
​
input_file_id
string
Example:
"file-jkvytbjtow"

​
completion_window
string
Example:
"24h"

​
status
string
Example:
"in_queue"

​
output_file_id
string
Example:
null

​
error_file_id
string
Example:
null

​
created_at
integer
Example:
1741685413

​
in_progress_at
integer
Example:
null

​
expires_at
integer
Example:
1741771813

​
finalizing_at
integer
Example:
null

​
completed_at
integer
Example:
null

​
failed_at
integer
Example:
null

​
expired_at
integer
Example:
null

​
cancelling_at
integer
Example:
null

​
cancelled_at
integer
Example:
null

​
request_counts
object
Example:
{}
​
metadata
object
Show child attributes



curl --request GET \
  --url https://api.siliconflow.cn/v1/batches/{batch_id} \
  --header 'Authorization: Bearer <token>'


  批量处理
获取batch任务列表
List your organization’s batches.

GET
/
batches

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Response

200

application/json
Successful response

​
object
string
Example:
"list"

​
data
object[]
Show child attributes

​
first_id
string
Example:
"first_batch_id"

​
last_id
string
Example:
"last_batch_id"

​
has_more
boolean
Example:
false


curl --request GET \
  --url https://api.siliconflow.cn/v1/batches \
  --header 'Authorization: Bearer <token>'





  批量处理
取消batch任务
This endpoint cancels a batch identified by its unique ID.

POST
/
batches
/
{batch_id}
/
cancel

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Path Parameters
​
batchId
stringrequired
Unique identifier of the batch to cancel

Response

200

application/json
Successful response

​
id
string
Example:
"batch_rdyqgrcgjg"

​
object
string
Example:
"batch"

​
endpoint
string
Example:
"/v1/chat/completions"

​
errors
string[]
Example:
null

​
input_file_id
string
Example:
"file-jkvytbjtow"

​
completion_window
string
Example:
"24h"

​
status
string
Example:
"in_queue"

​
output_file_id
string
Example:
null

​
error_file_id
string
Example:
null

​
created_at
integer
Example:
1741685413

​
in_progress_at
integer
Example:
null

​
expires_at
integer
Example:
1741771813

​
finalizing_at
integer
Example:
null

​
completed_at
integer
Example:
null

​
failed_at
integer
Example:
null

​
expired_at
integer
Example:
null

​
cancelling_at
integer
Example:
null

​
cancelled_at
integer
Example:
null

​
request_counts
object
Example:
null

​
metadata
object
Hide child attributes

​
metadata.description
string
Example:
"nightly eval job"



curl --request POST \
  --url https://api.siliconflow.cn/v1/batches/{batch_id}/cancel \
  --header 'Authorization: Bearer <token>'






平台系列
获取用户模型列表
Retrieve models information.

GET
/
models

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Query Parameters
​
type
enum<string>
The type of models

Available options: text, image, audio, video 
​
sub_type
enum<string>
The sub type of models. You can use it to filter models individually without setting type.

Available options: chat, embedding, reranker, text-to-image, image-to-image, speech-to-text, text-to-video 
Response

200

application/json
Successful response

​
object
string
Example:
"list"

​
data
object[]
Hide child attributes

​
data.id
string
Example:
"stabilityai/stable-diffusion-xl-base-1.0"

​
data.object
string
Example:
"model"

​
data.created
integer
Example:
0

​
data.owned_by
string
Example:
""


curl --request GET \
  --url https://api.siliconflow.cn/v1/models \
  --header 'Authorization: Bearer <token>'





平台系列
获取用户账户信息
Get user information including balance and status

GET
/
user
/
info

Try it
Authorizations
​
Authorization
stringheaderrequired
Use the following format for authentication: Bearer

Response

200

application/json
Successful response

​
code
integer
Example:
20000

​
message
string
Example:
"OK"

​
status
boolean
Example:
true

​
data
object
Hide child attributes

​
data.id
string
Example:
"userid"

​
data.name
string
This field will no longer be returned after June 11th, and a fixed empty string will be output instead.

Example:
"username"

​
data.image
string
This field will no longer be returned after June 11th, and a fixed empty string will be output instead.

Example:
"user_avatar_image_url"

​
data.email
string
This field will no longer be returned after June 11th, and a fixed empty string will be output instead.

Example:
"user_email_address"

​
data.isAdmin
boolean
Example:
false

​
data.balance
string
Example:
"0.88"

​
data.status
string
Example:
"normal"

​
data.introduction
string
Example:
""

​
data.role
string
Example:
""

​
data.chargeBalance
string
Example:
"88.00"

​
data.totalBalance
string
Example:
"88.88"

curl --request GET \
  --url https://api.siliconflow.cn/v1/user/info \
  --header 'Authorization: Bearer <token>'


  Get user information

import requests

url = "https://api.siliconflow.cn/v1/user/info"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.text)




语言模型
语言模型（LLM）使用说明手册
​
1. 模型核心能力
​
1.1 基础功能
文本生成：根据上下文生成连贯的自然语言文本，支持多种文体和风格。
语义理解：深入解析用户意图，支持多轮对话管理，确保对话的连贯性和准确性。
知识问答：覆盖广泛的知识领域，包括科学、技术、文化、历史等，提供准确的知识解答。
代码辅助：支持多种主流编程语言（如Python、Java、C++等）的代码生成、解释和调试。
​
1.2 进阶能力
长文本处理：支持4k至64k tokens的上下文窗口，适用于长篇文档生成和复杂对话场景。
指令跟随：精确理解复杂任务指令，如“用Markdown表格对比A/B方案”。
风格控制：通过系统提示词调整输出风格，支持学术、口语、诗歌等多种风格。
多模态支持：除了文本生成，还支持图像描述、语音转文字等多模态任务。
​
2. 接口调用规范
​
2.1 基础请求结构
您可以通过 openai sdk进行端到端接口请求
生成对话（点击查看详情）

    from openai import OpenAI  
    client = OpenAI(api_key="YOUR_KEY", base_url="https://api.siliconflow.cn/v1")  

    response = client.chat.completions.create(  
        model="deepseek-ai/DeepSeek-V3",  
        messages=[  
            {"role": "system", "content": "You are a helpful assistant."},  
            {"role": "user", "content": "Write a haiku about recursion in programming."}  
        ],  
        temperature=0.7,  
        max_tokens=1024,
        stream=True
    )  
    # 逐步接收并处理响应
    for chunk in response:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
        if chunk.choices[0].delta.reasoning_content:
            print(chunk.choices[0].delta.reasoning_content, end="", flush=True)

分析一幅图像（点击查看详情）

生成json数据（点击查看详情）

​
2.2 消息体结构说明
消息类型	功能描述	示例内容
system	模型指令，设定AI角色，描述模型应一般如何行为和响应	例如：“你是有10年经验的儿科医生”
user	用户输入，将最终用户的消息传递给模型	例如：“幼儿持续低烧应如何处理？“
assistant	模型生成的历史回复，为模型提供示例，说明它应该如何回应当前请求	例如：“建议先测量体温…”
你想让模型遵循分层指令时，消息角色可以帮助你获得更好的输出。但它们并不是确定性的，所以使用的最佳方式是尝试不同的方法，看看哪种方法能给你带来好的结果。
​
3. 模型系列选型指南
可以进入模型广场，根据左侧的筛选功能，筛选支持不同功能的语言模型，根据模型的介绍，了解模型具体的价格、模型参数大小、模型上下文支持的最大长度及模型价格等内容。
支持在playground进行体验（playground只进行模型体验，暂时没有历史记录功能，如果您想要保存历史的回话记录内容，请自己保存会话内容），想要了解更多使用方式，可以参考API文档

​
4. 核心参数详解
​
4.1 创造性控制
# 温度参数（0.0~2.0）   
temperature=0.5  # 平衡创造性与可靠性  

# 核采样（top_p）   
top_p=0.9  # 仅考虑概率累积90%的词集  
​
4.2 输出限制
max_tokens=1000  # 单词请求最大生成长度  
stop=["\n##", "<|end|>"]  # 终止序列，在返回中遇到数组中对应的字符串，就会停止输出 
frequency_penalty=0.5  # 抑制重复用词（-2.0~2.0）  
stream=true # 控制输出是否是流式输出，对于一些输出内容比较多的模型，建议设置为流式，防止输出过长，导致输出超时
​
4.3 语言模型场景问题汇总
1. 模型输出乱码
目前看到部分模型在不设置参数的情况下，容易出现乱码，遇到上述情况，可以尝试设置temperature，top_k，top_p，frequency_penalty这些参数。
对应的 payload 修改为如下形式，不同语言酌情调整
    payload = {
        "model": "Qwen/Qwen2.5-Math-72B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": "1+1=?",
            }
        ],
        "max_tokens": 200,  # 按需添加
        "temperature": 0.7, # 按需添加
        "top_k": 50,        # 按需添加
        "top_p": 0.7,       # 按需添加
        "frequency_penalty": 0 # 按需添加
    }
2. 关于max_tokens说明
max_tokens 与上下文长度相等，由于部分模型推理服务尚在更新中，请不要在请求时将 max_tokens 设置为最大值（上下文长度），建议留出 10k 左右作为输入内容的空间。
3. 关于context_length说明
不同的LLM模型，context_length是有差别的，具体可以在模型广场上搜索对应的模型， 查看模型具体信息。
4. 模型输出截断问题
可以从以下几方面进行问题的排查：
通过API请求时候，输出截断问题排查：
max_tokens设置：max_token设置到合适值，输出大于max_token的情况下，会被截断。
设置流式输出请求：非流式请求时候，输出内容比较长的情况下，容易出现504超时。
设置客户端超时时间：把客户端超时时间设置大一些，防止未输出完成，达到客户端超时时间被截断。
通过第三方客户端请求，输出截断问题排查：
CherryStdio 默认的 max_tokens 是 4096，用户可以通过设置，打开“开启消息长度限制”的开关，将max_token设置到合适值

5. 错误码处理
错误码	常见原因	解决方案
400	参数格式错误	检查temperature等请求参数的取值范围
401	API Key 没有正确设置	检查API Key
403	权限不够	最常见的原因是该模型需要实名认证，其他情况参考报错信息
429	请求频率超限	实施指数退避重试机制
503/504	模型过载	切换备用模型节点
​
5. 计费与配额管理
​
5.1 计费公式
总费用 = (输入tokens × 输入单价) + (输出tokens × 输出单价)
​
5.2 支持模型列表及单价
支持的模型及具体价格可以进入模型广场下的模型详情页查看。
​
6. 应用案例
​
6.1 技术文档生成
from openai import OpenAI
client = OpenAI(api_key="YOUR_KEY", base_url="https://api.siliconflow.cn/v1")
response = client.chat.completions.create(  
    model="Qwen/Qwen2.5-Coder-32B-Instruct",  
    messages=[{  
        "role": "user",  
        "content": "编写Python异步爬虫教程，包含代码示例和注意事项"  
    }],  
    temperature=0.7,  
    max_tokens=4096  
)  
​
6.2 数据分析报告
from openai import OpenAI
client = OpenAI(api_key="YOUR_KEY", base_url="https://api.siliconflow.cn/v1")
response = client.chat.completions.create(  
    model="Qwen/QVQ-72B-Preview",  
    messages=[    
        {"role": "system", "content": "你是数据分析专家，用Markdown输出结果"},  
        {"role": "user", "content": "分析2023年新能源汽车销售数据趋势"}  
    ],  
    temperature=0.7,  
    max_tokens=4096  
)  
模型能力持续更新中，建议定期访问模型广场获取最新信息。






批量推理
​
1. 概述
通过批量 API 发送批量请求到 SiliconFlow 云服务平台，不受在线的速率限制和影响，预期可以在 24 小时内完成，且价格降低 50%。该服务非常适合一些不需要立即响应的工作，比如大型的任务评估、信息分类与提取、文档处理等。批量处理结果文件的 URL 有效期为一个月，请及时转存，以防过期影响业务。
​
2. 使用流程
​
2.1 准备批量推理任务的输入文件
批量推理任务输入文件格式为 .jsonl，其中每一行都是一个完整的 API 请求的消息体，需满足以下要求：
每一行必须包含custom_id，且每个custom_id须在当前文件中唯一；
每一行的body中的必需包含messages对象数组，且数组中消息对象的role 为system、user或assistant之一，并且整个数组以user消息结束；
您可以为每一行数据按需设置相同或不同的推理参数，如设定不同的temperature、top_p；
如果您希望使用 OpenAI SDK 调用 SiliconFlow 批量推理，您需要保证同一输入文件中model是统一的。
每 batch 限制：单个 batch 对应的输入文件的大小最大1 G
批量推理输入限制：单个 批量推理 对应的输入文件的大小不超过 1 G，文件行数不超过 5000 行。 下面是一个包含 2 个请求的输入文件示例：
{"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "deepseek-ai/DeepSeek-V3", "messages": [{"role": "system", "content": "You are a highly advanced and versatile AI assistant"}, {"role": "user", "content": "How does photosynthesis work?"}], "stream": true, "max_tokens": 1514, "thinking_budget": 32768}}
{"custom_id": "request-2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "deepseek-ai/DeepSeek-V3", "messages": [{"role": "system", "content": "You are a highly advanced and versatile AI assistant"}, {"role": "user", "content": "Imagine a world where everyone can fly. Describe a day in this world."}], "stream": true, "max_tokens": 1583, "thinking_budget": 32768}}

其中custom_id和body的messages是必须内容，其他部分为非必需内容。
对于推理模型，可以通过 thinking_budget 字段控制模型的思维链输出长度，示例如下：
{"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "deepseek-ai/DeepSeek-R1", "messages": [{"role": "system", "content": "You are a highly advanced and versatile AI assistant"}, {"role": "user", "content": "How does photosynthesis work?"}], "stream": true, "max_tokens": 1514,"thinking_budget": 32768}}
{"custom_id": "request-2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "deepseek-ai/DeepSeek-R1", "messages": [{"role": "system", "content": "You are a highly advanced and versatile AI assistant"}, {"role": "user", "content": "Imagine a world where everyone can fly. Describe a day in this world."}], "stream": true, "max_tokens": 1583,"thinking_budget": 32768}}

​
2.2 上传批量推理任务的输入文件
您需要首先上传输入文件，以便在启动批量推理时使用。以下为使用 OpenAI SDK 调用 SiliconFlow 输入文件的示例。
from openai import OpenAI
client = OpenAI(
    api_key="YOUR_API_KEY", 
    base_url="https://api.siliconflow.cn/v1"
)

batch_input_file = client.files.create(
    file=open("batch_file_for_batch_inference.jsonl", "rb"),
    purpose="batch"
)
print(batch_input_file)
# 获取文件上传后的id
file_id = batch_input_file.data['id']
print(file_id)
这里需要记录下返回结果中的id，作为后面创建batch时候的请求参数。
​
2.3 创建批量推理任务
成功上传输入文件后，使用输入文件对象的 ID 创建批量推理任务，并设置任务参数。
对于对话模型，请求端点为/v1/chat/completions；
完成窗口目前支持设置24 ～ 336 小时（14 ✕ 24 小时）；
我们建议您通过extra_body设置任务需要使用的推理模型，如：extra_body={"replace":{"model": "deepseek-ai/DeepSeek-V3"}}，除非您的输入文件符合OpenAI的要求，文件中的每一行都具有相同的model；
如果您的extra_body中设置的模型，与输入文件中的model不一致，则任务实际使用模型以extra_body为准；
metadata参数可以用于备注一些额外的任务信息，如任务描述等。 以下为使用 OpenAI SDK 调用 SiliconFlow 输入文件的示例，input_file_id 从上一步完成上传的文件对象中获取。
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY", 
    base_url="https://api.siliconflow.cn/v1
)

batch_input_file_id = "file-abc123"
client.batches.create(
    input_file_id=batch_input_file_id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={
        "description": "nightly eval job"
    },
    extra_body={"replace":{"model": "deepseek-ai/DeepSeek-V3"}}
)

该请求将创建一个批量推理任务，并返回任务的状态信息。
​
2.4 检查批量推理状态
您可以随时检查批量处理任务的状态，代码示例如下：
from openai import OpenAI
client = OpenAI(
    api_key="YOUR_API_KEY", 
    base_url="https://api.siliconflow.cn/v1"
)

batch = client.batches.retrieve("batch_abc123")
print(batch)
返回的推理任务状态信息如下：
{
  "id": "batch_abc123",
  "object": "batch",
  "endpoint": "/v1/chat/completions",
  "errors": null,
  "input_file_id": "file-abc123",
  "completion_window": "24h",
  "status": "validating",
  "output_file_id": null,
  "error_file_id": null,
  "created_at": 1714508499,
  "in_progress_at": null,
  "expires_at": 1714536634,
  "completed_at": null,
  "failed_at": null,
  "expired_at": null,
  "request_counts": {
    "total": 0,
    "completed": 0,
    "failed": 0
  },
  "metadata": null
}
其中status包含以下几种状态：
in_queue： 批量推理任务在排队中
in_progress： 批量推理任务正在进行中
finalizing： 批量推理任务已完成，正在准备结果
completed： 批量推理任务已完成，结果已准备就绪
expired： 批量推理任务没有在预期完成时间内执行完成
cancelling： 批量推理任务取消中（等待执行中结果返回）
cancelled： 批量推理任务已取消
​
2.5 取消正在进行中的批量推理任务
如有必要，您可以取消正在进行的批量处理任务。批量处理任务状态将变为cancelling，直到在途的请求完成，之后该任务的状态将变为cancelled。
from openai import OpenAI
client = OpenAI(
    api_key="YOUR_API_KEY", 
    base_url="https://api.siliconflow.cn/v1"
)
client.batches.cancel("batch_abc123")
​
2.6 获得批量推理结果
系统将批量推理的结果文件按请求状态分别保存：
output_file_id：包含所有成功请求的输出结果文件。
error_file_id：包含所有失败请求的错误信息文件。
系统将保留结果文件 30 天。请务必在有效期内及时下载并备份相关数据。超过保存期限的文件将被自动删除，且无法恢复。
​
2.7 获取所有批量推理列表
支持查看用户下的所有批量推理任务列表,暂时不支持分页查询。
from openai import OpenAI
client = OpenAI(
    api_key="YOUR_API_KEY", 
    base_url="https://api.siliconflow.cn/v1"
)
response = client.batches.list().data
print(response)
​
2.8 批量推理任务超时（expired）
在指定时间未完成的批次最终会转入 expired 状态；该批次中未完成的请求会被取消，已完成请求的任何回复都会通过批量推理的输出文件提供。任何已完成的请求所消耗的tokens都将收取费用。
custom_id 已过期的请求将被写入错误文件，并显示如下信息。可以使用 custom_id 来检索已过期请求的请求数据。
{"id": "batch_req_123", "custom_id": "request-3", "response": null, "error": {"code": "batch_expired", "message": "This request could not be executed before the completion window expired."}}
{"id": "batch_req_123", "custom_id": "request-7", "response": null, "error": {"code": "batch_expired", "message": "This request could not be executed before the completion window expired."}}
​
3. 支持模型列表
目前仅支持端点/v1/chat/completions，且支持模型如下：
deepseek-ai/DeepSeek-V3
deepseek-ai/DeepSeek-R1
Qwen/QwQ-32B
deepseek-ai/DeepSeek-V3.1-Terminus
moonshotai/Kimi-K2-Instruct-0905
​
4. 输入限制：
Batch Job 输入限制与现有的按模型速率限制是分开的，参考如下条件：
每 batch 限制： 单个 batch 对应的输入文件的大小最大1 G。
说明：Batch Job 的请求不影响用户在线推理服务的 Rate Limits 使用。因此使用批量 API 不会消耗标准请求中的（用户，模型）维度的 Rate Limits的Request 或者 tokens 限制。
​
5. 费用说明
Batch 只能使用充值余额进行支付，具体价格如下：
SiliconFlow 平台推理模型价格表（单位：￥/百万 Tokens）
模型名称	实时推理 - 输入	实时推理 - 输出	批量推理 - 输入	批量推理 - 输出
DeepSeek-R1	¥4	¥16	¥2	¥8
DeepSeek-V3	¥2	¥8	¥1	¥4
Qwen/QwQ-32B	¥1	¥4	¥0.5	¥2
deepseek-ai/DeepSeek-V3.1-Terminus	¥4	¥12	¥2	¥6
moonshotai/Kimi-K2-Instruct-0905	¥4	¥16	¥2	¥8
注：如有大规模使用需求，欢迎 联系我们 了解专属方案。