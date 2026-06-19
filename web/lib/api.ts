import type { LaSoFullRequest, LaSoFullResponse } from "./types";

export async function fetchLaSoFull(
  body: LaSoFullRequest,
): Promise<LaSoFullResponse> {
  const res = await fetch("/api/v1/la-so-full", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((d: { msg?: string }) => d?.msg).filter(Boolean).join("; ")
          : undefined;
    throw new Error(data?.message || data?.message_vi || detail || "API error");
  }
  return data as LaSoFullResponse;
}
