from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

response = client.responses.create(
    model="gpt-3.5-turbo",
    input="Write a one-sentence bedtime story about an unicorn"
)
print(response.output_text)