import Link from "next/link";
import { footerNote, site } from "@/lib/content/site";
import { Wordmark } from "./Wordmark";

export function SiteFooter() {
  return (
    <footer className="border-t border-ink/12 bg-ground">
      <div className="mx-auto w-full max-w-shell px-4 py-10 md:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
          <div className="md:col-span-5">
            <Wordmark className="text-ink" />
            <p className="mt-3 max-w-prose text-meta text-muted">
              {site.description}
            </p>
          </div>

          <nav aria-label="Product" className="md:col-span-3 md:col-start-7">
            <p className="label-wire mb-3">Product</p>
            <ul className="flex flex-col gap-2 text-ui">
              <li>
                <Link href="/dashboard" className="text-muted transition-colors hover:text-ink">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link href="/api-keys" className="text-muted transition-colors hover:text-ink">
                  API keys
                </Link>
              </li>
              <li>
                <Link href="/external-services" className="text-muted transition-colors hover:text-ink">
                  External services
                </Link>
              </li>
              <li>
                <Link href="/webhooks" className="text-muted transition-colors hover:text-ink">
                  Webhooks
                </Link>
              </li>
            </ul>
          </nav>

          <nav aria-label="Reference" className="md:col-span-3">
            <p className="label-wire mb-3">Reference</p>
            <ul className="flex flex-col gap-2 text-ui">
              <li>
                <Link href="/docs" className="text-muted transition-colors hover:text-ink">
                  Documentation
                </Link>
              </li>
              <li>
                <Link href="/orchestrate" className="text-muted transition-colors hover:text-ink">
                  Playground
                </Link>
              </li>
              <li>
                <a
                  href={footerNote.apiDocs}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted transition-colors hover:text-ink"
                >
                  Swagger UI
                </a>
              </li>
              <li>
                <a
                  href={footerNote.liveApi}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted transition-colors hover:text-ink"
                >
                  Live API
                </a>
              </li>
            </ul>
          </nav>
        </div>

        <div className="mt-10 flex flex-col gap-2 border-t border-ink/12 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-mono text-micro text-muted">
            © {new Date().getFullYear()} OmniAPI
          </p>
          <p className="font-mono text-micro text-muted">
            Built with {footerNote.builtWith}
          </p>
        </div>
      </div>
    </footer>
  );
}
