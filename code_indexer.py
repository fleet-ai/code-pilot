import os
from dotenv import load_dotenv
from pathlib import Path
import pinecone
import uuid

from utils.utils import batch
from utils.embed import embed_code_chunks
from constants import (
    EXTENSION_TO_TREE_SITTER_LANGUAGE,
    EMBEDDINGS_MODEL,
    MAX_CONTEXT_LENGTH_EMBEDDINGS,
    INDEX_NAME,
    INDEX_ENVIRONMENT,
    NAMESPACE,
)
from code_splitter import CodeSplitter

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")


class CodeIndexer:
    src_dir: str
    target_chunk_tokens: int
    max_chunk_tokens: int
    enforce_max_chunk_tokens: bool
    token_model: str
    code_splitters = {}
    hash_cache = {}
    index = None

    def __init__(
        self,
        src_dir: str,
        target_chunk_tokens: int = 300,
        max_chunk_tokens: int = 1000,
        enforce_max_chunk_tokens: bool = False,
        coalesce: int = 50,
        token_model: str = "gpt-4",
    ):
        self.src_dir = src_dir
        self.target_chunk_tokens = target_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.enforce_max_chunk_tokens = enforce_max_chunk_tokens
        self.coalesce = coalesce
        self.token_model = token_model
        self._create_index()
        self.refresh_nodes()

    def add_file(self, file: str):
        ext = os.path.splitext(file)[1]
        text_splitter = self._get_code_splitter(ext)

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            chunks = text_splitter.split_text(text)
        chunks = [
            {
                "id": str(uuid.uuid4()),
                "text": chunk,
                "file": file.split("/src_code/", 1)[1]
                if "/src_code/" in file
                else file,
            }
            for chunk in chunks
        ]
        self.embed_code_chunks(chunks)

    def refresh_nodes(self):
        files = self._find_files(self.src_dir, EXTENSION_TO_TREE_SITTER_LANGUAGE)

        # For each file, split into chunks and index
        for file in files:
            self.add_file(str(file))

    def _find_files(self, path, include_ext={}):
        """
        Recursively find all files in a given path.

        Parameters:
            path (str): The root directory to start searching from.
            include_ext (dict): A dictionary of file extensions to include
                (keys are extensions including leading period if applicable).

        Returns:
            list: A list of full file paths for each file found.
        """
        # Convert path to an absolute path
        path = os.path.abspath(path)

        found_files = []

        for root, _, files in os.walk(path):
            for file in files:
                # Check if the file should be excluded based on its extension
                file_ext = os.path.splitext(file)[1]
                if file_ext in include_ext:
                    # Construct the full path of the file and append to list
                    full_path = Path(os.path.join(root, file)).resolve()
                    found_files.append(full_path)

        return set(found_files)

    def _get_code_splitter(self, ext) -> CodeSplitter:
        if ext not in EXTENSION_TO_TREE_SITTER_LANGUAGE:
            raise ValueError(f"Extension {ext} not supported.")
        language = EXTENSION_TO_TREE_SITTER_LANGUAGE[ext]
        if language not in self.code_splitters:
            text_splitter = CodeSplitter(
                language=language,
                target_chunk_tokens=self.target_chunk_tokens,
                max_chunk_tokens=self.max_chunk_tokens,
                enforce_max_chunk_tokens=self.enforce_max_chunk_tokens,
                coalesce=self.coalesce,
                token_model=self.token_model,
            )
            self.code_splitters[ext] = text_splitter

        return self.code_splitters[ext]

    def _create_index(self):
        pinecone.init(api_key=PINECONE_API_KEY, environment=INDEX_ENVIRONMENT)
        pinecone_index = pinecone.Index(INDEX_NAME)
        self.index = pinecone_index

        return pinecone_index

    def embed_code_chunks(self, chunks):
        vectors = []
        for chunk in chunks:
            embeddings = embed_code_chunks(
                chunks,
                model=EMBEDDINGS_MODEL,
                token_limit=MAX_CONTEXT_LENGTH_EMBEDDINGS,
            )
            for chunk, embedding in zip(chunks, embeddings):
                metadata = {
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "file": chunk["file"],
                    "type": "code",
                }
                vectors.append(
                    {
                        "id": str(uuid.uuid4()),
                        "values": embedding,
                        "metadata": metadata,
                    }
                )

        for vec_batch in batch(vectors, 100):
            self.index.upsert(vectors=vec_batch, namespace=NAMESPACE)

        print("Finished embedding chunk(s).")
