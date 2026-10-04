/**
 * "What We Learned in Python" and "What We Discovered" pages, one entry per
 * session.
 *
 * Every entry follows the same seven-part Python Notes pattern as the
 * student Course Kit's `lessons/sessions/sNN/student/python-notes.md`, and
 * mirrors that file (or, where `sourceFile` is set, is grounded in that
 * student file instead). Discovery is optional and only exists where a session has
 * an honest real-world connection. Add a session here when its notes are
 * written; do not add empty placeholders.
 */

export type TermMeaning = { term: string; meaning: string };

export type SessionLearning = {
  /** Session id, e.g. "S02". Must exist in `classSessions`. */
  id: string;
  /**
   * Course Kit file these notes follow, inside `lessons/sessions/sNN/student/`.
   * Defaults to `python-notes.md`; set it for sessions whose notes are grounded
   * in another student file because no `python-notes.md` exists yet.
   */
  sourceFile?: string;
  /** 1. Python concept */
  concepts: TermMeaning[];
  /** 2. Code we wrote */
  code: string;
  runCommand?: string;
  output: string;
  /** 3. What the code means: one row per important line. */
  meanings: TermMeaning[];
  /** 4. Why programmers use this, including uses outside Explore Studio. */
  why: string[];
  /** 5. What we debugged */
  debugged: { broken: string; error: string; explanation: string; fixed: string };
  /** 6. Key Python words */
  keyWords: TermMeaning[];
  /** 7. Try it yourself */
  tryIt: string[];
  /** Optional real-world Discovery, with fiction and fact kept apart. */
  discovery?: {
    topic: string;
    inNovasWorld: string[];
    inOurWorld: string[];
    question: string;
  };
};

export const learnSessions: SessionLearning[] = [
  {
    id: "S01",
    concepts: [
      { term: "print(...)", meaning: "Shows a value as output in the terminal." },
      {
        term: "string",
        meaning:
          "A piece of text, written inside matching quotation marks: \"like this\" or 'like this'.",
      },
      {
        term: "running a file",
        meaning: "Asking Python to follow the file's instructions from top to bottom.",
      },
    ],
    code: `print("The crystal lantern glows beside the path.")
print("A small robot waits by the landing pad.")
print("Tall stones circle an empty clearing.")`,
    runCommand: "python lessons/sessions/s01/student/starter.py",
    output: `The crystal lantern glows beside the path.
A small robot waits by the landing pad.
Tall stones circle an empty clearing.`,
    meanings: [
      { term: "print(", meaning: "“Show something in the terminal.”" },
      {
        term: "\"The crystal lantern glows beside the path.\"",
        meaning:
          "A string: the exact text to show. The quotes mark where it starts and ends. They are not printed.",
      },
      { term: ")", meaning: "The end of what print should show." },
      {
        term: "Three print lines",
        meaning: "Python runs them in order, so three lines of output appear in the same order.",
      },
    ],
    why: [
      "Output is how a program tells you what it is doing. Programmers use print to show results, check that code ran, and hunt for bugs.",
      "Almost every program works with text, so strings appear in nearly all Python code, far beyond games.",
    ],
    debugged: {
      broken: `print("The lantern flickers near the pond.')`,
      error: "SyntaxError: unterminated string literal (detected at line 1)",
      explanation:
        "The string starts with a double quote but ends with a single quote. Python keeps looking for a matching double quote and reaches the end of the line without finding one.",
      fixed: `print("The lantern flickers near the pond.")`,
    },
    keyWords: [
      { term: "print", meaning: "A built-in Python function that shows output." },
      { term: "string", meaning: "Text inside matching quotation marks." },
      { term: "quotation marks", meaning: "\" or '. The opening and closing marks must match." },
      { term: "output", meaning: "What a program shows when it runs." },
      { term: "SyntaxError", meaning: "Python cannot read the code because it breaks a writing rule." },
    ],
    tryIt: [
      "Add a fourth observation that uses single quotes: print('...').",
      "Predict what happens if you delete the closing ). Run it and compare.",
      "Print a string that contains an apostrophe, like \"Nova's map\". Which quotation marks make that work?",
    ],
  },
  {
    id: "S02",
    concepts: [
      { term: "variable", meaning: "A name that stores a value, so you can use the value later." },
      {
        term: "assignment",
        meaning: "Uses = to store a value under a name. In Python, = means “store this”, not “is equal to”.",
      },
      { term: "string", meaning: "Text in quotation marks, like \"Moon Compass\"." },
      { term: "integer", meaning: "A whole number with no quotation marks, like 240." },
      {
        term: "coordinates",
        meaning: "Numbers that describe a position. On the Trail screen, x is left/right and y is up/down.",
      },
    ],
    code: `object_name = "Moon Compass"
x = 240
y = 180
color = "purple"

print(object_name)
print(x, y)
print(color)`,
    runCommand: "python lessons/sessions/s02/student/starter.py",
    output: `Moon Compass
240 180
purple`,
    meanings: [
      {
        term: "object_name = \"Moon Compass\"",
        meaning: "Store the string \"Moon Compass\" under the variable name object_name.",
      },
      { term: "x = 240", meaning: "Store the integer 240 under the variable name x." },
      { term: "y = 180", meaning: "Store the integer 180 under the variable name y." },
      { term: "color = \"purple\"", meaning: "Store the string \"purple\" under the variable name color." },
      {
        term: "print(object_name)",
        meaning: "Show the value stored in object_name. No quotes, so Python uses the variable, not the word.",
      },
      { term: "print(x, y)", meaning: "Show both values on one line, separated by a space: 240 180." },
    ],
    why: [
      "Variables let a program remember information and reuse it by name. Change the value in one place and everything that uses the name follows.",
      "Integers can be compared and calculated with; text stored as a string cannot.",
      "Outside Explore Studio: a map app stores your location as numeric coordinates, a spreadsheet stores values under column names, and a science experiment stores measurements in variables.",
    ],
    debugged: {
      broken: `x = "240"
print(x + 100)`,
      error: "TypeError: can only concatenate str (not \"int\") to str",
      explanation:
        "\"240\" is text, not a number, so Python cannot add 100 to it. The object file has the same rule: x: \"240\" fails validation because the package needs an integer.",
      fixed: `x = 240
print(x + 100)  # 340`,
    },
    keyWords: [
      { term: "variable", meaning: "A name that stores a value." },
      { term: "value", meaning: "The data stored, like 240 or \"purple\"." },
      { term: "assignment, =", meaning: "Storing a value under a variable name." },
      { term: "string", meaning: "Text inside matching quotation marks." },
      { term: "integer", meaning: "A whole number, written without quotes." },
      { term: "coordinates", meaning: "Numbers that describe a position, like x and y." },
      { term: "TypeError", meaning: "Python was asked to combine values of types that do not fit together." },
    ],
    tryIt: [
      "Predict, then test: what moves when you change x = 240 to x = 340?",
      "Add print(type(x)) and print(type(color)) to the starter. What does Python say each type is?",
      "In my-explore-world/explorer.py and companion.py, replace every TODO with concrete choices for your own Explorer and Companion (or check your existing values, if you set these up before), then run both files and confirm your own values appear in the output.",
    ],
    discovery: {
      topic: "Coordinates, maps, and navigation",
      inNovasWorld: [
        "The Moon Compass is a fictional exploration tool: the expedition's first instrument in the story.",
        "In the program, it is a world object you placed with two integers, x and y.",
      ],
      inOurWorld: [
        "Coordinates are numbers that describe a position.",
        "Maps use coordinate systems too. Latitude says how far north or south of the equator a place is; longitude says how far east or west of the prime meridian. The Statue of Liberty is near 40.7° N, 74.0° W.",
        "On most maps north is up, so latitude grows as you go up. On a computer screen, y grows as you go down.",
        "Before GPS, navigators used maps, magnetic compasses, the positions of the Sun and stars, and careful records of speed, direction, and time.",
        "A magnetic compass needle lines up with Earth's magnetic field, so it points roughly north. Magnetic north is not exactly the same place as the geographic North Pole.",
      ],
      question:
        "What do coordinates describe? How is Nova's Moon Compass different from a real magnetic compass?",
    },
  },
  {
    id: "S03",
    sourceFile: "task-card.md",
    concepts: [
      {
        term: "f-string",
        meaning: "A string with an f right before the opening quote. Python fills in variables placed inside it.",
      },
      {
        term: "braces { }",
        meaning: "Curly braces inside an f-string mark where a variable's value goes.",
      },
      {
        term: "substitution",
        meaning: "Python replaces {object_name} with the value stored in object_name: Moon Compass.",
      },
      {
        term: "near vs. interacted",
        meaning:
          "near_message is the clue that appears when the player approaches. interacted_message is the reveal that appears after E is pressed nearby.",
      },
    ],
    code: `object_name = "Moon Compass"
near_message = f"The {object_name} needle trembles toward the dark trees."
interacted_message = f"The {object_name} points past the trees to a guide's lantern!"

print(near_message)
print(interacted_message)`,
    runCommand: "python lessons/sessions/s03/student/starter.py",
    output: `The Moon Compass needle trembles toward the dark trees.
The Moon Compass points past the trees to a guide's lantern!`,
    meanings: [
      {
        term: "near_message = f\"{object_name}\"",
        meaning:
          "The starter's unfinished line. Before you add a clue, the starter prints only Moon Compass on its first line.",
      },
      {
        term: "f\"The {object_name} needle trembles toward the dark trees.\"",
        meaning:
          "The f makes this an f-string. {object_name} becomes Moon Compass; the rest is your clue text.",
      },
      {
        term: "interacted_message = f\"...\"",
        meaning: "The reveal line, built the same way. It is the second line printed.",
      },
      {
        term: "print(near_message)",
        meaning: "Shows the finished clue, with the object name already filled in.",
      },
      {
        term: "when_near / when_interacted",
        meaning:
          "The YAML fields in objects/compass.yaml. Copy near_message's text into when_near and interacted_message's text into when_interacted. YAML gets plain text, with no braces.",
      },
    ],
    why: [
      "f-strings build a message from values you already have. Change object_name once and every message that uses it follows.",
      "They keep text readable: you see the whole sentence, with each variable right where its value will appear.",
      "Outside Explore Studio: an app greeting \"Welcome back, Sam!\", a score line in a game, or a weather report that fills in today's temperature are all built the same way.",
    ],
    debugged: {
      broken: `near_message = f"The {object_name needle begins to shimmer."`,
      error: "SyntaxError: invalid syntax. Perhaps you forgot a comma?",
      explanation:
        "The closing } after object_name is missing, so Python reads the rest of the line as code instead of text, and that code makes no sense. The error above is from Python 3.13; other versions may word the message differently, but it is always a SyntaxError on the f-string line.",
      fixed: `near_message = f"The {object_name} needle begins to shimmer."`,
    },
    keyWords: [
      { term: "f-string", meaning: "A string starting with f\" that can contain {variables}." },
      { term: "braces", meaning: "The curly brackets { and }. Every opening { needs a closing }." },
      { term: "substitution", meaning: "Replacing a variable name with its value." },
      { term: "when_near", meaning: "The YAML field shown when the player approaches." },
      { term: "when_interacted", meaning: "The YAML field shown after E is pressed nearby." },
      { term: "SyntaxError", meaning: "Python cannot read the code because it breaks a writing rule." },
    ],
    tryIt: [
      "Predict, then test: change object_name to \"Star Map\". What changes in both printed lines?",
      "Remove the f before the opening quote, run the file, and compare the output. What happens to the braces?",
      "If the two YAML message values were swapped, what would a player see when moving near? When pressing E?",
      "Write a second, harder clue that hints at the same reveal with less detail.",
    ],
  },
  {
    id: "S04",
    sourceFile: "task-card.md",
    concepts: [
      {
        term: "function",
        meaning: "A named, reusable set of steps. Define it once, then call it as many times as you need.",
      },
      {
        term: "def",
        meaning: "The keyword that defines a function: def, the function name, parentheses, then a colon.",
      },
      {
        term: "parameter",
        meaning: "The name in the definition's parentheses. In def greet(name):, name is the parameter.",
      },
      {
        term: "argument",
        meaning: "The value in a call's parentheses. In greet(\"Ari\"), \"Ari\" is the argument, and it becomes name.",
      },
      {
        term: "Python to the world",
        meaning:
          "greet(name) runs on your computer. The guide's greeting in the Trail is plain text in the YAML greeting field.",
      },
    ],
    code: `def greet(name):
    place = "Moonlit Trail"
    print(f"Welcome to {place}, {name}!")


greet("Ari")
greet("Sam")`,
    runCommand: "python lessons/sessions/s04/student/starter.py",
    output: `Welcome to Moonlit Trail, Ari!
Welcome to Moonlit Trail, Sam!`,
    meanings: [
      {
        term: "def greet(name):",
        meaning:
          "Defines a function named greet with one parameter, name. Defining it does not run it; nothing prints yet.",
      },
      {
        term: "place = \"Moonlit Trail\"",
        meaning:
          "The first body line. In the starter it says \"TODO: name your setting\" until you replace it with your setting name.",
      },
      {
        term: "print(f\"Welcome to {place}, {name}!\")",
        meaning:
          "Uses the value inside the function: {name} becomes whatever argument the call sent in. Both body lines are indented by the same four spaces.",
      },
      {
        term: "greet(\"Ari\")",
        meaning: "A call. It runs the body with name set to \"Ari\" and prints the first line.",
      },
      {
        term: "greet(\"Sam\")",
        meaning: "Your second call, with a name you choose. Same body, different argument, different line.",
      },
      {
        term: "greeting:",
        meaning:
          "The YAML field in character/guide.yaml. One sentence that tells who the guide is, what the trail problem is, and what help it needs. Press E beside the Moonlit Guide to see it in the speech bubble.",
      },
    ],
    why: [
      "Functions let you write a set of steps once and reuse it. Fix or change the body, and every call gets the change.",
      "Parameters make one function work for many values: the same greet body welcomes Ari, Sam, or anyone else.",
      "Outside Explore Studio: a game that greets each player by name, or an app that sends \"Happy birthday\" to whoever's birthday it is, calls one function with a different argument each time.",
    ],
    debugged: {
      broken: `greet()`,
      error: "TypeError: greet() missing 1 required positional argument: 'name'",
      explanation:
        "greet has one parameter, name, so every call needs one argument to fill it. greet() sends none. Read the final traceback line for the error type, then move upward to the first line naming starter.py to find the line number. Fix the call; do not remove or add a parameter to hide the error.",
      fixed: `greet("Kai")`,
    },
    keyWords: [
      { term: "function", meaning: "A named, reusable set of steps." },
      { term: "def", meaning: "The keyword that starts a function definition." },
      { term: "parameter", meaning: "The name in a definition's parentheses that receives a value." },
      { term: "argument", meaning: "The value placed in a call's parentheses." },
      { term: "call", meaning: "Using a function's name with parentheses to run its body." },
      { term: "indentation", meaning: "The four spaces that put lines inside the function body." },
      { term: "traceback", meaning: "Python's error report: the error type on the last line, and the file and line above it." },
    ],
    tryIt: [
      "Predict, then test: add greet(\"Kai\"). What exact line will it print?",
      "Change place to your own setting name. How many printed lines change?",
      "Remove the four spaces before the print line, run the file, and read the error. Then put them back.",
      "Rewrite the guide's YAML greeting in one sentence using your three voice words, then read it in the speech bubble.",
    ],
  },
  {
    id: "S05",
    sourceFile: "task-card.md",
    concepts: [
      {
        term: "list",
        meaning: "One value that holds several items in order, written inside square brackets [ ] with commas between the items.",
      },
      {
        term: "index",
        meaning: "An item's position number. Python counts from 0, so the first item is [0] and the second is [1].",
      },
      {
        term: "[-1]",
        meaning: "A negative index counts from the end. dialogue[-1] is always the final item, however long the list is.",
      },
      {
        term: "len(...)",
        meaning: "Counts the items in a list. A three-line conversation has len(dialogue) equal to 3.",
      },
      {
        term: "Python to the world",
        meaning:
          "The dialogue list runs on your computer. The guide's lines in the Trail are plain text in the YAML conversation field, in the same order.",
      },
    ],
    code: `dialogue = [
    "Guide: The dark stretch past the ridge won't clear.",
    "Guide: Three old marker-lights never burned out.",
    "Guide: Find those three lights and lead me home.",
]

print(dialogue[0])
print(dialogue[-1])
print(len(dialogue))`,
    runCommand: "python lessons/sessions/s05/student/starter.py",
    output: `Guide: The dark stretch past the ridge won't clear.
Guide: Find those three lights and lead me home.
3`,
    meanings: [
      {
        term: "dialogue = [",
        meaning: "Starts a list named dialogue. Everything up to the closing ] is one value: the whole conversation.",
      },
      {
        term: "\"Guide: The dark stretch past the ridge won't clear.\",",
        meaning:
          "Item 0, the situation. Each line is a string, and a comma separates it from the next item. In the starter it says \"TODO: write an opening line\" until you write your own.",
      },
      {
        term: "\"Guide: Three old marker-lights never burned out.\",",
        meaning: "Item 1, the optional middle clue. A two-line conversation leaves it out.",
      },
      {
        term: "\"Guide: Find those three lights and lead me home.\",",
        meaning: "The final item, the task: what the explorer should do next.",
      },
      {
        term: "print(dialogue[0])",
        meaning: "Shows the first line. The square brackets after a list name pick one item by its index.",
      },
      {
        term: "print(dialogue[-1])",
        meaning: "Shows the final line. -1 still works if the list has two lines instead of three.",
      },
      {
        term: "print(len(dialogue))",
        meaning: "Shows how many lines the list holds. The starter already prints this, so before your changes it prints 2.",
      },
      {
        term: "conversation:",
        meaning:
          "The YAML field in character/guide.yaml: the same 2–3 spoken lines, in the same order, without the \"Guide: \" label. Press E beside the Moonlit Guide once per line to see each one in the speech bubble.",
      },
    ],
    why: [
      "Lists keep related values together and in order, so one name can hold a whole conversation instead of three separate variables.",
      "Indexes let you reach any position directly, and [-1] always reaches the end, even when the list grows or shrinks.",
      "Outside Explore Studio: a music playlist, the messages in a group chat, and the lines a game character says are all ordered lists. Play them in a different order and the meaning changes.",
    ],
    debugged: {
      broken: `print(dialogue[3])`,
      error: "IndexError: list index out of range",
      explanation:
        "A three-line list has items at positions 0, 1, and 2. There is no position 3, so Python stops with an IndexError. Read the final traceback line for the error type, then move upward to the line naming starter.py. Use dialogue[-1] for the final line: it is correct for two lines or three.",
      fixed: `print(dialogue[-1])`,
    },
    keyWords: [
      { term: "list", meaning: "An ordered collection of items inside square brackets." },
      { term: "item", meaning: "One value stored in a list." },
      { term: "index", meaning: "An item's position number, starting at 0." },
      { term: "zero-based", meaning: "Counting positions from 0, not 1." },
      { term: "negative index", meaning: "A position counted from the end: -1 is the final item." },
      { term: "len", meaning: "The function that counts a list's items." },
      { term: "IndexError", meaning: "Python's error for asking for a position the list does not have." },
    ],
    tryIt: [
      "Predict, then test: what does print(dialogue[1]) show for your conversation?",
      "Swap two lines, predict how the story changes, run it, then restore the situation → clue → task order.",
      "Remove the middle line. What does len(dialogue) print now, and does dialogue[-1] still show your final line?",
      "In the Trail, press E once more after the final line. Which line comes next, and does M05 stay complete?",
    ],
  },
];

export const sessionsWithNotes = learnSessions.map((session) => session.id);
