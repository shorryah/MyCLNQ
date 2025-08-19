from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import List
from app.db.mongodb import chat_collection
import traceback
import requests
from fastapi import HTTPException
import os
from app.core.jwt_auth import jwt_required
from fastapi.responses import StreamingResponse
from datetime import datetime
from app.services.milvus_service import milvus_service
from langchain_ollama import ChatOllama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser




router = APIRouter()
baseurl = os.getenv("MY_CLNQ_SERVER_BASE_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_main_server = os.getenv("API_KEY_MYCLNQ_SERVER")

class ChatRequest(BaseModel):
    question: str
    symptoms: List[str] = Field(
        default_factory=list,
        description="List of symptoms to search for similar diseases. If empty, symptoms will be extracted from the question."
    )

class TokenResponse(BaseModel):
    token: str

def extract_symptoms(question: str) -> List[str]:
    """Extract symptoms from natural language using LLM"""
    try:
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        import json
        import re
        
        # Create a more direct prompt for symptom extraction
        prompt = """Extract medical symptoms from the following text. 
        Return ONLY a JSON array of symptom strings in lowercase.
        
        Example Input: "I've been having a headache and fever since yesterday"
        Example Output: ["headache", "fever"]
        
        Text to analyze: """ + question + """
        
        Return ONLY the JSON array: """
        
        # Use a simpler approach with direct LLM call
        llm = ChatOllama(model="mistral", temperature=0)
        
        # Get the raw response
        response = llm.invoke(prompt)
        
        # Extract JSON array using regex
        json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if json_match:
            try:
                symptoms = json.loads(json_match.group(0))
                if isinstance(symptoms, list):
                    # Clean and validate symptoms
                    return [
                        s.strip().lower() 
                        for s in symptoms 
                        if isinstance(s, str) and s.strip()
                    ]
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
        
        # Fallback: Try to extract symptoms directly from response
        print("Falling back to direct symptom extraction")
        symptoms = []
        for line in response.content.split('\n'):
            line = line.strip(' "\'[],.')
            if line and len(line) > 2:  # Filter out very short strings
                symptoms.append(line.lower())
        
        return symptoms[:5]  # Return up to 5 symptoms
        
    except Exception as e:
        print(f"Error in symptom extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

@router.post("/ask")
async def ask_medical_question(
    q: ChatRequest, 
    user_info: str = Depends(jwt_required)
):
    try:
        # Extract symptoms from question if not provided
        symptoms_to_search = q.symptoms
        if not symptoms_to_search and q.question:
            print("Extracting symptoms from question...")
            symptoms_to_search = extract_symptoms(q.question)
            print(f"Extracted symptoms: {symptoms_to_search}")
        else:
            print(f"Using provided symptoms: {symptoms_to_search}")

        # Search for similar diseases based on symptoms using Milvus
        disease_results = []
        disease_context = ""
        
        if symptoms_to_search:
            try:
                print(f"Searching for diseases with symptoms: {symptoms_to_search}")
                disease_results = milvus_service.search_similar_diseases(
                    symptoms=symptoms_to_search,
                    top_k=5  # Get top 3 most relevant diseases
                )
                print(f"Found {len(disease_results)} relevant diseases")
                print(disease_results)
                
                # Create context from disease results
                if disease_results:
                    disease_context = "\n".join([
                        f"Disease: {res['disease']}\n"
                        f"Relevant Symptoms: {res['symptoms']}\n"
                        f"Specialist: {res['specialist']}\n"
                        f"Confidence: {1 - res['score']:.2f}\n"  # Convert distance to similarity score
                        for res in disease_results
                    ])
                    print(f"Disease context created with {len(disease_results)} results")
                else:
                    disease_context = "No matching diseases found for the given symptoms."
                    print("No matching diseases found")
                    
            except Exception as e:
                print(f"Error searching diseases: {str(e)}")
                disease_results = []
                disease_context = "Error retrieving medical information. Please try again later."

        # Prepare natural language context from disease results
        if disease_results:
            disease_context = "Based on the symptoms you've described, here are some conditions that might be relevant:\n\n"
            for result in disease_results:
                # Convert symptoms list to natural language
                symptoms_list = result['symptoms'].split(',') if isinstance(result['symptoms'], str) else result['symptoms']
                symptoms_text = ", ".join(symptoms_list[:-1]) + (f" and {symptoms_list[-1]}" if len(symptoms_list) > 1 else symptoms_list[0] if symptoms_list else "")
                
                # Add condition information in natural language
                disease_context += (
                    f"• {result['disease']}: This condition is often associated with {symptoms_text}. "
                    f"It's one of the more likely possibilities based on the symptoms you've described."
                    f"You can consult with a {result['specialist']} for more clarification\n\n"
                )
            
            disease_context += (
                "\nMany conditions share similar symptoms, so it's important to consult with a healthcare professional "
                "for an accurate assessment of your specific situation."
            )
        else:
            disease_context = (
                "Based on the provided condition I am not able to confirm about the disease. Can you give me a more detailed description of the symptoms u are facing."
                "You should conatact a healthcare provider that can perform the necessary tests and examinations for a proper evaluation."
            )

        # Enhanced system prompt that combines context and general knowledge
        system_prompt = """You are a helpful medical assistant providing clear, natural-sounding medical information.
        
        Response Format:
        1. Start with the most likely conditions based on symptoms
        2. Group related conditions together
        3. Keep it brief (2-3 short paragraphs max)
        4. End with a single sentence about consulting a doctor
        
        Example:
        "Based on your symptoms, you might be experiencing [condition]. [Brief explanation]. 
        Other possibilities include [related conditions]. [Brief explanation if needed].
        
        If no specific conditions match in the database, provide general guidance:
        "Your symptoms could be related to several common conditions. It's best to consult with a healthcare professional for proper evaluation."
        
        Guidelines:
        - Never mention the database or information sources
        - Keep it conversational and natural
        - Avoid medical jargon
        - Don't list symptoms unless absolutely necessary
        - Focus on the most relevant 1-2 conditions
        - Keep it under 100 words
        - Never list more than 2-3 conditions
        - Always end with a recommendation to see a doctor
        
        Current Context:
        {disease_context}
        """

        # Store the initial chat data in database
        chat_data = {
            "user_id": user_info["user_id"],
            "question": q.question,
            "symptoms": q.symptoms,
            "disease_results": disease_results,
            "timestamp": datetime.utcnow()
        }
        chat_collection.insert_one(chat_data)

        # Create the chain with proper streaming setup
        llm = ChatOllama(
            model="mistral",
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            temperature=0
        )

        # Create the prompt template with context and question
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
            Instructions for responding:
            {instructions}
            
            User's Question: {question}
            
            Please provide a comprehensive response that combines:
            1. Information from the provided medical context (clearly labeled)
            2. Additional relevant medical knowledge (clearly labeled)
            3. Appropriate disclaimers about seeking professional medical advice
            """)
        ])
        
        # Create the chain with context, question, and instructions
        chain = (
            {
                "disease_context": lambda x: disease_context,
                "question": lambda x: x["question"],
                "instructions": lambda _: """
                    When responding to the user's medical question:
                    1. First address any information from the provided medical context
                    2. Then provide additional relevant information from your general knowledge
                    3. Clearly separate context-based and general information
                    4. If unsure about something, say so rather than guessing
                    5. Always recommend consulting a healthcare professional for medical advice
                    """
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        async def token_stream_generator():
            full_response = ""
            async for token in chain.astream({"question": q.question}):
                if token:
                    full_response += token
                    yield json.dumps({"token": token}) + "\n"
            
            # Store complete response after streaming finishes
            chat_collection.insert_one({
                "user_id": user_info["user_id"],
                "prompt": q.question,
                "response": full_response,
                "timestamp": datetime.now()
            })

        return StreamingResponse(
            token_stream_generator(),
            media_type="text/event-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



@router.post('/all_chats')
def all_chats(user: object = Depends(jwt_required)):
    try:
        chats = chat_collection.find({"email": user}).sort("timestamp", -1)
        return {
            "user_id": user,
            "chat_history": [{
                "chat_id": str(chat.get("_id")),
                "question": chat.get("prompt"),
                "answer": chat.get("response"),
                "timestamp": chat.get("timestamp")
            } for chat in chats]
        }
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
 