import logging
import openai  # replaced Groq

openai.api_key = "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"  # set provided key

def evaluate_decision_history(decision_history):
    try:
        # Set model for OpenAI
        model_to_use = "gpt-3.5-turbo"
        messages = [
        #     {
        #     "role": "system",
        #     "content": (
        #         "You are trying to find strong trends in this decision making history."
        #     )
        # },
            {
                "role": "user",
                "content": (
                    f"Here is my decision history:\n{decision_history}\n\n"
                    "Provide a very concise and specific summary of the trends in my decision making history. "
                    "For example, if I have compromised on salary for location, then say accepted a lower salary for a better location. "
                    "Accept ML jobs despite not having a lot of experience in ML. "
                    "Rejects jobs that are unclear about the role or have a lot of ambiguity. "
                    # "Please be as detailed as possible."
                ),
            },
        ]
        chat_completion = openai.ChatCompletion.create(
            model=model_to_use,
            messages=messages,
            temperature=0.0,
        )
        evaluation = chat_completion.choices[0].message.content
        logging.debug(f"AI Evaluation (OpenAI):\n{evaluation}")
        return evaluation
    except Exception as e:
        logging.error(f"Error during OpenAI evaluation: {e}", exc_info=True)
        return f"Error during AI evaluation: {e}\n\nCompatibility score out of 100: 0"
