# Lead Qualifier

A small Python command-line tool that receives a customer request, sends it through an HTTP POST request, and classifies the lead as **HOT**, **WARM**, or **COLD**.

## Features

- Accepts a customer request from the terminal
- Sends JSON using an HTTP POST request
- Reads the returned JSON response
- Classifies leads using keyword-based scoring
- Distinguishes HOT, WARM, and COLD leads
- Handles connection errors
- Handles request timeouts
- Handles HTTP errors
- Handles invalid JSON responses

## Lead Classification

### HOT

A lead is classified as HOT when the request contains strong buying intent or urgency.

Examples:

- `urgent`
- `as soon as possible`
- `asap`
- `budget`
- `ready to start`
- `need a developer`
- `hire`

Example:

```text
I need a developer to build a chatbot for my business ASAP.
