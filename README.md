**Intelligent Data Analyst Agent**

Overview

The Intelligent Data Analyst Agent is a Streamlit-based web application that provides advanced data analysis and visualization capabilities. Powered by the Together AI API (using the Llama-4-Maverick model), it intelligently processes user requests to analyze structured data (CSV, Excel), unstructured data (text, documents), and images. The agent dynamically generates Python code for custom analyses and visualizations, maintains conversation context for follow-up questions, and delivers insightful results.

Key features:





Dynamic Analysis: Generates tailored Python code for statistical analysis (e.g., correlations, outliers) and visualizations (e.g., histograms, scatter plots).



Context-Aware: Tracks conversation history to handle follow-up questions.



Multimodal Support: Analyzes CSV, Excel, TXT, DOC, PDF, PNG, JPG, and JPEG files.



Robust Error Handling: Ensures smooth operation with clear feedback for invalid inputs.

This project is ideal for users working with datasets like Medicaldataset.csv for applications in fields such as cardiac diagnostics.

Installation

Prerequisites





Python 3.8 or higher



A Together AI API key (sign up at Together AI)



Streamlit Cloud account (for deployment)

Local Setup





Clone the Repository:

'''git clone <your-repository-url>'''
'''cd <repository-name>'''



Install Dependencies: Create a virtual environment and install the required libraries:

'''python -m venv venv'''
'''source venv/bin/activate'''  # On Windows: '''venv\Scripts\activate'''
'''pip install -r requirements.txt'''



Set Up API Key: Create a .env file in the project root with your Together AI API key:

TOGETHER_API_KEY=your_actual_api_key_here



Run the App: Start the Streamlit app locally:

'''streamlit run app.py'''

Open your browser to http://localhost:8501.

Streamlit Cloud Deployment





Push to GitHub: Push your repository (containing app.py, model.py, and requirements.txt) to a GitHub repository.



Set Up Streamlit Cloud:





Log into Streamlit Cloud.



Create a new app and link it to your GitHub repository.



In the app settings, go to Secrets and add:

TOGETHER_API_KEY = "your_actual_api_key_here"



Deploy: Deploy the app. Streamlit Cloud will install dependencies from requirements.txt and run app.py.

Usage





Access the App:





Locally: Navigate to http://localhost:8501.



Streamlit Cloud: Use the app’s public URL.



Upload a File:





Upload a supported file (CSV, XLSX, TXT, DOC, PDF, PNG, JPG, JPEG), e.g., Medicaldataset.csv.



Enter a Request:





Input a request like:





“Visualize heart rate trends.”



“Analyze correlations between age and blood pressure.”



“Identify outliers in cholesterol.”



The agent generates and executes Python code for analysis or visualization.



View Results:





Results include text output (e.g., statistical summaries) and visualizations (e.g., plots saved as output.png).



Follow up with questions like “Which patients have high heart rates?” to leverage conversation history.

Example





File: Medicaldataset.csv (columns: age, heart_rate, blood_pressure)



Request: “visualize”



Output: A histogram of numeric columns (e.g., age, heart_rate) displayed in the app.



Follow-Up: “Show high heart rates.”





Output: A list of patients with heart rates above a threshold (e.g., 100).

Project Structure





app.py: Streamlit frontend for user interaction.



model.py: Core logic for file parsing, code generation, and API calls.



requirements.txt: Dependencies for Streamlit Cloud.



README.md: This file.

Dependencies

Listed in requirements.txt:





streamlit



pandas



numpy



matplotlib



seaborn



python-docx



PyPDF2



together

Troubleshooting





AuthenticationError: Ensure TOGETHER_API_KEY is set correctly in Streamlit Cloud secrets or .env.



ModuleNotFoundError: Verify all dependencies are installed via requirements.txt.



Code Execution Errors: Check Streamlit Cloud logs ('Manage app' > 'Logs') for details.



Contact: For issues, open a GitHub issue or contact the maintainer.

Contributing

Contributions are welcome! Please:





Fork the repository.



Create a feature branch (git checkout -b feature-name).



Commit changes (git commit -m 'Add feature').



Push to the branch (git push origin feature-name).



Open a pull request.

