from portkey_ai import Portkey

portkey = Portkey(
  api_key = "jeWm9ijVzpdKXt+iMgEI4Oh7A+Ou"
)

response = portkey.chat.completions.create(
    model = "@openai/gpt-5.4-mini",
    messages = [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is Portkey"}
    ],
    MAX_TOKENS = 512
)

print(response.choices[0].message.content)