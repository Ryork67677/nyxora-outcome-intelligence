from __future__ import annotations

from dataclasses import dataclass

from rag_v1.config import settings
from rag_v1.types import SearchHit


@dataclass
class GenerationResult:
    text: str
    usage: dict


class OpenAIGenerator:
    def __init__(self, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install OpenAI support: pip install -e '.[openai]'") from exc
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.generation_model

    def complete(self, instructions: str, input_text: str) -> GenerationResult:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=input_text,
        )
        usage = {}
        if getattr(response, "usage", None) is not None:
            obj = response.usage
            usage = obj.model_dump() if hasattr(obj, "model_dump") else {"raw": str(obj)}
        return GenerationResult(text=response.output_text, usage=usage)


def closed_book_answer(question: str) -> GenerationResult:
    if settings.generation_provider != "openai":
        raise ValueError("V1 implements OpenAI generation only; add another provider behind this interface if needed.")
    gen = OpenAIGenerator()
    return gen.complete(
        "Answer the question from your internal knowledge only. Do not browse or use external tools. "
        "If you are uncertain, say so. Be concise.",
        question,
    )


def rag_answer(question: str, hits: list[SearchHit]) -> GenerationResult:
    if settings.generation_provider != "openai":
        raise ValueError("V1 implements OpenAI generation only.")
    context_blocks = []
    for i, h in enumerate(hits, start=1):
        section = " > ".join(h.section_path)
        context_blocks.append(
            f"[S{i}] version={h.version_id} section={section} span={h.char_start}:{h.char_end}\n{h.text}"
        )
    context = "\n\n".join(context_blocks)
    prompt = f"Question:\n{question}\n\nRetrieved evidence:\n{context}"
    gen = OpenAIGenerator()
    return gen.complete(
        "Answer ONLY from the retrieved evidence. Cite supporting source labels like [S1]. "
        "If the evidence does not explicitly support the answer, say you do not have enough evidence.",
        prompt,
    )
