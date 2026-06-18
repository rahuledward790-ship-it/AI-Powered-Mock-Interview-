import os
import requests
from transformers import pipeline
import google.generativeai as genai

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "mistral:latest"
OLLAMA_TIMEOUT = 120

PROMPT_TEMPLATE = (
    "You are an expert interview coach and communication mentor.\n\n"
    "Read the question and the candidate answer carefully, then respond in a polished, professional, and user-friendly way.\n"
    "Provide exactly these numbered sections with a blank line between each one:\n"
    "1. Communication Feedback\n"
    "2. Grammar Improvements\n"
    "3. Confidence Analysis\n"
    "4. Better Professional Answer\n"
    "5. Communication Rating (1-10)\n"
    "6. Confidence Rating (1-10)\n"
    "7. Score out of 10\n\n"
    "Use short, clear sentences. Keep the tone helpful, positive, and professional.\n"
    "Question: {question}\n"
    "Answer: {answer}\n\n"
    "After the candidate answer, insert this marker on a new line:\n"
    "### BEGIN ANSWER\n"
    "Then write only the numbered list. Do not add any extra commentary or analysis after the list.\n"
)


def load_local_model():
    try:
        return pipeline(
            "text-generation",
            model="distilgpt2",
            device=-1,
        )
    except Exception as e:
        print("Error loading local AI model:", e)
        return None


local_model = load_local_model()


def call_gemini(question, answer):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash as default, fallback to gemini-pro if needed
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = PROMPT_TEMPLATE.format(question=question, answer=answer)
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print("Gemini 1.5 error, trying fallback:", e)
        try:
            model = genai.GenerativeModel('gemini-pro')
            prompt = PROMPT_TEMPLATE.format(question=question, answer=answer)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as ex:
            print("Gemini fallback error:", ex)
    return None


def call_ollama(question, answer):
    prompt = PROMPT_TEMPLATE.format(question=question, answer=answer)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 300,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            if "response" in data:
                return data["response"].strip()
            if "text" in data:
                return data["text"].strip()
        return None
    except Exception as e:
        print("Ollama request error:", e)
        return None


def sanitize_feedback_text(text):
    if not text:
        return text

    cleaned = text.replace("### BEGIN ANSWER", "")
    cleaned = cleaned.replace("###BEGIN ANSWER", "")
    return cleaned.strip()


# ANALYZE FUNCTION

def analyze_answer(question, answer):
    # 1. Try Gemini
    feedback = call_gemini(question, answer)
    feedback = sanitize_feedback_text(feedback)
    if feedback:
        if "1. Communication Feedback" in feedback or "2. Grammar Improvements" in feedback:
            return feedback

    # 2. Try Ollama next if the server is running
    feedback = call_ollama(question, answer)
    feedback = sanitize_feedback_text(feedback)
    if feedback:
        if "1. Communication Feedback" in feedback or "2. Grammar Improvements" in feedback:
            return feedback

    # 3. Fallback to local model
    if local_model is None:
        return "Error: No AI model available. Start Ollama server or install transformers model."

    prompt = PROMPT_TEMPLATE.format(question=question, answer=answer)
    try:
        result = local_model(
            prompt,
            max_new_tokens=250,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            return_full_text=False,
        )
        generated = result[0]["generated_text"].strip()
        generated = sanitize_feedback_text(generated)
        if "1. Communication Feedback" in generated:
            generated = generated[generated.index("1. Communication Feedback"):].strip()
        return generated
    except Exception as e:
        return f"Error: {str(e)}"