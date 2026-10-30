import { describe, expect, it } from "vitest";
import { formatDuration, formatMs, formatPct, timeAgo } from "../utils/format";

describe("format helpers", () => {
  it("formats milliseconds", () => {
    expect(formatMs(182)).toBe("182 ms");
    expect(formatMs(1500)).toBe("1.50 s");
    expect(formatMs(null)).toBe("–");
  });
  it("formats percentages", () => {
    expect(formatPct(100)).toBe("100%");
    expect(formatPct(99.123)).toBe("99.12%");
    expect(formatPct(undefined)).toBe("–");
  });
  it("formats durations", () => {
    expect(formatDuration(45)).toBe("45s");
    expect(formatDuration(300)).toBe("5m 0s");
    expect(formatDuration(3720)).toBe("1h 2m");
    expect(formatDuration(null)).toBe("–");
  });
  it("formats relative time", () => {
    const now = Date.parse("2026-10-29T10:00:00Z");
    expect(timeAgo("2026-10-29T09:59:00Z", now)).toBe("1m ago");
    expect(timeAgo(null, now)).toBe("never");
  });
});
