
import openai
import os
from dotenv import load_dotenv
load_dotenv()



def summarize_GPT_4(system_prompt, summarize_prompt):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": summarize_prompt,
            }
        ],
        temperature=0.1,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    print(response)
    return response