import { describe, expect, it } from "vitest";
import {
  CEREBRAS_MODELS,
  GROQ_MODELS,
  countResidualCJK,
  isAnthropicModel,
  isCerebrasModel,
  isGeminiModel,
  isGroqModel,
  isOpenAIModel,
  isOpenRouterModel,
  migrateModel,
} from "./App";

describe("provider model routing", () => {
  it("does not classify a Cerebras-only model as Groq", () => {
    // Regression test: gemma-4-31b only exists on Cerebras. It used to get
    // misrouted to Groq's API (404, model not found) because the backend picked
    // a provider from whichever API key was attached instead of the model ID.
    expect(isCerebrasModel("gemma-4-31b")).toBe(true);
    expect(isGroqModel("gemma-4-31b")).toBe(false);
  });

  it("classifies every Groq model id as Groq and nothing else", () => {
    for (const m of GROQ_MODELS) {
      expect(isGroqModel(m.id)).toBe(true);
      expect(isCerebrasModel(m.id)).toBe(false);
      expect(isOpenAIModel(m.id)).toBe(false);
      expect(isGeminiModel(m.id)).toBe(false);
      expect(isAnthropicModel(m.id)).toBe(false);
    }
  });

  it("classifies every Cerebras model id as Cerebras and nothing else", () => {
    for (const m of CEREBRAS_MODELS) {
      expect(isCerebrasModel(m.id)).toBe(true);
      expect(isGroqModel(m.id)).toBe(false);
      expect(isOpenAIModel(m.id)).toBe(false);
      expect(isGeminiModel(m.id)).toBe(false);
      expect(isAnthropicModel(m.id)).toBe(false);
    }
  });

  it("treats slash-containing ids that aren't Groq/Cerebras as OpenRouter", () => {
    expect(isOpenRouterModel("meta-llama/llama-3.3-70b-instruct:free")).toBe(true);
    // openai/gpt-oss-20b is a real Groq model id that happens to contain a slash —
    // it must not be misclassified as OpenRouter.
    expect(isOpenRouterModel("openai/gpt-oss-20b")).toBe(false);
  });

  it("classifies known Gemini and Anthropic model ids correctly", () => {
    expect(isGeminiModel("gemini-2.5-flash")).toBe(true);
    expect(isAnthropicModel("claude-sonnet-5")).toBe(true);
    expect(isGeminiModel("claude-sonnet-5")).toBe(false);
  });
});

describe("migrateModel", () => {
  it("maps a deprecated model id to its replacement", () => {
    expect(migrateModel("llama3-70b-8192")).toBe("llama-3.3-70b-versatile");
  });

  it("leaves unknown model ids unchanged", () => {
    expect(migrateModel("some-model-not-in-the-map")).toBe("some-model-not-in-the-map");
  });
});

describe("countResidualCJK", () => {
  it("returns 0 for pure Vietnamese/Latin text", () => {
    expect(countResidualCJK("Xin chào, đây là bản dịch tiếng Việt.")).toBe(0);
  });

  it("counts leftover Han/Japanese characters in an otherwise-translated string", () => {
    expect(countResidualCJK("Bản dịch còn sót 日本語 chưa dịch")).toBe(3);
  });
});
