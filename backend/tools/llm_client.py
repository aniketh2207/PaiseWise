import os
from pydantic import BaseModel, Field
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings

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
- Food: Delivery, Restaurant, Grocery, Canteen
- Travel: Auto/Cab, Train, Flight, Fuel, Bus
- Shopping: Clothes, Electronics, Stationery, General
- Utilities: Phone, Internet, Electricity
- Entertainment: Movies, OTT, Games, Events
- Education: Books, Courses, Fees
- Health: Medicine, Doctor
- Transfer: Sent to Friend, Received, Split
- Other: Miscellaneous

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
        result = parsing_chain.invoke({"slack_message": message})
        return result
    except Exception as e:
        print(f"Error while parsing the message{e}")
        return None

if __name__ == "__main__":
    test_msg = "80 canteen lunch vada pav"
    parsed_expense = parse_slack_expense(test_msg)
    if parsed_expense:
        print(f"Parsed Amount: ₹{parsed_expense.amount}")
        print(f"Category: {parsed_expense.category}/{parsed_expense.subcategory}")
        print(f"Reason: {parsed_expense.reason}")
        print(f"Confidence: {parsed_expense.confidence}")
