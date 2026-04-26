# 🤖 RAG-Based Customer Support Assistant

This project is a Retrieval-Augmented Generation (RAG) system designed to build an intelligent customer support assistant. It uses a PDF-based knowledge base to retrieve relevant information and generate context-aware responses using a Large Language Model (Google Gemini).

The system is enhanced with LangGraph for workflow orchestration and includes a Human-in-the-Loop (HITL) mechanism for handling low-confidence queries.

---

## 🎯 Project Objective

The main objective of this project is to design and implement a scalable AI-based customer support system that:
- Retrieves relevant information from a PDF knowledge base
- Generates intelligent responses using an LLM
- Uses workflow control for decision-making
- Includes human intervention for uncertain cases(HITL)
- Provides API documentation using Swagger
- Offers a user-friendly interface

---
## ⭐ Key Features

- 📄 PDF-based knowledge ingestion
- 🔍 Semantic search using embeddings
- 🗂 Vector storage using ChromaDB
- 🤖 Response generation using Google Gemini
- 🔁 LangGraph-based workflow orchestration
- 🤝 Human-in-the-Loop (HITL) escalation system
- 🌐 Interactive UI (Frontend)
- 📘 Swagger API documentation for testing endpoints

---

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

---
## 📘 Swagger API Documentation

After running the project, open:
```
http://localhost:8000/docs
```
👉 This provides interactive API testing for all backend endpoints.

## 🎥 Project Demo

- Input: User query is asked in terminal
- Output: Contextual answer from RAG system
- HITL: Activated when confidence is low

👉 Example:
User: What is refund policy?
Bot: Refunds are allowed within 7 days...

---

## 🏗 System Architecture


<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/216328bd-fc9f-45d4-974e-7441b876446b" />

---

## 🛠 Tech Stack

- Python  
- LangChain  
- LangGraph  
- ChromaDB  
- Google Gemini API  
- PyPDF
- FastAPI
- Swagger UI
- HTML, CSS, JavaScript

---
## 🎨 UI Features
- Interactive chat interface
- Real-time query-response system
- Integrated backend communication
- Improved user experience over CLI version

---

## 🚀 Future Enhancements
Multi-document knowledge base
Authentication system
Cloud deployment (AWS / GCP)
Advanced intent classification
Chat history memory

---

## 📸 Screenshots

<img width="1371" height="845" alt="image" src="https://github.com/user-attachments/assets/2be0fe2c-a51c-4ea4-8591-ad8078b4feaa" />

### Console version outputs
### 🧪 Query Response Example
- Shows how the system retrieves relevant information from the PDF knowledge base and generates a response using Gemini LLM.

<img width="1243" height="902" alt="image" src="https://github.com/user-attachments/assets/7c3a5eb1-1392-4186-893f-fac316ed7764" />

<br>
<img width="1276" height="957" alt="image" src="https://github.com/user-attachments/assets/6308db64-44ba-425d-9d5d-72275d7e234b" />

<br>
<img width="1276" height="930" alt="image" src="https://github.com/user-attachments/assets/b7317c76-10b3-43b7-8ee5-b545f456686b" />

### 🤝 Human-in-the-Loop (HITL) Activation Example
- Shows the system triggering HITL when confidence is low and asking for human intervention.
<img width="1088" height="379" alt="image" src="https://github.com/user-attachments/assets/85ba951c-5952-48cb-b69d-6b91bb295fad" />


### UI version outputs

### Dashboard

<img width="1916" height="912" alt="image" src="https://github.com/user-attachments/assets/fa6796ab-a558-4d8d-9994-f98feca66f31" />


### 🧪 Query Response Example

<img width="1915" height="905" alt="image" src="https://github.com/user-attachments/assets/c6925822-2681-43bc-b16a-8476ef396291" />
<br>
<img width="1911" height="906" alt="image" src="https://github.com/user-attachments/assets/18f365a9-54bd-46ed-903b-d4bd37b000a2" />

### 🤝 Human-in-the-Loop (HITL) Activation Example

<img width="1908" height="951" alt="image" src="https://github.com/user-attachments/assets/a050d818-c55f-4a93-8afd-af38a2ac42fd" />


## Fast API SWAGGER Output
<img width="1874" height="883" alt="image" src="https://github.com/user-attachments/assets/ea84e9a0-e7f5-4f82-8872-6d6c3840125a" />

---

## 🎥 Demo Video

👉 Watch Full Demo Here: https://drive.google.com/drive/folders/1mV1dEcCnXME8kCKfzgECmMC3luI1k5d1?usp=drive_link

---

## 🔗 LinkedIn Post
https://www.linkedin.com/posts/tejasri-somarouthu-78aa83355_generativeai-artificialintelligence-rag-ugcPost-7453901211042480128-6qQC?utm_source=share&utm_medium=member_desktop&rcm=ACoAAFidKJoBRLvumfdgwfmIDItuHoJpdXkBZuI

---

## 📝 Note

Due to ongoing semester examinations, this project was completed within limited time. A refined version with improved UI and explanation will be updated soon. The presentation PPT was created using the AI tool Gamma.

---

## 📌 Outcome

A fully functional AI-powered customer support system combining retrieval-based search with generative AI, making responses more accurate, scalable, and production-ready.

---
## 🙏 Acknowledgement

This project was developed as part of my Generative AI Internship at Innomatics Research Labs.
It provided hands-on experience in building real-world AI systems using RAG architecture.

---
## 👨‍💻Author 
**Tejasri - IN226103402(Gen-AI intern)**


  
