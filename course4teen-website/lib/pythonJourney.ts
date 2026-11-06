import { classSessions, sessionsWithSlides } from "./calendar";

export type PythonJourneyStep = {
  id: string;
  topic: string;
  concepts: string[];
  capability: string;
};

/**
 * Python objectives from docs/curriculum-sessions-01-15.md,
 * docs/curriculum-sessions-16-30.md and the session runbooks, using the
 * owner-approved S01–S30 Python Journey mapping. Independent of story data,
 * calendar titles/dates, and the detailed examples in lib/learn.ts.
 *
 * Server-rendered only: consumers must use publishedPythonSteps or
 * pythonJourneyThrough so unpublished objectives never reach public markup.
 */
const pythonJourneySteps: Record<string, PythonJourneyStep> = {
  "S01": {
    "id": "S01",
    "topic": "Output and strings",
    "concepts": [
      "print()",
      "string literals",
      "matching quotes"
    ],
    "capability": "Record observations as text and print them."
  },
  "S02": {
    "id": "S02",
    "topic": "Variables and basic types",
    "concepts": [
      "variables",
      "assignment",
      "strings",
      "integers",
      "x/y coordinates"
    ],
    "capability": "Store named values and distinguish text from numbers."
  },
  "S03": {
    "id": "S03",
    "topic": "f-strings",
    "concepts": [
      "f-strings",
      "braces",
      "substitution"
    ],
    "capability": "Build messages from variable values."
  },
  "S04": {
    "id": "S04",
    "topic": "Functions",
    "concepts": [
      "def",
      "function calls",
      "parameters",
      "arguments",
      "indentation",
      "traceback reading"
    ],
    "capability": "Define reusable behavior and call it with different values."
  },
  "S05": {
    "id": "S05",
    "topic": "Lists",
    "concepts": [
      "lists",
      "indexing",
      "zero-based positions",
      "negative indexing",
      "len()",
      "IndexError"
    ],
    "capability": "Store ordered data and retrieve items by position."
  },
  "S06": {
    "id": "S06",
    "topic": "Dictionaries and loops",
    "concepts": [
      "dictionaries",
      "key/value pairs",
      "key lookup",
      "for loop",
      "list of dictionaries",
      "iteration",
      "KeyError"
    ],
    "capability": "Model structured records and process a collection with one loop."
  },
  "S07": {
    "id": "S07",
    "topic": "Boolean state",
    "concepts": [
      "True",
      "False",
      "assignment",
      "changing state"
    ],
    "capability": "Represent two states and predict False → True → False changes."
  },
  "S08": {
    "id": "S08",
    "topic": "if / else",
    "concepts": [
      "conditions",
      "if",
      "else",
      "Boolean branches"
    ],
    "capability": "Choose between two behaviors based on state."
  },
  "S09": {
    "id": "S09",
    "topic": "Counters and loops",
    "concepts": [
      "integer counters",
      "updating values",
      "loops",
      "off-by-one reasoning",
      "basic assert"
    ],
    "capability": "Count repeated actions and verify when a goal is reached."
  },
  "S10": {
    "id": "S10",
    "topic": "Comparisons and assertions",
    "concepts": [
      "functions",
      "return",
      ">=",
      "boundary cases",
      "assertions"
    ],
    "capability": "Write and test a function that decides whether a numeric threshold is met."
  },
  "S11": {
    "id": "S11",
    "topic": "Boolean AND",
    "concepts": [
      "and",
      "truth tables",
      "two Boolean parameters"
    ],
    "capability": "Require two conditions to be true at the same time."
  },
  "S12": {
    "id": "S12",
    "topic": "Boolean OR",
    "concepts": [
      "or",
      "truth tables",
      "contrasting AND vs OR"
    ],
    "capability": "Accept either of two conditions."
  },
  "S13": {
    "id": "S13",
    "topic": "Boolean NOT",
    "concepts": [
      "not",
      "inversion"
    ],
    "capability": "Reverse a Boolean condition and explain the result."
  },
  "S14": {
    "id": "S14",
    "topic": "Reuse and refactoring",
    "concepts": [
      "dictionaries",
      "functions",
      "shared data",
      "eliminating duplication"
    ],
    "capability": "Reuse one named configuration in multiple places."
  },
  "S15": {
    "id": "S15",
    "topic": "Decomposition and state tracing",
    "concepts": [
      "small functions",
      "lists",
      "loops",
      "state",
      "assertions",
      "ordered sequences"
    ],
    "capability": "Break a multi-step puzzle into testable pieces and verify reset/success cases."
  },
  "S16": {
    "id": "S16",
    "topic": "Deeper data traversal",
    "concepts": [
      "nested records",
      "dictionary lookup",
      "enumerate()",
      "loops"
    ],
    "capability": "Read structured records and produce a numbered catalog."
  },
  "S17": {
    "id": "S17",
    "topic": "Searching and filtering",
    "concepts": [
      "functions",
      "parameters",
      "return values",
      "loops",
      "filtering",
      "counting matches"
    ],
    "capability": "Search a collection and return matching records while preserving order."
  },
  "S18": {
    "id": "S18",
    "topic": "Aggregation",
    "concepts": [
      "min()",
      "max()",
      "sum()",
      "averages",
      "empty-input contracts",
      "ties"
    ],
    "capability": "Summarize numeric data safely."
  },
  "S19": {
    "id": "S19",
    "topic": "Sorting and flattening",
    "concepts": [
      "nested data",
      "flattening",
      "sorted()",
      "key functions",
      "stable ordering"
    ],
    "capability": "Transform nested records and create a deterministic priority order."
  },
  "S20": {
    "id": "S20",
    "topic": "Data pipeline",
    "concepts": [
      "YAML loading",
      "validation",
      "search",
      "aggregation",
      "sorting",
      "transformation",
      "file output"
    ],
    "capability": "Build a deterministic end-to-end data pipeline."
  },
  "S21": {
    "id": "S21",
    "topic": "Defensive validation",
    "concepts": [
      "record shape",
      "required fields",
      "types",
      "ranges",
      "uniqueness",
      "diagnostics"
    ],
    "capability": "Validate malformed data and produce stable useful error messages."
  },
  "S22": {
    "id": "S22",
    "topic": "Debugging method",
    "concepts": [
      "observe",
      "hypothesis",
      "one change",
      "rerun",
      "compare evidence",
      "assertions"
    ],
    "capability": "Run a disciplined debugging loop and distinguish input, validation, and logic errors."
  },
  "S23": {
    "id": "S23",
    "topic": "Modular design",
    "concepts": [
      "modules",
      "data flow",
      "I/O boundary",
      "validation/rules",
      "build/output",
      "regression testing"
    ],
    "capability": "Split a working pipeline into modules while preserving exact behavior."
  },
  "S24": {
    "id": "S24",
    "topic": "Dictionaries as indexes and optimization",
    "concepts": [
      "linear search",
      "dictionary lookup",
      "ID→record index",
      "duplicate handling",
      "behavior-preserving refactor"
    ],
    "capability": "Improve lookup efficiency and code clarity without changing results."
  },
  "S25": {
    "id": "S25",
    "topic": "Integration",
    "concepts": [
      "combining modules/mechanics",
      "deterministic builds",
      "validation",
      "debugging"
    ],
    "capability": "Combine multiple supported systems into one working prototype."
  },
  "S26": {
    "id": "S26",
    "topic": "Program design",
    "concepts": [
      "decomposition",
      "planning",
      "dependencies",
      "bounded scope",
      "fallback planning"
    ],
    "capability": "Design a program before implementation and choose a feasible first slice."
  },
  "S27": {
    "id": "S27",
    "topic": "Function contracts and nested data",
    "concepts": [
      "responsibility maps",
      "function contracts",
      "imported helpers",
      "nested validation",
      "deterministic dictionaries"
    ],
    "capability": "Build a modular Python core from explicit contracts."
  },
  "S28": {
    "id": "S28",
    "topic": "File I/O and deterministic generation",
    "concepts": [
      "YAML input/output",
      "modular integration",
      "deterministic serialization",
      "validation"
    ],
    "capability": "Connect Python logic to stable generated Explorer Package files."
  },
  "S29": {
    "id": "S29",
    "topic": "Review and refactoring",
    "concepts": [
      "evidence-first review",
      "behavior-preserving refactoring",
      "technical feedback",
      "regression evidence"
    ],
    "capability": "Improve code after review while proving behavior remains unchanged."
  },
  "S30": {
    "id": "S30",
    "topic": "Explain and present a system",
    "concepts": [
      "modular architecture",
      "algorithm choices",
      "validation",
      "deterministic output",
      "recovery"
    ],
    "capability": "Explain, demonstrate, and recover a substantial Python project."
  }
};

export const PYTHON_JOURNEY_HREF = "/students/journey/#python-journey";
export const totalPythonSteps = Object.keys(pythonJourneySteps).length;

/** Calendar order; sessionsWithSlides is the sole publication boundary. */
export const publishedPythonSteps = classSessions
  .filter((session) => sessionsWithSlides.includes(session.id))
  .map((session) => pythonJourneySteps[session.id]);

export const currentPythonStep = publishedPythonSteps.at(-1);

/** A session sees its own cumulative history, never later published lessons. */
export function pythonJourneyThrough(session: string): PythonJourneyStep[] {
  const index = publishedPythonSteps.findIndex((step) => step.id === session);
  return index < 0 ? [] : publishedPythonSteps.slice(0, index + 1);
}
