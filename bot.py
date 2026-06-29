import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler 

load_dotenv()

app = App(
    token=os.getenv("SLACK_BOT_TOKEN")
)

@app.event("message")
def handle_message(message,say):
    if message.get("channel_type") == "im":
        user_text = message.get("text", "")
        say(f"Got it: '{user_text}' — agent coming soon!")     

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    print("PaiseWise Bot is running")
    handler.start() 
