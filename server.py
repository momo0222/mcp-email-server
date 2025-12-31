from typing import Any, Optional
import sys
from mcp.server.fastmcp import FastMCP
from gmail_client import GmailClient
from pydantic import BaseModel, Field

mcp = FastMCP("gmail_helper")
gmail_client = GmailClient()

class ListMessagesInput(BaseModel):
    max_results: int = Field(default=10, gt=0, le=50, description="Maximum number of emails to return")

class ReadEmailInput(BaseModel):
    gmail_id: str = Field(min_length=1, description="Unique ID of an email")

class SearchMessagesInput(BaseModel):
    query: str = Field(default='', description="Gmail search query")
    max_results: int = Field(default=10, gt=0, le=50, description="Maximum number of emails to return")

class SendEmailInput(BaseModel):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body text")
    thread_id: Optional[str] = Field(default=None, description="Thread ID to reply to (optional)")

@mcp.tool()
async def gmail_list_messages(params: ListMessagesInput) -> str:
    """List recent Gmail messages with subject, sender, and preview
    
    Returns a formatted string of emails with key details like who sent it, the id of the email,
    when it was sent, and a preview of the content
    """

    recent_msgs = gmail_client.list_messages(params.max_results)
    
    if not recent_msgs:
        return "No recent messages found"
    
    output = f"# Recent Emails ({len(recent_msgs)} messages)\n\n"

    for msg in recent_msgs:
        raw = gmail_client.get_message(msg['id'])
        parsed = gmail_client.parse_message(raw)
        output += f"## Subject: {parsed['subject']}\n"
        output += f"**ID:** `{parsed['id']}`\n" 
        output += f"**From:** {parsed['from']}\n"
        output += f"**Date:** {parsed['date']}\n"
        output += f"**Preview:** {parsed['snippet']}\n\n"

    return output

@mcp.tool()
async def gmail_read_email(params: ReadEmailInput) -> str:
    """Reads an email given its id and returns its sender, subject, body, and date

    Returns a formatted string of the email with sender, subject, body, and date
    """
    email = gmail_client.get_message(params.gmail_id)
    parsed = gmail_client.parse_message(email)

    output = "# Retrieved Email\n\n"
    output += f"## Subject: {parsed['subject']}\n"
    output += f"**From:** {parsed['from']}\n"
    output += f"**Date:** {parsed['date']}\n"
    output += f"**Body:**\n{parsed['body']}\n\n"
    return output

@mcp.tool()
async def gmail_search_messages(params: SearchMessagesInput) -> str:
    """Search gmail messages using Gmail query syntax
    
    Returns a formatted string of emails that satisfy the query with the same format
    as gmail_list_messages. Supports queries like 'from:email@example.com', 'subject:meeting'
    """
    msgs = gmail_client.list_messages(params.max_results, params.query)

    if not msgs:
        return "No messages found that match the query"
    
    output = f"# Search Relevant Emails ({len(msgs)} messages)\n\n"

    for msg in msgs:
        raw = gmail_client.get_message(msg['id'])
        parsed = gmail_client.parse_message(raw)
        output += f"## Subject: {parsed['subject']}\n"
        output += f"**ID:** `{parsed['id']}`\n" 
        output += f"**From:** {parsed['from']}\n"
        output += f"**Date:** {parsed['date']}\n"
        output += f"**Preview:** {parsed['snippet']}\n\n"

    return output

@mcp.tool()
async def gmail_suggest_reply(params: ReadEmailInput) -> str:
    """Generate smart reply suggestions for an email

    Returns a formatted string of three suggestions with different tones: casual, professional
    and detailed
    """
    email = gmail_client.get_message(params.gmail_id)
    parsed = gmail_client.parse_message(email)
    
    suggestions = gmail_client.generate_reply_suggestions(parsed_email=parsed)
    if not suggestions:
        return "No reply suggestions available"
    output = "# Reply Suggestions \n\n"
    output += "## Casual\n"
    output += f"{suggestions[0]}\n\n"
    output += "## Professional\n"
    output += f"{suggestions[1]}\n\n"
    output += "## Detailed\n"
    output += f"{suggestions[2]}\n\n"
    return output

@mcp.tool()
async def gmail_send_email(params: SendEmailInput) -> str:
    """Send an email or reply to a thread

    Can send a new email or reply to an existing conversaion by providing thread_id
    """
    sent = gmail_client.send_email(
        to=params.to, 
        subject=params.subject, 
        body=params.body, 
        thread_id=params.thread_id
    )

    if params.thread_id:
        return f"Reply sent to {params.to}"
    else:
        return f"Email sent to {params.to}\n Subject: {params.subject}"


if __name__ == "__main__":
    mcp.run()