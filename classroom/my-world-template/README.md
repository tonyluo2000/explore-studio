# My Explore World

**This folder belongs to you.**

Your explorer, your companion, your journal, and your own projects live here.
Course updates never replace this folder:

- the course folder, `explore-studio-course`, is the **Course Kit**. Your
  teacher may hand out a newer copy of it at any time;
- this folder, `my-explore-world`, is your **Student Workspace**. It lives at
  `~/my-explore-world`, beside the Course Kit, and stays yours all year. Never
  delete or replace it.

If `make-my-world.py` runs again, it only adds files that are missing. It never
changes or replaces a file that is already here.

| File or folder | What it is |
|---|---|
| `explorer.py` | Your explorer's name, appearance, personality, and favorite subject or interest. Run it to print your Explorer Card. |
| `companion.py` | Your companion's name, kind, personality, specialty or interest, and one future ability. Run it to print your Companion Card. |
| `journey.md` | **My Explore Journey**: your short after-class journal for the whole year. Open it in VS Code, add an entry, save. You will use it to prepare your S30 presentation. |
| `projects/moon-compass/` | Your editable S02 Explorer Package. Validate and launch this copy. |

Run every command from the Course Kit terminal, with `.venv` active, just like
the lesson commands:

```console
cd ~/explore-studio-course
source .venv/bin/activate
python ../my-explore-world/explorer.py
python ../my-explore-world/companion.py
```

In VS Code, keep the window open on `~/explore-studio-course` and open your
files from its terminal, for example `code ~/my-explore-world/explorer.py`.

The cards show your values. They do not change the Trail yet: in S02 you
walk as Nova, the class example, and your Moon Compass `x`, `y`, and `color`
are what change the world.

The Moon Compass package is also yours. From the Course Kit folder, validate it
with:

```console
explore-package validate ../my-explore-world/projects/moon-compass
```

Running `make-my-world.py` again never changes that package. A fresh seed is
copied only when a file is missing.

Nothing in this folder is uploaded, and no account is involved. Keep a backup
copy if your teacher suggests one.
