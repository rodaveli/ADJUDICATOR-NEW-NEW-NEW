import openai
import traceback
import os
from typing import List
from schemas import Argument, Judgement, Appeal

client = openai.OpenAI()
# client.api_key = os.getenv("OPENAI_API_KEY")
#test
# if not client.api_key:
#     raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

def get_ai_judgement(arguments: List[Argument], appeal: Appeal | None = None):
    prompt = """You are an AI judge for a debate app. Your task is to evaluate arguments and always choose a winner, even in subjective cases. Focus on the relative strength of the arguments rather than the absolute truth of the claims. Make your judgement fun and engaging. Respond in JSON format.

    Arguments:
    """
    print("DEBUG PRINT, CONTENT OF arguments IS: ", arguments)
    for i, arg in enumerate(arguments, 1):
        prompt += f"Argument {i} by {arg.username}:\n{arg.content}\n\n"  # Include username in prompt
        print("DEBUG PRINT, arg.username and rg.content are: ", arg.username, arg.content)

    if appeal:
        prompt += f"Appeal:\n{appeal.content}\n\n"

    prompt += """Please provide your judgement, including the content (full judgement text), winner (the username of the winner), winning argument, loser (the username of the loser), losing argument, and reasoning. Remember:
    1. Always choose a winner.
    2. Even if the topic is subjective, make a definitive choice based on argument quality."""

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are an AI judge for a debate app. Always choose a winner."},
                {"role": "user", "content": prompt}
            ],
            response_format=Judgement
        )

        judgement = completion.choices[0].message.parsed
        judgement_dict = judgement.model_dump(exclude={'id', 'session_id'})

        return judgement_dict

    except Exception as e:
        error_message = f"Error in get_ai_judgement: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {
            "content": f"An error occurred: {str(e)}",
            "winner": "Unknown",
            "winning_argument": "Unable to determine",
            "loser": "Unknown",
            "losing_argument": "Unable to determine",
            "reasoning": f"An error occurred: {str(e)}"
        }
