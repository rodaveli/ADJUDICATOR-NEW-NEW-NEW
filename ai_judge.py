import openai
import os
from typing import List
from schemas import Argument, Judgement, Appeal

client = OpenAI()
# client.api_key = os.getenv("OPENAI_API_KEY")

# if not client.api_key:
#     raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

def get_ai_judgement(arguments: List[Argument], appeal: Appeal = None):
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
        # Remove id and session_id as they are not part of the API response
        judgement_dict = judgement.model_dump(exclude={'id', 'session_id'})
        return judgement_dict

    except Exception as e:
        print(f"Error in get_ai_judgement: {str(e)}")
        return {
            "content": f"An error occurred: {str(e)}",
            "winner": "Argument 1",  # Default to Argument 1 in case of errors
            "winning_argument": "Unable to determine",
            "loser": "Argument 2",
            "losing_argument": "Unable to determine",
            "reasoning": f"An error occurred: {str(e)}"
        }

# # Example usage
if __name__ == "__main__":
    test_arguments = [
        Argument(id=1, content="Cowboys have 5 superbowls, and thus are better than the eagles.", session_id=1),
        Argument(id=2, content="Eagles have a more recent superbowl and tons more playoff wins in this millennium", session_id=1)
    ]
    result = get_ai_judgement(test_arguments)
    print(result)