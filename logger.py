import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

def log_action(email: dict, classification: str, action: dict):
    """Save a record of what the agent did
    
    Args:
        email: Parsed email dict (with from, subject, etc.)
        classification: What AI said (urgent, routine, spam, personal)
        action: What agent decided to do (reply, archive, notify)
    """
    log_entry = {
        'timestamp: ': datetime.now().isoformat(),
        'from': email.get('from'),
        'subject': email.get('subject'),
        'classification': classification,
        'action_type': action.get('type'),
        'action_reason': action.get('reason')
    }

    print(f"    [LOG] {classification} -> {action['type']}")
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = LOG_DIR / f"agent_{today}.log"

    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry)+'\n')