# Windows Setup: WSL, VS Code, and the Course Kit

> **Status:** Canonical student setup and update guide for Windows. Every other
> setup page links here. It ships inside the Course Kit as
> `docs/windows-wsl-setup.md`.

This page covers setting up a Windows computer once, checking you are ready
before each class, and getting each newer Course Kit. Do the steps in order. A
step marked **(adult)** may need a parent or teacher, because it asks for a
Windows administrator or a password.

The one supported Windows path is:

**Windows 11 → WSL 2 → Ubuntu → Python 3.11+ → VS Code connected to WSL →
Course Kit in the Ubuntu home folder.**

Native Windows Python and PowerShell are not supported for the course: the
Trail and Explorer Package export need Linux. On a Mac, skip the WSL steps, use
the **Terminal** app, and keep the same two folders.

## The two folders

You keep exactly two Explore Studio folders, side by side in your home folder:

| Folder | What is inside | Can it be replaced? |
|---|---|---|
| `~/explore-studio-course` | The **Course Kit**: lessons, task cards, the computer check, and the course tools in `~/explore-studio-course/.venv`. | **Yes.** Each newer Course Kit replaces this whole folder, `.venv` included. |
| `~/my-explore-world` | **Your world**: your explorer, companion, journal (`journey.md`), and projects. You make it in Session 2. | **No. Never delete, rename, or replace it.** Course Kit updates never touch it. |

`~` means your home folder. In Ubuntu that is `/home/<your Ubuntu name>`. Use
these exact names. Do not put either folder in Downloads, on the Desktop, inside
the other folder, or under `/mnt/c`.

- **Lesson commands run from `~/explore-studio-course`**, with its `.venv`
  active. That includes `explore-package`, the Trail, and
  `python3 check-my-computer.py`.
- **Your own work is saved in `~/my-explore-world`.** Anything you keep
  inside `~/explore-studio-course` can disappear when the Course Kit is
  replaced.
- **The course tools live in one place only: `~/explore-studio-course/.venv`.**
  Do not make a `.venv` in your home folder (`~/.venv`), in `my-explore-world`,
  or anywhere else.

## Am I ready? (before every class, under a minute)

1. Open **Ubuntu** (not PowerShell).
2. Run:

   ```console
   cd ~/explore-studio-course
   source .venv/bin/activate
   python3 check-my-computer.py
   ```

3. The summary at the end must say `(current)` for Course tools, and the last
   result line must be `READY FOR EXPLORE STUDIO`:

   ```text
     Course folder: OK
     Virtual environment: .venv
     Course tools: abc1234 (current)
     Trail dependency: OK

   READY FOR EXPLORE STUDIO
   ```

   Your seven letters and numbers will differ; only `(current)` matters.
4. `pwd` must end with `explore-studio-course`.
5. Launch your session's Trail command once and close it.

If any line says `[help]`, do what its arrow says, or show the summary to your
teacher. A teacher can tell what is wrong from those few lines.

## 1. Install WSL and Ubuntu (adult, once)

These commands run in **Windows PowerShell**, not inside Ubuntu.

1. Open the Start menu, type **PowerShell**, right-click **Windows PowerShell**
   (or **Terminal**), and choose **Run as administrator**.
2. Run:

   ```console
   wsl --install
   ```

3. **Restart Windows when it asks.** WSL does not work until you restart.
4. After the restart, open **Ubuntu** from the Start menu. The first time, it
   asks you to create a Linux username and password. This is a new account
   just for Ubuntu, not your Windows or school password. Nothing appears on
   screen while you type the password; that is normal. Remember it, because
   `sudo` asks for it.

Already have WSL? In PowerShell, run `wsl -l -v`. The `VERSION` column must say
`2`. If it says `1`, run `wsl --set-version <the name shown> 2`. If Linux
windows will not open later, run `wsl --update`, then `wsl --shutdown`, and
open Ubuntu again.

## 2. Use the Ubuntu terminal

Run every course command in the **Ubuntu** terminal. Open it from the Start menu
(type **Ubuntu**), or open a new Ubuntu tab in Windows Terminal. Later, the
VS Code terminal is an Ubuntu terminal too (step 6).

| Prompt looks like | What it is | Use it for course commands? |
|---|---|---|
| `name@computer:~$` | Ubuntu | **Yes** |
| `PS C:\Users\...>` | PowerShell | No (only for step 1) |
| `C:\Users\...>` | Command Prompt | No |

## 3. Install the Ubuntu packages and check Python (once)

In the Ubuntu terminal:

```console
sudo apt update
sudo apt install -y python3 python3-venv python3-pip unzip
python3 --version
```

The version must be **3.11 or newer**. Ubuntu 24.04, which `wsl --install`
gives new computers, has Python 3.12.

**If it shows 3.10 or older, stop here.** This is an older Ubuntu (such as
22.04), and installing `python3` again will not change its version. Ask an
adult to install Ubuntu 24.04 by running `wsl --install -d Ubuntu-24.04` in
Windows PowerShell, then open **Ubuntu 24.04** and continue from step 3 there.
Do not try to continue with the older Python.

## 4. Put the Course Kit in your Ubuntu home

Download `explore-studio-course.zip` from the course website. Windows saves it
in your Windows **Downloads** folder, which Ubuntu sees as
`/mnt/c/Users/<your Windows name>/Downloads/`. Copy it into your Ubuntu home
folder:

```console
cd ~
ls /mnt/c/Users/
cp /mnt/c/Users/YOUR-WINDOWS-NAME/Downloads/explore-studio-course.zip ~
```

Replace `YOUR-WINDOWS-NAME` with your folder name from the `ls` list. If
Windows saved the file as `explore-studio-course (1).zip`, use that name in
quotes.

Rather drag and drop? Run `explorer.exe .` in the Ubuntu terminal. It opens your
Ubuntu home folder in File Explorer. Drag the ZIP from Downloads into that
window.

Now unzip it **in Ubuntu** (not with Windows "Extract All"):

```console
cd ~
unzip -q explore-studio-course.zip
ls ~/explore-studio-course
```

You should see `START-HERE.md`, `check-my-computer.py`, and `lessons`. You can
then delete the ZIP with `rm ~/explore-studio-course.zip`.

| Do | Do not |
|---|---|
| `~/explore-studio-course` | `/mnt/c/Users/.../explore-studio-course` |

**Why not `/mnt/c`?** `/mnt/c` is your Windows drive, seen from Ubuntu. The
course is slow there, and Linux tools such as `.venv` and Explorer Package
export do not work reliably. Microsoft recommends keeping Linux project files
in the Linux home folder. The computer check reports a course folder under
`/mnt/c` as `[help]`.

## 5. Install the course tools, then check

```console
cd ~/explore-studio-course
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-student.txt
python3 check-my-computer.py
```

The last line must say `READY FOR EXPLORE STUDIO`. If it says
`SETUP HELP NEEDED`, fix each line marked `[help]` by following its arrow.

Every time you open a new terminal for class, start with
`cd ~/explore-studio-course` and `source .venv/bin/activate`. Your prompt then
starts with `(.venv)`.

Want to test a computer before downloading the course? Run the standalone
check from the course website with `python3 check-my-computer.py --computer-only`.
It checks only the computer, ends with `COMPUTER CHECK PASSED`, and never says
READY, because the course is not set up yet.

## 6. Open the course in VS Code

**Once:** install VS Code for Windows from
[code.visualstudio.com](https://code.visualstudio.com/). In VS Code, open
Extensions and install **WSL** (by Microsoft). The **Python** extension (by
Microsoft) is also helpful.

**Every session**, start VS Code from the Ubuntu terminal, in the Course Kit:

```console
cd ~/explore-studio-course
code .
```

- The first time, VS Code sets itself up inside Ubuntu. Wait for it to finish.
- The bottom-left corner must say **WSL: Ubuntu** (or **WSL: Ubuntu-24.04**).
  If it does not, close that window and run `code .` from the Ubuntu terminal
  again.
- Open a terminal with **Terminal → New Terminal**. It is an Ubuntu terminal
  already in `~/explore-studio-course`. If the prompt does not show `(.venv)`,
  run `source .venv/bin/activate`.
- To choose Python, press **Ctrl+Shift+P**, choose **Python: Select
  Interpreter**, and pick `./.venv/bin/python`.

**Your own files (from Session 2).** Keep this one VS Code window on the Course
Kit. Open a file from your world with a command in its terminal:

```console
code ~/my-explore-world/explorer.py
```

It opens beside the lesson files, and the terminal stays in the Course Kit.

| What | Where |
|---|---|
| Lesson command terminal | `~/explore-studio-course` |
| Your own files | `~/my-explore-world` |

Do not run `code .` from `~/my-explore-world`: that window's terminal starts in
your world folder, where there is no `.venv` and lesson commands do not work.
Do not open the course from File Explorer, from a `C:\` folder, or through
`\\wsl.localhost` in a VS Code window that does not say **WSL** in the corner.

The Trail opens as its own window. Click it once before using the keys.

## 7. Make your world folder (Session 2)

Your Session 2 task card tells you when. From the Course Kit:

```console
cd ~/explore-studio-course
python3 make-my-world.py
```

It creates `~/my-explore-world` beside the Course Kit. Running it again only
adds missing files; it never replaces your work, and it never touches an
existing `journey.md`.

## Get a newer Course Kit

Do this when your teacher says a new Course Kit is out, when the
**Course Kit version** printed by the computer check differs from the one on
the course website's Prepare page, or when the check says the course tools are
out of date. Do it **before class**, not in the middle of a lesson.

1. **Save your work first.** Your real work lives in `~/my-explore-world`,
   which the update never touches. Everything inside `~/explore-studio-course`
   is replaced, including lesson files you edited there during a session (for
   example under `lessons/sessions/`). Finish or note down any lesson edit you
   still need before you update.
2. **Close** VS Code and every Trail window. In the Ubuntu terminal, run
   `deactivate` if the prompt shows `(.venv)`.
3. **Copy the new ZIP** into your Ubuntu home, exactly as in step 4.
4. **Move the old Course Kit aside, then unzip the new one.** Never unzip on top
   of the old folder: that mixes old and new files and keeps the old `.venv`.

   ```console
   cd ~
   mv explore-studio-course explore-studio-course-old
   unzip -q explore-studio-course.zip
   ```

5. **Make a fresh `.venv`** and check:

   ```console
   cd ~/explore-studio-course
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-student.txt
   python3 check-my-computer.py
   ```

   You need `READY FOR EXPLORE STUDIO`, with `Course tools: ... (current)`.
6. **Only after READY**, remove the old copy and the ZIP:

   ```console
   rm -rf ~/explore-studio-course-old
   rm ~/explore-studio-course.zip
   ```

   Type these exactly. Never delete `~/my-explore-world`. If you are unsure,
   leave the old copy and ask your teacher.

On a Mac, use Terminal and get the ZIP with
`mv ~/Downloads/explore-studio-course.zip ~` in step 3. If Safari already
unzipped it, the new kit is the folder `~/Downloads/explore-studio-course`:
after step 4's `mv` line, run `mv ~/Downloads/explore-studio-course ~`
instead of `unzip`.

## Fix the course tools only

If the computer check says `COURSE TOOLS OUT OF DATE` but your Course Kit is
current, run this from the Course Kit with `.venv` active:

```console
python -m pip install --force-reinstall -r requirements-student.txt
python3 check-my-computer.py
```

Running the plain install again is not enough: it keeps the old version.

If the check says `VENV IN WRONG PLACE` because this `.venv` was moved or
copied, make a fresh one:

```console
cd ~/explore-studio-course
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-student.txt
python3 check-my-computer.py
```

(`deactivate` only matters if your prompt showed `(.venv)`. If it says
"command not found", that is fine.)

## Folders in the wrong place

If the computer check says `COURSE FOLDER IN WRONG PLACE`:

- **Under `/mnt/c`, in Downloads, or one course folder inside another:** follow
  steps 4 and 5 to unzip a fresh Course Kit into your home folder.
- **Somewhere else, such as the Desktop:** move the folder home, then make a
  fresh `.venv` as above (moving a folder breaks its `.venv`):

  ```console
  mv ~/Desktop/explore-studio-course ~
  ```

If you already have a `my-explore-world` folder somewhere else, first check
that `ls ~/my-explore-world` says "No such file or directory". Then move it
home too, for example `mv ~/Desktop/my-explore-world ~`. If both places
already have one, stop and ask your teacher. Never delete either copy.

## When the Trail looks wrong, check your setup first

An out-of-date or misplaced setup can look exactly like a bug in the lesson:
a Trail that looks different from the class slides or screenshots, an object
from the slides that is missing, or an error nobody else gets. Before
debugging your code, run the **Am I ready?** check above and fix each `[help]`
line, then try the lesson again.

| The check says | Do this |
|---|---|
| `WRONG FOLDER` | `cd ~/explore-studio-course`, then run the check again |
| `VENV NOT ACTIVE` | `source .venv/bin/activate` (or make the `.venv`: step 5) |
| `VENV IN WRONG PLACE` | `deactivate`, then use only `~/explore-studio-course/.venv` ([Fix the course tools only](#fix-the-course-tools-only)) |
| `COURSE TOOLS NOT INSTALLED` | `python -m pip install -r requirements-student.txt` |
| `COURSE TOOLS OUT OF DATE` | [Fix the course tools only](#fix-the-course-tools-only) |
| `COURSE FOLDER IN WRONG PLACE` | [Folders in the wrong place](#folders-in-the-wrong-place) |
| Your world folder is inside the Course Kit | [Folders in the wrong place](#folders-in-the-wrong-place) |
| Python is too old, or `unzip` is missing | Step 3 |
| WSL 1, or WSLg not found | Step 1 |
| Course Kit version differs from the course website's Prepare page | [Get a newer Course Kit](#get-a-newer-course-kit) |
