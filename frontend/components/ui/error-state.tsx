export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-signal/30 bg-signal/10 p-5 text-sm text-signal">
      <p className="font-semibold">Unable to load data</p>
      <p className="mt-2">{message}</p>
      <p className="mt-3 text-xs">
        Make sure the FastAPI backend is running on the configured API URL.
      </p>
    </div>
  );
}
