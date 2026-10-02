export const REPO = "https://github.com/ritvikreddygangula/Open-AutoData";
export const PAPER_BLOG = "https://facebookresearch.github.io/RAM/blogs/autodata/";
export const PAPER_ARXIV = "https://arxiv.org/abs/2606.25996";

export type Model = {
  role: string;
  model: string;
  vendor: string;
  logo: string;
  job: string;
  size: "SLM" | "LLM";
  params: string;
  hf: string;
  license: string;
  licenseUrl: string;
};

// Licenses verified against each model's Hugging Face card.
export const MODELS: Model[] = [
  {
    role: "Challenger",
    model: "GLM-5.3",
    vendor: "Z.ai",
    logo: "zhipu",
    job: "Reads the filing chunk and writes a context, a question, a reference answer and a 10 to 15 criterion rubric. Rewrites from scratch when a round fails.",
    size: "LLM",
    params: "large",
    hf: "https://huggingface.co/zai-org/GLM-5.3",
    license: "GLM-5.3 License",
    licenseUrl: "https://huggingface.co/zai-org/GLM-5.3/blob/main/LICENSE",
  },
  {
    role: "Quality verifier",
    model: "Nemotron 3 Super",
    vendor: "NVIDIA",
    logo: "nvidia",
    job: "Before anything is solved, checks that the context does not leak the answer, the question tests reasoning not recall, and the rubric is checkable.",
    size: "LLM",
    params: "120B, 12B active",
    hf: "https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
    license: "NVIDIA Nemotron Open Model License",
    licenseUrl: "https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license/",
  },
  {
    role: "Weak solver",
    model: "Llama 3.2 3B Instruct",
    vendor: "Meta",
    logo: "meta",
    job: "Answers 3 times from the context alone. Should miss. If it aces the question, the question is too easy.",
    size: "SLM",
    params: "3B",
    hf: "https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct",
    license: "Llama 3.2 Community License",
    licenseUrl: "https://www.llama.com/llama3_2/license/",
  },
  {
    role: "Strong solver",
    model: "DeepSeek V4.1 Flash",
    vendor: "DeepSeek",
    logo: "deepseek",
    job: "Same prompt, 3 times. Only runs if the weak solver struggled. Should land the answer without acing it.",
    size: "LLM",
    params: "large",
    hf: "https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash",
    license: "MIT",
    licenseUrl: "https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/LICENSE",
  },
  {
    role: "Rubric judge",
    model: "Nemotron 3 Super",
    vendor: "NVIDIA",
    logo: "nvidia",
    job: "Grades each answer on its own, criterion by criterion, met or not met. Never sees the reference answer. Code turns verdicts into a 0 to 100 score.",
    size: "LLM",
    params: "120B, 12B active",
    hf: "https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
    license: "NVIDIA Nemotron Open Model License",
    licenseUrl: "https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license/",
  },
  {
    role: "Benchmark judge",
    model: "Qwen3.8 2.4T-A95B",
    vendor: "Alibaba Qwen",
    logo: "qwen",
    job: "Blind A/B judge for the final benchmark. Never touches the loop, so the pipeline never grades itself.",
    size: "LLM",
    params: "2.4T, 95B active",
    hf: "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B",
    license: "Qwen3.8-Max License",
    licenseUrl: "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/blob/main/LICENSE",
  },
];

export const STACK = [
  { name: "LangGraph", logo: "langgraph" },
  { name: "OpenRouter", logo: "openrouter" },
  { name: "Snowflake", logo: "snowflake" },
  { name: "Hugging Face", logo: "huggingface" },
  { name: "Meta FAIR", logo: "meta" },
];

export const MARQUEE = [
  "Open-weight",
  "Agentic Self-Instruct",
  "Weak-to-strong gap",
  "Rubric-graded",
  "Leakage-checked",
  "LangGraph state machine",
  "Snowflake native",
  "Zero human labels",
  "Blind A/B benchmark",
  "Small language model in the loop",
];

export const AUTHORS =
  "Kulikov, Whitehouse, Wu, Nie, Saha, Helenowski, Yuan, Golovneva, Lanchantin, Bachrach, Foerster, Li, Fang, Sukhbaatar, Weston";
