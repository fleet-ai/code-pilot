import os
import numpy as np
import pinecone

from constants import MAX_CONTEXT_LENGTH, PROMPT, INDEX_NAME, INDEX_ENVIRONMENT
from utils.utils import get_num_tokens

from langchain.embeddings import OpenAIEmbeddings

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pinecone.init(api_key=PINECONE_API_KEY, environment=INDEX_ENVIRONMENT)
index = pinecone.Index(INDEX_NAME)

embedding_model = OpenAIEmbeddings(
    model="text-embedding-ada-002", openai_api_key=os.getenv("OPENAI_API_KEY")
)


def embed_query_dense(query):
    dense_vec = None
    if embedding_model is not None:
        dense_vec = np.array(embedding_model.embed_query(query))
    return dense_vec


def query_index(query, k=10, filter_dict=None, namespace=""):
    """Queries the Pinecone index"""
    dense_vec = embed_query_dense(query).tolist()
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


def parse_results(repo_url, results):
    token_count = 0
    context_text = ""
    for context in results:
        if "issue_id" in context["metadata"]:  # issue
            url = context["metadata"]["url"]
            text = context["metadata"]["body"]
            title = context["metadata"]["title"]
        elif "file" in context["metadata"]:  # src code
            url = repo_url + "/".join(context["metadata"]["file"].split("/")[1:])
            title = context["metadata"]["file"].split("/")[-1]
            text = context["metadata"]["text"]
        else:  # documentation
            url = context["metadata"]["url"]
            text = context["metadata"]["text"]
            title = context["metadata"]["title"]

        context_to_add = f"### {title} {url} ###\n{text}\n\n"
        # if the length of the context is above the token limit, skip it
        if (
            token_count
            + get_num_tokens(
                "<|im_start|>system" + PROMPT + "<|im_end|>\n" + context_to_add + "\n"
            )
        ) > MAX_CONTEXT_LENGTH:
            print("Context too long, skipping...")
            continue
        else:
            context_text += context_to_add + "\n"

    return context_text
