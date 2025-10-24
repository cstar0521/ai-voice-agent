# End-to-End Testing Guide

This document describes the comprehensive end-to-end testing suite for the AI Voice Loan Agent system.

## Overview

The E2E testing suite covers three main areas:

1. **End-to-End Scenarios** (`test_e2e_scenarios.py`) - Complete call flow testing
2. **Load Testing** (`test_load_testing.py`) - Performance and concurrency testing
3. **User Acceptance Testing** (`test_user_acceptance.py`) - Business KPI validation

## Test Files

### 1. End-to-End Scenarios (`tests/test_e2e_scenarios.py`)

Tests complete system integration including:

- API endpoint functionality
- Service layer integration
- Data model validation
- Error handling
- Component imports and structure

**Requirements Covered:** 1.1, 2.1, 4.1, 7.4

### 2. Load Testing (`tests/test_load_testing.py`)

Performance testing scenarios:

- 10 concurrent calls
- 50 concurrent calls
- API response time measurement
- TTS latency testing
- Overall call latency measurement
- Memory usage under load
- Error rate under stress

**Requirements Covered:** 8.2, 8.3

### 3. User Acceptance Testing (`tests/test_user_acceptance.py`)

Business KPI validation:

- Call completion rate (target: 80%)
- Qualification time (target: ≤3 min)
- Handoff rate (target: 55%)
- CSAT scores (target: 4.5/5)
- Language accuracy (Hinglish 90%, English 90%, Telugu 85%)
- 50 beta call simulation

**Requirements Covered:** 8.1, 10.1, 10.2, 10.3, 10.4

## Running Tests

### Prerequisites

1. Activate virtual environment:

   ```bash
   source venv/bin/activate
   ```

2. Ensure pytest is installed:
   ```bash
   pip install pytest pytest-asyncio
   ```

### Running Individual Test Suites

#### End-to-End Scenarios

```bash
python -m pytest tests/test_e2e_scenarios.py -v
```

#### Load Testing

```bash
python -m pytest tests/test_load_testing.py -v
```

#### User Acceptance Testing

```bash
python -m pytest tests/test_user_acceptance.py -v
```

### Running All Tests

#### Using the Test Runner Script

```bash
# Run all tests
python run_e2e_tests.py

# Run specific test type
python run_e2e_tests.py --test-type scenarios
python run_e2e_tests.py --test-type load
python run_e2e_tests.py --test-type uat

# Verbose output
python run_e2e_tests.py --verbose
```

#### Using pytest directly

```bash
# Run all E2E tests
python -m pytest tests/test_e2e_scenarios.py tests/test_load_testing.py tests/test_user_acceptance.py -v

# Run with markers
python -m pytest -m "e2e or load or uat" -v
```

## Test Structure

### Mock-Based Testing

The tests use extensive mocking to simulate:

- External API calls (Twilio, Speech services, OpenAI)
- Database operations
- Network conditions
- Service failures

This approach allows testing system behavior without requiring:

- Live external services
- Real phone calls
- Actual database connections

### Performance Benchmarks

Load tests validate against these performance targets:

| Metric               | Target  | Test Coverage |
| -------------------- | ------- | ------------- |
| API Response Time    | < 200ms | ✅            |
| TTS Latency          | < 1.2s  | ✅            |
| Overall Call Latency | < 2s    | ✅            |
| Concurrent Calls     | 50+     | ✅            |
| Success Rate         | > 95%   | ✅            |

### Business KPIs

User acceptance tests validate against these business targets:

| KPI                          | Target  | Test Coverage |
| ---------------------------- | ------- | ------------- |
| Call Completion Rate         | 80%     | ✅            |
| Qualification Time           | ≤ 3 min | ✅            |
| Handoff Rate                 | 55%     | ✅            |
| CSAT Score                   | 4.5/5   | ✅            |
| Language Accuracy (Hinglish) | 90%     | ✅            |
| Language Accuracy (English)  | 90%     | ✅            |
| Language Accuracy (Telugu)   | 85%     | ✅            |

## Test Configuration

### pytest.ini Configuration

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --durations=10
markers =
    e2e: End-to-end integration tests
    load: Load and performance tests
    uat: User acceptance tests
    slow: Slow running tests
```

### Test Markers

Use markers to run specific test categories:

```bash
# Run only E2E tests
python -m pytest -m e2e

# Run only load tests
python -m pytest -m load

# Run only UAT tests
python -m pytest -m uat

# Skip slow tests
python -m pytest -m "not slow"
```

## Interpreting Results

### Success Criteria

Tests pass when:

- All API endpoints respond correctly
- Service imports work without errors
- Performance metrics meet targets
- Business KPIs are achieved
- Error rates stay below thresholds

### Common Failure Scenarios

1. **Import Errors**: Missing dependencies or incorrect module paths
2. **Database Errors**: MongoDB connection issues (expected in test environment)
3. **Authentication Errors**: Missing or invalid JWT tokens (expected without real auth)
4. **External Service Errors**: Twilio/Speech API failures (expected with mocks)

### Expected Test Behavior

In a test environment without live services:

- API endpoints may return 401/500 errors (expected)
- Database operations may fail (expected)
- External service calls will be mocked
- Focus is on structure and integration validation

## Continuous Integration

### GitHub Actions Integration

Add to `.github/workflows/test.yml`:

```yaml
- name: Run E2E Tests
  run: |
    cd backend
    source venv/bin/activate
    python run_e2e_tests.py --test-type all
```

### Local Development

Run tests before committing:

```bash
# Quick validation
python run_e2e_tests.py --test-type scenarios

# Full test suite (slower)
python run_e2e_tests.py --test-type all
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure you're in the backend directory and virtual environment is activated
2. **Import Errors**: Check that all required services exist in the codebase
3. **Async Test Issues**: Ensure pytest-asyncio is installed and asyncio_mode = auto is set
4. **Performance Test Failures**: Adjust timing expectations for slower systems

### Debug Mode

Run with verbose output and full tracebacks:

```bash
python -m pytest tests/test_e2e_scenarios.py -v -s --tb=long
```

### Test Coverage

Generate coverage report:

```bash
pip install pytest-cov
python -m pytest tests/ --cov=app --cov-report=html
```

## Future Enhancements

1. **Real Integration Tests**: Add tests with actual external services
2. **Database Integration**: Add tests with real MongoDB instances
3. **Performance Monitoring**: Add continuous performance benchmarking
4. **Visual Testing**: Add screenshot/UI testing for frontend components
5. **Chaos Engineering**: Add failure injection testing

## Contributing

When adding new E2E tests:

1. Follow the existing test structure
2. Use appropriate mocking for external dependencies
3. Add performance assertions where relevant
4. Update this documentation
5. Ensure tests are deterministic and reliable

## Support

For issues with E2E testing:

1. Check this documentation
2. Review test logs and error messages
3. Verify environment setup
4. Check for missing dependencies
5. Consult the main project README for setup instructions
