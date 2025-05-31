import os
from together import Together
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from docx import Document
import PyPDF2
import base64
from dotenv import load_dotenv

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

SYSTEM_PROMPT = """You are an expert data scientist. You can:
- Analyze data from uploaded files (.csv, .xlsx, .doc, .txt, .pdf, images).
- Perform statistical analysis (e.g., mean, median, correlations) and generate insights.
- Create visualizations (e.g., bar, line, scatter plots) based on data.
- Answer questions about the data or files, including follow-up questions.
- For images, extract and analyze text or describe content to answer questions.
Provide clear, concise, and accurate responses. If a task requires code (e.g., analysis or visualization), generate and execute Python code. If clarification is needed, ask the user.
"""

def parse_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_doc(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return "\n".join([reader.pages[i].extract_text() for i in range(len(reader.pages))])

def parse_spreadsheet(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)
    return None

def encode_image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def parse_image(file_path, prompt="Describe the contents of this image."):
    base64_image = encode_image_to_base64(file_path)
    client = Together(api_key=TOGETHER_API_KEY)
    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}]
    )
    return response.choices[0].message.content

def analyze_data(df):
    summary = {
        "mean": df.mean(numeric_only=True).to_dict(),
        "median": df.median(numeric_only=True).to_dict(),
        "std": df.std(numeric_only=True).to_dict(),
        "correlation": df.corr().to_dict()
    }
    return summary


def query_data(df, question):
    summary = analyze_data(df)
    prompt = f"Data summary: {summary}\nUser question: {question}\nProvide a detailed answer."
    client = Together(api_key=TOGETHER_API_KEY)
    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def create_visualization(df, plot_type, x_col, y_col=None):
    plt.figure(figsize=(10, 6))
    if plot_type == "bar":
        sns.barplot(x=x_col, y=y_col, data=df)
    elif plot_type == "line":
        sns.lineplot(x=x_col, y=y_col, data=df)
    elif plot_type == "scatter":
        sns.scatterplot(x=x_col, y=y_col, data=df)
    plt.title(f"{plot_type.capitalize()} Plot")
    output_path = "output.png"
    plt.savefig(output_path)
    plt.close()
    return output_path

def answer_text_question(file_content, question):
    prompt = f"Context: {file_content}\nQuestion: {question}\nAnswer based on the context."
    client = Together(api_key=TOGETHER_API_KEY)
    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def answer_image_question(file_path, question):
    base64_image = encode_image_to_base64(file_path)
    client = Together(api_key=TOGETHER_API_KEY)
    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}]
    )
    return response.choices[0].message.content

def handle_followup_question(conversation_history, question):
    messages = conversation_history + [{"role": "user", "content": question}]
    client = Together(api_key=TOGETHER_API_KEY)
    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=messages
    )
    answer = response.choices[0].message.content
    updated_history = conversation_history + [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    return answer, updated_history

def data_analyst_agent(file_path, user_request, conversation_history=[]):
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in ['.csv', '.xlsx']:
        df = parse_spreadsheet(file_path)
        if "visualize" in user_request.lower():
            plot_type = "bar"
            x_col = df.columns[0]
            y_col = df.columns[1] if len(df.columns) > 1 else None
            return create_visualization(df, plot_type, x_col, y_col), conversation_history
        elif "analyze" in user_request.lower():
            answer = query_data(df, user_request)
            updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": answer}]
            return answer, updated_history
    elif file_ext in ['.txt', '.doc', '.pdf']:
        if file_ext == '.txt':
            content = parse_text(file_path)
        elif file_ext == '.doc':
            content = parse_doc(file_path)
        elif file_ext == '.pdf':
            content = parse_pdf(file_path)
        answer = answer_text_question(content, user_request)
        updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": answer}]
        return answer, updated_history
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        answer = answer_image_question(file_path, user_request)
        updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": answer}]
        return answer, updated_history
    else:
        return "Unsupported file type.", conversation_history

print("Data Analyst Agent is ready to process requests.")

