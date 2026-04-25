# Setup Instructions

## 1. Environment Setup

1.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    ```
2.  **Activate the Virtual Environment:**
    *   Windows: `venv\Scripts\activate`
    *   Mac/Linux: `source venv/bin/activate`
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 2. API Keys

Create a file named `.env` in the root directory (`d:\innomatics\Rag-Project\.env`) and add your Google API key:

```env
GOOGLE_API_KEY=your-google-api-key-here
```

*(Note: You can replace the Gemini models with other alternatives in `app.py` if needed).*

## 3. Running the Application

1.  **Ingest a Document (Optional but Recommended):**
    *   Place a sample PDF in your project directory (e.g., `sample_manual.pdf`).
    *   Open `app.py`, scroll to the bottom (`if __name__ == "__main__":`), uncomment the `pdf_path` and `setup_vector_store()` lines, and run it once to build the ChromaDB index.
    
2.  **Execute the LangGraph Workflow:**
    ```bash
    python app.py
    ```

## 4. How the Human-in-the-Loop (HITL) Simulation Works

When you run `app.py`, it simulates a workflow:
1.  It asks a query: "How do I reset my password?"
2.  If the vector DB doesn't have the answer, the LLM will grade itself with a `0.0` confidence score.
3.  The LangGraph router intercepts this low score and **pauses execution**.
4.  The script will prompt you in the terminal: `Human Agent, provide the answer:`
5.  Type your response and hit enter. The graph resumes and delivers your human answer as the final output.
