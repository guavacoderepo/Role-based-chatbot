import json
from openai import OpenAI
from app.schemas.schemes import User
from datetime import datetime
from typing import List, Dict
from app.config.settings import Settings

settings = Settings()

class LLMServices:
    def __init__(self, user: User, prompt: str | None = None):
        """
        Initialize the LLM service with a user and optional prompt.
        Loads the conversation history for the user.
        """
        self.user = user
        self.prompt = prompt
        self.history = self.retrive_conversations()

    def prompt_formate(self, rag_context: str = None, source_url: str = None) -> List[Dict]:
        """
        Format the prompt for the LLM, including system instructions, user-assistant history,
        and optionally RAG (retrieval-augmented generation) context.
        """
        system_prompt = (
            f"You are a helpful and knowledgeable AI assistant specializing in {self.user.role} at FinSolve Technologies. "
            "Your role is to provide accurate and concise answers to user questions."
        )

        # Add context if RAG is available
        if rag_context:
            system_prompt += (
                "\n\nUse the following context and the full chat history to answer the user's current question. "
                "If the question is a follow-up (e.g., 'explain more', 'why?', or builds on the last answer), you must look at the most recent exchanges in the history to formulate your response. "
                "Only say `That information is not available in the current context or knowledge base.` if neither the provided context nor any part of the chat history help answer the question. "
                "Do not use any external or assumed knowledge beyond the context or chat history."
                f"\n\nContext:\n{rag_context.strip()}"
            )
        
        # Begin building the full prompt sequence 
        prompt = [{"role": "system", "content": system_prompt}]

        # Include past messages from conversation history

        history = self.history[-3:] if len(self.history) > 3 else self.history
        for message in history:
            prompt.extend([
                {"role": "user", "content": message["prompt"]}, 
                {"role": "assistant", "content": message["response"]}
            ])                    

        # Append the current user input at the end
        prompt.append({"role": "user", "content": self.prompt})
        return prompt    

    def gpt_conversation_prompt(self, rag_context: str = None, source_url: str = None) -> str:
        """
        Send the formatted prompt to OpenAI's GPT model and return the generated response.
        """
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model='gpt-4o',
            messages=self.prompt_formate(rag_context, source_url)
        )

        return response.choices[0].message.content

    def retrive_conversations(self) -> List[Dict]:
        """
        Retrieve previous conversations from a JSON file for the current user.
        """
        history = []

        try:
            with open('app/data/conversations.json', 'r', encoding='utf-8') as file:
                conversation = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        # Filter only the current user's conversation history
        for item in conversation:
            if item.get("user", {}).get('username') == self.user.username:
                history.append(item)

        return history

    def update_conversation(self, prompt, response) -> None:
        """
        Save a new conversation entry to the JSON file for persistence.
        """
        try:
            with open('app/data/conversations.json', 'r', encoding='utf-8') as file:
                conversation: List[dict] = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            conversation = []

        # Append the new interaction
        conversation.append({
            "user": {
                "username": self.user.username,
                "role": self.user.role.value
            },
            "prompt": prompt,
            "response": response,
            "date": datetime.now().isoformat()
        })

        # Write back the updated conversation log
        with open('app/data/conversations.json', 'w', encoding='utf-8') as file:
            json.dump(conversation, file, indent=2)
