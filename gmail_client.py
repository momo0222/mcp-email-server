
class GmailClient:
    def __init__(self):
        pass

    def list_messages(self, max_results: int = 10) -> list:
        """
        Returns a list of recent emails, limited by max_results
        
        Args:
            max_results (int) : The maximum number of emails returned, with a default of 10
        """
        pass
    def get_message(self, message_id: str) -> dict:
        """
        Returns the details of a specific email by its id

        Args:
            message_id (str): The unique identifier of the email
        """
        pass
    def parse_message(self, dict: str) -> dict:
        """
        Parses raw message from Gmail API into a structured format
        Args:
            dict (str): The raw message data from Gmail API
        """
        pass