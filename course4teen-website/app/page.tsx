const contactHref =
  "mailto:hello@course4teen.com?subject=Course4Teen%20enrollment%20interest";

const outcomes = [
  {
    number: "01",
    title: "Code with purpose",
    text: "Use variables, functions, conditions, loops, lists, and dictionaries to solve visible problems.",
  },
  {
    number: "02",
    title: "Build an explorable world",
    text: "Shape terrain, place objects, create characters, and script interactions using real Python.",
  },
  {
    number: "03",
    title: "Think like a creator",
    text: "Break down ideas, debug thoughtfully, test changes, and explain the choices behind a project.",
  },
];

const sessionArc = [
  ["01–05", "Find your bearings", "Python foundations + first world edits"],
  ["06–15", "Make it respond", "Logic, loops, data + interactions"],
  ["16–25", "Make it yours", "Systems, characters + creative builds"],
  ["26–30", "Ship the story", "Polish, testing + final showcase"],
];

function ArrowIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
      <path d="M4 10h12m-5-5 5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SparkIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 28 28" fill="none">
      <path d="M14 2c.8 7.4 4.6 11.2 12 12-7.4.8-11.2 4.6-12 12-.8-7.4-4.6-11.2-12-12 7.4-.8 11.2-4.6 12-12Z" fill="currentColor" />
    </svg>
  );
}

export default function Home() {
  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>

      <header className="site-header">
        <a className="brand" href="#top" aria-label="Course4Teen home">
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <span>course4teen</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#program">Program</a>
          <a href="#parents">For parents</a>
          <a className="nav-cta" href={contactHref}>Join the next cohort</a>
        </nav>
      </header>

      <main id="main">
        <section className="hero" id="top">
          <div className="hero-copy">
            <p className="eyebrow"><span /> Live online coding for teens</p>
            <h1>Don&apos;t just play the world. <em>Build it.</em></h1>
            <p className="hero-lede">
              Learn real Python by creating characters, challenges, and an interactive world—one focused mission at a time.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href={contactHref}>Ask about enrollment <ArrowIcon /></a>
              <a className="text-link" href="#program">See how the course works <span aria-hidden="true">↓</span></a>
            </div>
            <dl className="hero-stats" aria-label="Course at a glance">
              <div><dt>30</dt><dd>live sessions</dd></div>
              <div><dt>45</dt><dd>minutes each</dd></div>
              <div><dt>1</dt><dd>world of your own</dd></div>
            </dl>
          </div>

          <div className="world-card" aria-label="Illustration of a student-built coding world">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="code-window">
              <div className="window-bar"><i /><i /><i /><span>my_world.py</span></div>
              <pre><code><b>def</b> open_secret_path():{"\n"}  bridge.<span>glow</span>(){"\n"}  explorer.move(<strong>forward</strong>)</code></pre>
            </div>
            <div className="terrain">
              <div className="mountain mountain-left" />
              <div className="mountain mountain-right" />
              <div className="path" />
              <div className="explorer"><span /></div>
              <div className="beacon"><SparkIcon /></div>
            </div>
            <p className="world-label"><span>Mission 12</span> The hidden signal</p>
          </div>
        </section>

        <section className="signal-strip" aria-label="Course approach">
          <p>Real code</p><i /><p>Small-group guidance</p><i /><p>A project worth sharing</p><i /><p>Built for curious minds</p>
        </section>

        <section className="section outcomes" id="program">
          <div className="section-intro">
            <p className="kicker">What students learn</p>
            <h2>From first command to a world that feels alive.</h2>
            <p>No disconnected drills. Every new idea gives students another way to shape what they see and experience.</p>
          </div>
          <div className="outcome-grid">
            {outcomes.map((outcome) => (
              <article className="outcome-card" key={outcome.number}>
                <span>{outcome.number}</span>
                <h3>{outcome.title}</h3>
                <p>{outcome.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section course-map">
          <div className="map-heading">
            <div><p className="kicker">The course journey</p><h2>Thirty missions.<br />A steady creative arc.</h2></div>
            <p>Each 45-minute live session introduces one clear concept, demonstrates it, then gives students room to apply it with support nearby.</p>
          </div>
          <ol className="session-list">
            {sessionArc.map(([range, title, text], index) => (
              <li key={range}>
                <span className="session-range">{range}</span>
                <span className="session-dot" aria-hidden="true"><i>{index + 1}</i></span>
                <div><h3>{title}</h3><p>{text}</p></div>
              </li>
            ))}
          </ol>
        </section>

        <section className="studio-section">
          <div className="studio-visual" aria-hidden="true">
            <div className="studio-grid" />
            <div className="studio-compass"><span>N</span><i /><b /></div>
            <p>EXPLORE<br />STUDIO</p>
          </div>
          <div className="studio-copy">
            <p className="kicker">Powered by Explore Studio</p>
            <h2>A creative playground with real code underneath.</h2>
            <p>Course4Teen is the guided learning experience. Explore Studio is the open-source environment students use to build and explore.</p>
            <p>It bridges the instant feedback of a game with the depth of Python—so the work feels playful without being pretend.</p>
            <a className="text-link light" href="https://github.com/tonyluo2000/explore-studio">Explore the open-source project <ArrowIcon /></a>
            <aside className="school-note" aria-label="School relationship">
              <span>Course offering</span>
              <p>
                Course4Teen is being developed for students and families at{" "}
                <a href="https://www.hxgny.org/">Huaxia Chinese Academy Greater New York</a>.
              </p>
            </aside>
          </div>
        </section>

        <section className="section parent-section" id="parents">
          <div className="parent-heading">
            <p className="kicker">Designed with families in mind</p>
            <h2>Supportive by design. Safe by default.</h2>
          </div>
          <div className="parent-content">
            <div className="parent-points">
              <article><span aria-hidden="true">01</span><div><h3>Live human guidance</h3><p>Students learn with an instructor who can answer questions, notice when they&apos;re stuck, and celebrate breakthroughs.</p></div></article>
              <article><span aria-hidden="true">02</span><div><h3>Purposeful screen time</h3><p>Sessions are focused and active: write, run, reflect, improve. Students leave with something they made.</p></div></article>
              <article><span aria-hidden="true">03</span><div><h3>Controlled sharing</h3><p>No unrestricted public chat. Student work is private by default, and shared-world publishing is reviewed and instructor controlled.</p></div></article>
            </div>
            <aside className="parent-note">
              <SparkIcon />
              <p>Questions before you commit?</p>
              <h3>Let&apos;s make sure the course is a good fit.</h3>
              <a href={contactHref}>Talk with us <ArrowIcon /></a>
            </aside>
          </div>
        </section>

        <section className="final-cta">
          <div className="cta-star" aria-hidden="true"><SparkIcon /></div>
          <p className="kicker">Ready for the next mission?</p>
          <h2>Give their curiosity<br />somewhere to go.</h2>
          <p>Tell us a little about your student and we&apos;ll share upcoming cohort details, timing, and next steps.</p>
          <a className="button button-light" href={contactHref}>Ask about enrollment <ArrowIcon /></a>
        </section>
      </main>

      <footer>
        <a className="brand footer-brand" href="#top"><span className="brand-mark" aria-hidden="true"><span /></span><span>course4teen</span></a>
        <p>Real Python. Real projects. Built for teens.</p>
        <div><a href="mailto:hello@course4teen.com">hello@course4teen.com</a><span>© {new Date().getFullYear()} Course4Teen</span></div>
      </footer>
    </>
  );
}
