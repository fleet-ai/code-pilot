import os

import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed_chunks(chunks, model="text-embedding-ada-002", token_limit=8191):
    embeddings = []
    current_batch = []
    current_batch_tokens = 0
    encoding = tiktoken.encoding_for_model(model)
    for chunk in chunks:
        next_batch_tokens = len(
            encoding.encode(
                "\n".join(current_chunk for current_chunk in current_batch + [chunk])
            )
        )
        if next_batch_tokens > token_limit:
            response = client.embeddings.create(
                input=current_batch,
                model=model,
            )
            for item in response.data:
                embeddings.append(item.embedding)
            current_batch_tokens = next_batch_tokens - current_batch_tokens
            current_batch = [chunk]
        else:
            current_batch_tokens = next_batch_tokens
            current_batch.append(chunk)

    if current_batch:
        response = client.embeddings.create(
            input=current_batch,
            model=model,
        )
        for item in response.data:
            embeddings.append(item.embedding)

    return embeddings


def embed_code_chunks(chunks, model="text-embedding-ada-002", token_limit=8191):
    embeddings = []
    current_batch = []
    current_batch_tokens = 0
    encoding = tiktoken.encoding_for_model(model)
    print("chunks:", chunks)
    for chunk in chunks:
        next_batch_tokens = len(
            encoding.encode(
                "\n".join(
                    current_chunk["text"] for current_chunk in current_batch + [chunk]
                )
            )
        )
        if next_batch_tokens > token_limit:
            response = client.embeddings.create(
                input=[current_chunk["text"] for current_chunk in current_batch],
                model=model,
            )
            for item in response.data:
                embeddings.append(item.embedding)
            current_batch_tokens = next_batch_tokens - current_batch_tokens
            current_batch = [chunk]
        else:
            current_batch_tokens = next_batch_tokens
            current_batch.append(chunk)

    if current_batch:
        response = client.embeddings.create(
            input=[current_chunk["text"] for current_chunk in current_batch],
            model=model,
        )
        for item in response.data:
            embeddings.append(item.embedding)

    return embeddings
