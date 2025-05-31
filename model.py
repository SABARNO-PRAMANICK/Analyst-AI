import os
import subprocess
import pandas as pd
from together import Together
import base64
import docx
import PyPDF2
import streamlit as st

TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY not found in Streamlit secrets or environment variables.")

SYSTEM_PROMPT = """You are an expert data scientist with advanced analytical skills. Your capabilities include:
- Analyzing structured data (CSV, Excel) with statistical methods (e.g., correlations, trends, outliers).
- Generating Python code for custom analyses or visualizations (e.g., bar, line, scatter plots) using pandas, matplotlib, or seaborn, saving visualizations to 'output.png'.
- Interpreting unstructured data (text, documents) and answering questions with context.
- Extracting and analyzing content from images (e.g., text, patterns).
- Maintaining conversation context for follow-up questions.
- Providing insightful, concise responses and asking for clarification if needed.

For requests involving data analysis or visualization, return *only* executable Python code wrapped in ```python``` markers. Use pandas to read 'temp_data.csv' and save visualizations to 'output.png'. For non-code requests, provide a detailed answer. If the request is unclear, suggest a relevant analysis or visualization and return the corresponding code or answer."""

def parse_spreadsheet(file_path):
    """Parse CSV or Excel files into a pandas DataFrame."""
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            return pd.read_excel(file_path)
        return None
    except Exception as e:
        return f"Error parsing spreadsheet: {str(e)}"

def generate_data_summary(df):
    """Generate a detailed summary of a DataFrame."""
    if isinstance(df, str):  # Error message from parsing
        return df
    summary = f"Columns: {list(df.columns)}\n"
    summary += f"Rows: {len(df)}\n"
    summary += f"Data Types:\n{df.dtypes.to_string()}\n"
    summary += f"Basic Statistics:\n{df.describe().to_string()}\n"
    summary += f"Missing Values:\n{df.isnull().sum().to_string()}\n"
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        summary += f"Correlations:\n{df[numeric_cols].corr().to_string()}"
    return summary

def parse_text(file_path):
    """Parse text files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error parsing text file: {str(e)}"

def parse_doc(file_path):
    """Parse .doc files."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error parsing .doc file: {str(e)}"

def parse_pdf(file_path):
    """Parse PDF files."""
    try:
        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            return "\n".join([pdf.pages[i].extract_text() for i in range(len(pdf.pages))])
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

def encode_image_to_base64(file_path):
    """Encode image files to base64 for API use."""
    try:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        return f"Error encoding image: {str(e)}"

def extract_code(response):
    """Extract Python code from the model response."""
    # Look for code block with ```python or ```
    code_pattern = r'```(?:python)?\n(.*?)\n```'
    match = re.search(code_pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()
    # If no code block, return None to trigger fallback
    return None

def execute_code(code, df):
    """Execute generated Python code securely."""
    if isinstance(df, str):  # Error from parsing
        return df, None
    try:
        df.to_csv('temp_data.csv', index=False)
        with open('temp_script.py', 'w') as f:
            f.write(code)
        result = subprocess.run(
            ['python', 'temp_script.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        stdout, stderr = result.stdout, result.stderr
        image_path = 'output.png' if os.path.exists('output.png') else None
        if result.returncode == 0:
            return stdout or "Analysis completed.", image_path
        else:
            return f"Code execution error: {stderr}", None
    except subprocess.TimeoutExpired:
        return "Timeout: Code execution exceeded 30 seconds.", None
    except Exception as e:
        return f"Error executing code: {str(e)}", None
    finally:
        if os.path.exists('temp_data.csv'):
            os.remove('temp_data.csv')
        if os.path.exists('temp_script.py'):
            os.remove('temp_script.py')

def data_analyst_agent(file_path, user_request, conversation_history=[]):
    """Main agent function for intelligent data analysis."""
    file_ext = os.path.splitext(file_path)[1].lower()
    client = Together(api_key=TOGETHER_API_KEY)
    
    # Build conversation history string
    history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history])
    
    # Process based on file type
    if file_ext in ['.csv', '.xlsx']:
        df = parse_spreadsheet(file_path)
        if isinstance(df, str):  # Error from parsing
            updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": df}]
            return df, None, updated_history
        
        data_summary = generate_data_summary(df)
        prompt = f"Previous conversation:\n{history_str}\n\nData summary:\n{data_summary}\n\nUser request: {user_request}\n\nReturn *only* executable Python code wrapped in ```python``` to address the request. Use pandas to read 'temp_data.csv'. For visualizations, use matplotlib/seaborn and save to 'output.png'. For analysis, print results. If the request is unclear (e.g., 'visualize'), generate code for a default visualization (e.g., histograms for numeric columns, bar chart for categorical columns)."
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            max_tokens=2000
        )
        raw_response = response.choices[0].message.content.strip()
        
        # Extract code from response
        code = extract_code(raw_response)
        if not code:
            # Fallback: Generate a default visualization (histogram for numeric columns)
            code = """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
df = pd.read_csv('temp_data.csv')
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
plt.figure(figsize=(10, 6))
for col in numeric_cols:
    sns.histplot(df[col], label=col, kde=True)
plt.title('Histograms of Numeric Columns')
plt.legend()
plt.savefig('output.png')
"""
            text_response = "No valid code provided by the model. Generating default histograms for numeric columns."
        else:
            text_response = "Analysis completed."
        
        # Execute the generated or fallback code
        stdout, image_path = execute_code(code, df)
        text_response = f"{text_response}\nOutput:\n{stdout}" + (f"\n\nVisualization saved to {image_path}" if image_path else "")
        updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": text_response}]
        return text_response, image_path, updated_history
    
    elif file_ext in ['.txt', '.doc', '.pdf']:
        content = parse_text(file_path) if file_ext == '.txt' else parse_doc(file_path) if file_ext == '.doc' else parse_pdf(file_path)
        if isinstance(content, str) and content.startswith("Error"):
            updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": content}]
            return content, None, updated_history
            
        prompt = f"Previous conversation:\n{history_str}\n\nDocument content: {content[:1000]}\n\nUser request: {user_request}\n\nProvide a detailed answer based on the content and history. If the request involves analysis, suggest relevant insights."
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            max_tokens=1000
        )
        text_response = response.choices[0].message.content
        updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": text_response}]
        return text_response, None, updated_history
    
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        base64_image = encode_image_to_base64(file_path)
        if isinstance(base64_image, str) and base64_image.startswith("Error"):
            updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": base64_image}]
            return base64_image, None, updated_history
            
        prompt = f"Previous conversation:\n{history_str}\n\nUser request: {user_request}\n\nAnalyze the image content and provide a response."
        messages = conversation_history + [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}]
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            max_tokens=1000
        )
        text_response = response.choices[0].message.content
        updated_history = messages + [{"role": "assistant", "content": text_response}]
        return text_response, None, updated_history
    
    else:
        text_response = "Unsupported file type. Please upload a CSV, XLSX, TXT, DOC, PDF, PNG, JPG, or JPEG file."
        updated_history = conversation_history + [{"role": "user", "content": user_request}, {"role": "assistant", "content": text_response}]
        return text_response, None, updated_history