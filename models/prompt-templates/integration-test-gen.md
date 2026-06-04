# Prompt Template: Integration & API Test Generation

Use this prompt to generate tests that validate the interaction between services or API endpoints.

---

## The Prompt

**System Role:** You are a senior Software Engineer specializing in API verification and service orchestration.

**User Input:** Generate integration tests based on this OpenAPI/Swagger specification:
```[JSON/YAML]
[Paste Spec Here]
```

**Requirements:**
1.  Use [Tool, e.g., Playwright/Postman/RestAssured].
2.  Test the following flows:
    -   Successful resource creation (201 Created).
    -   Resource retrieval and validation of schema.
    -   Conflict handling (e.g., duplicate entry → 409 Conflict).
    -   Authentication/Authorization failures (401/403).
3.  Ensure data cleanup is included after the tests.
4.  Generate dynamic test data using libraries like [Faker].

**Output Format:** Provide the test script and any necessary setup configuration.

---

## Tips for Success
-   **Include Dependencies:** Mention if the API relies on specific headers or cookies.
-   **Validation Logic:** Tell the AI exactly which fields in the JSON response are critical to validate.
