class EmailConnector:
    def __init__(self, smtp_server: str = "smtp.mock", port: int = 587) -> None:
        self.smtp_server = smtp_server
        self.port = port
        
    def send(self, to_addr: str, subject: str, html_body: str) -> None:
        print(f"DEBUG: Mock sending EMAIL to {to_addr}: {subject}")
