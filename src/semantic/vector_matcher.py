from typing import List, Tuple, Optional, Dict
import numpy as np


class VectorMatcher:
    def __init__(self, embeddings_model=None):
        self.embeddings_model = embeddings_model
        self.term_vectors: Dict[str, np.ndarray] = {}
        self.terms: List[str] = []

    def build_index(self, terms: List[str]):
        if not self.embeddings_model:
            return

        self.terms = terms
        vectors = self.embeddings_model.embed_documents(terms)
        for term, vector in zip(terms, vectors):
            self.term_vectors[term] = np.array(vector)

    def add_term(self, term: str, vector: np.ndarray):
        self.terms.append(term)
        self.term_vectors[term] = vector

    def find_similar(
        self,
        query: str,
        threshold: float = 0.8,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        if not self.embeddings_model or not self.terms:
            return []

        query_vector = np.array(
            self.embeddings_model.embed_query(query)
        )

        similarities = []
        for term, term_vector in self.term_vectors.items():
            sim = self._cosine_similarity(query_vector, term_vector)
            if sim >= threshold:
                similarities.append((term, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def find_similar_with_manual_vectors(
        self,
        query_vector: np.ndarray,
        threshold: float = 0.8,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        if not self.terms:
            return []

        similarities = []
        for term, term_vector in self.term_vectors.items():
            sim = self._cosine_similarity(query_vector, term_vector)
            if sim >= threshold:
                similarities.append((term, float(sim)))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0

        return dot_product / (norm1 * norm2)

    def clear(self):
        self.terms = []
        self.term_vectors = {}
