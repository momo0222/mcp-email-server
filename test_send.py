from gmail_client import GmailClient

client = GmailClient()

# Send to yourself!
result = client.send_email(
    to="joywang0222@gmail.com",  # ← Put your actual email
    subject="MCP Test Email",
    body="Hello! This is a test from my email agent. If you got this, everything works!"
)

print(f"Sent! Message ID: {result['id']}")