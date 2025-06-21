from openai import OpenAI
import copy
from local_workflow.local_logging.utils import get_logger

logger = get_logger(__name__)

class BaseAgent:
    
    def __init__(self, generation_configs, server_configs):
        self.generation_configs = generation_configs
        self.server_configs = server_configs
        self.messages = []
        endpoint=f"{server_configs['base_url']}:{server_configs['ports']}/v1"
        self.client = OpenAI(
            base_url=endpoint,
            api_key="-",
        )

    def generate(self, generation_configs=None):
        if generation_configs is None:
            generation_configs = self.generation_configs
        res = self.client.chat.completions.create(
            messages=self.messages,
            **generation_configs
        )
        try:
            message = res.choices[0].message
            return message
        except Exception as e: #e
            return ''
         
    def act(self, tool_schemas):
        generation_configs = copy.deepcopy(self.generation_configs)
        generation_configs['tools'] = tool_schemas
        generation_configs['tool_choice'] = 'required'
        try:
            return self.generate(generation_configs=generation_configs)
        except Exception as e:
            return f"Error in tool calling: {repr(e)}"

    def update(self, content, role, **kwargs):
        message = {
            "role": role,
            "content": content
        }
        message.update(kwargs)
        self.messages.append(message)
        logger.trace(f"{role} --\n{content if content else kwargs}")

    