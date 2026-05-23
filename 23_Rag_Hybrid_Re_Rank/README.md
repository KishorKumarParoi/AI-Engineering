# ai-engineering-bootcamp-prerequisites

Welcome to the prerequisites repository for the [End-to-End AI Engineering Bootcamp](https://maven.com/swirl-ai/end-to-end-ai-engineering)! This repository is dedicated to setting up your development environment and scafoling a simple project with a StreamLit UI frontend service decoupled from FastAPI server.

We strongly recomend you coding along the videos available in our YouTube channel rather than just cloning the repository and running the code.

---

[Video 1](https://youtu.be/3WsEgLtwsGs): Setting up your development environment

[Video 2](https://youtu.be/cGOGA7GFecI): Build and containerise your first chatbot

[Video 3](https://youtu.be/bZHaCAFAUCs): Moving the agent behind a FastAPI server

[Video 4](https://youtu.be/IcbzksbMhuM): Containerising Backend and Frontend

---


If you do need to run the code, this is how:

- Clone the repository.
- Run:
```bash
cp env.example .env
```

Edit `.env` and add your API keys:

```
OPENAI_API_KEY=your_google_api_key
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
```
Keep the remaining configuration as per ```.env.example```.


#### To run the project, execute:

```bash
make run-docker-compose
```

Streamlit application: http://localhost:8501

FastAPI documentation: http://localhost:8000/docs



## Contact

If you have any questions, feel free to contact me via aurimas@swirlai.com

You can also find me on:

- 🔗 [LinkedIn](https://www.linkedin.com/in/aurimas-griciunas)
- 🔗 [X](https://x.com/Aurimas_Gr)
- 🔗 [Newsletter](https://www.newsletter.swirlai.com/)