class SmsConnector:
    def __init__(self, api_key: str = "test") -> None:
        self.api_key = api_key
        
    def send(self, to_phone: str, body: str) -> None:
        print(f"DEBUG: Mock sending SMS to {to_phone}: {body}")
