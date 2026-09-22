/**
 * "What We Learned in Python" and "What We Discovered" pages, one entry per
 * session.
 *
 * Every entry follows the same seven-part Python Notes pattern as the
 * student Course Kit's `lessons/sessions/sNN/student/python-notes.md`, and
 * mirrors that file. Discovery is optional and only exists where a session has
 * an honest real-world connection. Add a session here when its notes are
 * written; do not add empty placeholders.
 */

export type TermMeaning = { term: string; meaning: string };

export type SessionLearning = {
  /** Session id, e.g. "S02". Must exist in `classSessions`. */
  id: string;
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
print("The river fountain sounds like quiet rain.")
print("Fern waits near the edge of the trail.")`,
    runCommand: "python lessons/sessions/s01/student/starter.py",
    output: `The crystal lantern glows beside the path.
The river fountain sounds like quiet rain.
Fern waits near the edge of the trail.`,
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
      broken: `print("The lantern flickers near the fountain.')`,
      error: "SyntaxError: unterminated string literal (detected at line 1)",
      explanation:
        "The string starts with a double quote but ends with a single quote. Python keeps looking for a matching double quote and reaches the end of the line without finding one.",
      fixed: `print("The lantern flickers near the fountain.")`,
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
      "In my-explore-world/companion.py, change every TODO string to describe your own companion, then run it.",
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
];

export const sessionsWithNotes = learnSessions.map((session) => session.id);
