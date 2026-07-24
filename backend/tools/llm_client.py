import os
from pydantic import BaseModel, Field
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import io


try:
    from backend.config import settings
    from backend.database.db import SessionLocal
    from backend.database.models import Category
except ModuleNotFoundError:
    from config import settings
    from database.db import SessionLocal
    from database.models import Category

def get_valid_categories_str() -> str:
    db = SessionLocal()
    try:
        categories = db.query(Category).all()
        # Group by parent (category) to get child names (subcategories)
        grouped = {}
        for cat in categories:
            parent = cat.parent or "Other"
            grouped.setdefault(parent, []).append(cat.name)
        
        # Format as string lines: "- Parent: Child1, Child2, ..."
        lines = []
        for parent, subcategories in grouped.items():
            lines.append(f"- {parent}: {', '.join(subcategories)}")
        return "\n".join(lines)
    finally:
        db.close()

class ExpenseLog(BaseModel):
    amount: float = Field(description="The transaction amount. Always positive.")
    category: str = Field(description="One of: Food, Travel, Shopping, Utilities, Entertainment, Education, Health, Transfer, Other")
    subcategory: str = Field(description="Valid subcategory mapping to the main category.")
    reason: str = Field(description="Short clean description, max 8 words.")
    merchant: Optional[str] = Field(None, description="Merchant name if explicitly mentioned, else null.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")

class ExpenseLogList(BaseModel):
    expenses: list[ExpenseLog] = Field(description="List of one or more parsed expense logs found in the input message.")

# initialize LLM 
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.2,
    api_key=settings.GEMINI_API_KEY
)

expense_parser = llm.with_structured_output(ExpenseLogList)   

system_prompt = """
You are an expense parser for a college student in India. 
Parse their casual message or log into a structured list of expense logs.

A message may contain a SINGLE transaction or MULTIPLE distinct transactions. Multiple transactions are distinguished using conjunctions like "and", "&", or punctuation like commas (","), semicolons, or newlines (e.g., "100 for auto and 50 for chai", "200 for books, 300 for mess, and 50 for rickshaw").
You MUST parse EVERY distinct transaction into its own individual item in the `expenses` list.

Output schema:
A list of expense logs under the key `expenses`:
[
  {{
    "amount": <float, positive>,
    "category": <one of the valid categories below>,
    "subcategory": <valid subcategory for that category>,
    "reason": <short clean description, max 8 words>,
    "merchant": <merchant name if explicitly mentioned, else null>,
    "confidence": <float 0.0-1.0>
  }}
]

Valid categories and subcategories:
{valid_categories}

Rules:
- Parse all separate transactions distinguished by "and", ",", "&", or line breaks into individual ExpenseLog objects in the `expenses` array.
- Amount is always positive regardless of direction.
- If the message mentions splitting with someone, category = Transfer/Split.
- Canteen, dhaba, mess, tiffin -> Food/Canteen.
- Auto, ola, uber, cab, rick -> Travel/Auto/Cab.
- If amount is missing for a transaction, set confidence = 0.0 for that item.
- College-specific terms: BITS, Pilani, mess, canteen, hostel -> context clues.
- Common abbreviations: auto -> Auto/Cab, zom -> Zomato, sw -> Swiggy, meds -> Medicine.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{slack_message}")
])

parsing_chain = prompt_template|expense_parser

def parse_slack_expense(message: str) -> Optional[ExpenseLogList]:
    """Parse a slack message into a list of expense logs"""
    try:
        categories_str = get_valid_categories_str()
        print(f"\n--- [LLM Client: Parsing Expense] ---")
        print(f"Input Message: '{message}'")
        result = parsing_chain.invoke({
            "slack_message": message,
            "valid_categories": categories_str
        })
        print(f"Parsed Expense Log: {result}\n------------------------------------")
        return result
    except Exception as e:
        print(f"[LLM Client Error] Error while parsing message '{message}': {e}")
        return None


def generate_summary(aggregates: dict) -> str:
    category_lines = "\n".join(
        f"  {cat}: ₹{amount:.0f}"
        for cat, amount in sorted(
            aggregates["by_category"].items(),
            key=lambda x: x[1],
            reverse=True
        )
    )

    prompt = f"""
        You are a concerned, strict yet intelligent and reasonable Indian parent reviewing your college student child's monthly expense report.
        Write a short, parental 3-4 line response balancing strictness with practical, wise advice based on this data.
        
        Rules:
        - Maintain your parental authority: be disappointed with wasteful/excessive spends (like eating out at restaurants, buying desserts repeatedly, or streaming subscriptions).
        - Be reasonable and intelligent about necessary expenses (like cycle repairs, medicine, books, or utilities).
        - Read the "Detailed Transaction List" below (which contains descriptions/reasons, e.g. "cycle repair") to comment on specific things intelligently. For example, if they spend ₹3,000 on "cycle repair", acknowledge that repairing their cycle is a smart choice to avoid high cab fares, but lecture them to bargain or make sure the mechanic didn't cheat them.
        - Give smart financial advice rather than blindly shouting. If they spend too much on restaurants, suggest eating at the canteen/mess or packing snacks.
        - Use relatable Telugu parenting phrases in actual Telugu script characters (like "బాబు" / "నాన్న", "డబ్బు చెట్లకు కాస్తుందా?" [Does money grow on trees?], "వృథా ఖర్చులు" [wasteful expenses], etc.) mixed directly into the English response. Write mostly in English but blend these Telugu script phrases in naturally. Use the ₹ symbol.

        Data:
        Month: {aggregates['month']}/{aggregates['year']}
        Total Spent: ₹{aggregates['total_spent']:.0f}
        Transactions Logged: {aggregates['transaction_count']}
        Top Merchant: {aggregates.get('top_merchant', 'N/A')}
        By Category (and Subcategory):
        {category_lines}

        Detailed Transaction List (reason/description, amount, category):
        {aggregates.get('transaction_list', 'N/A')}
"""
    result = llm.invoke(prompt)
    if isinstance(result.content, list):
        return "".join(block.get("text", "") for block in result.content if isinstance(block, dict) and block.get("type") == "text")
    return str(result.content)


def generate_parent_report_summary(report_data: dict) -> str:
    category_lines = "\n".join(
        f"  - {cat}: ₹{amount:.2f}"
        for cat, amount in sorted(
            report_data["by_category"].items(),
            key=lambda x: x[1],
            reverse=True
        )
    )

    prompt = f"""
        You are a helpful, professional personal finance analyst writing a monthly summary report for a college student's parent.
        Your goal is to provide a clear, concise, and structured overview (3-4 sentences/lines) of how their child has spent their money during the month.
        
        Guidelines:
        - Address the parent directly. Do not speak to or lecture the student (e.g. say "Your child spent..." rather than "You spent...").
        - Keep the tone respectful, analytical, and reassuring. Avoid overly harsh parenting scolding, but point out areas of high spend objectively.
        - Comment on key spending categories, total outgoing expenses, and any significant purchases from the transaction list.
        - Highlight if the child is maintaining a reasonable budget. Use the ₹ symbol for currency.
        
        Report Data:
        - Month: {report_data['month']}/{report_data['year']}
        - Total Outgoing (Debits): ₹{report_data['total_spent']:.2f}
        - Total Incoming (Credits): ₹{report_data['total_credits']:.2f}
        - Category Breakdown:
        {category_lines}
        
        Significant/Top Expenses:
        {report_data.get('transaction_list', 'None logged.')}
"""
    result = llm.invoke(prompt)
    if isinstance(result.content, list):
        return "".join(block.get("text", "") for block in result.content if isinstance(block, dict) and block.get("type") == "text")
    return str(result.content)


if __name__ == "__main__":
    test_msg = "80 canteen lunch vada pav"
    parsed_expense = parse_slack_expense(test_msg)
    if parsed_expense:
        print(f"Parsed Amount: Rs. {parsed_expense.amount}")
        print(f"Category: {parsed_expense.category}/{parsed_expense.subcategory}")
        print(f"Reason: {parsed_expense.reason}")
        print(f"Confidence: {parsed_expense.confidence}")
