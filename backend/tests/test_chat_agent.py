"""
Test suite for the PaiseWise LLM-based chat intent router.
Tests the classify_intent function from router_agent.py against
real Gemini API calls to verify correct routing of messages.
"""

import sys
import os

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.router_agent import classify_intent

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []

def run_test(test_name: str, message: str, history: list, expected_intents: list):
    """Run a single classification test and record the result."""
    intent = classify_intent(message, history)
    passed = intent in expected_intents
    status = PASS if passed else FAIL
    print(f"  {status}  {test_name}")
    print(f"         Message:  \"{message}\"")
    print(f"         Expected: {expected_intents}  |  Got: '{intent}'")
    if history:
        print(f"         History:  {len(history)} message(s)")
    print()
    results.append(passed)


def test_query_intents():
    """Test that spending questions are routed to 'query'."""
    print("=" * 60)
    print("TEST GROUP 1: Query Intent Classification")
    print("=" * 60)

    run_test(
        "Direct question with 'how'",
        "How much did I spend on food?",
        [],
        ["query"]
    )

    run_test(
        "Direct question with 'what'",
        "What was my biggest expense this month?",
        [],
        ["query"]
    )

    run_test(
        "Show command",
        "Show me my travel expenses",
        [],
        ["query"]
    )

    run_test(
        "Give command (previously failed with keywords)",
        "Give me a category breakdown",
        [
            {"role": "user", "content": "How much did I spend on food?"},
            {"role": "assistant", "content": "You spent ₹3,713 on food this month."}
        ],
        ["query"]
    )

    run_test(
        "Natural question with 'could'",
        "Could you tell me how much I spent yesterday?",
        [],
        ["query"]
    )

    run_test(
        "Question with question mark",
        "Total spending on entertainment?",
        [],
        ["query"]
    )


def test_log_intents():
    """Test that expense logging messages are routed to 'log'."""
    print("=" * 60)
    print("TEST GROUP 2: Log Intent Classification")
    print("=" * 60)

    run_test(
        "Simple expense log",
        "spent 200 on lunch",
        [],
        ["log"]
    )

    run_test(
        "Natural logging with 'put'",
        "Put down 120 for snacks",
        [],
        ["log"]
    )

    run_test(
        "Casual expense with merchant",
        "Zomato 350 for dinner",
        [],
        ["log"]
    )

    run_test(
        "Expense with 'log' verb",
        "Log 500 for taxi to airport",
        [],
        ["log"]
    )

    run_test(
        "Conversational expense log",
        "I just grabbed a coffee for 80",
        [],
        ["log"]
    )


def test_followup_intents():
    """Test that short follow-up replies are routed to 'followup'."""
    print("=" * 60)
    print("TEST GROUP 3: Follow-up Intent Classification")
    print("=" * 60)

    run_test(
        "Category follow-up after ambiguous log",
        "shopping",
        [
            {"role": "user", "content": "spent 500"},
            {"role": "assistant", "content": "Got ₹500 but not sure of the category. Reply with: food / travel / shopping etc."}
        ],
        ["followup", "log"]
    )

    run_test(
        "Yes confirmation follow-up",
        "yes",
        [
            {"role": "user", "content": "200 for auto"},
            {"role": "assistant", "content": "✅ ₹200 Travel/Auto/Cab | 'auto ride'. Is this correct?"}
        ],
        ["followup"]
    )

    run_test(
        "Thanks follow-up",
        "thanks",
        [
            {"role": "user", "content": "How much on food?"},
            {"role": "assistant", "content": "You spent ₹3,713 on food."}
        ],
        ["followup"]
    )


def test_edge_cases():
    """Test tricky edge cases that the old keyword router got wrong."""
    print("=" * 60)
    print("TEST GROUP 4: Edge Cases")
    print("=" * 60)

    run_test(
        "Ambiguous 'can you log' (should log, not query)",
        "Can you log 200 for lunch?",
        [],
        ["log"]
    )

    run_test(
        "Follow-up breakdown request (context-dependent query)",
        "breakdown by subcategory",
        [
            {"role": "user", "content": "How much did I spend on food?"},
            {"role": "assistant", "content": "You spent ₹3,713 on food this month."}
        ],
        ["query"]
    )

    run_test(
        "Single word 'food' after category prompt (follow-up)",
        "food",
        [
            {"role": "user", "content": "spent 300"},
            {"role": "assistant", "content": "Got ₹300 but not sure of the category. Reply with: food / travel / shopping etc."}
        ],
        ["followup", "log"]
    )


if __name__ == "__main__":
    print()
    print("[TEST] PaiseWise Chat Router Agent - Test Suite")
    print("=" * 60)
    print()

    test_query_intents()
    test_log_intents()
    test_followup_intents()
    test_edge_cases()

    # Summary
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print("=" * 60)
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\n[WARNING] Some tests failed. Review the output above.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
