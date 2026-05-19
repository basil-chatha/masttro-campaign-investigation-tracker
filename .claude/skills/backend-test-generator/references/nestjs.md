# NestJS + Jest

## Stack signals

- `@nestjs/core` in `package.json`
- Modules: `*.module.ts`, controllers: `*.controller.ts`, services: `*.service.ts`
- Existing `*.spec.ts` files use `Test.createTestingModule(...)`

## Default toolkit

- **Test framework**: `jest` (Nest scaffolds with this out of the box)
- **HTTP**: `supertest` for E2E, `Test.createTestingModule` for unit
- **DI**: Nest's `Test` builder lets you swap providers — use this instead of `jest.mock`

## Two test layers Nest projects usually have

1. **Unit / module tests** (`*.spec.ts` next to the file under test). Build a `TestingModule`, get the provider, exercise its methods.
2. **E2E tests** (`test/*.e2e-spec.ts`). Bootstrap the full app, hit it with supertest.

Keep them separated; the project usually has two Jest configs (`jest.config` and `test/jest-e2e.json`).

## Unit test of a service

```typescript
import { Test } from "@nestjs/testing";
import { CampaignsService } from "./campaigns.service";
import { CampaignsRepository } from "./campaigns.repository";

describe("CampaignsService", () => {
  let service: CampaignsService;
  let repo: jest.Mocked<CampaignsRepository>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        CampaignsService,
        {
          provide: CampaignsRepository,
          useValue: { findById: jest.fn() },
        },
      ],
    }).compile();

    service = module.get(CampaignsService);
    repo = module.get(CampaignsRepository);
  });

  it("returns the campaign when found", async () => {
    repo.findById.mockResolvedValue({ id: "1", name: "x" });
    expect(await service.get("1")).toEqual({ id: "1", name: "x" });
  });

  it("throws NotFound when missing", async () => {
    repo.findById.mockResolvedValue(null);
    await expect(service.get("1")).rejects.toThrow(/not found/i);
  });
});
```

## E2E test of a controller

```typescript
import { Test } from "@nestjs/testing";
import { INestApplication } from "@nestjs/common";
import * as request from "supertest";
import { AppModule } from "../src/app.module";

describe("Campaigns (e2e)", () => {
  let app: INestApplication;

  beforeAll(async () => {
    const module = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = module.createNestApplication();
    await app.init();
  });

  afterAll(() => app.close());

  it("GET /campaigns returns 200", () => {
    return request(app.getHttpServer()).get("/campaigns").expect(200);
  });
});
```

## Running

```bash
npm run test          # unit (fast)
npm run test:e2e      # E2E
npm run test:watch    # watch unit
npm run test:cov      # coverage
```
