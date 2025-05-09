import ast
import logging
import openai
import os
import sys
from config import user_info 
# Set your OpenAI API key
openai.api_key = "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"  # set provided key

decision_history = [{'decision': 'reject', 'job_id': 1, 'evaluation_shown': '• The job at Geotab Inc in Oakville, Canada, does not align with your desired location in the USA.\n• The role of Software Developer Intern for the MyGeotab cloud services is quite different from your background in autonomous robotics, software development, and DevOps.\n• The job posting lacks specific details on required skills, making it hard to assess a direct match with your profile.\n• The job is for an 8-month consecutive work term, which exceeds your preference for a 4-month co-op.\n• The job posting does not mention any specific technologies or frameworks that align closely with your skill set.'},
 {'decision': 'reject', 'job_id': 1, 'evaluation_shown': '• The job as a Project Management Assistant at S&C Electric Canada Ltd in Oakville, Canada, is not a good fit for you based on your desired location in the USA.\n• The role involves working with the Project Management Team, which is quite different from your background in autonomous robotics, software development, and DevOps.\n• The job requires an 8-month consecutive work term, which exceeds your preference for a 4-month co-op.\n• The job posting lacks specific details on required skills, making it hard to assess a direct match with your profile.\n• The listed location in Oakville, Ontario, differs from your desired location in the USA.'},
 {'decision': 'accept', 'job_id': 1, 'evaluation_shown': "• Strong matches in skills and qualifications:\n  - Your background in software development, autonomous robotics, and DevOps aligns well with the role of an Embedded Security Developer at ETAS.\n  - Your experience with Python, C/C++, and embedded systems development is directly relevant to the job's requirements.\n  - Familiarity with security concepts and working on embedded hardware that controls vehicles matches the job's needs.\n  - Your ability to work collaboratively in a small team setting aligns with the team integration aspect of the job responsibilities.\n\n• Missing qualifications:\n  - While the job posting mentions an interest in specific courses, it does not list explicit technical skills required beyond being smart, tenacious, and talented. However, your technical background seems to align well with the job's expectations.\n\n• The listed location in Waterloo, Canada, differs from your desired location in the USA."},
 {'decision': 'accept', 'job_id': 4, 'evaluation_shown': "• The job at AGF Investments Inc in Toronto, Canada, does not align with your desired location in the USA, similar to your rejection of positions in Toronto and Oakville, Canada. This mismatch in location preference significantly reduces the compatibility score.\n\n• The job is for the Fall 2025 term, which aligns with your preference for a 4-month co-op.\n\n• The role of GenAI Process Automation Developer Co-op involves working with GenAI technology to automate solutions within AGF's shared services organizations. This role seems more focused on automation and investment management rather than pure software development, which might not fully utilize your technical skills in software development and frameworks like Flask, React, ROS, and Docker based on your past experiences.\n\n• The job posting does not specify any required technical skills or languages that directly match your profile, making it a poor fit in terms of skills alignment.\n\n• The job requires a cover letter, which you have previously indicated is not something you want to do based on your past decisions."}]

# position involving AI
system_prompt = (
            "You are a brutally honest and no-nonsense co-op advisor, helping me choose which jobs to apply to. Don't sugarcoat anything. Be direct, realistic, and critical as needed. Avoid flattery. "
            "Your goal is to deliver a practical, harsh assessment of how well a job posting matches my profile and preferences, incorporating insights from my past decisions. "
            "Moreover, I am trying to find the best possible job for me, so if I seem overqualified for a job then it is not a good fit for me. Also assume that I am not trying to switch to a completely different field, so if the job is in a different field then it is not a good fit for me. "
            "Additionally, if the job belongs to an unrelated industry, assign a compatibility score no higher than 25.\n\n"
            "• **Crucially, incorporate insights from my decision history.** If this job resembles previously rejected positions, indicate why it might be a poor fit and reduce the score. Conversely, if it resembles accepted roles, note the similarity and raise the score.\n"
            "• If a key qualification is missing from my profile but implied by my work experience, recommend considering its inclusion (e.g., 'Consider adding [Technology] if you worked with it during your time as a [Role] at [Company]', but only if there is a very strong chance of it being true).\n"
            " - Only suggest adding skills that I am very likely to have, based on my work, education, or other experiences and ALWAYS include which experience it is based on.\n" 
            # "Example of a good response:\n"
            # "• Strong matches in skills and qualifications:\n"
            # "  - Your experience with Python, including scientific software development tools, aligns well with the requirement for Python in this role.\n"
            # "  - Familiarity with neural networks, Linux environments, and containerized applications like Docker matches the job's needs.\n"
            # "  - Your background in software development and working across tech stacks is relevant to the software development responsibilities outlined.\n\n"
            # "• Missing qualifications:\n"
            # "  - Lack of direct experience with modern website development frameworks like React.js, machine learning, and image processing standards might be a gap.\n\n"
            # "• The listed location in London, Ontario, differs from your desired location in the USA.\n\n"
            # " - Missing qualifications are ones listed in the job description but not in my profile.\n"
            # "• The job requires a cover letter, which is not something you want to do.\n\n"
            # "• The job requires a 4-month co-op, which is what you are looking for.\n\n"
            # "• Consider adding 'TensorFlow' to your profile, as you likely worked with it during your time as a [Role] at [Company].\n\n"
            "• End with a new line: 'Compatibility score out of 100: [score]'\n\n"
        )

# use job_details_debug1746553624.9544065.txt as brookfield_finance_job

with open("job_details_debug1746553624.9544065.txt", "r", encoding="utf-8") as f:
    content = f.read()

for line in content.splitlines():
    if line.startswith("Details:"):
        details_str = line[len("Details: "):].strip()
        try:
            brookfield_finance_job_details = ast.literal_eval(details_str)
        except Exception as e:
            logging.error("Error parsing details: %s", e)
        break

with open("job_details_debug1746646237.55516.txt", "r", encoding="utf-8") as f:
    content = f.read()

for line in content.splitlines():
    if line.startswith("Details:"):
        details_str = line[len("Details: "):].strip()
        try:
            groq_job_details = ast.literal_eval(details_str)
        except Exception as e:
            logging.error("Error parsing details: %s", e)
        break

with open("job_details_debug1746647492.6649308.txt", "r", encoding="utf-8") as f:
    content = f.read()

for line in content.splitlines():
    if line.startswith("Details:"):
        details_str = line[len("Details: "):].strip()
        try:
            magi_job_details = ast.literal_eval(details_str)
        except Exception as e:
            logging.error("Error parsing details: %s", e)
        break



user_prompt = (
    f"My Profile:\n{user_info}\n\n"
    f"My Recent Decisions:\n{decision_history}\n\n"
    f"Evaluate the fit of the following job based on my profile and recent decisions:\n{brookfield_finance_job_details}\n\n"
)

user_prompt2 = (
    # f"My Profile:\n{user_info}\n\n"
    # f"My Recent Decisions:\n{decision_history}\n\n"
    f"Evaluate the fit of the following job based on my profile and recent decisions:\n{groq_job_details}\n\n"
)

user_prompt3 = (
    # f"My Profile:\n{user_info}\n\n"
    # f"My Recent Decisions:\n{decision_history}\n\n"
    f"Evaluate the fit of the following job based on my profile and recent decisions:\n{magi_job_details}\n\n"
)

text = (
    "• **Missing qualifications:**\n"
    "- The job posting is for a Finance Intern position with a focus on CPA training, which is not aligned with your Computer Engineering background and technical skill set.\n"
    "- The role emphasizes financial planning, analysis, reporting, treasury, internal audit, investor relations, corporate finance, and taxation, areas that are not directly related to your expertise in software development and engineering.\n"
    "- The job requires a CPA designation or interest in pursuing it, which is not in line with your current career trajectory in the tech industry.\n"
    "- The location is in Toronto, Ontario, which does not match your preference for a job in the USA.\n\n"
    "• This job is in the finance sector, which is unrelated to your field of Computer Engineering, resulting in a low compatibility score.\n\n"
    "• It is not likely that you will want to apply to this job based on your history of rejecting jobs in unrelated fields and in locations outside of the USA.\n"
    "Compatibility score out of 100: 20\n\n"
)

text2 = (
    "• **Strong matches in skills and qualifications:**\n"
    "  - Your background in software development, including experience with Python, SQL, JavaScript, Flask, React, ROS, Docker, and C/C++, aligns well with the responsibilities of a Cloud DevOps Engineering Intern at Groq Inc.\n"
    "  - Your experience as a DevOps Developer in Fleet Software at OTTO Motors, a division of Clearpath Robotics, is particularly relevant to the role.\n"
    "• **Missing qualifications:**\n"
    "  - If you gained any expeirience with Google Cloud Platform (GCP) or other cloud-native solutions during your time at OTTO Motors, it might be beneficial to highlight that.\n"
    "• The listed salary of $38-41/hour CAD aligns well with your desired salary of $40/hour CAD.\n\n"
    "• The listed location is Toronto, Ontario, Canada, which is not in the USA.\n"
    "Compatibility score out of 100: 80\n\n"
)


text3 = (
    "• **Strong matches in skills and qualifications:**\n"
    " - Your background in software development, autonomous robotics, and tech stacks like Python, SQL, JavaScript, Flask, React, ROS, Docker, C/C++, etc., aligns well with the technical aspects of the role, the focus on AI applications and generative AI may not be explicitly highlighted in your profile.\n"

    "• **Missing qualifications:**\n"
    " - The role emphasizes working with Generative Artificial Intelligence (AI) and Large Language Models (LLMs), and optimizing features based on key performance indicators which may require specific experience with AI technologies beyond what is mentioned in your skills profile.\n"
    " - However, based on your past decisions, you seem open to exploring roles that involve AI and LLMs, so given that the location is in New York City, NY, USA, so this job may be a good fit for you.\n"
    " - Note that the salary is undisclosed, but that there is a $2000/month housing stipend to relocate to New York City.\n"
)


example_conversation = [
    {
        "role": "system",
        "content": system_prompt
    },
    # {
    #     "role": "user",
    #     "content": user_prompt
    # },
    # {
    #     "role": "assistant",
    #     "content": text
    # },
    # {
    #     "role": "user",
    #     "content": user_prompt2
    # },
    # {
    #     "role": "assistant",
    #     "content": text2
    # },
    {
        "role": "user",
        "content": user_prompt3
    },
    {
        "role": "assistant",
        "content": text3
    }
]

#export t

# • **Missing qualifications:**
#   - The job posting for the Junior Developer position at Tuq in Waterloo, Ontario, Canada, requires candidates to be a Canadian citizen, permanent resident, or a protected person as defined by the Immigration and Refugee Protection Act, which may not align with your citizenship status.
#   - The role emphasizes working on real projects for real clients and making valuable contributions that make a real difference, which might not fully utilize your background in software development, autonomous robotics, and tech stacks like Python, SQL, JavaScript, Flask, React, ROS, Docker, C/C++, etc.
#   - The salary range of $18.00 - $22.00 per hour falls below your desired rate of $40/hour CAD.
#   - The job posting requires the submission of a Grade Report, which might be an additional document requirement you prefer to avoid.

# • The job is located in Waterloo, Ontario, Canada, which differs from your desired location in the USA.


# • **Missing qualifications:**
#   - The job posting for the Software Engineering position at Magi Inc in New York City, NY, USA, emphasizes working on full-stack AI-powered applications in a fast-paced startup environment. While your background in software development, autonomous robotics, and tech stacks like Python, SQL, JavaScript, Flask, React, ROS, Docker, C/C++, etc., aligns well with the technical aspects, the focus on AI applications and generative AI may not be explicitly highlighted in your profile.
#   - The role involves building frontend and backend components of AI-powered applications, working with Generative Artificial Intelligence (AI) and Large Language Models (LLMs), and optimizing features based on key performance indicators. These responsibilities may require specific experience with AI technologies beyond what is mentioned in your skills profile.
#   - The compensation structure includes a salary plus a monthly housing stipend to relocate to New York City, which may not align with your desired hourly rate of $40 CAD based on past decisions.
#   - The location in New York City, NY, USA, aligns with your desired location.
