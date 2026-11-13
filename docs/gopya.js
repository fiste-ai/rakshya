// Nepali PII detection in a web page: the rules and the tokenizer run in WASM (./pkg, built
// from ../wasm), the tagger runs in ONNX Runtime Web. Nothing leaves the page.
//
//   const dist = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.31.1/dist/";
//   const ort = await import(dist + "ort.wasm.min.mjs");
//   import { load } from "./gopya.js";
//   const detector = await load({ ort, model: "https://huggingface.co/fiste-ai/gopya/resolve/main", runtime: dist });
//   const { spans, redacted } = await detector.detect("मेरो नाम ... हो");
//
// `model` is the address of a folder with tokenizer.json, tagger.json and onnx/model_quantized.onnx, and
// `runtime` the address of the files of ONNX Runtime Web. With `threads` above 1 the page must be
// cross-origin isolated.
//
// A span is { start, end, label, source }; start and end index the JavaScript string, and
// source is "rule" or "tagger".

import init, { Gopya, failure, find } from "./pkg/gopya.js";

export async function load({ ort, model, runtime, threads = 1 }) {
  const started = performance.now();
  const [, tokenizer, tagger, weights] = await Promise.all([
    init(),
    fetch(`${model}/tokenizer.json`).then((r) => r.text()),
    fetch(`${model}/tagger.json`).then((r) => r.text()),
    fetch(`${model}/onnx/model_quantized.onnx`).then((r) => r.arrayBuffer()),
  ]);
  const fetched = performance.now();
  const gopya = new Gopya(tokenizer, tagger);
  const tokenizerReady = performance.now();
  ort.env.wasm.wasmPaths = runtime;
  ort.env.wasm.numThreads = threads;
  const session = await ort.InferenceSession.create(weights, {
    executionProviders: ["wasm"],
    graphOptimizationLevel: "all",
  });
  const ready = performance.now();
  const timing = {
    fetch_ms: fetched - started,
    tokenizer_ms: tokenizerReady - fetched,
    session_ms: ready - tokenizerReady,
    model_bytes: weights.byteLength,
    tokenizer_bytes: tokenizer.length,
  };
  return new Detector(ort, gopya, session, timing);
}

class Detector {
  constructor(ort, gopya, session, timing) {
    this.ort = ort;
    this.gopya = gopya;
    this.session = session;
    this.timing = timing;
  }

  async detect(text) {
    const run = this.gopya.start(text);
    try {
      for (let i = 0; i < run.count; i++) {
        const ids = run.encode(i);
        const shape = [1, ids.length];
        const output = await this.session.run({
          input_ids: new this.ort.Tensor("int64", ids, shape),
          attention_mask: new this.ort.Tensor("int64", new BigInt64Array(ids.length).fill(1n), shape),
        });
        run.push(i, output.logits.data, output.trim_logits.data);
      }
      const spans = JSON.parse(run.finish()).map(([start, end, label, source]) => ({ start, end, label, source }));
      const result = { spans, redacted: run.redacted(), pieces: run.count };
      run.free();
      return result;
    } catch (error) {
      // A failure inside the WASM module leaves `run` unusable; say what the module reported.
      throw new Error(`${error.message || error}${failure() ? ": " + failure() : ""}`);
    }
  }
}

// The rules alone, with no model: identifiers as [{ start, end, label }].
export function rules(text) {
  return JSON.parse(find(text)).map(([start, end, label]) => ({ start, end, label }));
}

export { init };
