#!/bin/bash

# python -m vllm.entrypoints.openai.api_server \
#     --model Qwen/Qwen2.5-72B-Instruct \
#     --port 8088 \
#     --max_model_len 32768 \
#     --tensor_parallel_size 4 \
#     --tool-call-parser hermes \

python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.3-70B-Instruct \
    --port 8088 \
    --max_model_len 32768 \
    --tensor_parallel_size 4 \
    --tool-call-parser llama3_json \
    --chat-template chat_templates/tool_chat_template_llama3.1_json.jinja \