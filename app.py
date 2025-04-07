#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Filename:    app.py
# @Author:      Kuro
# @Time:        3/22/2025 6:20 PM

from services.db_service import DBService
from services.chatbot_service import ChatbotService

db_service = DBService()
chatbot_service = ChatbotService()

input_db = "of the given treatment or procedure."
user_question = "How effective is the treatment?"
db_results = db_service.query_milvus(input_db)
top1_table = None
top1_text = None

# get the top 1 table and text from the response by "id" if id startwith chunk mean text, startwith table mean table
for db_result in db_results:
    if db_result["id"].startswith("chunk") and top1_text is None:
        top1_text = db_result["metadata"]["text"]
    elif db_result["id"].startswith("table") and top1_table is None:
        top1_table = db_result["metadata"]["text"]
print(top1_table)
print(top1_text)
llm_answer = chatbot_service.answer_question(top1_table, top1_text, user_question)
print("Answer: ", llm_answer)
