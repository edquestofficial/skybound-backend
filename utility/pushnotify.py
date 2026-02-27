from typing import List
import firebase_admin as admin
from firebase_admin import credentials, messaging
import os
from  utility.statemgmt import state

# creds_path = os.path.join(os.path.dirname(__file__), "skybound-b63c2-firebase-adminsdk-fbsvc-e14f5bb985.json")
creds_path = os.environ["FIREBASE_CREDENTIALS"]
cred = credentials.Certificate(creds_path)
admin.initialize_app(cred)

async def send_notify (fcmToken: str, title: str, body: str):
    message_payload = messaging.Message(
        token=fcmToken,
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data={
            "type": "lead",
            "leadid": "0"
        },
        android=messaging.AndroidConfig(
            priority="high"
        )
    )

    response = messaging.send(message_payload)
    return response

def send_notifications(device_tokens: List[str], title: str, message: str, data: dict = None):
    """Send push notification to multiple device tokens using Firebase Cloud Messaging."""
    if not device_tokens:
        return
    set_val = set(device_tokens)
    if state.device_tokens in set_val:
        set_val.remove(state.device_tokens)
    responses = []
    # Send message to each token
    for token in set_val:
        try:
            notification_message = messaging.Message(
                token=token,
                notification=messaging.Notification(
                    title=title,
                    body=message
                ),
                data=data,
                android=messaging.AndroidConfig(
                    priority="high"
                )
            )
            response = messaging.send(notification_message)
            responses.append(response)
            print(f'Successfully sent message to {title}')
        except Exception as e:
            print(f'Failed to send message to : {str(e)}')
    
    return responses 