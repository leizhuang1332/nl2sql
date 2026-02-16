import pytest
import numpy as np
from unittest.mock import MagicMock
from src.semantic.vector_matcher import VectorMatcher


def test_vector_matcher_init():
    matcher = VectorMatcher()
    assert matcher is not None
    assert matcher.terms == []
    assert matcher.term_vectors == {}


def test_vector_matcher_with_model():
    matcher = VectorMatcher(embeddings_model=MagicMock())
    assert matcher.embeddings_model is not None


def test_vector_matcher_without_model():
    matcher = VectorMatcher()
    result = matcher.find_similar("销售")
    assert result == []


def test_vector_matcher_build_index():
    matcher = VectorMatcher()
    mock_model = MagicMock()
    mock_model.embed_documents.return_value = [[1, 0], [0, 1]]
    matcher.embeddings_model = mock_model

    matcher.build_index(["销售", "订单"])

    assert "销售" in matcher.terms
    assert "订单" in matcher.terms
    assert "销售" in matcher.term_vectors


def test_vector_matcher_add_term():
    matcher = VectorMatcher()
    vector = np.array([1.0, 0.0, 0.0])
    matcher.add_term("销售", vector)

    assert "销售" in matcher.terms
    assert "销售" in matcher.term_vectors
    np.testing.assert_array_equal(matcher.term_vectors["销售"], vector)


def test_vector_matcher_find_similar_with_mock():
    matcher = VectorMatcher()
    mock_model = MagicMock()
    mock_model.embed_documents.return_value = [[1, 0], [0, 1]]
    mock_model.embed_query.return_value = [1, 0]
    matcher.embeddings_model = mock_model

    matcher.build_index(["销售", "订单"])
    result = matcher.find_similar("销售", threshold=0.5)

    assert len(result) > 0


def test_cosine_similarity_identical():
    matcher = VectorMatcher()
    vec1 = np.array([1, 0])
    vec2 = np.array([1, 0])
    sim = matcher._cosine_similarity(vec1, vec2)
    assert sim == 1.0


def test_cosine_similarity_opposite():
    matcher = VectorMatcher()
    vec1 = np.array([1, 0])
    vec2 = np.array([-1, 0])
    sim = matcher._cosine_similarity(vec1, vec2)
    assert sim == -1.0


def test_cosine_similarity_orthogonal():
    matcher = VectorMatcher()
    vec1 = np.array([1, 0])
    vec2 = np.array([0, 1])
    sim = matcher._cosine_similarity(vec1, vec2)
    assert abs(sim) < 0.001


def test_cosine_similarity_zero_vector():
    matcher = VectorMatcher()
    vec1 = np.array([0, 0])
    vec2 = np.array([1, 0])
    sim = matcher._cosine_similarity(vec1, vec2)
    assert sim == 0


def test_vector_matcher_clear():
    matcher = VectorMatcher()
    vector = np.array([1.0, 0.0])
    matcher.add_term("销售", vector)
    matcher.clear()

    assert matcher.terms == []
    assert matcher.term_vectors == {}


def test_find_similar_with_manual_vectors():
    matcher = VectorMatcher()
    matcher.add_term("销售", np.array([1.0, 0.0]))
    matcher.add_term("订单", np.array([0.0, 1.0]))

    result = matcher.find_similar_with_manual_vectors(
        np.array([1.0, 0.0]),
        threshold=0.5
    )

    assert len(result) > 0
    assert result[0][0] == "销售"


def test_find_similar_top_k():
    matcher = VectorMatcher()
    matcher.add_term("销售", np.array([1.0, 0.0]))
    matcher.add_term("订单", np.array([0.9, 0.1]))
    matcher.add_term("客户", np.array([0.0, 1.0]))

    result = matcher.find_similar_with_manual_vectors(
        np.array([1.0, 0.0]),
        threshold=0.0,
        top_k=2
    )

    assert len(result) == 2
