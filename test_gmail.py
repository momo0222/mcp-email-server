from gmail_client import GmailClient

client = GmailClient()

messages = client.list_messages()

# for message in messages:
#     print(f"id:{message['id']} thread_id:{message['threadId']}")
first = messages[0]
msg_id = first['id']
full_msg = client.get_message(msg_id)
parsed = client.parse_message(full_msg)
print(f"From: {parsed['from']}")
print(f"Subject: {parsed['subject']}")
print(f"Date: {parsed['date']}")
print(f"\nBody:\n{parsed['body']}")

# print(f"Snippet: {full_msg.get('payload')}")