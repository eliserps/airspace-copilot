import { describe, expect, it } from "vitest";
import { parseBlock, readSse } from "./sse";

function streamOf(...chunks: string[]) {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
}

async function collect(stream: ReadableStream<Uint8Array>) {
  const events = [];
  for await (const event of readSse(stream)) events.push(event);
  return events;
}

describe("parseBlock", () => {
  it("reads event name and joins multi-line data", () => {
    expect(parseBlock("event: delta\ndata: a\ndata: b")).toEqual({ event: "delta", data: "a\nb" });
  });

  it("ignores comments and blocks without data", () => {
    expect(parseBlock(": keep-alive")).toBeNull();
  });
});

describe("readSse", () => {
  it("handles events split across network chunks", async () => {
    const events = await collect(
      streamOf(
        "event: delta\nda",
        'ta: {"text":"Hel',
        'lo"}\n\nevent: done\r\n',
        "data: {}\r\n\r\n",
      ),
    );
    expect(events).toEqual([
      { event: "delta", data: '{"text":"Hello"}' },
      { event: "done", data: "{}" },
    ]);
  });

  it("flushes a final event without a trailing blank line", async () => {
    expect(await collect(streamOf("event: done\ndata: {}"))).toEqual([
      { event: "done", data: "{}" },
    ]);
  });
});
