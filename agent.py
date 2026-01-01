import time
from gmail_client import GmailClient
from datetime import datetime
from logger import log_action

#Config
CHECK_INTERVAL = 60
DRY_RUN = False

#WHITELIST - always autoreply
AUTO_REPLY_WHITELIST = [
    'anthonywei341@gmail',
    'joywang0222@gmail.com'
]
#BLACKLIST - never autoreply
AUTO_REPLY_BLACKLIST = [
    'noreply@',
    'no-reply@',
    'donotreply@',
]

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
    sender = parsed_email['from'].lower()

    if any(blocked in sender for blocked in AUTO_REPLY_BLACKLIST):
        return {
            'type': 'notify',
            'reason': f"Blacklisted sender: {sender}"
        }

    is_whitelisted = any(allowed in sender for allowed in AUTO_REPLY_WHITELIST)

    if is_whitelisted:

        if classification in ['routine', 'spam', 'personal']:
            suggestion = client.generate_smart_reply(parsed_email=parsed_email)
            return {
                'type': 'reply',
                'message': suggestion
            }
        else:
            return {
                'type': 'urgent',
                'reason': 'Urgent email from whitelisted sender'
            }
    match classification:
        case 'urgent':
            return {
                'type': 'urgent',
                'reason': 'Urgent email requiring immediate attention'
            }
        case 'routine':
            return {
                'type': 'notify',
                'reason': 'Not whitelisted routine email'
            }
        case 'spam':
            return{
                'type': 'archive',
                'reason': 'Classified as spam'
            }
        case 'personal':
            return{
                'type': 'notify',
                'reason': 'Personal email'
            }
        case _:
            return {
                'type': 'unknown',
                'reason': 'Unknown c'
                'lassifcation'
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

def is_obvious_spam(parsed_email: dict) -> bool:
    """Quick spam detection before AI classification

    Args:
        parsed_email: dictionary of email with body for spam classification
    """
    spam_keywords = [
        #Marketing
        'unsubscribe', 'opt-out', 'promotional', 'deal', 'discount',
        'sale', "% off", 'limited time', 'act now', 'claim',
        # Automated
        'noreply', 'no-reply', 'donotreply', 'automated',
    ]
    spam_senders = [
        'marketing@', 'promo@', 'offers@', 'deals@',
        'noreply@', 'no-reply@', 'donotreply@',
    ]
    
    # Combine subject + from + snippet for checking
    text = f"{parsed_email['subject']} {parsed_email['from']} {parsed_email.get('snippet', '')}".lower()
    sender = parsed_email['from'].lower()
    
    # Check keywords in text
    if any(keyword in text for keyword in spam_keywords):
        return True
    
    # Check sender patterns
    if any(pattern in sender for pattern in spam_senders):
        return True
    
    return False

while True:
    try:
        #PERCEIVE
        new_emails = check_for_new_emails()

        if new_emails:
            print(f"Found {len(new_emails)} new email(s) \n")
            for email_id in new_emails:
                email = client.get_message(message_id=email_id)
                parsed = client.parse_message(message=email)
                sender = parsed['from']

                if not any(allowed in sender for allowed in AUTO_REPLY_WHITELIST) and is_obvious_spam(parsed_email=parsed):
                    action = {
                            'type': 'spam',
                            'reason': 'Classified by obvious spam detection'
                        }
                    log_action(parsed, 'spam', action)
                    execute_action(
                        action = action,
                        email=parsed
                    )
                    continue


                #DECIDE
                classification = client.classify_email(parsed_email=parsed)
                action = decide_action(parsed_email=parsed, classification=classification)

                # LOG IT!
                log_action(parsed, classification, action)

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