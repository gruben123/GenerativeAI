from dataclasses import dataclass
from typing import List, Optional
import uuid
from math import sqrt
import re

@dataclass
class Chunk:
    id: str
    text: str
    source: str
    position:int  # position of the chunk in the source document
    embedding: Optional[List[float]] = None
    
class VectorDBClient:
    """Stub - assume this wraps Pinecone/Milvus/Weaviate."""
    def __init__(self):
        self.store:List[Chunk]=[]
    
    def upsert(self, chunks: List[Chunk]) -> None:
        existing_ids={c.id: i for i, c in enumerate(self.store)}  #enumerate brings a tuple of index and value, then we create a dictionary with chunk id as key and index as value

        for c in chunks:
            if c.id in existing_ids:
                self.store[existing_ids[c.id]]=c
            else:
                self.store.append(c)

    def query(self, embedding: List[float], top_k: int) -> List[Chunk]:
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot=sum(x*y for x, y in zip(a, b)) 
            norm_a=sqrt(sum(x*x for x in a))
            norm_b=sqrt(sum(x*x for x in b))

            return dot/(norm_a*norm_b) if norm_a and norm_b else 0.0  #normalized dot product = (a*b)/(||a||*||b||)

        scored=[(cosine_similarity(embedding, c.embedding), c) for c in self.store if c.embedding is not None]
        scored.sort(key=lambda x: x[0], reverse=True)

        return [c for _, c in scored[:top_k]]

def embed(text: str) -> List[float]:
    dim=64
    vec=[0.0]*dim  #initialize a vector of zeros with length dim
    words=re.findall(r'[a-zA-Z]+', text.lower())

    for w in words:
        idx=hash(w) % dim
        vec[idx]+=1.0

    return vec

def rerank_score(query: str, chunk: Chunk) -> float:
    q_vec=embed(query)
    c_vec=chunk.embedding if not chunk.embedding is None else embed(chunk.text)
    dot=sum(x*y for x, y in zip(q_vec, c_vec))

    norm_q=sqrt(sum(x*x for x in q_vec))
    norm_c=sqrt(sum(x*x for x in c_vec))

    return dot/(norm_q*norm_c) if norm_q and norm_c else 0.0

def count_tokens(text: str) -> int:
    """approximate 4 characters per token"""
    return max(1, len(text) // 4)

class RAGPipeline:
    def __init__(self, db: VectorDBClient, chunk_size: int = 512, overlap: int = 64):
        self.db = db
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, text: str, source: str) -> List[Chunk]:
        # TODO: split text into overlapping chunks, tag with source + chunk_id
        sentences = [s.strip() for s in text.replace("\n", " ").split('.') if s.strip()]
        chunks = []
        current=""
        position = 0

        def flush(chunk_text:str) -> None:
            nonlocal position
            if chunk_text:
                chunks.append(Chunk(id=str(uuid.uuid4()), text=chunk_text, source=source, position=position))
                position+=1

        for sentence in sentences:
            candidate = (current + " " + sentence).strip() if current else sentence

            if not current:
                current = sentence
            else:
                candidate=current+" "+sentence

                if len(candidate.split()) < self.chunk_size:
                    current = candidate
                    continue

                flush(current)
                overlap_sentences = current[-self.overlap:] if self.overlap else ""
                current = (overlap_sentences + " " + sentence).strip()

            if len(current.split())>self.chunk_size:
                flush(current)
                current=""

        if current:
            flush(current)

        return chunks
        

    def ingest(self, text: str, source: str) -> None:
        chunks=self.chunk_document(text, source)

        for chunk in chunks:
            chunk.embedding=embed(chunk.text)

        self.db.upsert(chunks)

    def retrieve(self, query: str, top_k: int = 20, final_k: int = 5,
                 max_context_tokens: int = 2000) -> str:
        query_embedding = embed(query)
        candiates = self.db.query(query_embedding, top_k=top_k)
        
        seen=set()  #creates a new empty set
        deduped=[]

        for c in candiates:
            key=(c.source, c.position)

            if key not in seen:
                seen.add(key)
                deduped.append(c)

        #rerank it
        scored=[(rerank_score(query, c), c) for c in deduped]
        scored.sort(key=lambda x: x[0], reverse=True)
        top_reranked=[c for _, c in scored[:final_k]]

        assembled_parts=[]
        running_tokens=0

        for c in top_reranked:
            chunk_tokens=count_tokens(c.text)

            if running_tokens+chunk_tokens>max_context_tokens:
                break

            assembled_parts.append(c.text)
            running_tokens+=chunk_tokens

        return "\n-----\n".join(assembled_parts)

if __name__ == "__main__":
    sample_text=(
        "Cisco builds AI platforms that power networks."
        "RAG retrieves relevant information from a vector database and generates answers."
        "Responsible AI screens for toxicity and bias in generated content."
        "Secure controls protect confidential data and intellectual property."
    )

    pipeline=RAGPipeline(db=VectorDBClient(), chunk_size=60, overlap=15)
    chunks=pipeline.chunk_document(sample_text, source="sample_doc")
    
    print("Chunking================")

    for c in chunks:
        print(f"[{c.position}] ({len(c.text)} chars):{c.text}\n")

    pipeline.ingest(sample_text, source="sample_doc")
    context = pipeline.retrieve("How does Cisco IT handle document security?", top_k=10, final_k=3, max_context_tokens=200)

    print(f"Retrieved Context:\n{context}")