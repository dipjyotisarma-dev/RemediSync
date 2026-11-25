import Link from "next/link";

export default function NotFound(): React.ReactElement {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 text-center">
      <p className="font-mono-tabular text-[13px] text-ink-muted">404</p>
      <h2 className="mt-2 text-[20px] font-medium text-ink-primary">
        Page not found
      </h2>
      <p className="mt-1.5 max-w-md text-[13.5px] text-ink-secondary">
        The requested dispensary view does not exist. Return to the network
        overview to continue managing branch inventory.
      </p>
      <Link
        href="/overview"
        className="mt-5 inline-flex h-9 items-center justify-center rounded-control bg-accent px-4 text-[13.5px] font-medium text-ink-inverse transition-colors duration-150 hover:bg-accent-hover"
      >
        Open network overview
      </Link>
    </div>
  );
}
