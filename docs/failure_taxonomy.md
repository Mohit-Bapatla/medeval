# Failure Taxonomy

These planned labels are for MedEval v1 failure analysis. They are taxonomy
definitions, not claims that every category is fully implemented today.

| Category | Definition | Example Symptom | Likely Source |
| --- | --- | --- | --- |
| `retrieval_miss` | Required evidence is not retrieved. | The answer omits eligibility because the relevant source never appears in context. | retrieval |
| `retrieval_rank_failure` | Required evidence is retrieved too low to be used. | Gold evidence appears below the selected top-k window. | retrieval |
| `context_overload` | Too much or poorly scoped context causes relevant evidence to be ignored. | The answer cites a broad page but misses the narrow exception. | retrieval |
| `unsupported_claim` | The answer includes a factual claim not supported by source evidence. | Adds a deadline that is absent from the documents. | generation |
| `citation_mismatch` | A citation points to evidence that does not support the claim. | Cites a contact-info section for an eligibility statement. | citation |
| `missing_citation` | A claim that needs support has no citation. | Gives a required-document list without source references. | citation |
| `incomplete_answer` | The answer is directionally correct but omits required information. | Lists two of three required documents. | generation |
| `over_answering` | The answer goes beyond the question or source scope. | Provides treatment advice when asked only for program contact details. | generation |
| `failed_refusal` | The system answers when it should refuse or say unsupported. | Answers a private patient question not present in sources. | refusal |
| `over_refusal` | The system refuses a question that is answerable from the sources. | Refuses a public eligibility question with clear evidence. | refusal |
| `ambiguity_failure` | The system mishandles an ambiguous question. | Chooses one program without acknowledging multiple possible matches. | generation |
| `temporal_failure` | The answer ignores version dates, effective dates, or staleness. | Uses an outdated policy as if it were current. | data |
| `contradiction` | The answer conflicts with source evidence or internal constraints. | Says a service is free when the source states fees may apply. | generation |
| `bad_synthesis` | Multiple pieces of evidence are combined incorrectly. | Mixes eligibility from one program with benefits from another. | generation |
| `format_failure` | The response violates the required structure or machine-readable format. | Returns prose when JSON with citations was required. | format |

