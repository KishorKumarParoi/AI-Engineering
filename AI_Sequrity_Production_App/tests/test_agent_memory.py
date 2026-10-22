from app.agents.nodes.summarizer import summarize_conversation_if_needed


def test_no_summarization_on_short_history():
    msgs = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    res = summarize_conversation_if_needed(msgs, max_turns=6)
    assert len(res) == 2
