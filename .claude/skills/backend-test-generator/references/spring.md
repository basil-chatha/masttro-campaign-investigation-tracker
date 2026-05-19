# Spring Boot + JUnit 5

## Stack signals

- `pom.xml` or `build.gradle` referencing `spring-boot-starter-*`
- `@SpringBootApplication`, `@RestController`, `@Service`, `@Repository`
- Tests in `src/test/java/...`

## Default toolkit

- **Test framework**: JUnit 5 (`junit-jupiter`)
- **Assertions**: AssertJ (`assertThat(...).isEqualTo(...)`) — much more readable than JUnit's stock asserts
- **HTTP**: `MockMvc` for sync, `WebTestClient` for reactive WebFlux
- **Mocks**: Mockito (`@MockBean` to swap a Spring bean for a mock)
- **Slice annotations**: `@WebMvcTest(Controller.class)` boots only the web layer; `@DataJpaTest` boots only JPA. Faster than `@SpringBootTest`.

## Where tests live

```text
src/main/java/com/example/campaigns/CampaignsController.java
src/test/java/com/example/campaigns/CampaignsControllerTest.java
src/test/java/com/example/campaigns/CampaignsControllerIT.java   # integration
```

## Smallest useful controller test

```java
@WebMvcTest(CampaignsController.class)
class CampaignsControllerTest {

    @Autowired
    MockMvc mockMvc;

    @MockBean
    CampaignsService service;

    @Test
    void getHealth_returns200() throws Exception {
        mockMvc.perform(get("/health"))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.status").value("ok"));
    }

    @Test
    void getCampaign_returnsNotFound_whenMissing() throws Exception {
        when(service.findById("missing")).thenReturn(Optional.empty());
        mockMvc.perform(get("/campaigns/missing"))
               .andExpect(status().isNotFound());
    }
}
```

## Full-app integration test

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class CampaignsIT {
    @Autowired MockMvc mockMvc;

    @Test
    void list_returns200() throws Exception {
        mockMvc.perform(get("/campaigns")).andExpect(status().isOk());
    }
}
```

Use `@SpringBootTest` only when you need the full context. It's slow — prefer slice tests when possible.

## DB

- For repositories: `@DataJpaTest` with H2 by default, or Testcontainers for real Postgres parity.
- For services that touch the DB but don't need full HTTP: `@SpringBootTest` with `@Transactional` so each test rolls back.

## Running

```bash
./mvnw test                             # Maven
./mvnw test -Dtest=CampaignsControllerTest
./mvnw test -Dtest=CampaignsControllerTest#getHealth_returns200

./gradlew test                          # Gradle
./gradlew test --tests "com.example.campaigns.CampaignsControllerTest"
```
