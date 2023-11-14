import os
from dotenv import load_dotenv

import pinecone
from context import download_embeddings

from utils.utils import batch
from constants import (
    LIBRARY_NAME,
    INDEX_NAME,
    INDEX_ENVIRONMENT,
    NAMESPACE,
)

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pinecone.init(api_key=PINECONE_API_KEY, environment=INDEX_ENVIRONMENT)
index = pinecone.Index(INDEX_NAME)


def read_and_upsert(library_name):
    df = download_embeddings(library_name)

    def convert_row_to_dict(row):
        return {
            "id": row["id"],
            "values": [float(value) for value in row["dense_embeddings"]],
            "sparse_values": dict(row["sparse_values"]),
            "metadata": dict(row["metadata"]),
        }

    df["dict"] = df.apply(convert_row_to_dict, axis=1)
    vectors = df["dict"].tolist()

    vec_batches = list(batch(vectors, 100))
    for idx, vec_batch in enumerate(vec_batches):
        print(f"Upserting batch {idx}/{len(vec_batches)}...")
        index.upsert(vectors=vec_batch, namespace=NAMESPACE)

    print("Finished upserting")


if __name__ == "__main__":
    read_and_upsert(LIBRARY_NAME)
