from gmail_client import GmailClient

client = GmailClient()

messages = client.list_messages(max_results=1)

if messages:
    parsed = client.parse_message(client.get_message(messages[0]['id']))

    classified_email = client.classify_email(parsed_email=parsed)
    print(classified_email)