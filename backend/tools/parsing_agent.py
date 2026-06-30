from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

try:
    from backend.tools.llm_client import parse_slack_expense, ExpenseLog
    from backend.database.db import SessionLocal
    from backend.database.models import SlackLog
except ModuleNotFoundError:
    from tools.llm_client import parse_slack_expense, ExpenseLog
    from database.db import SessionLocal
    from database.models import SlackLog

class ParsingState(TypedDict):
    raw_message : str
    slack_message_id: str
    channel_id : str
    parsed_expense: Optional[ExpenseLog]
    is_valid:bool
    reply_message:str
    log_date:str

def parse_text(state:ParsingState) ->ParsingState:
     # Node 1 - Parses the raw text from the slack bot
    parsed_expense = parse_slack_expense(state['raw_message'])
    return {
        "parsed_expense":parsed_expense
    }

def validate_parse(state:ParsingState)->ParsingState:
    expense = state.get("parsed_expense")

    if not expense:
        return {
            "is_valid":False,
            "reply_message": "Sorry, I coulcn't understand the message from the slack bot"
        }
    if expense.amount <= 0 or expense.confidence < 0.6:
        reply = f"Got ₹{expense.amount if expense else 'unknown'} but not sure of the category. Reply with: food / travel / shopping etc."
        return {
            "is_valid":False,
            "reply_message":reply
        }

    return {
        "is_valid" : True
    }

def slack_save_log(state:ParsingState)->ParsingState:
    # Node 3 - Saves into the database
    db = SessionLocal()
    try :
        expense = state.get("parsed_expense")
        if expense:
            # Safely handle the log_date
            log_date_val = state.get("log_date")
            from datetime import date, datetime
            if isinstance(log_date_val, str):
                try:
                    log_date = datetime.strptime(log_date_val, "%Y-%m-%d").date()
                except ValueError:
                    log_date = date.today()
            elif isinstance(log_date_val, (date, datetime)):
                log_date = log_date_val
            else:
                log_date = date.today()

            log = SlackLog(
                slack_message_id=state["slack_message_id"],
                raw_message=state["raw_message"],
                amount=expense.amount,
                category=expense.category,
                subcategory=expense.subcategory,
                reason=expense.reason,
                merchant=expense.merchant if expense.merchant else "Not a merchant or UPI name",
                log_date=log_date,
                channel_id=state["channel_id"],
                parse_confidence=expense.confidence,
            )
            db.add(log)
            db.commit()
    finally:
        db.close()


def confirm_to_user(state:ParsingState)->ParsingState:
    #Node 4 - Confirmation to the user
    expense = state.get("parsed_expense")
    reply = f"✅ ₹{expense.amount} {expense.category}/{expense.subcategory} | '{expense.reason}'"
    return {"reply_message": reply}

def route_condition(state:ParsingState):
    if not state['is_valid']:
        return "ask_confirmation"
    else:
        return "slack_save_log"

workflow = StateGraph(ParsingState)
workflow.add_node("parse_message",parse_text)
workflow.add_node("validate_parse",validate_parse)
workflow.add_node("slack_save_log",slack_save_log)
workflow.add_node("ask_confirmation",lambda state:state)
workflow.add_node("confirm_to_user",confirm_to_user)

workflow.set_entry_point("parse_message")
workflow.add_edge("parse_message","validate_parse")
workflow.add_conditional_edges("validate_parse",route_condition)

workflow.add_edge("slack_save_log","confirm_to_user")


workflow.add_edge("ask_confirmation",END)
workflow.add_edge("confirm_to_user",END)

parse_agent=workflow.compile()

if __name__ == "__main__":
    # Ensure database tables exist
    try:
        from backend.database.db import init_db
    except ModuleNotFoundError:
        from database.db import init_db
    init_db()

    # Invoke the agent with all required state fields
    result = parse_agent.invoke({
        "raw_message": "120 paid for auto", 
        "slack_message_id": "123", 
        "channel_id": "C1",
        "log_date": "2026-06-30"  # Added log_date
    })
    print(result)





