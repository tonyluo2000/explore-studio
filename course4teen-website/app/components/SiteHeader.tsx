import Link from "next/link";

const contactHref =
  "mailto:hello@course4teen.com?subject=Course4Teen%20enrollment%20interest";

export default function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="Course4Teen home">
        <span className="brand-mark" aria-hidden="true"><span /></span>
        <span>course4teen</span>
      </Link>
      <nav aria-label="Main navigation">
        <Link href="/#program">Program</Link>
        <Link href="/calendar/">Calendar</Link>
        <Link href="/students/slides/">Student slides</Link>
        <Link href="/#parents">For parents</Link>
        <a className="nav-cta" href={contactHref}>Join the next cohort</a>
      </nav>
    </header>
  );
}
