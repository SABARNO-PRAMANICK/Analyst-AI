import os
import subprocess
import pandas as pd
from together import Together
import base64
import docx
import PyPDF2
import streamlit as st

TOGETHER_API_KEY = st.secrets.get("TOGETHER_API_KEY", os.getenv("TOGETHER_API_KEY"))
SYSTEM_PROMPT = "You are an expert data analyst. Provide accurate, insightful responses or generate Python code as requested."

def parse_spreadsheet(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)

def generate_data_summary(df):
    summary = f"Columns: {list(df.columns)}\n"
    summary += f"Rows: {len(df)}\n"
    summary += "Basic statistics:\n" + df.describe().to_string()
    return summary

def parse_text(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def parse_doc(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        return "\n".join([pdf.pages[i].extract_text() for i in range(len(pdf.pages))])

def encode_image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def execute_code(code, df):
    df.to_csv('temp_data.csv', index=False)
    with open('temp_script.py', 'w') as f:
        f.write(code)
    try:
        result = subprocess.run(
            ['python', 'temp_script.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        stdout, stderr = result.stdout, result.stderr
        image_path = 'output.png' if os.path.exists('output.png') else None
        if result.returncode == 0:
            return stdout, image_path
        else:
            return f"Error: {stderr}", None
    except subprocess.TimeoutExpired:
        return "Timeout: Code execution exceeded 30 seconds.", None
    finally:
        os.remove('temp_data.csv')
        os.remove('temp_script.py')

def data_analyst_agent(file_path, user_request, conversation_history=[]):
    file_ext = os.path.splitext(file_path)[1].lower()
    client = Together(api_key=TOGETHER_API_KEY)
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    if file_ext in ['.csv', '.xlsx']:
        df = parse_spreadsheet(file_path)
        data_summary = generate_data_summary(df)
        prompt = f"Previous conversation:\n{history_str}\n\nData summary: {data_summary}\n\nCurrent user request: {user_request}\n\nGenerate Python code to address the request, using pandas to read 'temp_data.csv'. For visualizations, save to 'output.png' with plt.savefig(). For analyses, print results."
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        code = response.choices[0].message.content
        stdout, image_path = execute_code(code, df)
        text_response = f"Analysis output:\n{stdout}" + (f"\n\nVisualization saved to {image_path}" if image_path else "")
        updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": text_response}]
        return text_response, image_path, updated_history
    
    elif file_ext in ['.txt', '.doc', '.pdf']:
        content = parse_text(file_path) if file_ext == '.txt' else parse_doc(file_path) if file_ext == '.doc' else parse_pdf(file_path)
        prompt = f"Previous conversation:\n{history_str}\n\nDocument content: {content}\n\nCurrent user request: {user_request}\n\nProvide a response based on the content and history."
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        text_response = response.choices[0].message.content
        updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": text_response}]
        return text_response, None, updated_history
    
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        base64_image = encode_image_to_base64(file_path)
        messages = conversation_history + [{"role": "user", "content": [
            {"type": "text", "text": user_request},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}]
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=messages
        )
        text_response = response.choices[0].message.content
        updated_history = messages + [{"role": "assistant", "content": text_response}]
        return text_response, None, updated_history
    
    else:
        return "Unsupported file type.", None, conversation_history

