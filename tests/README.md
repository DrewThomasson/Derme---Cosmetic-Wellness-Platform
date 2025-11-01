# Derme Test Suite

This directory contains the automated test suite for the Derme Cosmetic Wellness Platform, implementing the testing requirements from **Section 10: Testing**.

## Test Structure

The test suite is organized by the 5 major use cases:

### 1. User Registration (test_registration.py)
Tests for user account creation and validation:
- TC-REG-001: Successful user registration
- TC-REG-002: Duplicate username/email handling
- TC-REG-003: Password validation and mismatch handling
- Boundary condition tests (empty fields)

### 2. User Authentication (test_authentication.py)
Tests for user login and session management:
- TC-LOGIN-001: Successful login with correct credentials
- TC-LOGIN-002: Login failure with incorrect password
- TC-LOGIN-003: Login failure with non-existent user
- Session management and logout tests
- Protected route access tests

### 3. Allergen Management (test_allergen_management.py)
Tests for personal allergen tracking:
- TC-ALLERGEN-001: Add personal allergen with severity
- TC-ALLERGEN-002: Delete personal allergen
- TC-ALLERGEN-003: Validation of allergen input
- Multiple allergen management
- User isolation tests

### 4. Product Scanning (test_scanning.py)
Tests for OCR and product ingredient extraction:
- TC-SCAN-001: Successful ingredient extraction
- TC-SCAN-002: No image uploaded handling
- TC-SCAN-003: Unclear image handling
- Product save functionality (safe/allergic)
- Session management for scan results

### 5. Ingredient Analysis (test_ingredient_analysis.py)
Tests for allergen detection and cross-referencing:
- TC-ANALYSIS-001: User allergen detection
- TC-ANALYSIS-002: Known database allergen detection
- TC-ANALYSIS-003: Safe ingredient identification
- TC-ANALYSIS-004: Synonym matching
- TC-ANALYSIS-005: Edge cases (empty lists, special characters)

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_registration.py
```

### Run Specific Test Class or Function
```bash
pytest tests/test_registration.py::TestUserRegistration::test_successful_registration
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run Tests by Marker
```bash
# Run only registration tests
pytest -m registration

# Run only unit tests
pytest -m unit

# Exclude slow tests
pytest -m "not slow"
```

## Test Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

- **app**: Test Flask application with in-memory database
- **client**: Test client for making HTTP requests
- **test_user**: Pre-created test user
- **authenticated_client**: Test client with logged-in user
- **test_user_with_allergen**: User with a pre-defined allergen
- **known_allergen_db**: Database populated with known allergens

## Equivalence Class Partitioning

Tests follow equivalence class partitioning principles:

### User Registration
- **Username**: Empty, < 3 chars, 3-80 chars (valid), > 80 chars, duplicate
- **Email**: Empty, invalid format, valid format, duplicate
- **Password**: Empty, < 6 chars, 6+ chars (valid), mismatched confirmation

### Allergen Management
- **Ingredient Name**: Empty, 1-200 chars (valid), > 200 chars
- **Severity**: "mild", "moderate", "severe", "unknown"

### Product Scanning
- **Image**: No image, empty filename, valid image, unclear image
- **Ingredients**: 0 ingredients, 1 ingredient, 2-100 ingredients

### Ingredient Analysis
- **User Allergens**: 0 allergens, 1-5 allergens, 5-20 allergens, 20+ allergens
- **Ingredient Matches**: No matches, user allergen match, database match, synonym match

## Continuous Integration

Tests are automatically run on:
- Push to main/develop branches
- Pull requests to main/develop branches
- Daily at 2 AM UTC (scheduled)
- Manual workflow dispatch

See `.github/workflows/test.yml` and `.github/workflows/comprehensive-tests.yml` for CI configuration.

## Coverage Goals

Target coverage: 80%+

Key areas covered:
- ✅ User authentication and authorization
- ✅ Database operations (CRUD)
- ✅ Ingredient parsing and analysis
- ✅ Allergen detection and cross-referencing
- ✅ Error handling and validation
- ✅ Session management

## Test Documentation

Detailed test case specifications are available in `TEST_CASES.md` in the root directory, following the format:
- Test Case ID
- Description
- Test Inputs
- Expected Results
- Dependencies
- Initialization
- Test Steps
- Post-conditions

## Adding New Tests

When adding new tests:

1. Follow the existing structure and naming conventions
2. Use appropriate fixtures from `conftest.py`
3. Add test markers if creating a new category
4. Document test cases in `TEST_CASES.md`
5. Ensure tests are isolated and don't depend on execution order
6. Include both positive and negative test cases
7. Test boundary conditions

## Dependencies

Required packages for testing:
- pytest==7.4.3
- pytest-cov==4.1.0
- Flask==3.0.0
- Flask-Login==0.6.3
- Flask-SQLAlchemy==3.1.1

## Notes

- Tests use an in-memory SQLite database for isolation
- Each test gets a fresh database instance
- Tesseract OCR is required for full scanning tests
- Some tests may be skipped if Tesseract is not installed

---

**Last Updated:** October 2025  
**Test Count:** 50+ tests  
**Status:** ✅ All tests passing
