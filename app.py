import os
from typing import TypedDict, List
from pydantic import BaseModel, Field

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Using Free Alternatives!
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

# Load environment variables (e.g., GOOGLE_API_KEY)
load_dotenv()

# ==========================================
# 1. DATA STRUCTURES & STATE
# ==========================================

class AgentState(TypedDict):
    """The state dictionary passed between LangGraph nodes."""
    query: str
    context: List[str]
    draft_answer: str
    confidence: float
    final_answer: str
    needs_escalation: bool
    human_input: str

class LLMResponse(BaseModel):
    """Structured output expected from the LLM."""
    answer: str = Field(description="The answer to the user's query based on the context. If context is empty, return 'I do not have enough information'.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0. Set below 0.8 if you are unsure or context is missing.")
    needs_escalation: bool = Field(description="Set to true if the user asks for a human, or if you cannot answer the query using the context.")

# ==========================================
# 2. DOCUMENT INGESTION PIPELINE
# ==========================================

def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

def setup_vector_store(pdf_path: str, persist_directory: str = "./chroma_db"):
    """Loads a PDF, chunks it, and stores in ChromaDB."""
    print(f"\n[Ingestion] Loading PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"[Error] File not found: {pdf_path}. Skipping ingestion.")
        return None
        
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    
    # Clean chunks to prevent empty-string API errors
    chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
    
    embeddings = get_embeddings_model()
    
    # Clear the old database so old PDFs don't mix with new ones
    import shutil
    if os.path.exists(persist_directory):
        try:
            shutil.rmtree(persist_directory)
        except Exception:
            pass
            
    print(f"[Ingestion] Indexing {len(chunks)} chunks into a fresh ChromaDB...")
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    
    for i, chunk in enumerate(chunks):
        try:
            vectorstore.add_documents([chunk])
        except Exception as e:
            print(f"[Warning] Failed to index chunk {i+1}. It might be unreadable by the API. Skipping.")
            
    print("[Ingestion] Complete.")
    return vectorstore

def get_retriever(persist_directory: str = "./chroma_db"):
    """Loads existing ChromaDB as a retriever."""
    embeddings = get_embeddings_model()
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 3})

# ==========================================
# 3. LANGGRAPH NODES
# ==========================================

def retrieve_node(state: AgentState):
    """Retrieves relevant chunks from ChromaDB."""
    print("--- NODE: RETRIEVE ---")
    query = state["query"]
    retriever = get_retriever()
    try:
        docs = retriever.invoke(query)
        context = [doc.page_content for doc in docs]
    except Exception as e:
        context = []
        print(f"Retrieval warning/error (Vector DB might be empty): {e}")
        
    return {"context": context}

def generate_node(state: AgentState):
    """Generates answer using LLM and strict context."""
    print("--- NODE: GENERATE ---")
    query = state["query"]
    context = state["context"]
    
    # Switch to Google Gemini (Free Tier available)
    # Ensure you have GOOGLE_API_KEY in your .env file
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    parser = JsonOutputParser(pydantic_object=LLMResponse)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a customer support AI. You must answer the user's query using ONLY the provided context.\n"
                   "If the context is empty or does not contain the answer, set confidence to 0.0 and needs_escalation to true.\n"
                   "Context: {context}\n\n"
                   "Respond strictly in JSON matching this schema: {format_instructions}"),
        ("user", "Query: {query}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        context_str = "\n\n".join(context) if context else "No context found."
        response = chain.invoke({
            "query": query, 
            "context": context_str,
            "format_instructions": parser.get_format_instructions()
        })
        
        return {
            "draft_answer": response["answer"],
            "confidence": float(response.get("confidence", 0.0)),
            "needs_escalation": response.get("needs_escalation", True)
        }
    except Exception as e:
        print(f"Generation error: {e}")
        return {
            "draft_answer": "Error generating response. Ensure GOOGLE_API_KEY is valid.",
            "confidence": 0.0,
            "needs_escalation": True
        }

def human_intervention_node(state: AgentState):
    """Paused state waiting for Human input."""
    print("--- NODE: HUMAN_INTERVENTION (HITL) ---")
    human_input = state.get("human_input", "")
    
    if human_input:
        return {"final_answer": f"[Human Agent]: {human_input}"}
    else:
        return {"final_answer": "[System]: Escalated to support ticket. An agent will contact you."}

def finalize_node(state: AgentState):
    """Finalizes the automated response if confidence is high."""
    print("--- NODE: FINALIZE ---")
    return {"final_answer": f"[AI]: {state['draft_answer']}"}

# ==========================================
# 4. CONDITIONAL ROUTING
# ==========================================

def initial_router(state: AgentState):
    """Decides if we should retrieve or go straight to human."""
    query = state["query"].lower()
    escalation_keywords = ["human", "agent", "manager", "lawyer", "sue", "complaint"]
    
    if any(keyword in query for keyword in escalation_keywords):
        print("--- ROUTER: Escalate Trigger Detected in Query ---")
        return "human_intervention_node"
    print("--- ROUTER: Proceeding to Retrieval ---")
    return "retrieve_node"

def evaluate_confidence(state: AgentState):
    """Decides if the generated answer is good enough or needs a human."""
    confidence = state.get("confidence", 0.0)
    needs_escalation = state.get("needs_escalation", False)
    
    if needs_escalation or confidence < 0.8:
        print(f"--- EVALUATOR: Low Confidence ({confidence}) or Escalation Flagged. Routing to HITL ---")
        return "human_intervention_node"
    
    print(f"--- EVALUATOR: High Confidence ({confidence}). Outputting Answer ---")
    return "finalize_node"

# ==========================================
# 5. GRAPH BUILDER
# ==========================================

def build_graph():
    """Compiles the LangGraph state machine."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve_node", retrieve_node)
    workflow.add_node("generate_node", generate_node)
    workflow.add_node("human_intervention_node", human_intervention_node)
    workflow.add_node("finalize_node", finalize_node)
    
    workflow.set_conditional_entry_point(
        initial_router,
        {"retrieve_node": "retrieve_node", "human_intervention_node": "human_intervention_node"}
    )
    
    workflow.add_edge("retrieve_node", "generate_node")
    
    workflow.add_conditional_edges(
        "generate_node",
        evaluate_confidence,
        {"human_intervention_node": "human_intervention_node", "finalize_node": "finalize_node"}
    )
    
    workflow.add_edge("human_intervention_node", END)
    workflow.add_edge("finalize_node", END)
    
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["human_intervention_node"])
    return app

# ==========================================
# 6. RUN EXECUTION & HITL SIMULATION
# ==========================================
# 6. RUN EXECUTION & HITL SIMULATION (INTERACTIVE)
# ==========================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  RAG Support Assistant (LangGraph + HITL) - Free Tier")
    print("="*50)
    
    # 1. Dynamic PDF Loading
    print("\n[Setup] Let's configure the knowledge base.")
    print("Please select a PDF file from the popup window (or click Cancel to skip)...")
    
    # Use Tkinter to open a visual file picker
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw() # Hide the small empty tkinter window
    root.attributes('-topmost', True) # Force the file dialog to pop up on top of other windows
    
    pdf_choice = filedialog.askopenfilename(
        title="Select a PDF Knowledge Base",
        filetypes=[("PDF files", "*.pdf")]
    )
    
    if pdf_choice:
        print(f"Selected: {pdf_choice}")
        setup_vector_store(pdf_choice)
    else:
        print("No file selected. Proceeding with existing database.")
    
    # 2. Build Graph & State
    app = build_graph()
    thread_config = {"configurable": {"thread_id": "session_001"}}
    
    print("\n" + "="*50)
    print("  SYSTEM READY. Type 'exit' or 'quit' to stop.")
    print("="*50)
    
    # 3. Interactive Query Loop
    while True:
        user_query = input("\n[Customer Query]: ").strip()
        
        if user_query.lower() in ['exit', 'quit']:
            print("Shutting down support assistant. Goodbye!")
            break
            
        if not user_query:
            continue
            
        initial_state = {
            "query": user_query,
            "context": [],
            "draft_answer": "",
            "confidence": 0.0,
            "final_answer": "",
            "needs_escalation": False,
            "human_input": ""
        }
        
        # Run graph
        for event in app.stream(initial_state, thread_config):
            # You can uncomment this to debug the exact nodes executing
            # for key in event.keys(): print(f"  -> Executed node: {key}")
            pass
                
        # Check if graph paused for HITL
        current_state = app.get_state(thread_config)
        if current_state.next:
            print("\n" + "!"*50)
            print("  WORKFLOW PAUSED: Human Agent Intervention Required")
            print("!"*50)
            
            draft = current_state.values.get('draft_answer', 'None')
            conf = current_state.values.get('confidence', 0.0)
            reason = "User requested agent" if current_state.values.get('needs_escalation') else f"Low Confidence ({conf})"
            
            print(f"\nSystem Reason for Escalation: {reason}")
            print(f"Drafted Answer: {draft}")
            
            print("\n--- Agent Terminal ---")
            human_response = input("Type the correct answer for the user: ")
            
            # Update the state with human input
            app.update_state(thread_config, {"human_input": human_response})
            
            # Resume the graph
            for event in app.stream(None, thread_config):
                pass
                
        # Print Final Output
        final_state = app.get_state(thread_config)
        print("\n[Final Output]: " + final_state.values.get("final_answer", "Error."))