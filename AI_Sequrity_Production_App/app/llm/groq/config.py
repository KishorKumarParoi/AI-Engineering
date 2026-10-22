# import Portkey from 'portkey-ai';

# const portkey = new Portkey({
#   apiKey: "jeWm9ijVzpdKXt+iMgEI4Oh7A+Ou"
# });

# async function main() {
#   const response = await portkey.chat.completions.create({
#     messages: [
#       { role: "system", content: "You are a helpful assistant" },
#       { role: "user", content: "What is Portkey" }
#     ],
#     model: "@groq1/llama-3.1-8b-instant",
#     MAX_TOKENS: 512
#   });

#   console.log(response.choices[0].message.content);
# }

# main();

from portkey_ai import Portkey

portkey = Portkey(
  api_key = "jeWm9ijVzpdKXt+iMgEI4Oh7A+Ou"
)

response = portkey.chat.completions.create(
    model = "@groq2/llama-3.1-70b-versatile",
    messages = [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is Portkey"}
    ],
    MAX_TOKENS = 512
)

print(response.choices[0].message.content)