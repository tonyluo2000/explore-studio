import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import { classSessions, sessionsWithSlides } from "../../../../lib/calendar";
import { learnSessions, type TermMeaning } from "../../../../lib/learn";

type Params = { session: string };

export const dynamicParams = false;

export function generateStaticParams(): Params[] {
  return learnSessions.map((entry) => ({ session: entry.id.toLowerCase() }));
}

function findSession(slug: string) {
  const learning = learnSessions.find((entry) => entry.id.toLowerCase() === slug);
  const session = classSessions.find((entry) => entry.id.toLowerCase() === slug);
  return learning && session ? { learning, session } : null;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { session: slug } = await params;
  const found = findSession(slug);
  if (!found) return {};
  const { session } = found;
  return {
    title: `${session.id} Python Notes · ${session.title} | Course4Teen`,
    description: `What we learned in Python in Course4Teen session ${session.id}, ${session.title}: the concept, the code, what it means, and what we debugged.`,
    alternates: { canonical: `/students/learn/${slug}/` },
  };
}

function MeaningTable({ caption, rows, codeTerms }: { caption: string; rows: TermMeaning[]; codeTerms: boolean }) {
  return (
    <div className="slide-map-wrap">
      <table className="slide-map">
        <caption className="slide-map-caption">{caption}</caption>
        <tbody>
          {rows.map((row) => (
            <tr key={row.term}>
              <th scope="row">{codeTerms ? <code>{row.term}</code> : <strong>{row.term}</strong>}</th>
              <td>{row.meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function LearnPage({ params }: { params: Promise<Params> }) {
  const { session: slug } = await params;
  const found = findSession(slug);
  if (!found) notFound();
  const { learning, session } = found;
  const hasSlides = sessionsWithSlides.includes(session.id);

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        <section className="section slides-hero">
          <p className="kicker">
            {session.id} &middot; {session.title}
          </p>
          <h1>What we learned in Python</h1>
          <p className="calendar-lede">
            The Python from session {session.id}, one idea at a time.{" "}
            {learning.sourceFile ? (
              <>
                These notes follow{" "}
                <code>lessons/sessions/{slug}/student/{learning.sourceFile}</code>{" "}
                in your course folder.
              </>
            ) : (
              <>
                The same notes are in your course folder as{" "}
                <code>lessons/sessions/{slug}/student/python-notes.md</code>.
              </>
            )}
          </p>
          {hasSlides ? (
            <p className="calendar-lede">
              <Link className="text-link" href={`/students/slides/${slug}/`}>
                Back to the {session.id} slides
              </Link>
            </p>
          ) : null}
        </section>

        <section className="section slide-deck">
          <article className="slide-card">
            <p className="kicker">1 &middot; Python concept</p>
            <h2>The idea</h2>
            <div className="slide-body">
              <MeaningTable caption="Today's Python" rows={learning.concepts} codeTerms={false} />
            </div>
          </article>

          <article className="slide-card">
            <p className="kicker">2 &middot; Code we wrote</p>
            <h2>The code</h2>
            <div className="slide-body">
              <pre className="slide-code"><code>{learning.code}</code></pre>
              {learning.runCommand ? (
                <>
                  <p>Run it from the course folder:</p>
                  <pre className="slide-code"><code>{learning.runCommand}</code></pre>
                </>
              ) : null}
              <p>Output:</p>
              <pre className="slide-code slide-output"><code>{learning.output}</code></pre>
            </div>
          </article>

          <article className="slide-card">
            <p className="kicker">3 &middot; What the code means</p>
            <h2>Line by line</h2>
            <div className="slide-body">
              <MeaningTable caption="Each important line" rows={learning.meanings} codeTerms />
            </div>
          </article>

          <article className="slide-card">
            <p className="kicker">4 &middot; Why programmers use this</p>
            <h2>Beyond this lesson</h2>
            <div className="slide-body">
              {learning.why.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          </article>

          <article className="slide-card">
            <p className="kicker">5 &middot; What we debugged</p>
            <h2>A bug worth understanding</h2>
            <div className="slide-body">
              <pre className="slide-code"><code>{learning.debugged.broken}</code></pre>
              <pre className="slide-code slide-output"><code>{learning.debugged.error}</code></pre>
              <p>{learning.debugged.explanation}</p>
              <p>Fixed:</p>
              <pre className="slide-code"><code>{learning.debugged.fixed}</code></pre>
            </div>
          </article>

          <article className="slide-card">
            <p className="kicker">6 &middot; Key Python words</p>
            <h2>Words to know</h2>
            <div className="slide-body">
              <MeaningTable caption="Vocabulary" rows={learning.keyWords} codeTerms={false} />
            </div>
          </article>

          <article className="slide-card">
            <p className="kicker">7 &middot; Try it yourself</p>
            <h2>Your turn</h2>
            <div className="slide-body">
              <ol className="slide-steps">
                {learning.tryIt.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
            </div>
          </article>
        </section>

        {learning.discovery ? (
          <section className="section discovery-section" aria-labelledby="discovery-heading">
            <p className="kicker">What we discovered</p>
            <h2 id="discovery-heading">{learning.discovery.topic}</h2>
            <div className="discovery-grid">
              <article className="discovery-card discovery-fiction">
                <p className="discovery-tag">In Nova&rsquo;s world &middot; fiction</p>
                {learning.discovery.inNovasWorld.map((line) => (
                  <p key={line}>{line}</p>
                ))}
              </article>
              <article className="discovery-card discovery-fact">
                <p className="discovery-tag">In our world &middot; fact</p>
                <ul>
                  {learning.discovery.inOurWorld.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </article>
            </div>
            <p className="discovery-question">
              <strong>Think about it:</strong> {learning.discovery.question}
            </p>
          </section>
        ) : null}
      </main>
      <SiteFooter />
    </>
  );
}
