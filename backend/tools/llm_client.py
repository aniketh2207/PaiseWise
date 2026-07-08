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
    amount:float = Field(description="The transaction amount. Always positive.")
    category:str = Field(description="One of: Food, Travel, Shopping, Utilities, Entertainment, Education, Health, Transfer, Other")
    subcategory: str = Field(description="Valid subcategory mapping to the main category.")
    reason: str = Field(description="Short clean description, max 8 words.")
    merchant: Optional[str] = Field(None, description="Merchant name if explicitly mentioned, else null.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")

# initialize LLM 
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.2,
    api_key=settings.GEMINI_API_KEY
)

expense_parser = llm.with_structured_output(ExpenseLog)   

system_prompt = """
You are an expense parser for a college student in India. 
Parse their casual Slack message into a structured expense log.

    Output schema:
{{
"amount": <float, positive>,
"category": <one of the valid categories below>,
"subcategory": <valid subcategory for that category>,
"reason": <short clean description, max 8 words>,
"merchant": <merchant name if explicitly mentioned, else null>,
}}
"confidence": <float 0.0-1.0>


Valid categories and subcategories:
{valid_categories}

Rules:
- Amount is always positive regardless of direction.
- If the message mentions splitting with someone, category = Transfer/Split.
- Canteen, dhaba, mess, tiffin -> Food/Canteen.
- Auto, ola, uber, cab, rick -> Travel/Auto/Cab.
- If amount is missing, confidence = 0.0.
- College-specific terms: BITS, Pilani, mess, canteen, hostel -> context clues.
- Common abbreviations: auto -> Auto/Cab, zom -> Zomato, sw -> Swiggy, meds -> Medicine.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{slack_message}")
])

parsing_chain = prompt_template|expense_parser

def parse_slack_expense(message: str) -> ExpenseLog:
    """Parse a slack message into an expense log"""
    try:
        categories_str = get_valid_categories_str()
        result = parsing_chain.invoke({
            "slack_message": message,
            "valid_categories": categories_str
        })
        return result
    except Exception as e:
        print(f"Error while parsing the message: {e}")
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
        You are summarizing a college student's monthly expenses in India.
        Write a short, friendly 3-4 line summary based on this data.
        Mention total spent, biggest category, and one useful observation.
        Be conversational, not robotic. Use ₹ symbol.

        Data:
        Month: {aggregates['month']}/{aggregates['year']}
        Total Spent: ₹{aggregates['total_spent']:.0f}
        Transactions Logged: {aggregates['transaction_count']}
        Top Merchant: {aggregates.get('top_merchant', 'N/A')}
        By Category:
        {category_lines}
"""
    result = llm.invoke(prompt)
    return result.content


    
if __name__ == "__main__":
    test_msg = "80 canteen lunch vada pav"
    parsed_expense = parse_slack_expense(test_msg)
    if parsed_expense:
        print(f"Parsed Amount: Rs. {parsed_expense.amount}")
        print(f"Category: {parsed_expense.category}/{parsed_expense.subcategory}")
        print(f"Reason: {parsed_expense.reason}")
        print(f"Confidence: {parsed_expense.confidence}")
