import type { Metadata } from "next";
import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";

export const metadata: Metadata = {
  title: "Prepare for S01 | Course4Teen",
  description:
    "Everything a Course4Teen student needs before Session 1: computer requirements, the student download package, Python setup, and the readiness check.",
  alternates: { canonical: "/students/prepare/" },
};

const DOWNLOADS_DIR = path.join(process.cwd(), "public", "downloads");

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
  ["macOS", "Supported directly."],
  ["Windows", "Supported through WSL2 with Ubuntu and WSLg."],
  [
    "Phone, tablet, or Chromebook",
    "Not supported as a primary coding device. A supported computer with a physical keyboard is required.",
  ],
];

export default function PrepareForS01Page() {
  const zipSize = fileSizeLabel("explore-studio-course.zip");
  const checkerSize = fileSizeLabel("check-my-computer.py");

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <section className="section slides-hero">
          <p className="kicker">Before Session 1</p>
          <h1>Get your computer ready for S01.</h1>
          <p className="calendar-lede">
            No Git client and no GitHub account are needed to start. Unzip the
            student package, check the computer, install the course tools
            once, and you&apos;re ready for{" "}
            <Link className="text-link" href="/students/slides/s01/">
              Session 1
            </Link>
            .
          </p>
        </section>

        <section className="section slide-deck">
          <article className="slide-card" id="check-computer">
            <p className="kicker">Check your computer</p>
            <h2>Confirm the computer is ready</h2>
            <div className="slide-body">
              <p>Course4Teen needs a computer that meets these minimums:</p>
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
              <p>
                Download the check below and run it before installing
                anything &mdash; it reads only this computer&apos;s hardware
                and never asks for a password or an account.
              </p>
            </div>
          </article>

          <article className="slide-card" id="download">
            <p className="kicker">Download student package</p>
            <h2>Get the course files</h2>
            <div className="slide-body">
              <ul className="prep-downloads">
                <li>
                  <a className="button button-primary" href="/downloads/explore-studio-course.zip" download>
                    Download explore-studio-course.zip ({zipSize})
                  </a>
                  <p>
                    Sessions 1&ndash;30, the shared world packages, and the
                    computer check &mdash; everything needed to start, with no
                    teacher material inside.
                  </p>
                </li>
                <li>
                  <a className="button" href="/downloads/check-my-computer.py" download>
                    Download check-my-computer.py ({checkerSize})
                  </a>
                  <p>
                    The same computer check on its own, if you want to test
                    this machine before downloading the full package.
                  </p>
                </li>
              </ul>
              <p>
                Unzip the course file and move the{" "}
                <code>explore-studio-course</code> folder somewhere you can
                find it &mdash; your home folder or Desktop on macOS, or your
                Ubuntu home folder (not <code>/mnt/c</code>) on Windows WSL2.
              </p>
            </div>
          </article>

          <article className="slide-card" id="setup">
            <p className="kicker">Set up Python environment</p>
            <h2>Install the course tools once</h2>
            <div className="slide-body">
              <p>From inside the unzipped <code>explore-studio-course</code> folder:</p>
              <pre className="slide-code">
                <code>{`python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-student.txt
explore-package --help`}</code>
              </pre>
              <p>
                This is the only step that needs the internet. If{" "}
                <code>explore-package</code> is not found, confirm your prompt
                shows <code>(.venv)</code> and run the install command again.
              </p>
            </div>
          </article>

          <article className="slide-card" id="readiness-check">
            <p className="kicker">Run readiness check</p>
            <h2>Test a real Trail window</h2>
            <div className="slide-body">
              <p>Run the computer check once more, now that the course tools are installed:</p>
              <pre className="slide-code">
                <code>python3 check-my-computer.py</code>
              </pre>
              <p>Read the last line:</p>
              <ul className="prep-list">
                <li>
                  <strong>READY FOR EXPLORE STUDIO</strong> &mdash; move on to Session 1.
                </li>
                <li>
                  <strong>SETUP HELP NEEDED</strong> &mdash; show the lines marked{" "}
                  <code>[help]</code> to a teacher or an adult before continuing.
                </li>
              </ul>
            </div>
          </article>

          <article className="slide-card" id="start-s01">
            <p className="kicker">Start S01</p>
            <h2>Run your first script</h2>
            <div className="slide-body">
              <pre className="slide-code">
                <code>python lessons/sessions/s01/student/starter.py</code>
              </pre>
              <p>
                Then open{" "}
                <Link className="text-link" href="/students/slides/s01/">
                  the S01 slides
                </Link>{" "}
                and follow along, or check the{" "}
                <Link className="text-link" href="/calendar/">
                  class calendar
                </Link>{" "}
                for your session date.
              </p>
            </div>
          </article>

          <article className="slide-card" id="help">
            <p className="kicker">Need help?</p>
            <h2>Support before class</h2>
            <div className="slide-body">
              <ul className="prep-list">
                <li>Git and a GitHub account are not required for S01. Git is introduced later, when the class is ready for it.</li>
                <li>Your Zoom link and passcode are sent privately by your teacher &mdash; never posted on this website or any public page.</li>
                <li>
                  If <code>check-my-computer.py</code> ends with{" "}
                  <strong>SETUP HELP NEEDED</strong>, email{" "}
                  <a href="mailto:hello@course4teen.com">hello@course4teen.com</a>{" "}
                  before your first session rather than at the start of S01.
                </li>
              </ul>
            </div>
          </article>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
