from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document

import logging
import json
from pathlib import Path
from typing import List, Union

class VectorStore:
    def __init__(self):
        self._vector_store = None

        # Initialize embedding model
        self._embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

        # Initialize logging
        self._logger = logging.getLogger(__name__)

        self._logger.info("Vector store initialized")

    def load_documents_json(self, file_path: str) -> List[Document]:
        """Load documents from a JSON file."""

        with open(file_path, 'r') as f:
            data = json.load(f)

            docs: List[Document] = []
            for doc in data:
                op_name = doc["name"]
                op_full_name = doc["full_name"]
                op_cat = doc["category"]
                use_case = doc["use_case"]
                precond = doc["preconditions"]
                desc = doc["description"]
                example = doc["example"]

                page_content = f"""Operator: {op_name}
                Full name: {op_full_name}
                Category: {op_cat}
                Description: {desc}
                Use Case: {use_case}
                Preconditions: {precond}
                Example: {example}"""

                metadata = {
                    "op_name": op_name,
                    "op_full_name": op_full_name,
                    "category": op_cat,
                }

                self._logger.debug(f"Page Content: {page_content}")
                self._logger.debug(f"Metadata: {metadata}")

                docs.append(Document(page_content=page_content, metadata=metadata))

            self._logger.info(f"Loaded {len(docs)} documents from {file_path}")
            return docs

    def create_vector_store(self, documents: List[Document]):
        """
        Create vector store from documents or text files.

        Args:
            documents: A list of Document objects
        Raises:
            ValueError: If documents cannot be processed or vectorized
        """
        try:

            self._logger.info("Creating vector store")
            self._vector_store = FAISS.from_documents(
                documents,
                self._embeddings
            )
            self._logger.info("Vector store created successfully")

            return self._vector_store

        except Exception as e:
            self._logger.error(f"Error creating vector store: {str(e)}")
            raise ValueError(f"Error creating vector store: {str(e)}")

    def save_vector_store(self, path: Union[str, Path]):
        """Save the vector store to disk."""
        if self._vector_store is None:
            raise ValueError("No vector store to save")

        path = Path(path)
        self._vector_store.save_local(str(path))
        self._logger.info(f"Vector store saved to {path}")

    def load_vector_store(self, path: Union[str, Path]):
        """Load a vector store from disk."""
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Vector store path does not exist: {path}")

        self._vector_store = FAISS.load_local(str(path), self.embeddings)
        self._logger.info(f"Vector store loaded from {path}")
