import logging
import openai
from src.utils.config import user_info
from src.utils.constants import co_op_averages
import os
from dotenv import load_dotenv

# Set OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def evaluate_job_fit(job_details, user_profile, decision_history_evaluation):
    try:
        # Set model for OpenAI
        model_to_use = "gpt-3.5-turbo"
        messages = [
            {
            "role": "system",
            "content": (
                "You are a brutally honest and no-nonsense co-op advisor, helping me choose which jobs to apply to. Don't sugarcoat anything. Be direct, realistic, and critical as needed. Avoid flattery. "
                "Your goal is to deliver a practical, harsh assessment of how well a job posting matches my profile and preferences, incorporating insights from my past decisions. "
                "Moreover, I am trying to find the best possible job for me, so if I seem overqualfiied for a job then it is not a good fit for me. Also assume that I am not trying to switch to a completely different field, so if the job is in a different field then it is not a good fit for me. "
                "Ignore soft skils"
                # "If the co op duration is longer than what I am looking for, then it is not a good fit for me. "
                # "**Input:**\n"
                # "1. **My Profile:** Contains skills, degree, salary, and location expectations.\n"
                # "2. **My Recent Decisions:** A list of jobs that I recently accepted or rejected including their evaluation texts. Use them to infer my implicit preferences.\n"
                # "3. **Job Details:** Specifics of the current job posting to evaluate.\n\n"
                "**Output Format:**\n"
                "• **Crucially, incorporate insights from my decision history.** If this job resembles previously rejected positions, indicate why it might be a poor fit and reduce the score. Conversely, if it resembles accepted roles, note the similarity and raise the score.\n"
                "• If a key qualification is missing from my profile but implied by my work experience, recommend considering its inclusion (e.g., 'Consider adding [Technology] if you worked with it during your time as a [Role] at [Company]', but only if there is a very strong chance of it being true).\n"
                " - Only suggest adding skills that I am very likely to have, based on my work, education, or other experiences and ALWAYS include which experience it is based on.\n" 
                "Example of a good response:\n"
                "• Strong matches in skills and qualifications:\n"
                "  - Your experience with Python, including scientific software development tools, aligns well with the requirement for Python in this role.\n"
                "  - Familiarity with neural networks, Linux environments, and containerized applications like Docker matches the job's needs.\n"
                "  - Your background in software development and working across tech stacks is relevant to the software development responsibilities outlined.\n\n"
                " • Missing qualifications:\n"
                "  - Lack of direct experience with modern website development frameworks like React.js, machine learning, and image processing standards might be a gap.\n\n"
                # "• The listed location in London, Ontario, differs from your desired location in the USA.\n\n"
                " - Missing qualifications are ones listed in the job description but not in my profile.\n"
                # " • The listed salary of $25/hour is significantly lower than your desired salary of $40/hour CAD.\n\n"
                # " or • The salary is not specified.\n\n"
                # "• The job requires a cover letter, which is not something you want to do.\n\n"
                # "• The job is a startup, which you are not interested in.\n\n"
                "• The job requires a 4-month co-op, which is what you are looking for.\n\n"
                "• Consider adding 'TensorFlow' to your profile, as you likely worked with it during your time as a [Role] at [Company].\n\n"
                # compromise on salary for location
                "• This might be a job that you would be interested in, given your history of [trend from decision history evaluation].\n\n"
                "- Only include the following if it actually applies:\n"                
                f"• End with a new line: 'Compatibility score out of 100: X, Salary in CAD: Y, Category: Z'\n\n"
                "-Don't include terms such as 'intern' or 'assistant' in the category.\n"
                # f" - NEVER put 'not specified' for salary, if the job details says 'Students are paid salary based on their current co-op term', then refer to {co_op_averages}.\n\n"
                "- The score should be calculated as follows:\n"
                "  - 50 points allocated to the skills, qualifications, and industry match.\n"
                # "  - 15 points for salary expectations.\n"
                # "  - 15 points for location.\n"
                "  - 10 points for the duration of the co-op.\n"
                "  - 40 points for decision history if applicable.\n\n"
                " - formatted as 'Compatibility score out of 100: X, Salary in CAD: Y, Category: Z'\n\n"

                # "- Be concise and factual.\n"
                # "- Do not use introductory phrases like 'Here are the bullet points:'.\n"
                # "- Avoid extraneous justifications or redundant points.\n"
                # "- Base the score on overall fit, considering both profile and decision history."
            )
            },
            {
            "role": "user",
            "content": (
                f"My Profile:\n{user_profile}\n\n"
                f"An evaluation of my recent decisions:\n{decision_history_evaluation}\n\n"
                f"Evaluate the fit of the following job based on my profile and recent decisions:\n{job_details}\n\n"
            )
            }
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
