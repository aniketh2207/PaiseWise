import os
from sqlalchemy import text
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler 
from backend.tools.parsing_agent import parse_agent
from backend.tools.llm_client import generate_summary,generate_sql,generate_answer
from backend.tools.db_tools import get_monthly_aggregates
from backend.config import settings
from backend.database.db import SessionLocal
from datetime import datetime
app = App(
    token=settings.SLACK_BOT_TOKEN
)


@app.command("/summary")
def get_month_summary(ack,respond,command):
    ack() # slack commands needs to be resolved within 3 secs 
    now = datetime.now()
    aggregates = get_monthly_aggregates(now.month,now.year)
    if aggregates['transaction_count'] == 0:
        respond("No transactions occured this month")
        return
    summary = generate_summary(aggregates)
    respond(summary)

@app.command("/ask")
def handle_ask_query(ack, respond, command):
    ack() 
    
    user_question = command.get("text", "").strip()
    if not user_question:
        respond("Please ask a question! (e.g., /ask How much did I spend on food today?)")
        return
    db = SessionLocal()

    try:
        # 1. Get the SQL string
        generated_sql = generate_sql(user_question)
        
        # 2. Get the database data
        db_result = db.execute(text(generated_sql)).fetchall()
        
        # 3. Get the natural language string
        final_answer = generate_answer(user_question, db_result)
        
        # 4. Send to Slack
        respond(final_answer)
        
    except Exception as e:
        print(f"Error: {e}")
        respond("Sorry, I had trouble parsing that. Could you rephrase?")
    finally:
        db.close()
    

@app.event("message")
def handle_message(event,say,logger):
    if "bot_id" in event:
        return 

    if event.get("channel_type") == "im":
        user_text = event.get("text","")
        try:
            result = parse_agent.invoke({
            "raw_message":user_text,
            "slack_message_id":event["ts"],
            "channel_id":event["channel"]
            })
            reply = result.get("reply_message", "Expense logged successfully!")
            say(reply)
        except Exception as e:
            logger.error(f"An exception has occurred. Error: {e}")
            say("Oops, I ran into an issue parsing that expense.")

if __name__ == "__main__":
    handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
    handler.start()    
       

        
