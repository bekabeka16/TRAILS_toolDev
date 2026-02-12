import os
from typing import List, Dict, Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI


def _get_clients():
    # Azure OpenAI client
    aoai = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )

    # Azure AI Search client
    search = SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name=os.environ["AZURE_SEARCH_INDEX"],
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"]),
    )

    return aoai, search


def embed_query(aoai: AzureOpenAI, text: str) -> List[float]:
    emb_deployment = os.environ["AZURE_OPENAI_EMBED_DEPLOYMENT"]
    resp = aoai.embeddings.create(model=emb_deployment, input=text)
    return resp.data[0].embedding


def retrieve_chunks(
    search: SearchClient,
    query_text: str,
    query_vector: List[float],
    k: int = 6,
    course_id: str | None = None,
    tenant_id: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Assumes Azure AI Search index has fields like:
      - chunk (text)
      - title
      - docId
      - page (optional)
      - chunkId (optional)
      - tenantId/courseId (optional, filterable)
      - chunkEmbedding (vector)
    Adjust field names below to match your index!
    """

    # Safety filters 
    filters = []
    if course_id:
        filters.append(f"courseId eq '{course_id}'")
    if tenant_id:
        filters.append(f"tenantId eq '{tenant_id}'")

    filter_expr = " and ".join(filters) if filters else None

    # Hybrid retrieval: keyword + vector (works well for demos)
    # NOTE: field names must match index schema.
    results = search.search(
        search_text=query_text,
        vector_queries=[{
            "vector": query_vector,
            "k": k,
            "fields": "chunkEmbedding"
        }],
        select=["chunk", "title", "docId", "page", "chunkId", "sourceUrl"],
        filter=filter_expr,
        top=k
    )

    chunks = []
    for r in results:
        chunks.append({
            "chunk": r.get("chunk", ""),
            "title": r.get("title", ""),
            "docId": r.get("docId", ""),
            "page": r.get("page", None),
            "chunkId": r.get("chunkId", r.get("id", "")),
            "sourceUrl": r.get("sourceUrl", None),
        })
    return chunks


def build_prompt_with_citations(chunks: List[Dict[str, Any]]) -> str:
    """
    Packs chunks into a compact context block with citation tags.
    """
    lines = []
    for i, c in enumerate(chunks, start=1):
        cite = f"[C{i} | {c.get('title','')} p.{c.get('page','?')}]"
        text = c.get("chunk", "").strip().replace("\n", " ")
        lines.append(f"{cite} {text}")
    return "\n".join(lines)


def answer_question(question: str, course_id: str | None = None, tenant_id: str | None = None) -> Dict[str, Any]:
    aoai, search = _get_clients()

    qvec = embed_query(aoai, question)
    chunks = retrieve_chunks(search, question, qvec, k=6, course_id=course_id, tenant_id=tenant_id)

    context = build_prompt_with_citations(chunks)

    system = (
        "You are a reading assistant for students.\n"
        "Rules:\n"
        "1) Use ONLY the provided context to answer.\n"
        "2) If the context does not contain the answer, say you don't have enough information.\n"
        "3) Always include citations like [C1], [C2] next to the claims they support.\n"
        "4) Keep the answer concise for a demo.\n"
    )

    user = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Answer with citations."
    )

    chat_deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
    resp = aoai.chat.completions.create(
        model=chat_deployment,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    answer = resp.choices[0].message.content

    return {
        "answer": answer,
        "citations": [
            {
                "tag": f"C{i+1}",
                "title": c.get("title"),
                "docId": c.get("docId"),
                "page": c.get("page"),
                "chunkId": c.get("chunkId"),
                "sourceUrl": c.get("sourceUrl"),
            }
            for i, c in enumerate(chunks)
        ],
    }
