# Course4Teen website

The static marketing site for [course4teen.com](https://course4teen.com). It is a small Next.js App Router project using TypeScript and Tailwind CSS, with no backend or runtime server requirement.

## Local development

Requires Node.js 20.9 or newer.

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Quality checks

```bash
npm run lint
npm run build
```

`next build` writes the fully static site to `out/` because `output: "export"` is enabled in `next.config.ts`.

## Deploy to Cloudflare Pages

Connect the repository to Cloudflare Pages with:

- Root directory: `course4teen-website`
- Build command: `npm run build`
- Build output directory: `out`
- Node.js version: 20.9 or newer

Alternatively, after building locally and authenticating Wrangler:

```bash
npx wrangler pages deploy out --project-name course4teen-website
```

Point the `course4teen.com` custom domain at the Pages project after the first deployment. Security headers in `public/_headers` are included in the static output.
