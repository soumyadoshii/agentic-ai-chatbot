import os
import time
import logging
import requests
import urllib.parse
import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory, LangDetectException
from langdetect.detector import Detector

# Configure logging
logger = logging.getLogger(__name__)

# Set seed for consistent language detection results
DetectorFactory.seed = 0  

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize embeddings globally to prevent redundant API calls
embeddings = GoogleGenerativeAIEmbeddings(model='models/embedding-001')

# Cache the FAISS database in memory to eliminate disk I/O latency
@st.cache_resource(show_spinner=False)
def get_vector_store():
    """Load the FAISS vector database once and cache it in memory."""
    try:
        if os.path.exists('faiss_index'):
            return FAISS.load_local('faiss_index', embeddings, allow_dangerous_deserialization=True)
        return None
    except Exception as e:
        logger.error(f"Error loading vector database: {e}")
        return None

def get_pdf_text(pdf_docs) -> list:
    docs = [] 
    for loc in pdf_docs:
        text = ""
        pdf_doc = PdfReader(loc)
        for page in pdf_doc.pages: 
            text += page.extract_text()
        docs.append(text) 
    return docs

def get_text_chunks(docs) -> dict:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=250)
    chunks = dict() 
    for index, i in enumerate(docs):
        chunk = text_splitter.split_text(text=i) 
        chunks[index] = chunk 
    return chunks

def vector_store(chunks) -> None:
    def general_vectorstore(index):
        try:
            vectorestore_common = FAISS.load_local(folder_path='faiss_index', index_name='index', embeddings=embeddings, allow_dangerous_deserialization=True)
            vectorestore_common.add_texts(index)
            vectorestore_common.save_local(folder_path='faiss_index', index_name='index')
        except:
            index = FAISS.from_texts(index, embedding=embeddings)
            index.save_local(folder_path='faiss_index', index_name='index')

        vectorestore_common = FAISS.load_local(folder_path='faiss_index', index_name='index', embeddings=embeddings, allow_dangerous_deserialization=True)
        return vectorestore_common

    for index in chunks:
        if index == 0:
            vectorestore_common = general_vectorstore(chunks[index])
        else:
            vectorestore_common.add_texts(chunks[index])
    
    vectorestore_common.save_local(folder_path='faiss_index', index_name='index')
    
    # Clear the Streamlit cache so newly trained docs are loaded immediately
    st.cache_resource.clear()

def detect_language(text):
    """ Enhanced language detection with multiple methods and confidence checking """
    if len(text.strip()) < 10:
        logger.info("Text too short for reliable detection, defaulting to English")
        return "en" 
    
    english_indicators = ["the", "is", "are", "what", "how", "can", "which", "where", "when", "who", "does", "will", "why", "this", "that", "it", "in", "of", "to", "and"]
    english_word_count = sum(1 for word in text.lower().split() if word in english_indicators)
    
    try:
        try:
            DetectorFactory.seed = 0
            simple_lang = detect(text)
            if simple_lang in ["en", "es", "fr", "de", "it"]:
                return simple_lang
        except LangDetectException as e:
            logger.warning(f"Simple language detection failed: {e}")
        
        try:
            DetectorFactory.seed = 0
            detector = Detector(DetectorFactory())
            detector.append(text)
            languages = detector.get_probabilities()
            
            if not languages:
                return "en"
                
            primary_lang = languages[0].lang
            primary_prob = languages[0].prob
            
            if primary_lang == "ro" and len(text.split()) >= 3:
                if english_word_count >= 1 or primary_prob < 0.8:
                    return "en"
            
            if primary_prob < 0.6:
                return "en"
                
            return primary_lang
            
        except Exception as e:
            logger.warning(f"Detailed language detection failed: {e}")
            if english_word_count >= 1:
                return "en"
            
    except Exception as e:
        logger.error(f"All language detection methods failed: {e}")
    
    return "en"

def verify_language(text, detected_lang):
    """ Secondary verification for detected language using lexical analysis """
    # Scrubbed specific corporate terminology, using generic enterprise terms
    domain_terms = ["system", "platform", "dashboard", "analytics", "data", "user", "report", "process"]
    
    if any(term in text.lower() for term in domain_terms):
        return "en"
    
    language_markers = {
        "en": ["the", "is", "are", "what", "how", "can", "does", "why", "when", "who", "which", "will", "system", "platform", "data", "user", "dashboard", "report", "configuration", "account", "setup"],
        "es": ["el", "la", "los", "las", "es", "son", "como", "qué", "cómo", "puede", "por qué"],
        "fr": ["le", "la", "les", "est", "sont", "comment", "pourquoi", "quand", "qui", "quel"],
        "de": ["der", "die", "das", "ist", "sind", "wie", "warum", "wann", "wer", "welche"],
        "ro": ["este", "sunt", "cum", "de ce", "când", "cine", "care"]
    }
    
    if len(text.split()) > 15:
        return detected_lang
        
    text_lower = text.lower()
    words = text_lower.split()
    
    detected_markers = 0
    if detected_lang in language_markers:
        detected_markers = sum(1 for word in words if word in language_markers[detected_lang])
    
    english_markers = sum(1 for word in words if word in language_markers["en"])
    
    if detected_lang != "en" and detected_markers < 2 and english_markers >= 1:
        return "en"
    
    return detected_lang

def enhanced_language_detection(text):
    text_for_detection = text.replace("?", "").strip()
    initial_lang = detect_language(text_for_detection)
    verified_lang = verify_language(text, initial_lang)
    return verified_lang

def translate_text(text, target_lang="en", retry_count=2):
    """ Enhanced translation function with error handling and retries """
    if len(text.strip()) < 5 or not text.strip():
        return text
        
    for attempt in range(retry_count + 1):
        try:
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            if translated and translated.strip() and translated != text:
                return translated
        except Exception as e:
            if attempt < retry_count:
                time.sleep(1)
    
    try:
        base_url = "https://translate.googleapis.com/translate_a/single"
        url = f"{base_url}?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0 and len(result[0]) > 0:
                translated = ''.join([sentence[0] for sentence in result[0] if sentence[0]])
                return translated
    except Exception as e:
        logger.error(f"Fallback translation failed: {e}")
    
    return text

def conv_chain(vectorestore)->ConversationalRetrievalChain:
    """ Create a conversation chain with improved language handling and prompt template """
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-001', temperature=0.2, top_p=0.85, top_k=40, max_output_tokens=4096)
    
    # Completely generic enterprise prompt template
    prompt = PromptTemplate(
        input_variables=['chat_history', 'question'],
        template=(
        "You are a highly skilled technical analyst and business assistant. "
        "Your task is to provide precise, factual, and actionable information based strictly on the provided context documents.\n\n"
        
        "RESPONSE PRIORITY GUIDELINES:\n"
        "1. FACTUAL ACCURACY: Only answer based on information explicitly found in the reference documents.\n"
        "2. CLARITY: Use simple, direct language that translates well across languages.\n"
        "3. RELEVANCE: Address the exact question asked without unnecessary information.\n"
        "4. COMPLETENESS: Cover all aspects of the question when possible.\n\n"
        
        "RESPONSE CONSTRAINTS:\n"
        "- If information is missing from the context, clearly state: 'Based on the available information, I cannot provide details about [specific aspect]. Please contact system support or an administrator for more information.'\n"
        "- Avoid using idioms, cultural references, or complex grammatical structures that might not translate well.\n"
        "- Use universal terminology rather than highly niche jargon unless it is defined in the text.\n"
        "- For technical terms specific to the documentation, include a brief definition in parentheses the first time you use them.\n"
        "- When describing procedures, list steps in clear numerical order.\n"
        "- For complex features, explain both HOW they work and WHY they are beneficial.\n\n"
        
        "CONTEXT UTILIZATION:\n"
        "- Carefully analyze ALL provided context documents before answering.\n"
        "- Prioritize information from the most relevant context chunks.\n"
        "- When multiple context chunks contain relevant information, synthesize a comprehensive answer.\n"
        "- If contexts seem contradictory, prioritize the most specific or recent information.\n\n"
        
        "RESPONSE LENGTH MANAGEMENT:\n"
        "- Ensure responses are complete and not cut off mid-explanation.\n"
        "- For complex topics, provide a complete answer that covers all aspects thoroughly.\n"
        "- If a response would be very long, structure it with clear sections and bullet points.\n"
        "- Always complete your thoughts and never leave sentences unfinished.\n\n"
        
        "ENHANCED RESPONSE STRUCTURE:\n"
        "1. Direct answer to the question in 1-2 sentences (always complete this section)\n"
        "2. Detailed explanation with specific examples from the provided context (ensure this section is thorough)\n"
        "3. Relevant business benefits, use cases, or technical implementation details if applicable\n"
        "4. Brief summary that encapsulates the complete answer (always include this)\n\n"
        
        "COMPLETION INSTRUCTIONS:\n"
        "- Always provide a complete response that fully addresses the question.\n"
        "- Never end your response abruptly or mid-explanation.\n"
        "- If elaborating on a complex topic, ensure all points are fully developed.\n"
        "- Always include a concluding statement or summary at the end of your response.\n\n"
        
        "Previous conversation:\n{chat_history}\n\n"
        "User Question: {question}\n\n"
        "Response:"
    )
)

    retriever = vectorestore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 8,                
            "score_threshold": 0.25,  
            "fetch_k": 15,
            "filter": None           
        }
    )
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        condense_question_prompt=prompt,
        chain_type='stuff',
    )
    
    return chain

def user_input(user_question, chat_history):
    """ Process user input with improved multilingual support """
    
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    if user_question.lower() in greetings:
        return "Hello! How can I assist you today?"
    
    user_lang = enhanced_language_detection(user_question)
    
    if user_lang != "en":
        try:
            translated_question = translate_text(user_question, target_lang="en")
        except Exception as e:
            logger.error(f"Translation error: {e}")
            translated_question = user_question  
    else:
        translated_question = user_question
    
    try:
        new_db = get_vector_store()
        
        if new_db is None:
            return "Knowledge base not found. Please log in as an Admin and upload training documents first."
            
        chain = conv_chain(new_db)
        
        messages = []
        for i in range(0, len(chat_history), 2):
            if i < len(chat_history):
                messages.append(HumanMessage(content=chat_history[i]))
            if i+1 < len(chat_history):
                messages.append(AIMessage(content=chat_history[i+1]))
        
        response = chain.invoke({
            "question": translated_question,
            "chat_history": messages
        })
        
        english_response = response.get("answer", "Sorry, I couldn't find an answer.")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        english_response = "I'm sorry, I'm having trouble processing your request right now. Please try again."
    
    if user_lang != "en":
        try:
            final_response = translate_text(english_response, target_lang=user_lang)
        except Exception as e:
            logger.error(f"Response translation error: {e}")
            final_response = english_response  
    else:
        final_response = english_response
    
    return final_response