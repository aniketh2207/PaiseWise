from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage

try:
    from backend.tools.llm_client import llm
except ModuleNotFoundError:
    from tools.llm_client import llm

intent_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are an intent classifier for a personal finance mobile application.
    Analyze the user's latest message and the conversation history, and classify the user's intent into exactly one of four categories:

    - 'query': If the user is asking a question about their spending, requesting a summary, breakdown, comparison, list, or report (e.g. "how much did I spend", "show food spend", "give me breakdown", "compare to last month").
    - 'log': If the user is trying to record a new expense, log a purchase, or add a transaction (e.g. "spent 200 on lunch", "put 100 for taxi", "log 500 for dinner").
    - 'followup': If the message is a short follow-up clarification or category selection in response to a previous question from the assistant (e.g. if the assistant asked "What category was the ₹500 spend?" and the user replies "shopping" or "travel").
    - 'conversational': If the message is casual chit-chat, a greeting, a thank you, or a general acknowledgment that does not involve logging or querying (e.g. "thanks", "hello", "ok", "cool", "bye", "good morning", "nice").

    Output ONLY one of these strings: 'query', 'log', 'followup', or 'conversational'. Do not write explanations, code blocks, or punctuation.
    """),
    ("placeholder", "{chat_history}"),
    ("human", "{message}")
])

intent_chain = intent_prompt | llm | StrOutputParser()

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

def classify_intent(message: str, history=None) -> str:
    """Classifies user message intent into 'query', 'log', 'followup', or 'conversational'."""
    chat_history = _format_history(history or [])
    result = intent_chain.invoke({
        "message": message,
        "chat_history": chat_history
    }).strip().lower()

    # Clean up output formatting if LLM includes quotes or symbols
    for s in ["'", '"', ".", "`"]:
        result = result.replace(s, "")

    result = result.strip()
    if result not in ["query", "log", "followup", "conversational"]:
        # Fallback to query if ambiguous
        return "query"
    return result

conversational_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are PaiseWise, a friendly personal finance assistant inside a mobile app.
    The user has sent a casual or conversational message (like a greeting, thank you, or acknowledgment).
    Respond naturally and warmly in 1-2 short sentences. Gently remind them that you can help log expenses or answer spending questions.
    Keep it concise — this is a mobile chat bubble.
    """),
    ("placeholder", "{chat_history}"),
    ("human", "{message}")
])
conversational_chain = conversational_prompt | llm | StrOutputParser()

def generate_conversational_reply(message: str, history=None) -> str:
    """Generates a natural conversational response for greetings, thanks, etc."""
    chat_history = _format_history(history or [])
    return conversational_chain.invoke({
        "message": message,
        "chat_history": chat_history
    })
