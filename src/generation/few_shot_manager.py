import json
from typing import List, Dict, Optional
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate


class FewShotManager:
    def __init__(self):
        self.examples: List[Dict[str, str]] = []

    def add_example(self, question: str, sql: str):
        self.examples.append({"question": question, "sql": sql})

    def get_prompt_with_examples(
        self,
        schema: str,
        question: str,
        example_count: int = 3
    ) -> str:
        selected = self.examples[-example_count:]

        example_prompt = PromptTemplate(
            input_variables=["question", "sql"],
            template="问题: {question}\nSQL: {sql}"
        )

        few_shot_prompt = FewShotPromptTemplate(
            examples=selected,
            example_prompt=example_prompt,
            prefix="以下是一些示例：\n\n",
            suffix=f"\n\n基于以下数据库 Schema，将用户问题转换为 SQL。\n\nSchema:\n{schema}\n\n用户问题: {{question}}\n\nSQL:",
            input_variables=["question"]
        )

        return few_shot_prompt.format(question=question)

    def load_examples_from_file(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.examples = data.get("examples", [])

    def save_examples_to_file(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({"examples": self.examples}, f, ensure_ascii=False, indent=2)

    def clear_examples(self):
        self.examples = []

    def get_example_count(self) -> int:
        return len(self.examples)
