class AgentMaxIterationsException(Exception):
    def __init__(
        self,
        message="I'm having trouble processing your query. Could you please clarify or provide more details? Alternatively, you might try resubmitting your request later.",
    ):
        self.message = message
        super().__init__(self.message)
