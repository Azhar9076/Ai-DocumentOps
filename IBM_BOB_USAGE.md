# IBM Bob Usage in AI DocumentOps

> **Project:** AI DocumentOps
> **Purpose:** AI-powered document intelligence, extraction, validation, and compliance auditing
> **AI Development Tool:** IBM Bob
> **Repository:** https://github.com/Azhar9076/Ai-DocumentOps
> **Live Application:** https://ai-documentops-1.onrender.com

---

## 1. Overview

**AI DocumentOps** is an enterprise-oriented document intelligence and compliance audit platform designed to automate the processing of unstructured business documents such as invoices and contracts.

The platform combines document parsing, AI-powered information extraction, mathematical validation, confidence scoring, and human-in-the-loop routing into a single workflow.

The primary processing pipeline is:

```text
Document Upload
       ↓
Document Parsing
       ↓
Document Classification
       ↓
Field Extraction
       ↓
Confidence Scoring
       ↓
Mathematical & Rule Validation
       ↓
Decision / Routing
       ↓
Auto Approval or Human Review
```

**IBM Bob** was used as an AI-powered pair programmer and agentic development assistant throughout the development of the project.

IBM Bob supported multiple stages of development, including:

* Project planning
* System architecture
* Backend development
* Frontend development
* API implementation
* AI prompt engineering
* Schema design
* Validation logic
* Debugging
* Testing
* Deployment troubleshooting
* Code refinement

IBM Bob did not replace the development and testing process. Generated code and suggestions were reviewed, adapted, tested, and integrated into the final implementation.

---

# 2. Role of IBM Bob in the Project

IBM Bob was used as a development companion inside the development environment.

The development approach was based on an iterative process:

```text
Requirement
     ↓
Prompt IBM Bob
     ↓
Generate / Modify Implementation
     ↓
Review Code
     ↓
Run & Test
     ↓
Identify Errors
     ↓
Debug with IBM Bob
     ↓
Refine Implementation
     ↓
Commit to GitHub
     ↓
Deploy
```

This approach allowed the team to move quickly from requirements to working features while maintaining manual review and testing of the generated implementation.

---

# 3. Project Planning and Architecture

IBM Bob was used during the planning stage to break the document processing problem into smaller and independently testable components.

The system was organized around a multi-stage document execution pipeline.

## 3.1 Document Ingestion

The first stage accepts business documents such as PDF invoices and other supported documents.

Responsibilities include:

* File upload
* File validation
* Document metadata collection
* Processing initiation
* Passing the document to the parsing layer

---

## 3.2 Document Parsing

IBM Docling is used to process document content and convert complex document structures into machine-readable information.

The parsing stage handles:

* Text extraction
* Document structure
* Multi-page documents
* Tables
* Layout information
* Structured document content

IBM Bob assisted in designing the integration and supporting backend implementation around the document-processing workflow.

---

## 3.3 Document Classification

The system determines the type of document being processed.

Examples include:

* Invoice
* Contract
* Business form
* Other supported business documents

Classification information is passed to subsequent processing stages so that the appropriate extraction logic can be applied.

---

## 3.4 Field Extraction

The AI extraction stage identifies important business fields from the processed document.

For invoices, examples include:

* Vendor name
* Invoice number
* Invoice date
* Due date
* Currency
* Subtotal
* Tax amount
* Total amount

The extracted information is returned in a structured format suitable for validation and database processing.

---

## 3.5 Confidence Scoring

Each extracted field can be associated with a confidence score.

The confidence information is used to determine whether the extracted information is reliable enough for automatic processing or should be reviewed by a human.

Example routing logic:

```text
Confidence >= 90%
        ↓
Automatic Processing

Confidence 70% - 89%
        ↓
Human Review

Confidence < 70%
        ↓
Action Required
```

---

# 4. IBM Bob Usage During Code Development

IBM Bob was used to accelerate development of both backend and frontend components.

## 4.1 Backend Development

IBM Bob assisted with the development of:

* FastAPI route handlers
* API endpoints
* Pydantic models
* Request validation
* Response schemas
* Document-processing utilities
* AI integration modules
* Validation utilities
* Error handling
* Database interaction logic

The generated implementation was reviewed and tested before being used in the application.

---

## 4.2 Frontend Development

IBM Bob assisted with the implementation and refinement of the application interface.

Frontend areas included:

* Document upload interface
* Processing status indicators
* Pipeline progress display
* Extracted field visualization
* Confidence score indicators
* Mathematical validation alerts
* Verification workspace
* Human-in-the-loop review interface

The UI was designed to make the document processing state easy to understand.

---

# 5. IBM Bob Usage for AI Integration

IBM Bob was used to assist with integration of AI capabilities into the document processing pipeline.

The AI layer was designed to provide structured information rather than unrestricted natural-language responses.

The desired output structure contains information such as:

```json
{
  "document_type": "invoice",
  "fields": {
    "vendor_name": {
      "value": "Example Vendor",
      "confidence": 0.96
    },
    "invoice_number": {
      "value": "INV-001",
      "confidence": 0.98
    },
    "subtotal": {
      "value": 100.00,
      "confidence": 0.99
    },
    "tax": {
      "value": 18.00,
      "confidence": 0.98
    },
    "total": {
      "value": 118.00,
      "confidence": 0.99
    }
  }
}
```

IBM Bob assisted in developing prompts and implementation patterns intended to make AI responses structured and suitable for downstream validation.

---

# 6. Prompts Used with IBM Bob

The following are representative prompts used during the development process.

## Prompt 1 — IBM watsonx.ai SDK Integration

```text
Generate a production-ready Python client module for integrating the ibm-watsonx-ai SDK with a FastAPI document processing application.

The module should:
- Authenticate using environment variables.
- Initialize the IBM watsonx.ai client.
- Support foundation model invocation.
- Use deterministic generation settings where appropriate.
- Handle API exceptions.
- Return structured responses suitable for downstream document processing.
- Keep credentials outside the source code.
```

### Purpose

This prompt was used to accelerate the creation of the AI model integration layer and establish a reusable backend wrapper around the IBM watsonx.ai SDK.

---

## Prompt 2 — Zero-Shot JSON Extraction

```text
Act as an enterprise document processing engine.

Create a system prompt for an IBM Granite model that extracts structured information from business documents.

The output must:
- Be strictly valid JSON.
- Identify the document type.
- Extract important key-value fields.
- Provide a confidence score between 0.0 and 1.0 for each extracted field.
- Normalize dates.
- Normalize numeric values.
- Avoid adding information that does not exist in the source document.
- Return missing fields as null instead of inventing values.
```

### Purpose

The objective was to produce predictable structured output that could be validated by deterministic application logic.

---

## Prompt 3 — Mathematical Integrity Validation

```text
Write a Python utility function that receives extracted Subtotal, Tax Amount, and Total Amount values from an invoice.

The function should:
- Validate whether Subtotal + Tax Amount equals Total Amount.
- Handle numeric values safely.
- Calculate the difference when a discrepancy exists.
- Set is_math_valid to false when the values do not match.
- Return a human-readable audit message.
- Handle missing or invalid numeric values safely.
```

### Purpose

This prompt was used to assist in implementing deterministic invoice arithmetic validation.

---

## Prompt 4 — Confidence-Based Routing

```text
Implement document routing logic based on extraction confidence.

Use the following rules:

- Confidence >= 0.90: Auto Processing
- Confidence >= 0.70 and < 0.90: Human Review
- Confidence < 0.70: Action Required

The implementation should return a clear routing status and explanation.
```

### Purpose

This supported the implementation of automated document routing based on extraction reliability.

---

## Prompt 5 — Deployment Debugging

```text
Analyze the following deployment error and identify the likely root cause.

Review:
- Python version compatibility
- Package metadata
- Dependency versions
- Build configuration
- Native dependencies
- Environment variables

Provide the recommended changes required to successfully deploy the FastAPI application.
```

### Purpose

IBM Bob was used to help analyze deployment failures and identify configuration or dependency-related issues.

---

# 7. Mathematical Audit Engine

One of the important deterministic components of AI DocumentOps is the invoice mathematical validation engine.

The system checks the relationship:

```text
Subtotal + Tax = Total
```

For example:

```text
Subtotal = $100.00
Tax      = $18.00
Expected Total = $118.00
```

If the invoice states:

```text
Total = $135.00
```

the system identifies the discrepancy.

Example audit result:

```text
Invoice Math Error

Expected Total: $118.00
Stated Total:   $135.00
Difference:     $17.00

is_math_valid = false
```

IBM Bob assisted in developing the utility logic and handling edge cases around numeric validation.

The final mathematical decision is deterministic and does not depend solely on the AI model.

This design helps reduce the risk of an AI model accepting mathematically inconsistent invoice information.

---

# 8. Confidence-Based Human-in-the-Loop Routing

IBM Bob also assisted with implementing confidence-based routing.

The system can use extraction confidence to determine the next action.

| Confidence | Routing         | Meaning                    |
| ---------- | --------------- | -------------------------- |
| >= 90%     | Auto Processing | High-confidence extraction |
| 70–89%     | Human Review    | Requires verification      |
| < 70%      | Action Required | Low-confidence extraction  |

Example:

```text
Document
   ↓
AI Extraction
   ↓
Confidence Evaluation
   ↓
┌─────────────────────────────┐
│ Confidence >= 90%           │
│         ↓                   │
│ Automatic Processing        │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Confidence 70–89%           │
│         ↓                   │
│ Human Review                │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Confidence < 70%            │
│         ↓                   │
│ Action Required             │
└─────────────────────────────┘
```

IBM Bob assisted with the implementation and refinement of this routing logic.

---

# 9. Debugging and Error Resolution

IBM Bob was used during development to investigate errors and improve the reliability of the application.

Examples of issues addressed included:

### Python Dependency Problems

IBM Bob was used to analyze package compatibility and dependency configuration.

### Cloud Deployment Errors

During deployment, IBM Bob assisted in analyzing build and environment errors encountered on Render.

### API Integration Issues

IBM Bob helped analyze API request and response handling, authentication configuration, and error handling.

### Runtime Errors

Tracebacks and application errors were provided to IBM Bob for analysis, after which suggested fixes were reviewed and tested.

The final solution was always validated by running the application rather than accepting generated changes without testing.

---

# 10. Testing and Validation

IBM Bob assisted in preparing and refining tests for different components of the application.

Testing areas included:

* Document upload
* PDF processing
* Document classification
* Field extraction
* Confidence scoring
* Invoice arithmetic validation
* Routing logic
* API responses
* Error handling
* Deployment configuration

Example invoice test cases:

| Test Case             | Subtotal |     Tax |   Total | Expected Result |
| --------------------- | -------: | ------: | ------: | --------------- |
| Valid Invoice         |      100 |      18 |     118 | Valid           |
| Math Error            |      100 |      18 |     135 | Invalid         |
| Zero Tax              |      100 |       0 |     100 | Valid           |
| Missing Total         |      100 |      18 | Missing | Review          |
| Invalid Numeric Value |      100 | Invalid |     118 | Action Required |

These tests help verify that deterministic validation operates independently of AI-generated interpretation.

---

# 11. Technologies Used

## AI Development

* IBM Bob

## AI and Foundation Models

* IBM watsonx.ai
* IBM Granite
* `ibm/granite-3-8b-instruct`
* IBM Granite models used during experimentation and development

## Document Processing

* IBM Docling

## Backend

* Python
* FastAPI
* Pydantic
* Uvicorn

## Frontend

* React
* Next.js
* Tailwind CSS

## Database

* PostgreSQL
* Neon Serverless PostgreSQL

## Deployment

* Render
* Vercel

## Source Control

* Git
* GitHub

---

# 12. Key Contributions of IBM Bob

IBM Bob contributed to several areas of the AI DocumentOps development process.

### Development Acceleration

IBM Bob reduced the amount of repetitive boilerplate coding required during development and helped accelerate implementation of backend and frontend components.

### Architecture Assistance

IBM Bob helped break down the application into logical processing stages and implementation tasks.

### AI Prompt Engineering

IBM Bob assisted in designing prompts for structured extraction and predictable JSON responses.

### Backend Development

IBM Bob assisted with FastAPI routes, Pydantic schemas, utility functions, and integration modules.

### Frontend Development

IBM Bob assisted with dashboard components, processing indicators, validation alerts, and document review interfaces.

### Debugging

IBM Bob was used to analyze errors and suggest fixes during development and deployment.

### Testing

IBM Bob assisted with test-case generation, validation logic, and edge-case analysis.

### Deployment

IBM Bob helped investigate dependency and environment issues during cloud deployment.

---

# 13. Development Impact

The use of IBM Bob improved the development workflow by providing rapid assistance during implementation, debugging, and refinement.

The main benefits observed were:

* Faster implementation of repetitive code.
* Faster exploration of alternative implementation approaches.
* Faster debugging of development errors.
* Improved prompt development.
* Faster creation of validation utilities.
* Assistance with frontend component development.
* Faster troubleshooting of deployment problems.
* More structured development workflow.

IBM Bob was used as an **AI development assistant**, while implementation decisions, testing, and final integration remained part of the development process.

---

# 14. Final Application Workflow

The final AI DocumentOps workflow can be represented as:

```text
                 ┌──────────────────┐
                 │  Document Upload │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │  IBM Docling    │
                 │ Document Parsing│
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Classification   │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ IBM Granite / AI │
                 │ Field Extraction │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Confidence Score │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Rule Validation  │
                 └────────┬─────────┘
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
       High Confidence          Low / Medium
              ↓                       ↓
       Auto Processing         Human Review
              │                       │
              └───────────┬───────────┘
                          ↓
                 ┌──────────────────┐
                 │ Audit / Database │
                 └──────────────────┘
```

---

# 15. Final Result

The completed **AI DocumentOps** platform provides an end-to-end document intelligence workflow.

The system is designed to:

* Ingest business documents.
* Parse PDFs and structured document content.
* Classify documents.
* Extract relevant business fields.
* Generate confidence scores.
* Normalize extracted values.
* Validate invoice mathematics.
* Detect arithmetic discrepancies.
* Route documents based on confidence.
* Support human-in-the-loop verification.
* Maintain an auditable processing workflow.

The combination of AI-powered extraction and deterministic validation allows the system to use AI where it is useful while keeping critical financial validation rules explicit and testable.

---

# 16. Project Links

## GitHub Repository

https://github.com/Azhar9076/Ai-DocumentOps

## Live Application

https://ai-documentops-1.onrender.com

## Demo

The project demonstration video is included as part of the project submission and demonstrates:

1. Document upload
2. Document processing
3. AI extraction
4. Confidence scoring
5. Mathematical validation
6. Human-in-the-loop review
7. Final processing result

---

# 17. Conclusion

IBM Bob played an important role as an AI-powered development assistant throughout the AI DocumentOps project.

It was used for planning, code generation, prompt engineering, UI development, debugging, testing, and deployment troubleshooting.

The development process followed a human-reviewed workflow in which IBM Bob generated suggestions or implementations, the development team reviewed them, and the resulting functionality was tested before being integrated.

This demonstrates the practical use of **IBM Bob as an agentic software development assistant** in building an AI-powered enterprise document processing application.

**IBM Bob Usage Summary:**

```text
Plan
 ↓
Prompt
 ↓
Generate
 ↓
Review
 ↓
Test
 ↓
Debug
 ↓
Refine
 ↓
Deploy
```

**Project:** AI DocumentOps
**Development Assistant:** IBM Bob
**Repository:** https://github.com/Azhar9076/Ai-DocumentOps
**Live Application:** 
