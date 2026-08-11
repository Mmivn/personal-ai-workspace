# Lead Qualifier

A simple Python tool for analyzing incoming customer requests and automatically classifying leads by priority.

## Features

- Accepts a customer request from the command line
- Sends the request using an HTTP POST request
- Processes the server response
- Classifies leads as HOT, WARM, or COLD
- Handles network errors and timeouts

## Example

Input:

I need a developer to build a chatbot for my business ASAP.

Output:

===== LEAD ANALYSIS =====
Request: I need a developer to build a chatbot for my business ASAP.
Lead status: HOT
=========================

## Lead Classification

- HOT — customer shows strong buying intent or urgency
- WARM — customer is interested but not urgent
- COLD — customer has weak or unclear buying intent

## Run

```bash
python tools/lead_qualifier/main.py