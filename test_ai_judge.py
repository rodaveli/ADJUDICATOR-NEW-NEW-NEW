import openai
import traceback
import os
from typing import List
from schemas import Argument, Judgement, Appeal

client = openai.OpenAI()
# client.api_key = os.getenv("OPENAI_API_KEY")

# if not client.api_key:
#     raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

def get_ai_judgement(arguments: List[Argument], appeal: Appeal | None = None):
    prompt = """You are an AI judge for a debate app. Your task is to evaluate arguments and always choose a winner, even in subjective cases. Focus on the relative strength of the arguments rather than the absolute truth of the claims. Make your judgement fun and engaging. Respond in JSON format.

Arguments:
"""

    for i, arg in enumerate(arguments, 1):
        prompt += f"Argument {i}:\n{arg.content}\n\n"

    if appeal:
        prompt += f"Appeal:\n{appeal.content}\n\n"

    prompt += """Please provide your judgement, including the content (full judgement text), winner, winning argument, loser, losing argument, and reasoning. Remember:
1. Always choose a winner (either 'Argument 1' or 'Argument 2').
2. Even if the topic is subjective, make a definitive choice based on argument quality."""

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",  # Use the appropriate model version
            messages=[
                {"role": "system", "content": "You are an AI judge for a debate app. Always choose a winner."},
                {"role": "user", "content": prompt}
            ],
            response_format=Judgement
        )

        judgement = completion.choices[0].message.parsed
        judgement_dict = judgement.model_dump(exclude={'id', 'session_id'})

        # Add these lines to get the usernames
        # winning_username = next((arg.username for arg in arguments if arg.content == judgement_dict['winning_argument']), "Unknown")
        # losing_username = next((arg.username for arg in arguments if arg.content == judgement_dict['losing_argument']), "Unknown")

        # judgement_dict['winning_username'] = winning_username
        # judgement_dict['losing_username'] = losing_username

        winning_user_id = next((arg.user_id for arg in arguments if arg.content == judgement_dict['winning_argument']), "Unknown")
        losing_user_id = next((arg.user_id for arg in arguments if arg.content == judgement_dict['losing_argument']), "Unknown")

        judgement_dict['winning_user_id'] = winning_user_id
        judgement_dict['losing_user_id'] = losing_user_id

        return judgement_dict

    except Exception as e:
        error_message = f"Error in get_ai_judgement: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {
            "content": f"An error occurred: {str(e)}",
            "winner": "Argument 1",  # Default to Argument 1 in case of errors
            "winning_argument": "Unable to determine",
            "winning_username": "Unknown",
            "loser": "Argument 2",
            "losing_argument": "Unable to determine",
            "losing_username": "Unknown",
            "reasoning": f"An error occurred: {str(e)}"
        }

# # Example usage
if __name__ == "__main__":
    # Test case 1: Basic argument comparison
    test_arguments1 = [
        Argument(id=1, content="Cowboys have 5 superbowls, and thus are better than the eagles.", user_id="user1", session_id=1),
        Argument(id=2, content="Eagles have a more recent superbowl and tons more playoff wins in this millennium", user_id="user2", session_id=1)
    ]
    print("Test Case 1: Basic argument comparison")
    result1 = get_ai_judgement(test_arguments1)
    print(result1)
    print("\n")

    # Test case 2: Single argument (edge case)
    test_arguments2 = [
        Argument(id=1, content="The Earth is flat because it looks flat from the ground.", user_id="user3", session_id=2)
    ]
    print("Test Case 2: Single argument (edge case)")
    result2 = get_ai_judgement(test_arguments2)
    print(result2)
    print("\n")

    # Test case 3: Three arguments (edge case)
    test_arguments3 = [
        Argument(id=1, content="Coffee is the best morning drink.", user_id="user4", session_id=3),
        Argument(id=2, content="Tea is superior to coffee in every way.", user_id="user5", session_id=3),
        Argument(id=3, content="Water is the healthiest and most essential morning drink.", user_id="user6", session_id=3)
    ]
    print("Test Case 3: Three arguments (edge case)")
    result3 = get_ai_judgement(test_arguments3)
    print(result3)
    print("\n")

    # Test case 4: Arguments with appeal
    test_arguments4 = [
        Argument(id=1, content="Pineapple belongs on pizza because it adds a unique sweet and tangy flavor.", user_id="user7", session_id=4),
        Argument(id=2, content="Pineapple should never be on pizza as it ruins the traditional Italian flavors.", user_id="user8", session_id=4)
    ]
    test_appeal = Appeal(id=1, content="I appeal the decision because pineapple on pizza is a matter of personal taste and shouldn't be judged objectively.", user_id="user9", session_id=4)
    print("Test Case 4: Arguments with appeal")
    result4 = get_ai_judgement(test_arguments4, test_appeal)
    print(result4)
