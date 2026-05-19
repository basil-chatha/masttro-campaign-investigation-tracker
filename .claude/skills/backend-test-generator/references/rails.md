# Rails + RSpec or minitest

## Stack signals

- `Gemfile` with `rails` and either `rspec-rails` or just stock `Rails` (minitest)
- `app/controllers`, `app/models`, `config/routes.rb`
- `spec/` directory → RSpec; `test/` directory → minitest

## Default toolkit

### RSpec
- **Test framework**: `rspec-rails`
- **HTTP**: request specs (preferred) — full middleware stack
- **Factories**: `factory_bot_rails`
- **Fixtures**: `faker` for realistic-but-deterministic data (seed it)
- **Mocks**: RSpec mocks (`allow(x).to receive(:y)`) or `webmock` for HTTP

### minitest
- **Test framework**: built-in
- **HTTP**: `ActionDispatch::IntegrationTest`
- **Fixtures**: YAML fixtures in `test/fixtures/`

## Where tests live

```text
spec/                       # RSpec
  models/
  requests/
  services/
  factories/
  rails_helper.rb
test/                       # minitest
  models/
  controllers/
  fixtures/
  test_helper.rb
```

Always prefer **request specs over controller specs** in modern Rails — request specs run through the actual middleware and routing, controller specs don't.

## Smallest useful request spec (RSpec)

```ruby
require "rails_helper"

RSpec.describe "Campaigns", type: :request do
  describe "GET /campaigns" do
    it "returns 200" do
      get "/campaigns"
      expect(response).to have_http_status(:ok)
    end
  end
end
```

## Factories

```ruby
# spec/factories/campaigns.rb
FactoryBot.define do
  factory :campaign do
    sequence(:name) { |n| "Campaign #{n}" }
    status { "active" }
  end
end

# usage
let(:campaign) { create(:campaign) }
```

## DB strategy

Rails wraps each test in a transaction by default — fast and isolated. If a test uses multiple processes / threads (Capybara), switch to `database_cleaner-active_record` with a truncation strategy for that test.

## Model specs — what's worth testing

- Validations: `expect(build(:campaign, name: nil)).not_to be_valid`
- Custom scopes: `Campaign.active` returns the right rows
- Domain methods: state transitions, calculations
- **Don't** test associations directly (`belongs_to :user`) — that's testing Rails

## Running

```bash
bundle exec rspec                         # full suite
bundle exec rspec spec/requests/campaigns_spec.rb
bundle exec rspec spec/requests/campaigns_spec.rb:42  # single test by line
bundle exec rspec --only-failures

# minitest
bin/rails test
bin/rails test test/controllers/campaigns_controller_test.rb
```
