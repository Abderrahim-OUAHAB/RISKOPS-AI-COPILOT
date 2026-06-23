from openai import OpenAI, OpenAIError

from app.core.config import settings

PLACEHOLDER_API_KEYS = {
    "",
    "replace_with_your_key_later",
    "your_openai_api_key",
    "your_api_key",
}


class OpenAIConfigurationError(Exception):
    pass


class OpenAIServiceError(Exception):
    pass


def _get_client() -> OpenAI:
    api_key = settings.openai_api_key.strip()
    if api_key.lower() in PLACEHOLDER_API_KEYS:
        raise OpenAIConfigurationError(
            "OPENAI_API_KEY is missing or still set to the placeholder value."
        )

    return OpenAI(api_key=api_key)


def create_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    client = _get_client()
    try:
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
    except OpenAIError as exc:
        raise OpenAIServiceError("OpenAI embedding request failed.") from exc

    embeddings = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
    return embeddings


def generate_answer(question: str, context_chunks: list[str]) -> str:
    client = _get_client()
    context = "\n\n".join(context_chunks)
    system_prompt = (
        "You are AI RiskOps Copilot. Answer in French. "
        "Use only the provided sources. If the sources are insufficient, say that "
        "you do not know instead of inventing information."
    )
    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Sources:\n{context}\n\n"
        "Answer with a concise business-risk summary grounded in the sources."
    )

    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
    except OpenAIError as exc:
        raise OpenAIServiceError("OpenAI answer generation request failed.") from exc

    answer = response.choices[0].message.content
    if not answer:
        raise OpenAIServiceError("OpenAI returned an empty answer.")

    return answer.strip()
