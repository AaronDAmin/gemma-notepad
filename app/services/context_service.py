"""Builds prompts for the AI using document context."""


class ContextService:

    def build_explain_prompt(self, selected_text: str,
                              context: str, doc_name: str) -> str:
        return (
            f"You are a helpful study assistant. "
            f"The user is reading a document called \"{doc_name}\".\n\n"
            f"Here is the surrounding context from the document:\n"
            f"---\n{context}\n---\n\n"
            f"The user selected this passage:\n"
            f"\"{selected_text}\"\n\n"
            f"Explain this passage clearly and concisely. "
            f"Focus on what the document says, and add general knowledge only "
            f"if it helps understanding. Keep your answer under 150 words."
        )

    def build_question_prompt(self, selected_text: str,
                               context: str, question: str) -> str:
        return (
            f"You are a helpful study assistant.\n\n"
            f"Context from the document:\n"
            f"---\n{context}\n---\n\n"
            f"Selected passage: \"{selected_text}\"\n\n"
            f"User question: {question}\n\n"
            f"Answer the question based on the document context. "
            f"Be concise and clear."
        )


# Module-level singleton
context_service = ContextService()
