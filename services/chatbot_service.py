#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Filename:    chatbot_service.py
# @Author:      Kuro
# @Time:        3/22/2025 7:27 PM

import streamlit as st
import sqlite3
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer
from configuration.config import EMBEDDING_MODEL, MILVUS_HOST, MILVUS_PORT, COLLECTION_NAME, CHATBOT_MODEL_NAME
import httpx


class ChatbotService:
    def __init__(self):
        # Initialize Milvus connection
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        self.collection = Collection(COLLECTION_NAME)
        self.collection.load()

        # Initialize embedding model
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # Initialize SQLite connection
        self.conn = sqlite3.connect("patients.db")
        self.cursor = self.conn.cursor()

        # Initialize Groq client with httpx client
        try:
            from groq import Groq
            self.client = Groq(
                api_key="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",
                http_client=httpx.Client(verify=False)
            )
        except Exception as e:
            st.error(f"Failed to initialize Groq client: {str(e)}")
            self.client = None

        self.system_message = """You are a medical AI assistant specialized in heart failure.
        Respond only with a clear final answer based strictly on the ESC guidelines and the patient information provided.
        Do not include any internal thoughts, reasoning steps, or explanations of your thought process.
        Cite the ESC guideline sources briefly if relevant. Do not preface or summarize your reasoning."""

    def get_patient_data(self, patient_id):
        """Retrieve patient data from SQLite database"""
        self.cursor.execute(
            "SELECT * FROM patient_info WHERE patient_id = ?", (patient_id,))
        patient_data = self.cursor.fetchone()
        if patient_data:
            columns = [description[0]
                       for description in self.cursor.description]
            return dict(zip(columns, patient_data))
        return None

    def search_guidelines(self, query, top_k=5):
        """Search Milvus database for relevant guidelines"""
        # Generate embedding for the query
        query_embedding = self.embedder.encode(query).tolist()

        # Search parameters
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        # Perform the search
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )

        return results[0]

    def generate_patient_response(self, patient_id, user_query):
        """Generate a response based on patient data and guidelines"""
        if not self.client:
            return "Error: Chatbot service is not properly initialized. Please try again later."

        # Get patient data
        patient_data = self.get_patient_data(patient_id)
        if not patient_data:
            return "Patient not found. Please check the patient ID."

        # Create a context-aware query
        context_query = f"""
        Patient Information:
        - Age: {patient_data.get('age')}
        - Sex: {patient_data.get('sex')}
        - Heart Failure Type: {patient_data.get('hf_type')}
        - Symptoms: {patient_data.get('symptoms')}
        - Medications: {patient_data.get('medications')}
        
        Question: {user_query}
        """

        # Search for relevant guidelines
        search_results = self.search_guidelines(context_query)

        # Format the guidelines for the AI model
        guidelines_text = "\n\n".join([f"Guideline {i+1}: {hit.entity.get('text')}"
                                       for i, hit in enumerate(search_results)])

        # Create the prompt for Groq
        user_message = f"""
        Patient Information:
        {context_query}
        
        Relevant ESC Guidelines:
        {guidelines_text}
        
        Using the patient’s information and the ESC guidelines, write an answer in simple, clear, and reassuring language that is easy to understand for someone without medical training.

        Do not include citations, medical jargon, or any explanations of how you arrived at the answer.

        Just give the final answer in a way that helps the patient feel informed and supported. The response should be brief but not overly short—enough to feel complete and helpful.
        Do not show your reasoning or thinking process."""

        try:
            # Get response from Groq
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message}
            ]

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=CHATBOT_MODEL_NAME
            )

            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_doc_response(self, patient_id, user_query):
        """Generate a response based on patient data and guidelines"""
        if not self.client:
            return "Error: Chatbot service is not properly initialized. Please try again later."

        # Get patient data
        patient_data = self.get_patient_data(patient_id)
        if not patient_data:
            return "Patient not found. Please check the patient ID."

        # Create a context-aware query
        context_query = f"""
        Patient Information:
        - Age: {patient_data.get('age')}
        - Sex: {patient_data.get('sex')}
        - Heart Failure Type: {patient_data.get('hf_type')}
        - Symptoms: {patient_data.get('symptoms')}
        - Medications: {patient_data.get('medications')}
        
        Question: {user_query}
        """

        # Search for relevant guidelines
        search_results = self.search_guidelines(context_query)

        # Format the guidelines for the AI model
        guidelines_text = "\n\n".join([f"Guideline {i+1}: {hit.entity.get('text')}"
                                       for i, hit in enumerate(search_results)])

        # Create the prompt for Groq
        user_message = f"""
        Patient Information:
        {context_query}
        
        Relevant ESC Guidelines:
        {guidelines_text}
        
        Based on the patient's clinical profile and the ESC guidelines, provide a medically accurate and concise answer.

        You may use appropriate medical terminology, include relevant citations from the ESC guidelines, and explain the clinical rationale where necessary.

        However, avoid including any meta-level reasoning or commentary about your thinking process—just provide the medically grounded recommendation or explanation supported by guideline references.
        Do not show your reasoning or thinking process."""

        try:
            # Get response from Groq
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message}
            ]

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=CHATBOT_MODEL_NAME
            )

            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def close(self):
        """Close database connections"""
        self.conn.close()
        connections.disconnect("default")

# Streamlit UI for the chatbot


def chat_interface(patient_id, mode):
    st.title("Heart Failure Guidelines Chatbot")

    # Initialize chatbot service
    chatbot = ChatbotService()

    # Display patient info
    patient_data = chatbot.get_patient_data(patient_id)
    if patient_data:
        st.subheader(f"Patient: {patient_data.get('name')}")
        st.write(f"Age: {patient_data.get('age')}")
        st.write(f"HF Type: {patient_data.get('hf_type')}")
        st.write(f"Current Medications: {patient_data.get('medications')}")

    # Chat interface
    user_query = st.text_input(
        "Ask a question about heart failure guidelines:")

    if user_query and mode == "Doctor":
        response = chatbot.generate_doc_response(patient_id, user_query)
        st.write(response)

    if user_query and mode == "Patient":
        response = chatbot.generate_patient_response(patient_id, user_query)
        st.write(response)

    # Close connections when done
    chatbot.close()
