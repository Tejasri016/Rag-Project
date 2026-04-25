# RAG-Based Customer Support Assistant - Low-Level Design (LLD)

## 2. Low-Level Design (LLD)

### 2.1 Module-wise Breakdown

#### 2.1.1 Document Processing Module
*   **Purpose:** Ingests raw PDF documents and extracts text content.
*   **Input:** File path to the PDF (`str`).
*   **Process:** Utilizes `PyPDFLoader` from `langchain_community.document_loaders`. It iterates through each page, extracting text and metadata (like page number and source file).
*   **Output:** List of `Document` objects.

#### 2.1.2 Chunking Module
*   **Purpose:** Breaks down large extracted texts into semantically contiguous segments.
*   **Input:** List of `Document` objects.
*   **Process:** Utilizes `RecursiveCharacterTextSplitter`.
    *   `chunk_size`: 1000 characters (ensures enough context for the LLM).
    *   `chunk_overlap`: 200 characters (prevents splitting sentences/ideas abruptly).
    *   `separators`: `["\n\n", "\n", " ", ""]` (prioritizes splitting at paragraphs, then sentences, then words).
*   **Output:** List of chunked `Document` objects.

#### 2.1.3 Embedding Module
*   **Purpose:** Generates vector embeddings for text chunks and queries.
*   **Input:** Text string (`str`).
*   **Process:** Uses an embedding model (e.g., `GoogleGenerativeAIEmbeddings` with `models/gemini-embedding-2` or `HuggingFaceEmbeddings` for open-source). Converts the text into a fixed-length float array representing semantic meaning.
*   **Output:** Float array (Vector: `List[float]`).

#### 2.1.4 Retrieval Module
*   **Purpose:** Fetches the most relevant document chunks based on a user query.
*   **Input:** Embedded User Query (`List[float]`).
*   **Process:** Connects to ChromaDB. Performs a similarity search (Cosine Similarity or L2 distance). Returns the top-k (e.g., k=3) chunks.
*   **Output:** List of `Document` objects (Context).

#### 2.1.5 Query Processing Module
*   **Purpose:** Interacts with the LLM to generate the final response.
*   **Input:** User Query (`str`), Context Chunks (`List[str]`).
*   **Process:** Formats a strict prompt template instructing the LLM to answer *only* using the provided context. Requires the LLM to return a structured JSON response containing the `answer` and a self-rated `confidence_score` (0.0 to 1.0).
*   **Output:** JSON Object containing the answer and confidence score.

#### 2.1.6 Graph Execution Module (LangGraph)
*   **Purpose:** Orchestrates the state flow between routing, retrieval, generation, and escalation.
*   **Input:** Initial Graph State.
*   **Process:** Executes nodes based on edge conditions. Manages the persistence of state using `MemorySaver` (in-memory checkpointer).
*   **Output:** Final Graph State containing the final answer.

#### 2.1.7 HITL Module
*   **Purpose:** Handles human intervention when automated resolution fails.
*   **Input:** Current Graph State (containing query, context, and failed draft/reason).
*   **Process:** Interrupts the graph execution. Waits for external input (human updating the state with a manual answer). Resumes the graph once input is received.
*   **Output:** Updated Graph State with human-provided answer.

---

### 2.2 Data Structures

#### 2.2.1 Graph State Object (`TypedDict`)
The central state passed between all LangGraph nodes.
```python
from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    question: str
    context: List[str]
    draft_answer: str
    final_answer: str
    confidence: float
    escalate_reason: str
    human_input: str
```

#### 2.2.2 Query-Response Schema (LLM Structured Output)
Used to force the LLM to return a standardized format.
```python
from pydantic import BaseModel, Field

class LLMResponse(BaseModel):
    answer: str = Field(description="The formulated answer based on context.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0.")
    needs_escalation: bool = Field(description="True if the query cannot be answered using the context.")
```

#### 2.2.3 Document & Chunk Format
```json
{
  "page_content": "To reset your password, navigate to settings and click...",
  "metadata": {
    "source": "user_manual.pdf",
    "page": 12,
    "chunk_id": "doc1_chunk4"
  }
}
```

---

### 2.3 LangGraph Workflow Logic

#### 2.3.1 Nodes (Functions that modify the State)
1.  **`retrieve_node`**: Takes `state["question"]`, queries ChromaDB, updates `state["context"]`.
2.  **`generate_node`**: Takes `state["question"]` and `state["context"]`, calls LLM. Updates `state["draft_answer"]` and `state["confidence"]`.
3.  **`human_intervention_node`**: A dummy node where execution is paused. Takes `state["human_input"]` and sets it as `state["final_answer"]`.

#### 2.3.2 Edges (Conditional Transitions)
1.  **START -> Router Logic**: Checks if query needs direct escalation (e.g., regex matching "speak to human").
    *   If True -> `human_intervention_node`
    *   If False -> `retrieve_node`
2.  **`retrieve_node` -> `generate_node`**: Unconditional edge.
3.  **`generate_node` -> Conditional Evaluator**:
    *   If `confidence` > 0.8 -> END
    *   If `confidence` <= 0.8 or `needs_escalation` is True -> `human_intervention_node`
4.  **`human_intervention_node` -> END**: Unconditional edge after human provides input.

---

### 2.4 Conditional Routing & Confidence Logic
*   **When to Answer:** If the LLM generates a response and self-assigns a confidence score strictly greater than `0.8` (80%), the system considers the answer reliable and delivers it.
*   **When to Escalate (Direct):** A regex or simple rule-based router checks the initial query for keywords: `["agent", "human", "manager", "complaint", "sue"]`. If matched, bypasses retrieval and goes to HITL.
*   **Low Confidence Logic:** If the context returned by ChromaDB is empty, or the LLM cannot find the answer in the context, the LLM sets `needs_escalation = True` or outputs a confidence `< 0.8`. The conditional edge intercepts this and routes the state to the HITL node instead of returning an unhelpful "I don't know" to the user.

---

### 2.5 Human-in-the-Loop (HITL) Design
*   **Escalation Trigger:** Invoked by LangGraph's `interrupt_before` functionality. When the graph reaches the `human_intervention_node`, execution halts.
*   **Human Response Integration:** The application exposes an interface (or CLI script) that:
    1.  Reads the paused state (shows the Agent the User Query and Context).
    2.  Prompts the Agent for input.
    3.  Updates the graph state with `{"human_input": "Agent's typed answer"}`.
    4.  Calls `graph.stream(None, thread_config)` to resume execution from the paused node.

---

### 2.6 API Design (System Boundaries)

**POST `/api/v1/query`**
*   **Description:** Submits a query to the LangGraph application.
*   **Input JSON:**
    ```json
    {
      "user_id": "user_123",
      "session_id": "session_999",
      "query": "How do I reset my router?"
    }
    ```
*   **Output JSON (If Auto-Resolved):**
    ```json
    {
      "status": "resolved",
      "answer": "To reset your router, hold the back button for 10 seconds.",
      "confidence": 0.95
    }
    ```
*   **Output JSON (If Escalated):**
    ```json
    {
      "status": "pending_human",
      "message": "We are connecting you to an agent. Please hold.",
      "thread_id": "session_999"
    }
    ```

**POST `/api/v1/human-respond`**
*   **Description:** Submits the human agent's response to resume the graph.
*   **Input JSON:**
    ```json
    {
      "thread_id": "session_999",
      "agent_response": "I have remotely reset your router for you."
    }
    ```

---

### 2.7 Error Handling
*   **No Chunks Found:** If ChromaDB returns zero chunks (or similarity distance is too high), `state["context"]` is empty. The `generate_node` detects this and automatically triggers an escalation instead of hallucinating.
*   **LLM API Failure / Timeout:** Implement `Tenacity` retry logic with exponential backoff on the LLM call. If it fails 3 times, gracefully degrade by routing to the `human_intervention_node` with an `escalate_reason: "system_error"`.
*   **Invalid Input:** Input validation at the API layer (using Pydantic) to ensure the query is a string and not excessively long (e.g., > 1000 chars) to prevent prompt injection or token limit exhaustion.
