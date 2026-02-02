import instructor
from openai import OpenAI
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda

class InstructorAdapter:
    """
    Wraps the Instructor client to make it compatible with 
    LangChain's .invoke() and .with_structured_output() interfaces.
    """
    def __init__(self, base_url: str, model: str, temperature: float = 0):
        self.raw_client = OpenAI(
            base_url=base_url,
            api_key="ollama" 
        )
        # Patch it with Instructor
        self.client = instructor.patch(self.raw_client, mode=instructor.Mode.JSON)
        self.model = model
        self.temperature = temperature
        self.model_name = model # Compatibility field for LangChain

    def _convert_messages(self, messages: list[BaseMessage]) -> list[dict]:
        """Convert LangChain messages to OpenAI/Ollama format."""
        formatted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append({"role": "user", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                formatted.append({"role": "system", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted.append({"role": "assistant", "content": msg.content})
            else:
                formatted.append({"role": "user", "content": str(msg.content)})
        return formatted

    def invoke(self, input_data: str | list[BaseMessage]) -> AIMessage:
        """
        Mimics LangChain's invoke for standard text generation.
        """
        messages = self._convert_messages(input_data) if isinstance(input_data, list) else [{"role": "user", "content": input_data}]
        
        # Standard generation using the underlying client (bypassing instructor validation for plain text)
        response = self.raw_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        return AIMessage(content=response.choices[0].message.content)

    def with_structured_output(self, schema):
        """
        Mimics LangChain's structured output, but uses Instructor backend.
        Returns a RunnableLambda that fits into LangChain pipelines.
        """
        def _run_instructor(input_data):
            messages = self._convert_messages(input_data) if isinstance(input_data, list) else [{"role": "user", "content": input_data}]
            
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_model=schema,
                temperature=self.temperature,
                max_retries=3
            )
        
        return RunnableLambda(_run_instructor)