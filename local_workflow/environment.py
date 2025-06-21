from jinja2 import Environment, FileSystemLoader
import json
import yaml
from abc import ABC, abstractmethod
import copy

class AbstractGame(ABC):
    def __init__(self, configs, setup_data, tools=[], results_path=''):
        self.configs = configs
        self.setup_data = setup_data
        self.tools = {tool.__name__ if hasattr(tool, '__name__') else tool.func.__name__ : tool for tool in tools}
        with open(configs['tool']['schema_path'], 'r') as infile:
            tool_schemas = yaml.safe_load(infile)
        self.tool_schemas = {tool_schema['function']['name']: tool_schema for tool_schema in tool_schemas}
        self.jinja_env = Environment(
            loader=FileSystemLoader(configs['template']['dir']),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.solution = None
        self.correctness = False
        self.CALL_TYPE = {'action': self.action, 'think': self.think}
        self.results_path = results_path

    def think(self, agent):
        output = agent.generate()
        content = output.content
        agent.update(content, role="assistant")
        return {'outcome': content}
    
    @abstractmethod
    def tool_handler(self, agent, tools_avail):
        pass

    def action(self, agent, tools_avail, retry_limit=1):
        for attempt in range(retry_limit):
            initial_message_count = len(agent.messages)
            try:
                output = self.tool_handler(agent, tools_avail=tools_avail)
                # Only return if this is the last attempt or if we want to continue iterating
                if attempt == retry_limit - 1:
                    return {'outcome': output}
                # Continue to next iteration to let model process tool results
                continue
            except Exception as e:
                messages_added = len(agent.messages) > initial_message_count
                resubmit_msg = f"The previous action failed: {repr(e)}. Please try again."
                
                if attempt < retry_limit - 1:
                    if not messages_added:
                        agent.update("I encountered an error while processing your request.", role="assistant")
                    agent.update(resubmit_msg, role="user")
        return {'outcome': None}

    def _core_loop(self, agent):
        for step in self.configs['template']['core_loop']:
            output = self.CALL_TYPE[step['call_type']](agent, **step['additional_args'])
            if self.solution is not None: break
            content = self.jinja_env.get_template(step['next_template_path']).render(output)
            agent.update(
                content,
                role="user"
            )

    def play(self, agent):
        self._on_start(agent)
        while self.solution is None:
            self._core_loop(agent)
        self._on_end(agent)
    
    def verify_solution(self):
        verifier_config = self.configs.get('verifier', {})
        verifier_type = verifier_config.get('type', 'none')
        correctness = False
        try:
            if verifier_type == 'tool':
                tool_name = verifier_config['tool_name']
                if tool_name in self.tools:
                    correctness = self.tools[tool_name](**self.solution)
            elif verifier_type == "custom":
                module_name = verifier_config.get('module', 'external_tools')
                function_name = verifier_config.get('function', 'check_solution')
                module = __import__(module_name)
                verifier_func = getattr(module, function_name)
                correctness = verifier_func(self.solution)
        except Exception as e:
            pass
        return correctness

    def _on_start(self, agent):
        # Add system prompt
        system_prompt_path = self.configs['template'].get('system_prompt_path')
        if system_prompt_path:
            system_prompt = self.jinja_env.get_template(system_prompt_path).render(self.setup_data)
            agent.update(system_prompt, role="system")
        # Add user prompt
        user_prompt_path = self.configs['template'].get('user_prompt_path')
        if user_prompt_path:
            user_prompt = self.jinja_env.get_template(user_prompt_path).render(self.setup_data)
            agent.update(user_prompt, role="user")
            
    def _on_end(self, agent):
        self.correctness = self.verify_solution()
        result = {
            "solution": self.solution,
            "correctness": self.correctness,
            "messages": agent.messages if hasattr(agent, "messages") else []
        }
        if self.results_path:
            with open(self.results_path, "a") as outfile:
                outfile.write(json.dumps(result) + "\n")
        
class QwenGame(AbstractGame):
    def tool_handler(self, agent, tools_avail):
        tool_schemas = [self.tool_schemas[tool_name] for tool_name in tools_avail]
        message = agent.act(tool_schemas=tool_schemas)
        content = message.content or None
        # Check if response contains tool calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in message.tool_calls
            ]
            agent.update(content, role="assistant", tool_calls=tool_calls)
            output = copy.deepcopy(tool_calls)
            for tool_call in output: 
                tool_call['function']['arguments'] = json.loads(tool_call['function']['arguments'])
        else:
            agent.update(content, role="assistant")
            output = content 
        if type(output) == list:
            # Execute tools and add results
            for tool_call in output:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']
                if tool_name == "submit_solution":
                    self.solution = tool_args
                    return
                if tool_name in tools_avail and tool_name in self.tools:
                    tool_call['output'] = self.tools[tool_name](**tool_args)
                    agent.update(
                        role="tool",
                        content=str(tool_call['output']),
                        tool_call_id=tool_call['id'],
                    )
            # Let assistant process tool results before adding user message
            assistant_response = agent.generate().content  # This should process the tool results
            agent.update(assistant_response, role='assistant')
            
        # final response
        return output

class LlamaGame(AbstractGame):
    def tool_handler(self, agent, tools_avail):
        tool_schemas = [self.tool_schemas[tool_name] for tool_name in tools_avail]
        message = agent.act(tool_schemas=tool_schemas)
        content = message.content or None
        # Check if response contains tool calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in message.tool_calls
            ]
            # TODO: Llama can only handle a single tool call at once...?
            tool_calls = tool_calls[:1]
            agent.update(content, role="assistant", tool_calls=tool_calls)
            output = copy.deepcopy(tool_calls)
            for tool_call in output: 
                tool_call['function']['arguments'] = json.loads(tool_call['function']['arguments'])
        else:
            agent.update(content, role="assistant")
            output = content 
        if type(output) == list:
            # Execute tools and add results
            for tool_call in output:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']
                if tool_name == "submit_solution":
                    self.solution = tool_args
                    return
                if tool_name in tools_avail and tool_name in self.tools:
                    tool_call['output'] = self.tools[tool_name](**tool_args)
                    agent.update(
                        role="tool",
                        content=str(tool_call['output']),
                        tool_call_id=tool_call['id'],
                    )
            # Let assistant process tool results before adding user message  
            assistant_response = agent.generate().content  # This should process the tool results
            agent.update(assistant_response, role='assistant')
            
        # final response
        return output