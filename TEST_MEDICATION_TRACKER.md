# Medication Tracker Unit Tests Documentation

## Overview
This document describes the unit tests for the medication tracker feature in the Derme Cosmetic Wellness Platform. The tests are written using Python's `unittest` framework (equivalent to JUnit for Java).

## Test File
**Location**: `test_medication_tracker.py`

## Running the Tests

### Run all tests:
```bash
python test_medication_tracker.py
```

### Run with verbose output:
```bash
python -m unittest test_medication_tracker -v
```

### Run a specific test:
```bash
python -m unittest test_medication_tracker.MedicationTrackerTestCase.test_add_medication_route_valid_data
```

## Test Coverage

### Model Tests (5 tests)
1. **test_medication_model_creation** - Tests creating a Medication model with all fields
2. **test_medication_model_defaults** - Tests default values (active=True, created_date)
3. **test_medication_log_model_creation** - Tests creating a MedicationLog model
4. **test_medication_log_relationship** - Tests the one-to-many relationship between Medication and MedicationLog
5. **test_medication_cascade_delete** - Tests that deleting a medication also deletes associated logs

### Route Tests - Add Medication (3 tests)
6. **test_add_medication_route_valid_data** - Tests adding a medication with all required and optional fields
7. **test_add_medication_route_missing_name** - Tests validation when name is missing (required field)
8. **test_add_medication_route_missing_frequency** - Tests validation when frequency is missing (required field)

### Route Tests - Edit Medication (2 tests)
9. **test_edit_medication_route_authorized** - Tests editing a medication as the owner
10. **test_edit_medication_route_unauthorized** - Tests that users cannot edit other users' medications

### Route Tests - Delete Medication (1 test)
11. **test_delete_medication_route** - Tests soft-deleting a medication (sets active=False)

### Route Tests - Log Medication (1 test)
12. **test_log_medication_route** - Tests logging medication intake with timestamp and notes

### Route Tests - View Routes (3 tests)
13. **test_medication_reminders_route** - Tests viewing medication reminders
14. **test_medication_history_route** - Tests viewing medication history
15. **test_medications_list_route** - Tests viewing all medications

### Additional Tests (4 tests)
16. **test_medications_list_excludes_inactive** - Tests that inactive medications are filtered out
17. **test_medication_times_parsing** - Tests that medication times are properly parsed and stored as JSON
18. **test_medication_without_login** - Tests that medication routes require authentication
19. **test_add_medication_without_login** - Tests that adding medication requires authentication

## Total: 19 Test Cases

## Features Tested

### Medication Model
- ✅ CRUD operations
- ✅ Field validation
- ✅ Default values
- ✅ Relationships with MedicationLog
- ✅ Cascade delete behavior

### MedicationLog Model
- ✅ Creating logs
- ✅ Tracking medication intake
- ✅ Timestamps and notes
- ✅ Relationship with Medication

### API Endpoints
- ✅ POST `/medications/add` - Add new medication
- ✅ POST `/medications/edit/<id>` - Edit medication
- ✅ POST `/medications/delete/<id>` - Soft delete medication
- ✅ POST `/medications/log/<id>` - Log medication intake
- ✅ GET `/medications` - View all active medications
- ✅ GET `/medications/reminders` - View medication reminders
- ✅ GET `/medications/history` - View medication history

### Security & Authorization
- ✅ Login required for all medication routes
- ✅ Users can only edit/delete their own medications
- ✅ User isolation - one user cannot access another user's data

### Data Integrity
- ✅ Required field validation
- ✅ JSON parsing for medication times
- ✅ Soft delete (preserves data)
- ✅ Cascade delete for logs

## Test Environment
- **Framework**: Python unittest (similar to JUnit)
- **Database**: SQLite in-memory (isolated for each test)
- **Web Framework**: Flask with test client
- **Coverage**: All medication tracker features

## Test Isolation
Each test case:
- Uses a fresh in-memory database
- Creates a new test user
- Cleans up after completion
- Is independent of other tests

## Assertions Used
- `assertEqual()` - Check exact matches
- `assertIsNotNone()` - Check object exists
- `assertTrue()` / `assertFalse()` - Check boolean values
- `assertIn()` / `assertNotIn()` - Check list membership

## Example Test Output
```
======================================================================
MEDICATION TRACKER UNIT TESTS
======================================================================

test_add_medication_route_valid_data ... ok
test_medication_model_creation ... ok
test_log_medication_route ... ok
...

----------------------------------------------------------------------
Ran 19 tests in 3.353s

OK

======================================================================
✓ ALL TESTS PASSED!
  Ran 19 tests successfully
======================================================================
```

## Maintenance
When adding new medication tracker features:
1. Add corresponding test cases to `test_medication_tracker.py`
2. Follow existing test patterns
3. Ensure test isolation (use setUp/tearDown)
4. Run all tests to ensure no regressions
5. Update this documentation

## Related Files
- `app.py` - Main application with Medication and MedicationLog models
- `test_forgot_password.py` - Example test file for reference
- `requirements.txt` - Dependencies including Flask and SQLAlchemy
