# Technical Documentation: RAG-Based Customer Support Assistant

## 3. Technical Documentation

### 3.1 What is RAG?
**Simple Explanation:** Imagine an open-book exam. If you ask a student a question from memory, they might guess or remember incorrectly (hallucination). RAG (Retrieval-Augmented Generation) is like giving the student the exact textbook page containing the answer before they respond. It "augments" the AI's generation process by "retrieving" facts first.

**Technical Explanation:** RAG is an architecture that grounds Large Language Models (LLMs) on proprietary or external data. It solves the limitation of LLMs having a static training cutoff. By indexing documents into a dense vector space (using embeddings) and performing a similarity search against a user's query, RAG retrieves the most semantically relevant text chunks. These chunks are injected into the LLM's prompt context window, forcing the model to synthesize an answer based *only* on the provided data, significantly reducing hallucinations.

### 3.2 System Architecture Overview
The system relies on a **stateful graph architecture** orchestrated by LangGraph. Unlike traditional linear RAG pipelines (Query -> Retrieve -> Answer), this architecture introduces conditional routing. The workflow evaluates the user query, determines the path (RAG vs. Direct Escalation), performs retrieval, generates an answer with a confidence score, and contains cycles/interruptions to allow Human-in-the-Loop (HITL) intervention when automated resolution fails.

### 3.3 Design Decisions

*   **Chunk Size (1000 chars, 200 overlap):** 
    *   *Why:* 1000 characters is approximately 200-250 words, which is usually enough to capture a full paragraph or a complete thought in a manual. The 200-character overlap prevents cutting off mid-sentence, ensuring the LLM doesn't lose context at the boundaries.
*   **Embedding Choice (`models/gemini-embedding-2`):** 
    *   *Why:* Google's `gemini-embedding-2` provides state-of-the-art semantic representation at a very low cost (with free tier limits). For completely local/free execution, HuggingFace's BGE models (e.g., `BAAI/bge-small-en`) are top-tier open-source alternatives.
*   **Retrieval Method (Cosine Similarity):** 
    *   *Why:* Cosine similarity measures the angle between vectors rather than their magnitude. This is highly effective for text search, where a short query and a long document chunk might have different magnitudes but point in the same semantic direction.
*   **Prompt Engineering (Strict Context Grounding):** 
    *   *Why:* The prompt explicitly instructs: "Answer the question using ONLY the provided context. If the context does not contain the answer, output a confidence of 0.0." This constraint is critical for customer support to prevent the LLM from making up company policies.

### 3.4 Workflow Explanation (LangGraph)
*   **Nodes:** The system consists of distinct functional blocks: `Retrieve` (calls vector DB), `Generate` (calls LLM), and `HITL` (pauses execution). 
*   **State Movement:** Every node receives the `AgentState` object, mutates a specific key (e.g., the `Retrieve` node appends to `state["context"]`), and returns the mutated state. LangGraph handles passing this updated state to the next node.

### 3.5 Conditional Logic Explanation
The edges between nodes aren't hardcoded; they are evaluated dynamically:
1.  **Post-Generation Check:** After the `Generate` node, a conditional function checks the LLM's self-reported `confidence` score.
2.  **Routing:** If `confidence > 0.8`, the graph routes to the `END` node, outputting the answer to the user. If `confidence <= 0.8`, it routes to the `HITL` node. This prevents sending unsure, potentially harmful answers to customers.

### 3.6 Human-in-the-Loop (HITL)
*   **Benefits:** Guarantees 100% accuracy on complex or novel queries. Builds user trust because they aren't stuck in an endless "I don't understand" AI loop. It also allows the organization to collect data on questions the RAG system fails at, highlighting areas to improve documentation.
*   **Limitations:** Introduces latency. The graph state must be saved to disk/DB (check-pointing) because a human might take 10 minutes or 2 hours to respond.

### 3.7 Challenges and Trade-offs
*   **Trade-off: Speed vs. Accuracy.** Adding self-reflection (LLM grading its own confidence) adds an extra LLM call or requires a more complex, slower structured output generation, increasing latency but drastically improving accuracy.
*   **Challenge: Table/Image Parsing in PDFs.** Standard text loaders struggle with tables in PDFs. *Workaround:* For this phase, we rely on raw text extraction, but future phases would require OCR or specialized parsers (like `UnstructuredLoader`).

### 3.8 Testing Strategy
**Unit Testing:** Test the router logic (ensure trigger words always route to HITL).
**Integration Testing (Sample Queries):**
1.  *Standard RAG Query:* "How do I factory reset my device?" -> Should route to Retrieve -> Generate -> Output.
2.  *Out-of-Scope Query:* "What is the meaning of life?" -> Retrieve (returns irrelevant chunks) -> Generate (detects no answer) -> Low Confidence -> Routes to HITL.
3.  *Escalation Query:* "I want to speak to a human." -> Direct routing to HITL.

### 3.9 Future Enhancements
*   **Semantic Caching:** Store common queries and their answers (e.g., using Redis) to bypass the LLM entirely for frequently asked questions, saving cost and time.
*   **Multi-Query Retrieval:** Have an LLM rewrite the user's initial query into 3 different variations before searching ChromaDB to improve the chances of finding the right chunks.
