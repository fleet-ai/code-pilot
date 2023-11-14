import os
import argparse
from dotenv import load_dotenv

import pinecone
from context import download_embeddings

from utils.utils import batch
from constants import (
    INDEX_NAME,
    INDEX_ENVIRONMENT,
    NAMESPACE,
    PATH_TO_SRC_CODE,
)
from code_indexer import CodeIndexer

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
            "metadata": {**dict(row["metadata"]), "type": "documentation"},
        }

    df["dict"] = df.apply(convert_row_to_dict, axis=1)
    vectors = df["dict"].tolist()

    vec_batches = list(batch(vectors, 100))
    for idx, vec_batch in enumerate(vec_batches):
        print(f"Upserting batch {idx}/{len(vec_batches)}...")
        index.upsert(vectors=vec_batch, namespace=NAMESPACE)

    print("Finished upserting")


def read_and_upsert_source_code():
    _ = CodeIndexer(src_dir=PATH_TO_SRC_CODE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--code",
        action="store_true",
        help="Boolean on whether or not to scrape and upsert source code",
    )
    parser.add_argument(
        "--library_name",
        type=str,
        default=None,
        help="Library name from Fleet Context to read and upsert",
    )
    args = parser.parse_args()

    if args.source_code:
        read_and_upsert_source_code()
    elif args.lib_name:
        read_and_upsert(args.lib_name)
    else:
        print("Please provide either --code or --lib_name argument.")


if __name__ == "__main__":
    main()
