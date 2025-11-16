# Quick Reference Guide - Testing Infrastructure

## For Developers

### Running Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run specific use case
pytest tests/test_registration.py        # Use Case 1
pytest tests/test_authentication.py      # Use Case 2
pytest tests/test_allergen_management.py # Use Case 3
pytest tests/test_scanning.py            # Use Case 4
pytest tests/test_ingredient_analysis.py # Use Case 5

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html
# Then open htmlcov/index.html in browser

# Run specific test
pytest tests/test_registration.py::TestUserRegistration::test_successful_registration
```

### Validate Test Setup

```bash
# Run validation script
./validate_tests.sh
```

## For Project Managers

### Test Coverage Overview

| Use Case | Description | Test Count | File |
|----------|-------------|------------|------|
| 1 | User Registration | 7 | test_registration.py |
| 2 | User Authentication | 11 | test_authentication.py |
| 3 | Allergen Management | 10 | test_allergen_management.py |
| 4 | Product Scanning | 12 | test_scanning.py |
| 5 | Ingredient Analysis | 13 | test_ingredient_analysis.py |
| **Total** | | **53+** | |

### Key Documents

- `TEST_CASES.md` - Detailed test case specifications
- `tests/README.md` - Test suite documentation
- `TESTING_SUMMARY.md` - Implementation summary

### CI/CD Status

Tests run automatically on:
- ✅ Every push to main/develop
- ✅ Every pull request
- ✅ Daily at 2 AM UTC
- ✅ Manual trigger available

View results: GitHub Actions → Workflows → "Comprehensive Testing"

## For QA Team

### Test Case Format

Each test case includes:
- **Test Case ID** (e.g., TC-REG-001)
- **Description** - What is being tested
- **Test Inputs** - Input values
- **Expected Results** - Expected behavior
- **Dependencies** - Prerequisites
- **Test Steps** - Execution steps
- **Post-conditions** - Final state

### Test Categories

All tests use equivalence class partitioning:

**Example - Registration Password:**
- Empty password (invalid)
- Short password < 6 chars (invalid)
- Valid password ≥ 6 chars (valid)
- Mismatched confirmation (invalid)

### Manual Testing

While automated tests cover functionality, manual testing should verify:
- UI/UX elements
- Visual design
- Accessibility
- Cross-browser compatibility
- Mobile responsiveness

## For Instructors/Reviewers

### Section 10 Requirements ✅

**Section 10.1 - Test Cases:**
- ✅ 5 major use cases identified
- ✅ Equivalence class partitioning applied
- ✅ Test specifications documented
- ✅ Format: ID, Description, Inputs, Results, Dependencies, Steps, Post-conditions

**Section 10.2 - JUnit Testing:**
- ✅ Pytest framework used (Python's JUnit equivalent)
- ✅ 53+ automated unit tests
- ✅ Test fixtures and configuration
- ✅ CI/CD integration
- ✅ Coverage reporting

### Architecture

```
Repository Root
├── TEST_CASES.md              # Test case specifications
├── TESTING_SUMMARY.md         # Implementation summary
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Includes pytest dependencies
├── validate_tests.sh          # Test validation script
├── .github/
│   └── workflows/
│       ├── test.yml                      # Basic test workflow
│       └── comprehensive-tests.yml       # Full test suite
└── tests/
    ├── README.md              # Test documentation
    ├── conftest.py            # Fixtures and configuration
    ├── test_registration.py
    ├── test_authentication.py
    ├── test_allergen_management.py
    ├── test_scanning.py
    └── test_ingredient_analysis.py
```

### Testing Methodology

1. **Requirements-Based Testing**
   - Tests derived from functional requirements
   - Mapped to specific use cases

2. **Equivalence Class Partitioning**
   - Input domains divided into equivalence classes
   - At least one test per class
   - Boundary value testing

3. **Test Independence**
   - Fresh database per test
   - No test dependencies
   - Parallel execution support

4. **Coverage Analysis**
   - Measured with pytest-cov
   - HTML reports generated
   - Target: 80%+ coverage

## Common Commands

```bash
# Quick test run
pytest tests/ -v --tb=short

# Test with timing
pytest tests/ -v --durations=10

# Test specific marker
pytest -m registration
pytest -m authentication
pytest -m allergen
pytest -m scanning
pytest -m analysis

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Show local variables on failure
pytest tests/ -l

# Quiet output
pytest tests/ -q
```

## Troubleshooting

### Issue: Import errors
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Tesseract OCR errors in scanning tests
**Solution:** Install Tesseract
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Issue: Database errors
**Solution:** Tests use in-memory database, no setup needed
- Ensure SQLAlchemy is installed
- Check app.py is in current directory

### Issue: No tests collected
**Solution:** Check test discovery
```bash
pytest --collect-only tests/
```

## Contact

For questions or issues with the test infrastructure:
- Review documentation in `tests/README.md`
- Check test case specifications in `TEST_CASES.md`
- Run validation script: `./validate_tests.sh`
- Check GitHub Actions for CI/CD status

---

**Quick Start:** `pip install -r requirements.txt && pytest tests/ -v`
