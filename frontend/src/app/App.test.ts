import { describe, expect, it } from "vitest";
import {
  CEREBRAS_MODELS,
  GROQ_MODELS,
  countResidualCJK,
  groupFilesByFolderPath,
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

describe("groupFilesByFolderPath", () => {
  // Regression test: syncing a folder with department subfolders (e.g. the
  // AanJSC_Documents/{Executive,Finance,HR,...} structure) used to dump every file
  // from every subfolder into one collection named after the top-level folder,
  // ignoring the subfolder structure entirely. It was then fixed the OTHER way too
  // far — subfolders became separate top-level collections, losing the parent
  // folder name entirely (e.g. syncing the whole AanJSC_Documents tree no longer
  // showed up as one big folder with department subfolders in the KB browser).
  // The correct behavior keeps both: "<top-level folder>/<subfolder>".
  it("splits files into one group per immediate subfolder, prefixed with the top-level folder", () => {
    const files = [
      { webkitRelativePath: "AanJSC_Documents/Executive/02_BaoCao.pdf" },
      { webkitRelativePath: "AanJSC_Documents/Executive/23_SoDo.docx" },
      { webkitRelativePath: "AanJSC_Documents/Finance/08_KiemToan.pdf" },
      { webkitRelativePath: "AanJSC_Documents/HR/06_HRPolicy.pdf" },
    ];
    const groups = groupFilesByFolderPath(files);
    const byCollection = Object.fromEntries(groups.map((g) => [g.collection, g.files.length]));
    expect(groups.length).toBe(3);
    expect(byCollection["AanJSC_Documents/Executive"]).toBe(2);
    expect(byCollection["AanJSC_Documents/Finance"]).toBe(1);
    expect(byCollection["AanJSC_Documents/HR"]).toBe(1);
  });

  it("uses the top-level folder name as a single collection when there are no subfolders", () => {
    const files = [
      { webkitRelativePath: "FlatFolder/a.pdf" },
      { webkitRelativePath: "FlatFolder/b.pdf" },
    ];
    const groups = groupFilesByFolderPath(files);
    expect(groups.length).toBe(1);
    expect(groups[0].collection).toBe("FlatFolder");
    expect(groups[0].files.length).toBe(2);
  });

  it("handles a mix of root-level files and subfolder files", () => {
    const files = [
      { webkitRelativePath: "Root/readme.pdf" },
      { webkitRelativePath: "Root/Engineering/spec.docx" },
    ];
    const groups = groupFilesByFolderPath(files);
    const byCollection = Object.fromEntries(groups.map((g) => [g.collection, g.files.length]));
    expect(groups.length).toBe(2);
    expect(byCollection["Root"]).toBe(1);
    expect(byCollection["Root/Engineering"]).toBe(1);
  });
});
