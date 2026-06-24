"""Tiny deterministic n-gram language model for constrained experiments."""

from __future__ import annotations

from collections import defaultdict

from .tokenizer import tokenize


class NGramLanguageModel:
    def __init__(self, order: int = 2) -> None:
        if order < 1:
            raise ValueError("order must be at least 1")
        self.order = order
        self.transitions: dict[tuple[str, ...], list[str]] = defaultdict(list)
        self.vocabulary: set[str] = set()

    def train(self, text: str) -> None:
        tokens = _word_tokens(text)
        self.vocabulary.update(tokens)
        if len(tokens) <= self.order:
            return
        for index in range(len(tokens) - self.order):
            prefix = tuple(tokens[index : index + self.order])
            next_token = tokens[index + self.order]
            self.transitions[prefix].append(next_token)

    def generate(self, seed_text: str, max_tokens: int = 24) -> str:
        seed_tokens = [token for token in _word_tokens(seed_text) if token in self.vocabulary]
        if len(seed_tokens) >= self.order and tuple(seed_tokens[-self.order :]) in self.transitions:
            prefix = tuple(seed_tokens[-self.order :])
        elif seed_tokens:
            prefix = self._prefix_containing(seed_tokens)
        else:
            prefix = self._first_prefix()
        if not prefix:
            return ""

        generated = list(prefix)
        seen_prefixes: set[tuple[str, ...]] = set()
        for _ in range(max(max_tokens - len(generated), 0)):
            choices = self.transitions.get(prefix)
            if not choices or prefix in seen_prefixes:
                break
            seen_prefixes.add(prefix)
            next_token = choices[0]
            generated.append(next_token)
            prefix = tuple(generated[-self.order :])
        return " ".join(generated[:max_tokens])

    def _first_prefix(self) -> tuple[str, ...]:
        if not self.transitions:
            return ()
        return sorted(self.transitions)[0]

    def _prefix_containing(self, seed_tokens: list[str]) -> tuple[str, ...]:
        seed_set = set(seed_tokens)
        for prefix in self.transitions:
            if seed_set.intersection(prefix):
                return prefix
        return self._first_prefix()


def _word_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token.isalpha()]
