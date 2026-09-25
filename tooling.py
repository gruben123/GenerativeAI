class Tools:
    def __init__(self):
        self.registry = {}

    def register(self, name, func):
        self.registry[name] = func

    def get_tool(self, name):
        return self.registry.get(name)