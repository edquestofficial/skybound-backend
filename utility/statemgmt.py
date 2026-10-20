class userinfo:
    def __init__(self):
        self.value = None
        self.device_tokens = ""
    
    def setvalue(self,value):
        self.value = value
    def set_device_tokens(self, device_tokens):
        self.device_tokens = device_tokens

state = userinfo()
