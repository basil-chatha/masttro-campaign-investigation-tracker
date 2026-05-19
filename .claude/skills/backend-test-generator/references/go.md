# Go (`net/http`, chi, gin, fiber, gRPC)

## Stack signals

- `go.mod` defines the module
- HTTP handlers: `func(w http.ResponseWriter, r *http.Request)`, or framework router decorators
- Tests live in `*_test.go` next to the code they test

## Default toolkit

- **Test framework**: built-in `testing` package
- **HTTP**: `net/http/httptest` for handler tests
- **Assertions**: stdlib `t.Fatal`/`t.Error` is fine; `testify/require` is widely used too
- **Mocks**: hand-rolled fakes against interfaces (Go's preference); `gomock` if the project already uses it
- **Table-driven tests**: idiomatic in Go for any function with branching

## Where tests live

Right next to the code:

```text
internal/
  campaigns/
    service.go
    service_test.go
    handler.go
    handler_test.go
```

Package matches the file under test (`package campaigns`), or `package campaigns_test` for black-box testing.

## Smallest useful handler test

```go
package campaigns_test

import (
    "net/http"
    "net/http/httptest"
    "testing"

    "example.com/internal/campaigns"
)

func TestHealthReturns200(t *testing.T) {
    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    rr := httptest.NewRecorder()

    campaigns.HealthHandler(rr, req)

    if rr.Code != http.StatusOK {
        t.Fatalf("expected 200, got %d", rr.Code)
    }
}
```

For full router tests (chi, gin, etc.), build the router exactly as `main` does and call `router.ServeHTTP(rr, req)`.

## Table-driven test

```go
func TestValidateName(t *testing.T) {
    cases := []struct {
        name    string
        input   string
        wantErr bool
    }{
        {"valid", "Campaign A", false},
        {"empty rejected", "", true},
        {"too long rejected", strings.Repeat("x", 256), true},
    }
    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            err := campaigns.ValidateName(tc.input)
            if (err != nil) != tc.wantErr {
                t.Fatalf("ValidateName(%q) error = %v, wantErr %v", tc.input, err, tc.wantErr)
            }
        })
    }
}
```

## Fakes via interfaces

Define a small interface where you would otherwise inject a concrete type, then provide a fake in tests:

```go
type CampaignRepo interface {
    FindByID(ctx context.Context, id string) (*Campaign, error)
}

type fakeRepo struct{ campaign *Campaign }
func (f *fakeRepo) FindByID(ctx context.Context, id string) (*Campaign, error) {
    return f.campaign, nil
}
```

This is much simpler than `gomock` for most cases.

## Running

```bash
go test ./...                                  # full suite
go test ./internal/campaigns                   # one package
go test -run TestHealthReturns200 ./internal/campaigns
go test -race ./...                            # with race detector
go test -count=1 ./...                         # bypass cache
go test -v ./...                               # verbose
go test -cover ./...                           # coverage
```
