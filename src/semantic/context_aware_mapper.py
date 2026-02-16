from typing import Dict, List, Optional


class ContextAwareMapper:
    def __init__(self, semantic_mapper=None):
        self.mapper = semantic_mapper
        self.field_contexts: Dict[str, Dict] = {}

    def add_context(
        self,
        field: str,
        context_keywords: List[str],
        priority: int = 1
    ):
        if field not in self.field_contexts:
            self.field_contexts[field] = {
                "keywords": [],
                "priority": priority
            }

        self.field_contexts[field]["keywords"].extend(context_keywords)

    def remove_context(self, field: str):
        if field in self.field_contexts:
            del self.field_contexts[field]

    def resolve_ambiguous_field(
        self,
        business_term: str,
        question_context: str
    ) -> Optional[str]:
        candidate_fields = []

        for field, context_info in self.field_contexts.items():
            keywords = context_info["keywords"]
            for keyword in keywords:
                if keyword in business_term:
                    candidate_fields.append((field, context_info["priority"]))

        if not candidate_fields:
            return None

        if len(candidate_fields) == 1:
            return candidate_fields[0][0]

        best_field = None
        best_score = -1

        for field, priority in candidate_fields:
            score = self._calculate_context_score(field, question_context)

            if score > best_score:
                best_score = score
                best_field = field

        return best_field

    def get_candidates(self, business_term: str) -> List[str]:
        candidates = []
        for field, context_info in self.field_contexts.items():
            keywords = context_info["keywords"]
            for keyword in keywords:
                if keyword in business_term:
                    candidates.append(field)
        return list(set(candidates))

    def _calculate_context_score(self, field: str, context: str) -> float:
        if field not in self.field_contexts:
            return 0

        keywords = self.field_contexts[field]["keywords"]
        score = 0

        for keyword in keywords:
            if keyword in context:
                score += 1

        score += self.field_contexts[field]["priority"]

        return score

    def get_all_fields(self) -> List[str]:
        return list(self.field_contexts.keys())

    def get_field_keywords(self, field: str) -> List[str]:
        if field in self.field_contexts:
            return self.field_contexts[field]["keywords"]
        return []
