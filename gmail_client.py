from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.message import EmailMessage
import base64
import html
import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
load_dotenv()
client = OpenAI()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    'https://www.googleapis.com/auth/gmail.send',
    ]

class PotentialReplies(BaseModel):
    casual: str = Field(description="Short, friendly reply")
    professional: str = Field(description="Formal, professional reply")
    detailed: str = Field(description="Thorough, detailed reply")

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
        

    def list_messages(self, max_results: int = 10, query: str = '') -> list:
        """
        Returns a list of recent emails, limited by max_results
        
        :param self: Description
        :param max_results: maximum number of emails returned
        :param query: Gmail search query (e.g., 'from:someone@gmail.com')
        :type max_results: int
        :return: a list of max_results emails
        :rtype: list
        """
        results = self.service.users().messages().list(
            userId="me",
            maxResults=max_results,
            q=query
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
    
    def classify_email(self, parsed_email: dict) -> str:
        """Classify email as urgent, personal, routine, or spam

        :param self: this
        :param parsed_email: Parsed email dict with subject, from, and snippet
        :type parsed_email: dict
        :return: Classification of the email as either 'urgent', 'personal', 'routine', or 'spam'
        :rtype: str
        """
        prompt = f"""Classify this email as one of: urgent, personal, routine, or spam

                Subject: {parsed_email['subject']}
                From: {parsed_email['from']}
                Preview: {parsed_email['snippet']}

                Respond with just one word: urgent, personal, routine, or spam"""
        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )
        return response.output_text.strip().lower()

    def generate_reply_suggestions(self, parsed_email: dict) -> list:
        """
        Generate 3 reply suggestions using OpenAI
        
        :param self: Description
        :param parsed_email: Parsed email dict with subject, from, and snippet
        :type parsed_email: dict
        :return: List of 3 reply suggestions: [casual, professional, detailed]
        :rtype: list
        """
        prompt = f"""Generate three responses for this email with the tones: casual, professional, and detailed
            Subject: {parsed_email['subject']}
            From: {parsed_email['from']}
            Body: {parsed_email['body']}
            
            Return the response in a list
        """
        response = client.responses.parse(
            model="gpt-4o-mini",
            input=prompt,
            text_format=PotentialReplies
        )
        if response.output_parsed:
            return [response.output_parsed.casual, response.output_parsed.professional, response.output_parsed.detailed]
        return []
    
    def generate_smart_reply(self, parsed_email: dict) -> str:
        """Generate a single, contextually appropriate reply"""
        print(f"DEBUG: parsed_email keys: {parsed_email.keys()}")
        prompt = f"""Generate ONLY the body of an email reply. Do NOT include subject line or headers.

        From: {parsed_email['from']}
        Subject: {parsed_email['subject']}
        Body: {parsed_email['body']}

        Based on the sender and content, write a reply with the appropriate tone (casual, professional, or detailed).
        Keep it concise but helpful. Write ONLY the reply body text with appropriate tone. Start directly with the greeting."""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )
    
        return response.output_text

    def send_email(self, to: str, subject: str, body: str, thread_id: Optional[str]=None) -> dict:
        message = EmailMessage()
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)
        if thread_id:
            # These headers tell Gmail this is part of a conversation
            message['In-Reply-To'] = f'<{thread_id}@mail.gmail.com>'
            message['References'] = f'<{thread_id}@mail.gmail.com>'
        encoded_msg = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_msg}

        if thread_id:
            create_message['threadId'] = thread_id
        
        send_message = self.service.users().messages().send(userId='me', body=create_message).execute()
        
        return send_message
    
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
        decoded_bytes = base64.urlsafe_b64decode(body)
        text = decoded_bytes.decode('utf-8')
        return text.replace('\r\n', '\n').replace('\r', '\n')
