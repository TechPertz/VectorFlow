# VectorFlow Tests

This directory contains tests for the VectorFlow application, organized to exactly mirror the app's structure.

## Testing Philosophy

Our testing structure emphasizes both unit and integration testing:

- **Unit Tests**: Focus on testing individual components in isolation with mocked dependencies
- **Integration Tests**: Test the interaction between components and external services

We use both mock data and real API calls where appropriate:

- **Mock Tests**: Use fake/stub data to ensure consistent, fast testing without external dependencies
- **Real Data Tests**: Connect to actual services (like Cohere API) to verify real-world behavior

## Requirements

- Python 3.8+
- `pytest` and `pytest-asyncio` 
- Cohere API key (for integration tests)

## Setup

1. Set your Cohere API key in a `.env` file in the root directory:
   ```
   COHERE_API_KEY=your_api_key_here
   ```

2. Install testing dependencies:
   ```bash
   pip install pytest pytest-asyncio
   ```

## Running Tests

From the root directory of the project:

```bash
# Run all tests
python -m pytest VectorFlow/tests/

# Run only unit tests
python -m pytest VectorFlow/tests/ -m unit

# Run only integration tests
python -m pytest VectorFlow/tests/ -m integration

# Run tests with real API calls
python -m pytest VectorFlow/tests/ -m real

# Combining markers
python -m pytest VectorFlow/tests/ -m "unit and not real"

# Run specific test file
python -m pytest VectorFlow/tests/services/test_embeddings.py

# Run with verbose output
python -m pytest VectorFlow/tests/ -v
```

## Test Structure

The test directory exactly mirrors the app directory structure:

```
VectorFlow/
├── app/
│   ├── api/
│   │   └── endpoints/
│   ├── core/
│   ├── db/
│   ├── models/
│   └── services/
│       └── embeddings.py
└── tests/
    ├── api/
    │   └── endpoints/
    ├── core/
    ├── db/
    ├── models/
    └── services/
        └── test_embeddings.py  # Contains both unit and integration tests
```

## Test Classes

For a clean separation of concerns, we organize tests by type:

- `TestXxxUnit`: Contains unit tests with mocked dependencies
- `TestXxxIntegration`: Contains integration tests with real dependencies

## Test Markers

We use pytest markers to categorize tests:

- `@pytest.mark.unit`: For unit tests
- `@pytest.mark.integration`: For integration tests
- `@pytest.mark.mock`: For tests using mock data
- `@pytest.mark.real`: For tests using real services

## Adding New Tests

When adding tests for a new component:

1. Follow the same directory structure as in the app
2. Use the appropriate test class structure for unit and integration tests
3. Apply markers to enable selective test running 