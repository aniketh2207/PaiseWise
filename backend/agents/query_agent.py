from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage

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
    - IMPORTANT: Always use the 'bank_transactions' table as the primary source of truth for spending queries (totals, breakdowns, comparisons). It contains the actual reconciled bank amounts. Only use 'slack_logs' if the user explicitly asks about their manual logs or logged reasons.
    - For bank_transactions, filter spending with type = 'debit'. Credits (type = 'credit') are incoming money.
    - To filter by month or year, use the 'month' and 'year' integer columns on bank_transactions (e.g., month = 7 AND year = 2026).
    - Use LOWER() for text comparisons to prevent case sensitivity issues.
    - All transactions are done in Rupees.
    """),
    ("placeholder", "{chat_history}"),
    ("human", "{question}")
])
sql_chain = sql_generation_prompt | llm | StrOutputParser()

response_formatting_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a helpful, premium personal finance assistant inside the PaiseWise mobile app.
    Take the user's original question and the raw SQL database result, and formulate a friendly, beautifully formatted response.
    
    Formatting Guidelines:
    - Use clean Markdown formatting.
    - Always use the Indian Rupee symbol (₹) for all currency values (e.g., ₹1,250 instead of 1250, Rs. 1250, or INR).
    - If there are lists or multiple rows of data, format them using clean markdown bullet points, or structured tables.
    - Organize the information logically with clear headings if necessary.
    - Translate raw database tuple formats (like `[(120.0,)]` or `[('Rent', 15000)]`) into clean, conversational language.
    - Do not show raw SQL terms, technical data structures, or code blocks in the output.
    - Keep it clear, readable, and perfectly suited for a mobile chat bubble.
    """),
    ("placeholder", "{chat_history}"),
    ("human", "Question: {question}\nSQL Result: {result}")
])
response_chain = response_formatting_prompt | llm | StrOutputParser()

def _format_history(history):
    formatted = []
    for msg in history:
        role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "")
        content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
        
        if role == "user":
            formatted.append(HumanMessage(content=content))
        elif role == "assistant":
            formatted.append(AIMessage(content=content))
    return formatted

def generate_sql(query: str, history=None) -> str:
    """Takes a user question and returns a raw SQL string."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    chat_history = _format_history(history or [])

    return sql_chain.invoke({
        "current_date": today_str,
        "chat_history": chat_history,
        "question": query
    }).strip()

def generate_answer(question: str, raw_sql_result: str, history=None) -> str:
    """Takes the question and the DB data, and returns a natural language string."""
    chat_history = _format_history(history or [])

    return response_chain.invoke({
        "question": question,
        "result": str(raw_sql_result),
        "chat_history": chat_history
    })
