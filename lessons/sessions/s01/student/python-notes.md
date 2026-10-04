# What We Learned in Python — S01

Session 1 · Explorer's Field Notes

## 1. Python concept

- **`print(...)`** shows a value as output in the terminal.
- A **string** is a piece of text. In Python, you write a string inside
  matching quotation marks: `"like this"` or `'like this'`.
- **Running a Python file** means asking Python to follow the file's
  instructions from top to bottom.

## 2. Code we wrote

```python
print("The crystal lantern glows beside the path.")
print("A small robot waits by the landing pad.")
print("Tall stones circle an empty clearing.")
```

We ran it from the course folder:

```console
python lessons/sessions/s01/student/starter.py
```

## 3. What the code means

| Code | What it means |
|---|---|
| `print(` | "Show something in the terminal." |
| `"The crystal lantern glows beside the path."` | A string: the exact text to show. The quotes mark where it starts and ends. They are not printed. |
| `)` | The end of what `print` should show. |
| Three `print` lines | Python runs them in order, so three lines of output appear in the same order. |

Output:

```text
The crystal lantern glows beside the path.
A small robot waits by the landing pad.
Tall stones circle an empty clearing.
```

## 4. Why programmers use this

Output is how a program tells you what it is doing. Programmers use `print` to
show results, to check that code ran, and to hunt for bugs by printing what
they expect to see. Almost every program works with text, so strings appear
in nearly all Python code, far beyond games.

## 5. What we debugged

```python
print("The lantern flickers near the pond.')
```

Python reported:

```text
SyntaxError: unterminated string literal (detected at line 1)
```

The string starts with a double quote `"` but ends with a single quote `'`.
Python keeps looking for a matching `"` and reaches the end of the line
without finding one. Fix: make both quotes match.

```python
print("The lantern flickers near the pond.")
```

## 6. Key Python words

| Word | Meaning |
|---|---|
| `print` | A built-in Python function that shows output. |
| string | Text inside matching quotation marks. |
| quotation marks | `"` or `'`. The opening and closing marks must match. |
| output | What a program shows when it runs. |
| `SyntaxError` | Python cannot read the code because it breaks a writing rule. |

## 7. Try it yourself

1. Add a fourth observation that uses single quotes: `print('...')`.
2. Predict what happens if you delete the closing `)`. Run it and compare.
3. Print a string that contains an apostrophe, like `"Nova's map"`. Which
   quotation marks make that work?
