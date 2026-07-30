# Unlimited-OCR Inspector

Streamlit inspector for [Baidu Unlimited-OCR](https://github.com/baidu/Unlimited-OCR) (MIT license, arXiv:2606.23050) — a DeepSeek-OCR-lineage 3B vision-language model for long-document parsing, served via a vLLM OpenAI-compatible endpoint.

## 1. Start the vLLM server (GPU host)

Requires the dedicated `vllm/vllm-openai:unlimited-ocr` image (a stock/pip vLLM build won't register the model correctly) and the `--logits_processors` flag (without it, long documents loop on repeated tokens):

```bash
docker run -d --gpus all \
  --privileged --ipc=host \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --name unlimited-ocr \
  vllm/vllm-openai:unlimited-ocr \
  baidu/Unlimited-OCR \
  --trust-remote-code \
  --logits_processors vllm.model_executor.models.unlimited_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching \
  --mm-processor-cache-gb 0 \
  --tensor-parallel-size 1
```

Server exposes an OpenAI-compatible endpoint at `http://<host>:8000/v1`. No API key needed — vLLM auth is `EMPTY`.

## 2. Point the app at your server

Set `UNLIMITED_OCR_URL=http://<host>:8000/v1` in the repo-root `.env` (or paste it into the app's sidebar).

## 3. Run the Streamlit app

```bash
streamlit run unlimited_ocr/app.py
```

## Notes

- Prompt must start with the literal `<image>` token — omitting it returns empty output. Per the official README, single images use `<image>document parsing.`, PDF/multi-page pages use `<image>Multi page parsing.` (the app picks the right one automatically).
- `window_size` is 128 for single images, 1024 for multi-page PDFs.
- Server must be started with `--logits_processors vllm.model_executor.models.unlimited_ocr:NGramPerReqLogitsProcessor` or output can loop on repeated tokens.
- Raw output wraps the whole page in `<PAGE>...</PAGE>` and inlines the label + box together in one tag: `<|det|>title [x1, y1, x2, y2]<|/det|>` followed by the recognized text for that element — coordinates normalized 0-999 relative to the original image. "Clean Markdown" mode strips all of this to plain text; the bounding-box viewer parses it into color-coded boxes.

## No bounding boxes showing up?

The app's "Bounding Box Viewer" needs `<|det|>` tokens in the raw output. If it says none were found:
1. Confirm you're on a build that includes the `Multi page parsing.` vs `document parsing.` prompt fix (PDF pages previously used the wrong prompt and silently lost grounding).
2. Confirm the vLLM server is the dedicated `vllm/vllm-openai:unlimited-ocr` (or `-cu129`) Docker image — a stock/pip vLLM build doesn't register `UnlimitedOCRForCausalLM` and may not enter the grounding-generation path at all.
3. Confirm the server was started with `--logits_processors vllm.model_executor.models.unlimited_ocr:NGramPerReqLogitsProcessor` (a server startup flag, separate from the client's `extra_body.vllm_xargs`).
