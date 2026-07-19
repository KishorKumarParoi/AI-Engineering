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
#     model: "@openai/gpt-5.4-mini",
#     MAX_TOKENS: 512
#   });

#   console.log(response.choices[0].message.content);
# }

# main();