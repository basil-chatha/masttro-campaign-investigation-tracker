# Node / Express + Jest or Vitest

## Stack signals

- `express` in `package.json` dependencies
- `app.get/post/put/delete(...)` route handlers
- `package.json` `scripts.test` already defined? That tells you the runner.

## Default toolkit

- **Test framework**: `jest` (most common) or `vitest` (faster, more modern). Use whichever the project already uses.
- **HTTP client**: `supertest`
- **DB**: depends — Prisma + test database, raw `pg` + transaction rollback, or an in-memory store for unit tests.
- **Mocks**: `jest.mock` / `vi.mock`, or `nock` for outbound HTTP

## Where tests live

```text
src/
  routes/
    campaigns.ts
__tests__/             # or tests/ or spec/, follow the project
  routes/
    campaigns.test.ts
```

Jest picks up `*.test.ts`, `*.spec.ts`, and files in `__tests__/` by default. Vitest is similar.

## Export the app, not just the listening server

To make routes testable, the project should export the Express `app` (without `app.listen(...)`) so tests can pass it to supertest. If the project only exports a started server, refactor minimally to separate "create app" from "start server", or note this limitation in the summary.

```typescript
// src/app.ts
export const app = express();
app.use("/campaigns", campaignsRouter);

// src/server.ts
import { app } from "./app";
app.listen(3000);
```

## Smallest useful test

```typescript
import request from "supertest";
import { app } from "../src/app";

describe("GET /health", () => {
  it("returns 200 with status ok", async () => {
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });
});
```

## Mocking modules

```typescript
import { jest } from "@jest/globals";
import * as paymentClient from "../src/clients/payment";

jest.spyOn(paymentClient, "charge").mockResolvedValue({ id: "ch_test" });
```

For Vitest: `vi.spyOn`, `vi.mock`. For ESM-only projects, prefer `vi.mock` — Jest's ESM support is rougher.

## Async / promises

`supertest` returns a thenable; always `await` it. Don't forget to return promises from `it(...)` or your test will report success while the async work was still running:

```typescript
// good
it("...", async () => {
  await request(app).get("/x").expect(200);
});

// bad — test passes regardless
it("...", () => {
  request(app).get("/x").expect(200);
});
```

## Running

```bash
npm test                          # whatever package.json says
npx jest path/to/file.test.ts     # single file
npx jest -t "campaign creation"   # name filter
npx vitest run                    # vitest, single pass
npx vitest                        # vitest, watch
```
