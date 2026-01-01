import time
from gmail_client import GmailClient
from datetime import datetime

#Config
CHECK_INTERVAL = 60
DRY_RUN = False

print("Email agent starting...")
print(f"     Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
print(f"     Checking every {CHECK_INTERVAL} seconds\n\n")

client = GmailClient()
seen = set()

def check_for_new_emails() -> list:
    """PERCEIVE: Check for unread emails

    Returns:
        A list of new email IDs that are new and unread
    """
    unread = client.list_messages(max_results=100, query='is:unread')
    unread_ids = [msg['id'] for msg in unread if msg['id'] not in seen]
    return unread_ids

def decide_action(parsed_email: dict, classification: str) -> dict:
    """DECIDE: What should we do with the email?

    Args:
        parsed_email: Parsed email with from, subject, body, etc
        classification: urgent', 'routine', 'spam', or 'personal'
        
    Returns:
        Action dict like {'type': 'reply', 'message': '...'} or {'type': 'archive'}
    """
    match classification:
        case 'urgent':
            return {
                'type': 'urgent',
                'reason': 'Urgent email requiring immediate attention'
            }
        case 'routine':
            suggestion = client.generate_smart_reply(parsed_email=parsed_email)
            return {
                'type': 'reply',
                'message': suggestion
            }
        case 'spam':
            return{
                'type': 'archive',
                'reason': 'Classified as spam'
            }
        case 'personal':
            return{
                'type': 'notify',
                'reason': 'personal email'
            }
        case _:
            return {
                'type': 'unknown',
                'reason': 'Unknown classifcation'
            }

def execute_action(action: dict, email: dict):
    """ACT: Execute the decided action

    Args:
        action: dict specifying what action to take
        email: parsed email dict
    """
    action_type = action['type']

    print(f"\n Email from: {email['from']}")
    print(f"    Subject:{email['subject']}")
    print(f"    Action:{action_type.upper()}")

    match action_type:
        case 'urgent':
            print(f"    Reason: {action['reason']}")
        case 'reply':
            if DRY_RUN:
                print(f"   [DRY RUN] Would send reply:")
                print(f"   {action['message'][:100]}...")
            else:
                client.send_email(
                    to=email['from'],  # Reply to sender, not yourself!
                    subject=f"Re: {email['subject']}",
                    body=action['message'],
                    thread_id=email.get('threadId')
                )
                print(f"   Reply sent!")
        case 'archive':
            print(f"    Reason: {action['reason']}")
            #to be implemented
        case 'notify':
            print(f"    Reason: {action['reason']}")
        case _:
            print(" No action done")

while True:
    try:
        #PERCEIVE
        new_emails = check_for_new_emails()

        if new_emails:
            print(f"Found {len(new_emails)} new email(s) \n")
            for email_id in new_emails:
                email = client.get_message(message_id=email_id)
                parsed = client.parse_message(message=email)

                #DECIDE
                classification = client.classify_email(parsed_email=parsed)
                action = decide_action(parsed_email=parsed, classification=classification)

                #EXECUTE
                execute_action(action=action, email=parsed)
                seen.add(email_id)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No new emails..")
        time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\nAgent stopped by User")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(CHECK_INTERVAL)