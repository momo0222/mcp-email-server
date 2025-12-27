from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import html
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class GmailClient:
    def __init__(self, credentials_path: str="credentials.json", token_path: str="token.json"):
        """
        Initialize Gmail Client with OAuth Credentials
        
        :param self: Description
        :param credentials_path: path to oauth credentials json
        :type credentials_path: str
        :param token_path: path to save/load auth token
        :type token_path: str

        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open (token_path, 'w') as file:
                file.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)
        

    def list_messages(self, max_results: int = 10) -> list:
        """
        Returns a list of recent emails, limited by max_results
        
        :param self: Description
        :param max_results: maximum number of emails returned
        :type max_results: int
        :return: a list of max_results emails
        :rtype: list
        """
        results = self.service.users().messages().list(
            userId="me",
            maxResults=max_results
        ).execute()
        return results.get("messages", [])
        
    def get_message(self, message_id: str) -> dict:
        """
        Returns the details of a specific email by its id
        
        :param self: Description
        :param message_id: The unique identifier of the email
        :type message_id: str
        :return: Full message data
        :rtype: dict
        
        """
        return self.service.users().messages().get(
            userId="me",
            id=message_id,
            format='full'
        ).execute()
        
    def parse_message(self, message: dict) -> dict:
        """
        Parses raw message from Gmail API into a structured format
        
        :param self: Description
        :param dict: The raw message data from Gmail API
        :type dict: str
        :return: Parsed message with subject, from, to, date, body
        :rtype: dict
        
        """
        headers = message["payload"]["headers"]
        parsed = {
            'id': message['id'],
            'threadId': message['threadId'],
            'snippet': html.unescape(message.get('snippet', ''))
        }
        keys = ["subject", "from", "to", "date"]
        for header in headers:
            name = header["name"].lower()
            if name in keys:
                parsed[name] = header["value"]
        parsed["body"] = self._get_body(message['payload'])

        return parsed
        
    def _get_body(self, payload: dict) -> str:
        if 'body' in payload and 'data' in payload['body']:
            return self._decode_body(payload['body']['data'])
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if 'data' in part.get('body', {}):
                        return self._decode_body(part['body']['data'])
            for part in payload['parts']:
                if part.get('mimeType') == 'text/html':
                    if 'data' in part.get('body', {}):
                        return self._decode_body(part['body']['data'])
        return 'Could not extract body'

    def _decode_body(self, body: str) -> str:
        decoded_bytes = base64.b64decode(body)
        text = decoded_bytes.decode('utf-8')
        return text.replace('\r\n', '\n').replace('\r', '\n')
