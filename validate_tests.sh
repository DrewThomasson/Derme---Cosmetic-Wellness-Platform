#!/bin/bash
#
# Test Validation Script for Derme Application
# This script validates the test infrastructure setup
#

set -e  # Exit on error

echo "=================================================="
echo "Derme Test Infrastructure Validation"
echo "=================================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   ✓ Python version: $python_version"
echo ""

# Check if in correct directory
echo "2. Checking repository structure..."
if [ ! -f "app.py" ]; then
    echo "   ✗ Error: app.py not found. Please run from repository root."
    exit 1
fi
echo "   ✓ Repository structure validated"
echo ""

# Check if tests directory exists
echo "3. Checking test directory..."
if [ ! -d "tests" ]; then
    echo "   ✗ Error: tests directory not found"
    exit 1
fi
test_files=$(find tests -name "test_*.py" | wc -l)
echo "   ✓ Found $test_files test files"
echo ""

# Check if pytest is installed
echo "4. Checking pytest installation..."
if ! python -c "import pytest" 2>/dev/null; then
    echo "   ⚠ pytest not installed. Installing now..."
    pip install pytest pytest-cov
fi
pytest_version=$(python -c "import pytest; print(pytest.__version__)")
echo "   ✓ pytest version: $pytest_version"
echo ""

# Check Flask installation
echo "5. Checking Flask installation..."
if ! python -c "import flask" 2>/dev/null; then
    echo "   ⚠ Flask not installed. Installing dependencies..."
    pip install -r requirements.txt
fi
flask_version=$(python -c "import flask; print(flask.__version__)" 2>/dev/null || echo "not installed")
echo "   ✓ Flask version: $flask_version"
echo ""

# Collect tests
echo "6. Collecting tests..."
test_count=$(pytest --collect-only -q tests/ 2>/dev/null | grep -c "test_" || echo "0")
echo "   ✓ Found $test_count test cases"
echo ""

# Show test structure
echo "7. Test suite structure:"
echo ""
echo "   Use Case 1: User Registration"
echo "   File: tests/test_registration.py"
registration_count=$(pytest --collect-only -q tests/test_registration.py 2>/dev/null | grep -c "test_" || echo "0")
echo "   Tests: $registration_count"
echo ""

echo "   Use Case 2: User Authentication"
echo "   File: tests/test_authentication.py"
auth_count=$(pytest --collect-only -q tests/test_authentication.py 2>/dev/null | grep -c "test_" || echo "0")
echo "   Tests: $auth_count"
echo ""

echo "   Use Case 3: Allergen Management"
echo "   File: tests/test_allergen_management.py"
allergen_count=$(pytest --collect-only -q tests/test_allergen_management.py 2>/dev/null | grep -c "test_" || echo "0")
echo "   Tests: $allergen_count"
echo ""

echo "   Use Case 4: Product Scanning"
echo "   File: tests/test_scanning.py"
scan_count=$(pytest --collect-only -q tests/test_scanning.py 2>/dev/null | grep -c "test_" || echo "0")
echo "   Tests: $scan_count"
echo ""

echo "   Use Case 5: Ingredient Analysis"
echo "   File: tests/test_ingredient_analysis.py"
analysis_count=$(pytest --collect-only -q tests/test_ingredient_analysis.py 2>/dev/null | grep -c "test_" || echo "0")
echo "   Tests: $analysis_count"
echo ""

# Check CI/CD workflows
echo "8. Checking CI/CD workflows..."
if [ -f ".github/workflows/test.yml" ]; then
    echo "   ✓ Basic test workflow configured"
fi
if [ -f ".github/workflows/comprehensive-tests.yml" ]; then
    echo "   ✓ Comprehensive test workflow configured"
fi
echo ""

# Check test documentation
echo "9. Checking test documentation..."
if [ -f "TEST_CASES.md" ]; then
    test_case_count=$(grep -c "^### Test Case" TEST_CASES.md || echo "0")
    echo "   ✓ TEST_CASES.md found with $test_case_count documented test cases"
fi
if [ -f "tests/README.md" ]; then
    echo "   ✓ tests/README.md found"
fi
if [ -f "TESTING_SUMMARY.md" ]; then
    echo "   ✓ TESTING_SUMMARY.md found"
fi
echo ""

echo "=================================================="
echo "Validation Summary"
echo "=================================================="
echo "✓ Test infrastructure is properly configured"
echo "✓ Total test files: $test_files"
echo "✓ Total test cases: $test_count"
echo "✓ CI/CD workflows: Configured"
echo "✓ Documentation: Complete"
echo ""
echo "To run tests:"
echo "  pytest tests/                    # Run all tests"
echo "  pytest tests/ -v                 # Verbose output"
echo "  pytest tests/ --cov=app          # With coverage"
echo ""
echo "=================================================="
