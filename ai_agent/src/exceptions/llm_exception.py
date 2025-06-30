

class AgentException(Exception):
    pass

class LLMError(AgentException):
    
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
class LLMDoesNotExists(LLMError):

    def __init__(self, model_name):
        self.model_name = model_name
        super().__init__(f"Model '{model_name}' does not exist.")