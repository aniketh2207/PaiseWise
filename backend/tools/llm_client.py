import os
from pydantic import BaseModel, Field
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime


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

sql_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are an expert SQL generator for a personal finance application.
    Given a user's question, output ONLY a valid PostgreSQL query that answers the question.
    Do not wrap the text in markdown code blocks (like ```sql), do not write explanations, just return the raw SQL string.

    The database contains a table named 'slack_logs' with this schema:
    - id (INTEGER, primary key)
    - amount (FLOAT) -> All amounts here are money spent
    - category (VARCHAR) -> e.g., 'Food', 'Travel', 'Shopping', 'Utilities', 'Entertainment', 'Health'
    - subcategory (VARCHAR) -> e.g., 'Delivery', 'Auto/Cab', 'Medicine'
    - reason (VARCHAR) -> The user's typed reason
    - merchant (VARCHAR)
    - log_date (DATE) -> The date the expense occurred

    Rules:
    - Today's date is: {current_date}
    - To filter by month or year, use PostgreSQL EXTRACT, e.g., EXTRACT(MONTH FROM log_date) = 6 AND EXTRACT(YEAR FROM log_date) = 2026.
    - Use LOWER() for text comparisons to prevent case sensitivity issues.
    - All transactions are done in Rupees.
    """),
    ("human", "{question}")
])
sql_chain = sql_generation_prompt | llm | StrOutputParser()

response_formatting_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a helpful personal finance assistant. 
    Take the user's original question and the raw SQL database result, and formulate a friendly, concise response.
    Keep it short and straight to the point for a Slack message.
    """),
    ("human", "Question: {question}\nSQL Result: {result}")
])
response_chain = response_formatting_prompt | llm | StrOutputParser()

def generate_sql(query: str) -> str:
    """Takes a user question and returns a raw SQL string."""
    today_str = datetime.now().strftime("%Y-%m-%d")

    return sql_chain.invoke({
        "current_date": today_str,
        "question": query
    }).strip()

def generate_answer(question: str, raw_sql_result: str) -> str:
    """Takes the question and the DB data, and returns a natural language string."""

    return response_chain.invoke({
        "question": question,
        "result": str(raw_sql_result)
    })
    
if __name__ == "__main__":
    test_msg = "80 canteen lunch vada pav"
    parsed_expense = parse_slack_expense(test_msg)
    if parsed_expense:
        print(f"Parsed Amount: ₹{parsed_expense.amount}")
        print(f"Category: {parsed_expense.category}/{parsed_expense.subcategory}")
        print(f"Reason: {parsed_expense.reason}")
        print(f"Confidence: {parsed_expense.confidence}")
