import logging
from groq import Groq
from config import GROQ_API_KEY, user_info

def evaluate_job_fit(job_details, user_profile, decision_history):
    groq_api_key = GROQ_API_KEY
    if not groq_api_key:
        logging.error("Error: Groq API key not found. Set the GROQ_API_KEY environment variable or provide it directly.")
        return "Error: Groq API key not configured."
    try:
        client = Groq(api_key=groq_api_key)
        model_to_use = "llama3-8b-8192"
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an expert job fit evaluator. Your goal is to assess how well a job posting matches a user's profile and preferences, considering their past decisions on similar jobs.\n\n"
                    f"**Input:**\n"
                    f"1.  **User Profile:** Contains skills, degree, salary/location expectations.\n"
                    f"2.  **Recent User Decisions:** A list of jobs the user recently accepted or rejected, including the evaluation text they saw for that job. Use this history to understand the user's implicit preferences and refine your assessment.\n"
                    f"3.  **Job Details:** The details of the current job posting to evaluate.\n\n"
                    f"**Output Format:**\n"
                    f"Generate concise bullet points highlighting key aspects of the job's fit, followed by a compatibility score.\n"
                    f"Use the following structure:\n\n"
                    f"• Mention strong matches in programming languages (e.g., 'Strong matches in programming languages, including Python, SQL').\n"
                    f"• Comment on degree relevance (e.g., 'Strong background in Computer Engineering which is likely relevant to the Software Engineer role').\n"
                    f"• If salary is provided and significantly lower than expectation, state it clearly (e.g., 'The listed salary of $X is significantly lower than the user's expectation of $Y.').\n"
                    f"• If location is provided and significantly different, state it clearly (e.g., 'The listed location of [City, State] is significantly different from the user's expectation of [Expected Location].').\n"
                    f"• **Crucially, incorporate insights from the user's decision history.** If the current job resembles previously rejected jobs (based on the evaluation text shown), mention why it might also be a poor fit and adjust the score down. If it resembles accepted jobs, highlight the similarities and adjust the score up.\n"
                    f"• Conclude with the compatibility score on a new line: 'Compatibility score out of 100: [score]'\n\n"
                    f"**Constraints:**\n"
                    f"- Be concise and factual.\n"
                    f"- Do not add introductory phrases like 'Here are the bullet points:'.\n"
                    f"- Do not add justifications like 'which is also mentioned in the job description'.\n"
                    f"- Base the score on the overall fit, considering profile match AND decision history patterns."
                )
            },
            {
                "role": "user",
                "content": (
                    f"User Profile: {user_profile}\n"
                    f"Recent User Decisions: {decision_history}\n" # Format the list nicely
                    f"Evaluate the fit of the following job based on the user profile AND their recent decisions: {job_details}\n"
                    f"Provide reasoning and a 'Compatibility score out of 100:' line."
                )
            }
        ]
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_to_use,
        )
        evaluation = chat_completion.choices[0].message.content
        logging.debug(f"AI Evaluation (Groq):\n{evaluation}")
        return evaluation
    except Exception as e:
        logging.error(f"Error during Groq evaluation: {e}", exc_info=True)
        return f"Error during AI evaluation: {e}\n\nCompatibility score out of 100: 0"
