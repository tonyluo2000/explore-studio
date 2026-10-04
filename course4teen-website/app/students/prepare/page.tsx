import type { Metadata } from "next";
import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";
import { courseKitVersion } from "../../../lib/courseKit";

export const metadata: Metadata = {
  title: "Prepare for class | Course4Teen",
  description:
    "Get ready for any Course4Teen session: the Windows/WSL setup guide, the Course Kit download and update, and the one-minute \"Am I ready?\" check.",
  alternates: { canonical: "/students/prepare/" },
};

const DOWNLOADS_DIR = path.join(process.cwd(), "public", "downloads");

/** The one canonical setup and update guide; it also ships inside the Course Kit. */
const WINDOWS_SETUP_GUIDE =
  "https://github.com/tonyluo2000/explore-studio/blob/main/docs/windows-wsl-setup.md";

/** The "Am I ready?" commands, identical to the guide's checklist. */
const READY_CHECK = `cd ~/explore-studio-course
source .venv/bin/activate
python3 check-my-computer.py`;

function fileSizeLabel(fileName: string): string {
  const bytes = fs.statSync(path.join(DOWNLOADS_DIR, fileName)).size;
  const kb = bytes / 1024;
  return kb >= 1000 ? `${(kb / 1024).toFixed(1)} MB` : `${Math.round(kb)} KB`;
}

const requirements: Array<[string, string]> = [
  ["Python", "3.11 or newer"],
  ["Memory (RAM)", "8 GB minimum"],
  ["Free storage", "5 GB minimum"],
  ["Internet", "Stable connection"],
  ["Microphone", "Required"],
  ["Webcam", "Recommended"],
  ["Headphones", "Recommended"],
];

const supportedDevices: Array<[string, string]> = [
  ["Windows", "Windows 11 with WSL 2 and Ubuntu. Run every course command in the Ubuntu terminal, not PowerShell."],
  ["macOS", "Supported directly, in the Terminal app."],
  [
    "Phone, tablet, or Chromebook",
    "Not supported as a primary coding device. A supported computer with a physical keyboard is required.",
  ],
];

export default function PrepareForClassPage() {
  const zipSize = fileSizeLabel("explore-studio-course.zip");
  const checkerSize = fileSizeLabel("check-my-computer.py");
  const kitVersion = courseKitVersion();

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <section className="section slides-hero">
          <p className="kicker">Before every class</p>
          <h1>Prepare for class.</h1>
          <p className="calendar-lede">
            Set up once, check you are ready in under a minute before each
            session, and update the Course Kit when a new one is out. No Git
            client and no GitHub account are needed.
          </p>
          <p className="calendar-lede">
            <strong>On Windows?</strong> Follow the one step-by-step{" "}
            <a className="text-link" href={WINDOWS_SETUP_GUIDE}>
              Windows setup guide
            </a>{" "}
            for WSL, Ubuntu, VS Code, the Course Kit, and updates.
          </p>
        </section>

        <section className="section slide-deck">
          <article className="slide-card" id="ready">
            <p className="kicker">Am I ready?</p>
            <h2>The one-minute check before every class</h2>
            <div className="slide-body">
              <p>Open Ubuntu (Terminal on a Mac) and run:</p>
              <pre className="slide-code">
                <code>{READY_CHECK}</code>
              </pre>
              <ul className="prep-list">
                <li>
                  The summary says <code>Course tools: &hellip; (current)</code>{" "}
                  and the last line says <strong>READY FOR EXPLORE STUDIO</strong>.
                </li>
                <li>
                  <code>pwd</code> ends with <code>explore-studio-course</code>.
                </li>
                <li>Your session&apos;s Trail command opens and closes.</li>
              </ul>
              <p>
                <strong>SETUP HELP NEEDED</strong>? Follow the arrow under each{" "}
                <code>[help]</code> line, or send the summary lines to your
                teacher before class.
              </p>
            </div>
          </article>

          <article className="slide-card" id="folders">
            <p className="kicker">Two folders</p>
            <h2>Course Kit and your world</h2>
            <div className="slide-body">
              <ul className="prep-list">
                <li>
                  <code>~/explore-studio-course</code>: the{" "}
                  <strong>Course Kit</strong> and its <code>.venv</code>.
                  Replaceable.
                </li>
                <li>
                  <code>~/my-explore-world</code>: <strong>your own work</strong>.
                  Never delete it.
                </li>
              </ul>
              <p>
                Run lesson commands from <code>~/explore-studio-course</code>{" "}
                with its <code>.venv</code> active. Save your own work in{" "}
                <code>~/my-explore-world</code>. On Windows both live in the
                Ubuntu home folder, never under <code>/mnt/c</code>.
              </p>
            </div>
          </article>

          <article className="slide-card" id="download">
            <p className="kicker">Course Kit</p>
            <h2>Download and install</h2>
            <div className="slide-body">
              <ul className="prep-downloads">
                <li>
                  <a className="button button-primary" href="/downloads/explore-studio-course.zip" download>
                    Download explore-studio-course.zip ({zipSize})
                  </a>
                  <p>
                    Current Course Kit version:{" "}
                    <strong>
                      <code>{kitVersion}</code>
                    </strong>
                    . The check prints yours on its <em>Course Kit version</em>{" "}
                    line.
                  </p>
                </li>
              </ul>
              <p>
                Unzip it so the folder is exactly{" "}
                <code>~/explore-studio-course</code>, then install the course
                tools once:
              </p>
              <pre className="slide-code">
                <code>{`cd ~/explore-studio-course
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-student.txt
python3 check-my-computer.py`}</code>
              </pre>
              <p>
                Open the course in VS Code with <code>code .</code> from{" "}
                <code>~/explore-studio-course</code>. On Windows, the
                bottom-left corner must say <strong>WSL</strong>. The{" "}
                <a className="text-link" href={WINDOWS_SETUP_GUIDE}>
                  Windows setup guide
                </a>{" "}
                shows how to move the ZIP from Windows Downloads into Ubuntu.
              </p>
            </div>
          </article>

          <article className="slide-card" id="update">
            <p className="kicker">Get a newer Course Kit</p>
            <h2>Replace the Course Kit, keep your world</h2>
            <div className="slide-body">
              <p>
                When your teacher hands out a newer Course Kit, or your Course
                Kit version differs from the one above, follow{" "}
                <a className="text-link" href={`${WINDOWS_SETUP_GUIDE}#get-a-newer-course-kit`}>
                  Get a newer Course Kit
                </a>{" "}
                before class. In short:
              </p>
              <ul className="prep-list">
                <li>
                  Move the old folder aside (
                  <code>mv explore-studio-course explore-studio-course-old</code>
                  ), unzip the new one, make a fresh <code>.venv</code>, install,
                  and check.
                </li>
                <li>Never unzip on top of the old Course Kit.</li>
                <li>
                  Lesson files you edited inside the Course Kit are replaced.{" "}
                  <code>~/my-explore-world</code> is never touched.
                </li>
                <li>Delete the old copy only after the check says READY.</li>
              </ul>
            </div>
          </article>

          <article className="slide-card" id="help">
            <p className="kicker">Something looks wrong?</p>
            <h2>Check your setup before your code</h2>
            <div className="slide-body">
              <ul className="prep-list">
                <li>
                  If the Trail looks different from the class slides, run the
                  Am I ready? check first. An out-of-date Course Kit or course
                  tools can look exactly like a bug.
                </li>
                <li>
                  <code>COURSE TOOLS OUT OF DATE</code>? From the Course Kit
                  with <code>.venv</code> active, run the command below. A
                  plain rerun of the install keeps the old version.
                </li>
              </ul>
              <pre className="slide-code">
                <code>python -m pip install --force-reinstall -r requirements-student.txt</code>
              </pre>
              <p>
                Still stuck? Email{" "}
                <a href="mailto:hello@course4teen.com">hello@course4teen.com</a>{" "}
                with the check&apos;s summary lines before your session.
              </p>
            </div>
          </article>

          <article className="slide-card" id="computer">
            <p className="kicker">Computer requirements</p>
            <h2>What the computer needs</h2>
            <div className="slide-body">
              <dl className="prep-table">
                {requirements.map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
              <ul className="prep-list">
                {supportedDevices.map(([label, value]) => (
                  <li key={label}>
                    <strong>{label}:</strong> {value}
                  </li>
                ))}
              </ul>
              <ul className="prep-downloads">
                <li>
                  <a className="button" href="/downloads/check-my-computer.py" download>
                    Download check-my-computer.py ({checkerSize})
                  </a>
                  <p>
                    Test a computer before installing the course with{" "}
                    <code>python3 check-my-computer.py --computer-only</code>.
                    It never asks for a password or an account.
                  </p>
                </li>
              </ul>
            </div>
          </article>

          <article className="slide-card" id="first-class">
            <p className="kicker">New to the course?</p>
            <h2>Your first session</h2>
            <div className="slide-body">
              <p>
                Start with{" "}
                <Link className="text-link" href="/students/slides/s01/">
                  the S01 slides
                </Link>{" "}
                and check the{" "}
                <Link className="text-link" href="/calendar/">
                  class calendar
                </Link>{" "}
                for your session date. Your Zoom link and passcode are sent
                privately by your teacher, never posted on this website.
              </p>
            </div>
          </article>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
