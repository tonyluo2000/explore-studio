# What We Learned in Python — S02

Session 2 · Place Your First Prop

## 1. Python concept

- A **variable** is a name that stores a value, so you can use the value later.
- **Assignment** uses `=` to store a value under a name. In Python, `=` means
  "store this", not "is equal to".
- A **string** is text in quotation marks, like `"Moon Compass"`.
- An **integer** is a whole number with no quotation marks, like `240`.
- **Coordinates** are numbers that describe a position. On the Trail screen,
  `x` is left/right and `y` is up/down.

## 2. Code we wrote

```python
object_name = "Moon Compass"
x = 240
y = 180
color = "purple"

print(object_name)
print(x, y)
print(color)
```

And in our own world folder, `my-explore-world/explorer.py`:

```python
explorer_name = "TODO: your explorer's name"
personality = "TODO: one personality trait"
print("Explorer:", explorer_name)
```

## 3. What the code means

| Code | What it means |
|---|---|
| `object_name = "Moon Compass"` | Store the string `"Moon Compass"` under the variable name `object_name`. |
| `x = 240` | Store the integer `240` under the variable name `x`. |
| `y = 180` | Store the integer `180` under the variable name `y`. |
| `color = "purple"` | Store the string `"purple"` under the variable name `color`. |
| `print(object_name)` | Show the value stored in `object_name`. No quotes, so Python uses the variable, not the word. |
| `print(x, y)` | Show both values on one line, separated by a space: `240 180`. |

Output:

```text
Moon Compass
240 180
purple
```

On the Trail screen, a bigger `x` moves the Moon Compass right, and a bigger
`y` moves it **down**. Screen coordinates start at the top-left corner.

## 4. Why programmers use this

Variables let a program remember information and reuse it by name. Change the
value in one place and everything that uses the name follows. Numbers stored as
integers can be compared and calculated with; text stored as strings cannot.

Outside Explore Studio, the same ideas are everywhere: a map app stores your
location as numeric coordinates, a spreadsheet stores values under column
names, and a science experiment stores measurements in variables.

## 5. What we debugged

**Same number, wrong type.** These two lines look alike, but they store
different kinds of value:

```python
x = 240     # an integer: a number Python can calculate with
x = "240"   # a string: the text characters 2, 4, 0
```

Try adding to the string version:

```python
x = "240"
print(x + 100)
```

Python reports:

```text
TypeError: can only concatenate str (not "int") to str
```

Python cannot add a number to text. Remove the quotes, `x = 240`, and
`print(x + 100)` shows `340`.

The object file has the same rule: `x: "240"` fails validation because the
package needs an integer. Write `x: 240`.

## 6. Key Python words

| Word | Meaning |
|---|---|
| variable | A name that stores a value. |
| value | The data stored, like `240` or `"purple"`. |
| assignment, `=` | Storing a value under a variable name. |
| string | Text inside matching quotation marks. |
| integer | A whole number, written without quotes. |
| coordinates | Numbers that describe a position, like `x` and `y`. |
| `TypeError` | Python was asked to combine values of types that do not fit together. |

## 7. Try it yourself

1. Predict, then test: what moves when you change `x = 240` to `x = 340`?
2. Add `print(type(x))` and `print(type(color))` to the starter. What does
   Python say each type is?
3. In `my-explore-world/companion.py`, change every `TODO` string to describe
   your own companion, then run it.
