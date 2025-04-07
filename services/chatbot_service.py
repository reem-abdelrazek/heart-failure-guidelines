#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Filename:    chatbot_service.py
# @Author:      Kuro
# @Time:        3/22/2025 7:27 PM

from groq import Groq

from ..configuration.config import CHATBOT_MODEL_NAME


class ChatbotService:
    def __init__(self):
        self.client = Groq(
            api_key="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")
        self.system_message = "You are a medical AI assistant specialized in providing evidence-based answers using data extracted from PDFs. Your responses must rely solely on the context provided via db_table_result and db_text_result. Do not introduce any external information. If the provided data does not contain sufficient evidence to answer the question, simply respond with 'I don't know'."

    def answer_question(self, db_table_result, db_text_result, question):
        # Create prompt with context and question
        user_message = f"Using the provided PDF data (db_table_result and db_text_result) as context, please answer the following medical question: {question}\n\n"

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_message},
        ]

        chat_completion = self.client.chat.completions.create(
            messages=messages, model=CHATBOT_MODEL_NAME)
        answer = chat_completion.choices[0].message.content
        return answer
