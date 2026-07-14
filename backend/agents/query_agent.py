from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

try:
    from backend.tools.llm_client import llm
except ModuleNotFoundError:
    from tools.llm_client import llm

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
    - matched_txn_id (INTEGER) -> Foreign key referencing bank_transactions.id (if reconciled/matched)

    The database also contains a table named 'bank_transactions' with this schema:
    - id (INTEGER, primary key)
    - date (DATE) -> The date of the transaction
    - time (TIME) -> The time of the transaction
    - amount (FLOAT) -> The transaction amount
    - type (VARCHAR) -> 'debit' (outgoing money/spent) or 'credit' (incoming money/received)
    - upi_id (VARCHAR) -> UPI ID involved in the transaction
    - upi_name (VARCHAR) -> UPI Name of the party
    - raw_description (VARCHAR) -> Raw bank transaction text
    - is_business_upi (BOOLEAN)
    - reconcile_status (VARCHAR) -> 'matched', 'auto_categorized', 'needs_annotation', or 'user_annotated'
    - category (VARCHAR) -> e.g., 'Food', 'Travel', 'Shopping', 'Utilities', 'Entertainment', 'Health'
    - subcategory (VARCHAR) -> e.g., 'Delivery', 'Auto/Cab', 'Medicine'
    - reason (VARCHAR)
    - slack_log_id (INTEGER) -> References slack_logs.id (if reconciled/matched)
    - needs_annotation (BOOLEAN)
    - notes (VARCHAR)
    - month (INTEGER)
    - year (INTEGER)

    Rules:
    - Today's date is: {current_date}
    - To filter by month or year, use PostgreSQL EXTRACT, e.g., EXTRACT(MONTH FROM log_date) = 6 AND EXTRACT(YEAR FROM log_date) = 2026. For bank transactions, you can also use the 'month' and 'year' integer columns or extract from the 'date' column.
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
