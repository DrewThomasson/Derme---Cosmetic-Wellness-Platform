# Derme Test Suite

This directory contains comprehensive tests for the Derme Cosmetic Wellness Platform application.

## Test Files

### `test_app.py`
Comprehensive test suite with 18 test cases covering:

- **User Model Tests**: Password hashing, security questions, user creation
- **Database Model Tests**: UserAllergen, SafeProduct, AllergicProduct models
- **Helper Function Tests**: Ingredient parsing and normalization
- **Ingredient Synonym Tests**: Synonym detection
- **Allergen Detection Tests**: Potential allergen detection and ingredient analysis
- **Route Tests**: Page loading and authentication
- **Known Allergen Tests**: Allergen database

### `test_forgot_password.py`
Focused test for the forgot password functionality with security questions.

## Running Tests Locally

### Run all tests:
```bash
python test_app.py
```

### Run forgot password test:
```bash
python test_forgot_password.py
```

### Using unittest:
```bash
python -m unittest test_app.py
```

## Test Coverage

The test suite covers:
- ✅ User authentication (login, registration, password reset)
- ✅ Database models and relationships
- ✅ Ingredient parsing and normalization
- ✅ Allergen detection logic
- ✅ Route protection and authentication
- ✅ Security question functionality

## CI/CD Integration

Tests are automatically run via GitHub Actions on:
- Push to main/master/develop branches
- Pull requests to main/master/develop branches
- Manual workflow dispatch

The workflow tests against Python 3.9, 3.10, and 3.11 to ensure compatibility.

## Test Database

Tests use a separate SQLite database (`test.db`) that is created and destroyed for each test case to ensure test isolation.

## Adding New Tests

To add new tests:

1. Create a new test class inheriting from `unittest.TestCase`
2. Add `setUp()` and `tearDown()` methods to manage test database
3. Write test methods starting with `test_`
4. Add the test class to the test suite in `run_tests()` function

Example:
```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        # Set up test environment
        pass
    
    def tearDown(self):
        # Clean up after test
        pass
    
    def test_something(self):
        # Your test code here
        self.assertEqual(1 + 1, 2)
```

## Test Results

Current test status: **18/18 tests passing** ✅

All tests are designed to be simple, basic, and reliable to ensure core functionality works correctly.
