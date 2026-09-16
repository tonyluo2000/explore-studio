import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer>
      <Link className="brand footer-brand" href="/">
        <span className="brand-mark" aria-hidden="true"><span /></span>
        <span>course4teen</span>
      </Link>
      <p>Real Python. Real projects. Built for teens.</p>
      <div>
        <a href="mailto:hello@course4teen.com">hello@course4teen.com</a>
        <span>© {new Date().getFullYear()} Course4Teen</span>
      </div>
    </footer>
  );
}
