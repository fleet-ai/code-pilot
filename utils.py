import os
import numpy as np
import tiktoken
import pinecone

from langchain.embeddings import OpenAIEmbeddings
from pinecone_text.sparse import BM25Encoder

index = pinecone.Index("libraries")

embedding_model = OpenAIEmbeddings(
    model="text-embedding-ada-002", openai_api_key=os.environ["OPENAI_API_KEY"]
)
sparse_model = BM25Encoder()
sparse_model.fit(["test"])


def hybrid_scale(dense, sparse, alpha: float):
    """Hybrid vector scaling using a convex combination

    alpha * dense + (1 - alpha) * sparse

    Args:
        dense: Array of floats representing
        sparse: a dict of `indices` and `values`
        alpha: float between 0 and 1 where 0 == sparse only and 1 == dense only
    """
    if alpha < 0 or alpha > 1:
        raise ValueError("Alpha must be between 0 and 1")
    # scale sparse and dense vectors to create hybrid search vecs
    hsparse = {
        "indices": sparse["indices"],
        "values": [v * (1 - alpha) for v in sparse["values"]],
    }
    hdense = [v * alpha for v in dense]
    return hdense, hsparse


def embed_query_dense(query):
    dense_vec = None
    if embedding_model is not None:
        dense_vec = np.array(embedding_model.embed_query(query))
    return dense_vec


def embed_query_sparse(query):
    sparse_vec = None
    if sparse_model is not None:
        sparse_vec = sparse_model.encode_queries(query)
    return sparse_vec


def query_index(query, k=10, filter_dict=None, alpha=0.5, namespace=""):
    """Queries the Pinecone index"""
    dense_vec, sparse_vec = None, None
    dense_vec = embed_query_dense(query).tolist()

    # We will only do hybrid search get the sparse vector if we initialize with a sparse_model
    if sparse_model:
        sparse_vec = embed_query_sparse(query)
        dense_vec, sparse_vec = hybrid_scale(dense_vec, sparse_vec, alpha=alpha)

    if sparse_vec is not None:
        res = index.query(
            top_k=int(k),
            include_metadata=True,
            vector=dense_vec,
            sparse_vector=sparse_vec,
            filter=filter_dict,
            namespace=namespace,
        )
    else:
        res = index.query(
            top_k=int(k),
            include_metadata=True,
            vector=dense_vec,
            filter=filter_dict,
            namespace=namespace,
        )

    if res and res.get("matches"):
        results = [
            {
                "id": r["id"],
                "score": r["score"],
                "values": r["values"],
                "metadata": r["metadata"],
            }
            for r in res.get("matches")
        ]
        return results
    else:
        return []


def get_num_tokens(text):
    """Get number of tiktoken tokens"""
    encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
    return len(encoding.encode(text, allowed_special={"<|endoftext|>"}))
