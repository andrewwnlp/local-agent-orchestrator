# Local Agent Orchestrator

A flexible framework for building and evaluating agentic applications with language models. This system provides a configurable pipeline for creating agents that can think, act, and use tools to solve complex problems.

## Overview

The Local Agent Orchestrator is designed to work with OpenAI-compatible language model servers and provides a structured environment for agents to interact with tools and solve tasks through a configurable core loop. While the current example focuses on GSM8K mathematical reasoning, the framework is general-purpose and can be adapted to various agentic applications.

## Architecture

The framework consists of several key components:

- **Agent**: Handles communication with the language model
- **Environment/Game**: Manages the task execution and tool interactions
- **Tools**: External functions the agent can call
- **Templates**: Jinja2 templates for prompts and responses
- **Configuration**: YAML-based configuration for all aspects of the pipeline

## Quick Start
0. **Installation and setup**
```bash
# Clone the repository
git clone <repository-url>
cd local_agent

# Install dependencies
conda create -n local-agent python=3.12
conda activate local-agent
pip install uv
uv pip install vllm
pip install datasets openai
```

1. **Configure your language model server** to be OpenAI-compatible
2. **Set up your configuration file** (see gsm8k.yaml as an example)
3. **Define your tools** in the tool schemas file
4. **Create your prompt templates** in the templates directory
5. **Install local_workflow** from source
```bash
pip install --editable .
```

6. **Run the pipeline**:
```bash
python llm/run.py --config_file configs/gsm8k.yaml --log-level INFO
```

## Configuration

### Main Configuration File (gsm8k.yaml)

The configuration file defines all aspects of your agentic pipeline:

#### Data Configuration
```yaml
data:
  dataset_path: openai/gsm8k  # HuggingFace dataset path
  subset: main                # Dataset subset
  split: test                 # Data split to use
```

#### Server Configuration
```yaml
server:
  base_url: http://<your url here>  # Base URL of your OpenAI-compatible server
  ports: 8088                       # Port number
```

#### Generation Configuration
```yaml
generation:
  model: meta-llama/Llama-3.3-70B-Instruct  # Model name
  temperature: 0.6           # Sampling temperature
  top_p: 0.95               # Top-p sampling
```

#### Tool Configuration
```yaml
tool:
  schema_path: "external_tools/tool_schemas.yaml"  # Path to tool definitions
  handler: LlamaGame         # Game class to use (LlamaGame or QwenGame)
```

#### Template Configuration
```yaml
template:
  dir: "templates"           # Directory containing Jinja2 templates
  system_prompt_path: "system_prompt.jinja"
  user_prompt_path: "user_prompt.jinja"
  core_loop:                 # The main execution loop (see below)
    - call_type: "think"
      additional_args: {}
      next_template_path: "thinking_response.jinja"
    - call_type: "action"
      additional_args:
        tools_avail:
          - add
          - subtract
          - multiply
          - divide
          - submit_solution
        retry_limit: 1
      next_template_path: "action_response.jinja"
```

#### Verifier Configuration
```yaml
verifier:
  type: tool                 # Options: "tool", "custom", "none"
  tool_name: "verify"        # Tool to use for verification
```

## Core Loop

The core loop is the heart of the framework, defining how the agent iterates through thinking and acting phases:

### Loop Structure

Each step in the core loop has three components:

1. **`call_type`**: Either `"think"` or `"action"`
2. **`additional_args`**: Arguments passed to the call type handler
3. **`next_template_path`**: Template to render after this step

### Call Types

#### Think
- Allows the agent to reason about the problem
- Generates text without tool calls
- Updates the conversation with the agent's thoughts

#### Action
- Enables the agent to use tools
- Requires `tools_avail` list specifying available tools
- Supports `retry_limit` for handling failed tool calls
- Processes tool results and updates the conversation

### Example Core Loop

```yaml
core_loop:
  - call_type: "think"
    additional_args: {}
    next_template_path: "thinking_response.jinja"
  - call_type: "action"
    additional_args:
      tools_avail:
        - calculator
        - search
        - submit_solution
      retry_limit: 2
    next_template_path: "action_response.jinja"
```

This creates a loop where the agent:
1. Thinks about the problem
2. Takes an action using available tools
3. Continues until a solution is submitted

## Tools

### Tool Schema Format

Tools are defined in YAML format following OpenAI's function calling schema:

```yaml
- type: function
  function:
    name: add
    description: returns the sum of two input values `a` and `b`
    parameters:
      type: object
      properties:
        a:
          type: number
          description: augend
        b:
          type: number
          description: addend
```

### Special Tools

- **`submit_solution`**: Ends the game loop when called
- **`verify`**: Used by the verifier to check solution correctness

### Implementing Tools

Tools are Python functions that the agent can call:

```python
def add(a, b):
    return a + b

def verify(submission, solution):
    return submission == solution
```

## Game Handlers

The framework provides two game handler implementations:

### LlamaGame
- Optimized for Llama models
- Handles single tool calls at a time
- Processes tool results before continuing

### QwenGame
- Optimized for Qwen models
- Supports multiple tool calls in one turn
- Different conversation flow handling

## Templates

Templates use Jinja2 for dynamic prompt generation:

### System Prompt (`system_prompt.jinja`)
```jinja
You are a helpful assistant that can solve math problems step by step.
```

### User Prompt (`user_prompt.jinja`)
```jinja
Problem: {{ question }}
Please solve this step by step.
```

### Response Templates
Templates that guide the agent's next actions based on the previous step's outcome.

## Verification

The framework supports multiple verification methods:

### Tool-based Verification
```yaml
verifier:
  type: tool
  tool_name: "verify"
```

### Custom Verification
```yaml
verifier:
  type: custom
  module: "external_tools"
  function: "check_solution"
```

### No Verification
```yaml
verifier:
  type: none
```

## Extending the Framework

### Adding New Tasks

1. **Create a new configuration file** with your dataset and tools
2. **Define task-specific tools** in a tool schema file
3. **Create appropriate templates** for your domain
4. **Implement any custom verification logic**

### Adding New Game Handlers

Create a new class inheriting from `AbstractGame`:

```python
class CustomGame(AbstractGame):
    def tool_handler(self, agent, tools_avail):
        # Custom tool handling logic
        pass
```

### Custom Tools

Add new tools by:
1. Implementing the function in Python
2. Adding the schema to your tool schemas file
3. Including it in the `tools_avail` list in your configuration

## Logging and Results

The framework provides comprehensive logging and saves results in JSONL format:

```json
{
  "solution": {"submission": 42},
  "correctness": true,
  "messages": [...]
}
```

Set logging levels with `--log-level` (DEBUG, TRACE, INFO, WARNING, ERROR, CRITICAL).

*REAMDE.md generated by claude-4 sonnet*