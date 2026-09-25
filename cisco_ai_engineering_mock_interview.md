# Mock Coding Interview: AI Engineering Technical Leader (Cisco IT)

Based on the job description, this practice set focuses on the four things they'll almost certainly probe: **RAG pipelines**, **agentic orchestration**, **responsible AI (toxicity/bias screening)**, and **secure document processing**. Each problem is written the way a live coding round tends to be — a prompt, starter code with gaps, constraints, and follow-up questions an interviewer would ask after you finish.

Treat this as a 60–90 minute session. Time-box each problem to 20–25 minutes, then move on even if incomplete — that's realistic interview behavior.

---

## Problem 1: RAG Retrieval Pipeline with Reranking

**Prompt:** You're given a stubbed vector database client. Implement a `RAGPipeline` class that:
1. Chunks a document with overlap
2. Embeds and upserts chunks with metadata (source, chunk_id)
3. Retrieves top-k candidates for a query
4. Reranks candidates using a simple relevance heuristic (you may assume a `rerank_score(query, doc)` function exists)
5. Returns a formatted context string ready for prompt injection, respecting a max token budget

```python
from dataclasses import dataclass
from typing import List, Optional
import uuid

@dataclass
class Chunk:
    id: str
    text: str
    source: str
    embedding: Optional[List[float]] = None

class VectorDBClient:
    """Stub - assume this wraps Pinecone/Milvus/Weaviate."""
    def upsert(self, chunks: List[Chunk]) -> None: ...
    def query(self, embedding: List[float], top_k: int) -> List[Chunk]: ...

def embed(text: str) -> List[float]:
    """Stub - assume this calls an embedding model."""
    ...

def rerank_score(query: str, chunk: Chunk) -> float:
    """Stub - assume this calls a cross-encoder or LLM-based reranker."""
    ...

def count_tokens(text: str) -> int:
    """Stub - assume tiktoken-style counting."""
    ...

class RAGPipeline:
    def __init__(self, db: VectorDBClient, chunk_size: int = 512, overlap: int = 64):
        self.db = db
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, text: str, source: str) -> List[Chunk]:
        # TODO: split text into overlapping chunks, tag with source + chunk_id
        pass

    def ingest(self, text: str, source: str) -> None:
        # TODO: chunk, embed, upsert
        pass

    def retrieve(self, query: str, top_k: int = 20, final_k: int = 5,
                 max_context_tokens: int = 2000) -> str:
        # TODO: embed query, fetch top_k, rerank to final_k,
        # assemble context string without exceeding max_context_tokens
        pass
```






**Constraints:**
- Chunking must not split mid-sentence when avoidable (bonus).
- Retrieval must be robust to `db.query` returning duplicates across overlapping chunks — dedupe by source+position proximity.
- `retrieve` must never exceed `max_context_tokens`, even if that means dropping lower-ranked chunks.

**Follow-up questions an interviewer would ask:**
- How would you handle stale embeddings when the source document is updated?
- How would you evaluate retrieval quality before shipping (e.g., recall@k, RAGAS-style metrics)?
- What changes if you need multi-tenant isolation (customer A can't retrieve customer B's chunks)?
- How would you swap this to a hybrid search (BM25 + vector) without changing the public interface?

---

## Problem 2: Agentic Tool-Orchestration Loop

**Prompt:** Implement an agent loop that lets an LLM call tools iteratively until it produces a final answer, with guardrails: max iterations, timeout per tool call, and structured error recovery (a failed tool call should be reported back to the model, not crash the loop).

```python
from typing import Callable, Dict, Any, List
import time

class Tool:
    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description

class LLMClient:
    """Stub - assume this wraps a chat completion API with function calling."""
    def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Returns either {'type': 'tool_call', 'name': ..., 'args': ...}
        or {'type': 'final', 'content': ...}"""
        ...

class AgentExecutor:
    def __init__(self, llm: LLMClient, tools: List[Tool],
                 max_iterations: int = 8, tool_timeout_s: float = 10.0):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.max_iterations = max_iterations
        self.tool_timeout_s = tool_timeout_s

    def run(self, user_query: str) -> str:
        # TODO: implement the loop:
        # 1. maintain message history
        # 2. call llm.chat with available tools
        # 3. if tool_call -> execute with timeout, catch exceptions,
        #    append tool result (or error) to history, continue
        # 4. if final -> return content
        # 5. if max_iterations exceeded -> return a graceful fallback message
        pass

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        # TODO: enforce timeout, catch exceptions, return string result or error string
        pass
```

**Constraints:**
- A tool that isn't registered should produce a recoverable error the model sees, not a crash.
- A tool that hangs past `tool_timeout_s` must be aborted (discuss thread/async approach even if you don't fully implement it).
- The loop must terminate deterministically — no infinite loops on a model that keeps calling tools.

**Follow-up questions:**
- How would you add human-in-the-loop approval for a "high-risk" tool (e.g., one that sends emails or modifies data)?
- How do you prevent prompt injection from tool outputs hijacking the agent's next action?
- How would you add observability here (this is where LangSmith-style tracing fits) — what would you log per step?
- How does this change for a multi-agent setup where a planner delegates to sub-agents?

---

## Problem 3: Responsible AI — Toxicity & Bias Screening Gate

**Prompt:** Build a `SafetyGate` that screens both the incoming prompt and the model's output before it's returned to a user, logging every decision for audit purposes (a hard requirement in regulated enterprise environments like Cisco IT).

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import datetime

class SafetyVerdict(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    FLAG_FOR_REVIEW = "flag_for_review"

@dataclass
class SafetyResult:
    verdict: SafetyVerdict
    categories: List[str] = field(default_factory=list)
    score: float = 0.0
    reason: Optional[str] = None

class ToxicityClassifier:
    """Stub - assume this wraps a moderation model/API."""
    def classify(self, text: str) -> Dict[str, float]:
        """Returns category -> score, e.g. {'toxicity': 0.03, 'bias': 0.4}"""
        ...

class AuditLogger:
    def log(self, event: Dict) -> None:
        """Stub - assume append-only, tamper-evident storage."""
        ...

class SafetyGate:
    def __init__(self, classifier: ToxicityClassifier, audit_log: AuditLogger,
                 block_threshold: float = 0.8, review_threshold: float = 0.5):
        self.classifier = classifier
        self.audit_log = audit_log
        self.block_threshold = block_threshold
        self.review_threshold = review_threshold

    def screen(self, text: str, direction: str, request_id: str) -> SafetyResult:
        # TODO:
        # 1. classify text
        # 2. determine verdict based on thresholds (any category above block -> BLOCK,
        #    above review but below block -> FLAG_FOR_REVIEW, else ALLOW)
        # 3. write an audit log entry regardless of verdict (include request_id,
        #    direction ["input"/"output"], categories, scores, verdict, timestamp)
        # 4. return SafetyResult
        pass
```

**Constraints:**
- Every call must produce an audit log entry, even ALLOW verdicts (regulatory requirement — you need a record of what was screened, not just what was blocked).
- Blocking should never leak the blocked content into logs in plaintext if the category is something like PII (discuss redaction).
- Design should support adding new categories (e.g., "regulatory_violation") without changing the gate's interface.

**Follow-up questions:**
- How would you handle false positives at scale — what's your appeals/override workflow?
- How do you keep the classifier itself from drifting, and how do you monitor for that?
- How does this integrate with existing enterprise governance/legal review processes (the JD calls this out explicitly)?
- Where does this gate sit in the request path for a RAG system — before retrieval, after generation, or both? Why?

---

## Problem 4: Secure Document Ingestion Pipeline (System-design-flavored coding)

**Prompt:** Sketch and partially implement a pipeline stage that classifies incoming documents by sensitivity and enforces access control before they're indexed into the vector DB used by Problem 1.

```python
from enum import Enum
from typing import List, Set

class SensitivityLevel(Enum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    RESTRICTED = 3

class DocumentClassifier:
    """Stub - assume this uses an LLM or regex/DLP rules to classify."""
    def classify(self, text: str) -> SensitivityLevel: ...
    def detect_pii(self, text: str) -> List[str]: ...  # returns PII types found

class AccessControlledIngestionPipeline:
    def __init__(self, classifier: DocumentClassifier, rag_pipeline,
                 encryptor, audit_log: AuditLogger):
        self.classifier = classifier
        self.rag_pipeline = rag_pipeline
        self.encryptor = encryptor
        self.audit_log = audit_log

    def ingest_document(self, text: str, source: str,
                         uploader_id: str, allowed_groups: Set[str]) -> None:
        # TODO:
        # 1. detect PII; if found and sensitivity is CONFIDENTIAL/RESTRICTED,
        #    redact or reject depending on policy
        # 2. classify sensitivity
        # 3. encrypt at rest before storage (assume self.encryptor.encrypt(text) -> bytes)
        # 4. tag chunk metadata with sensitivity level + allowed_groups for
        #    row-level access control at retrieval time
        # 5. audit log the ingestion decision
        # 6. only then call self.rag_pipeline.ingest(...)
        pass

    def retrieve_for_user(self, query: str, user_groups: Set[str]) -> str:
        # TODO: retrieve, then filter out chunks whose allowed_groups
        # don't intersect user_groups, before returning context
        pass
```

**Follow-up questions:**
- How do you retrofit access control onto an already-embedded index if a document's sensitivity is reclassified later?
- What's your key management story for the encryptor — who can decrypt, and how do you rotate keys without re-ingesting everything?
- How would you demonstrate compliance (e.g., to legal/governance teams) that this pipeline actually enforces the policy end-to-end?

---

## How to run this practice session

1. Set a timer. Don't look at follow-up questions until you've written code.
2. Talk out loud as you code — narrate trade-offs, even alone. Interviewers weight this heavily for a "Technical Leader" title.
3. After each problem, answer the follow-ups as if an interviewer just asked them on the spot.
4. If you finish early, add: unit tests, type hints, and a note on how you'd containerize/deploy this piece (CI/CD, since it's in the minimum qualifications).

## What they're likely actually scoring you on

- **Correctness under ambiguity** — the stubs are intentionally underspecified; reasonable assumptions stated out loud matter more than guessing the "right" API.
- **Production instincts** — token budgets, timeouts, idempotency, dedup, audit trails. This role is IT operations, not a research lab.
- **Responsible AI fluency** — Problem 3 is not optional flavor; expect it to be a real, scored part of the interview given how explicitly the JD calls it out.
- **Security-first thinking** — encryption, access control, and PII handling woven through the whole pipeline, not bolted on.
- **Leadership signal** — how you narrate trade-offs and mentor-style explain decisions, since this is a "Technical Leader" title, not an IC role.

If you want, I can also run a live version of this with you turn-by-turn (you write code, I play interviewer and push back), or generate reference solutions for self-grading.
