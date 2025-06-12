import json
from openai import OpenAI
from app.schemas.schemes import User
from datetime import datetime
from typing import List, Dict
from app.config.settings import Settings

settings = Settings()

class LLMServices:
    def __init__(self, user:User, prompt:str | None =None,):
        self.user = user
        self.prompt = prompt
        self.history = self.retrive_conversations()

    def prompt_formate(self, rag_context:str=None) -> List[Dict]:
       
        system_prompt = (
            f"You are a helpful and knowledgeable AI assistant specializing in {self.user.role} at FinSolve Technologies. "
            "Your role is to provide accurate and concise answers to user questions."
        )

        if rag_context:
            system_prompt += (
                "\n\nUse the following context and the full chat history to answer the user's current question. "
                "If the question is a follow-up (e.g., 'explain more', 'why?', or builds on the last answer), you must look at the most recent exchanges in the history to formulate your response. "
                "Only say `I don't know` if neither the provided context nor any part of the chat history help answer the question. "
                "If your answer is based on information in the context, include a source URL in markdown format like `[🔗 View source](URL)`. "
                "Do not use any external or assumed knowledge beyond the context or chat history."
                f"\n\nContext:\n{rag_context.strip()}"
            )



        prompt = [{"role": "system", "content": system_prompt}]

        for message in self.history:
            prompt.extend([
                {"role": "user", "content": message["prompt"]}, 
                {"role": "assistant", "content": message["response"]}
            ])                    
        prompt.append({"role": "user", "content": self.prompt})
        return prompt    


    def gpt_conversation_prompt(self, rag_context:str=None) -> str:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model = 'gpt-4o',
            messages = self.prompt_formate(rag_context)
        )

        return response.choices[0].message.content

    def retrive_conversations(self)->List[Dict]:
        history = []

        try:
            with open('app/data/conversations.json', 'r', encoding='utf-8') as file:
                conversation = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        for item in conversation:
            if item.get("user", {}).get('username') == self.user.username:
                history.append(item)
        
        return history

    def update_conversation(self, prompt, response) -> None:
        try:
            with open('app/data/conversations.json', 'r', encoding='utf-8') as file:
                conversation: List[dict] = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            conversation = []

        conversation.append({
            "user": {
                "username": self.user.username,
                "role": self.user.role.value
            },
            "prompt": prompt,
            "response": response,
            "date": datetime.now().isoformat()
        })

        with open('app/data/conversations.json', 'w', encoding='utf-8') as file:
            json.dump(conversation, file, indent=2)
