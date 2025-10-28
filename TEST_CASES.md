# Test Cases Documentation - Derme Application

## Section 10.1: Test Cases

This document contains requirements-based tests (functionality testing) for the 5 major use cases of the Derme application.

---

## Use Case 1: User Registration

### Equivalence Class Partitioning

**Username:**
- Valid: 3-80 characters, alphanumeric and underscores
- Invalid: Empty, < 3 characters, > 80 characters, duplicate username

**Email:**
- Valid: Valid email format (user@domain.com)
- Invalid: Empty, invalid format, duplicate email

**Password:**
- Valid: 6+ characters
- Invalid: Empty, < 6 characters, passwords don't match

---

### Test Case 1.1: Successful User Registration

**Test Case ID:** TC-REG-001

**Description:** Verify that a user can successfully register with valid credentials

**Test Inputs:**
- Username: "testuser123"
- Email: "testuser@example.com"
- Password: "SecurePass123"
- Confirm Password: "SecurePass123"

**Expected Results:**
- User is created in database
- Success message displayed: "Registration successful! Please log in."
- User is redirected to login page
- Password is hashed in database

**Dependencies:** Database must be initialized

**Initialization:** Clean database or ensure username/email don't exist

**Test Steps:**
1. Navigate to registration page
2. Enter valid username "testuser123"
3. Enter valid email "testuser@example.com"
4. Enter password "SecurePass123"
5. Enter confirm password "SecurePass123"
6. Click submit button

**Post-conditions:** User record exists in database with hashed password

---

### Test Case 1.2: Registration with Duplicate Username

**Test Case ID:** TC-REG-002

**Description:** Verify that registration fails when username already exists

**Test Inputs:**
- Username: "existinguser" (already in database)
- Email: "newemail@example.com"
- Password: "SecurePass123"
- Confirm Password: "SecurePass123"

**Expected Results:**
- Registration fails
- Error message displayed: "Username already exists"
- User remains on registration page
- No new user created in database

**Dependencies:** Existing user with username "existinguser" must exist

**Initialization:** Create a user with username "existinguser"

**Test Steps:**
1. Navigate to registration page
2. Enter existing username "existinguser"
3. Enter new email "newemail@example.com"
4. Enter password "SecurePass123"
5. Enter confirm password "SecurePass123"
6. Click submit button

**Post-conditions:** No new user record created

---

### Test Case 1.3: Registration with Mismatched Passwords

**Test Case ID:** TC-REG-003

**Description:** Verify that registration fails when passwords don't match

**Test Inputs:**
- Username: "newuser"
- Email: "newuser@example.com"
- Password: "SecurePass123"
- Confirm Password: "DifferentPass456"

**Expected Results:**
- Registration fails
- Error message displayed: "Passwords do not match"
- User remains on registration page
- No new user created

**Dependencies:** None

**Initialization:** Clean database

**Test Steps:**
1. Navigate to registration page
2. Enter username "newuser"
3. Enter email "newuser@example.com"
4. Enter password "SecurePass123"
5. Enter different confirm password "DifferentPass456"
6. Click submit button

**Post-conditions:** No user record created

---

## Use Case 2: User Login/Authentication

### Equivalence Class Partitioning

**Username:**
- Valid: Existing username in database
- Invalid: Non-existent username, empty

**Password:**
- Valid: Correct password for the username
- Invalid: Incorrect password, empty

---

### Test Case 2.1: Successful Login

**Test Case ID:** TC-LOGIN-001

**Description:** Verify that a registered user can successfully log in with correct credentials

**Test Inputs:**
- Username: "testuser"
- Password: "correctpassword"

**Expected Results:**
- User is authenticated
- User is redirected to dashboard
- Session is created for user
- User profile information is loaded

**Dependencies:** User "testuser" must exist in database

**Initialization:** Create user with username "testuser" and password "correctpassword"

**Test Steps:**
1. Navigate to login page
2. Enter username "testuser"
3. Enter password "correctpassword"
4. Click login button

**Post-conditions:** User session is active, user is authenticated

---

### Test Case 2.2: Login with Incorrect Password

**Test Case ID:** TC-LOGIN-002

**Description:** Verify that login fails with incorrect password

**Test Inputs:**
- Username: "testuser"
- Password: "wrongpassword"

**Expected Results:**
- Authentication fails
- Error message displayed: "Invalid username or password"
- User remains on login page
- No session is created

**Dependencies:** User "testuser" must exist in database

**Initialization:** User "testuser" exists with different password

**Test Steps:**
1. Navigate to login page
2. Enter valid username "testuser"
3. Enter incorrect password "wrongpassword"
4. Click login button

**Post-conditions:** No user session created

---

### Test Case 2.3: Login with Non-existent User

**Test Case ID:** TC-LOGIN-003

**Description:** Verify that login fails for non-existent user

**Test Inputs:**
- Username: "nonexistentuser"
- Password: "anypassword"

**Expected Results:**
- Authentication fails
- Error message displayed: "Invalid username or password"
- User remains on login page
- No session is created

**Dependencies:** None

**Initialization:** Ensure username "nonexistentuser" does not exist

**Test Steps:**
1. Navigate to login page
2. Enter non-existent username "nonexistentuser"
3. Enter any password "anypassword"
4. Click login button

**Post-conditions:** No user session created

---

## Use Case 3: Allergen Management

### Equivalence Class Partitioning

**Ingredient Name:**
- Valid: 1-200 characters, non-empty string
- Invalid: Empty string, > 200 characters

**Severity:**
- Valid: "mild", "moderate", "severe", "unknown"
- Invalid: Empty, invalid severity level

---

### Test Case 3.1: Add Personal Allergen

**Test Case ID:** TC-ALLERGEN-001

**Description:** Verify that authenticated user can add a personal allergen

**Test Inputs:**
- User ID: Authenticated user
- Ingredient Name: "Methylisothiazolinone"
- Severity: "severe"

**Expected Results:**
- Allergen is added to user's allergen list
- Success message displayed
- Allergen appears in user's allergen management page
- Database record created with correct user_id

**Dependencies:** User must be authenticated

**Initialization:** User logged in, allergen does not already exist for user

**Test Steps:**
1. Navigate to allergen management page
2. Enter ingredient name "Methylisothiazolinone"
3. Select severity "severe"
4. Click add allergen button

**Post-conditions:** UserAllergen record exists in database for this user

---

### Test Case 3.2: Delete Personal Allergen

**Test Case ID:** TC-ALLERGEN-002

**Description:** Verify that authenticated user can delete a personal allergen

**Test Inputs:**
- User ID: Authenticated user
- Allergen ID: Existing allergen ID for the user

**Expected Results:**
- Allergen is removed from user's allergen list
- Success message displayed
- Allergen no longer appears in allergen management page
- Database record is deleted

**Dependencies:** User must be authenticated and have at least one allergen

**Initialization:** User logged in with existing allergen in database

**Test Steps:**
1. Navigate to allergen management page
2. Identify allergen to delete
3. Click delete button for that allergen
4. Confirm deletion

**Post-conditions:** UserAllergen record is deleted from database

---

### Test Case 3.3: Add Allergen with Empty Name

**Test Case ID:** TC-ALLERGEN-003

**Description:** Verify that adding allergen with empty name fails

**Test Inputs:**
- User ID: Authenticated user
- Ingredient Name: "" (empty string)
- Severity: "moderate"

**Expected Results:**
- Allergen is not added
- Error message displayed
- User remains on allergen management page
- No database record created

**Dependencies:** User must be authenticated

**Initialization:** User logged in

**Test Steps:**
1. Navigate to allergen management page
2. Leave ingredient name field empty
3. Select severity "moderate"
4. Click add allergen button

**Post-conditions:** No new UserAllergen record created

---

## Use Case 4: Product Scanning (OCR & Ingredient Extraction)

### Equivalence Class Partitioning

**Image Input:**
- Valid: Clear image with readable text, supported formats (JPG, PNG)
- Invalid: No image, corrupted image, image without text, unsupported format

**Extracted Ingredients:**
- Valid: 1-100 ingredients detected, comma/semicolon separated
- Invalid: No ingredients detected, malformed text

---

### Test Case 4.1: Successful Product Scan with Clear Image

**Test Case ID:** TC-SCAN-001

**Description:** Verify that product ingredients are correctly extracted from a clear image

**Test Inputs:**
- User ID: Authenticated user
- Image: Clear photo of ingredient list
- Expected ingredients: ["Water", "Glycerin", "Methylisothiazolinone", "Fragrance"]

**Expected Results:**
- OCR successfully extracts text from image
- Ingredients are parsed correctly
- Ingredient analysis is performed
- Results page displays detected ingredients
- Session contains scan results

**Dependencies:** User must be authenticated, Tesseract OCR installed

**Initialization:** User logged in, valid image file prepared

**Test Steps:**
1. Navigate to scan page
2. Upload clear image of ingredient list
3. Click scan button
4. Wait for processing

**Post-conditions:** Scan results stored in session, user redirected to results page

---

### Test Case 4.2: Scan with No Image Uploaded

**Test Case ID:** TC-SCAN-002

**Description:** Verify that scan fails gracefully when no image is provided

**Test Inputs:**
- User ID: Authenticated user
- Image: None (no file selected)

**Expected Results:**
- Error message displayed: "No image uploaded"
- User remains on scan page
- No processing occurs
- No session data created

**Dependencies:** User must be authenticated

**Initialization:** User logged in

**Test Steps:**
1. Navigate to scan page
2. Do not select any image file
3. Click scan button

**Post-conditions:** No scan results created, user on scan page

---

### Test Case 4.3: Scan with Unclear Image (No Ingredients Detected)

**Test Case ID:** TC-SCAN-003

**Description:** Verify handling of image where no ingredients can be detected

**Test Inputs:**
- User ID: Authenticated user
- Image: Blurry or unreadable image

**Expected Results:**
- OCR processes image but extracts no valid ingredients
- Warning message displayed: "No ingredients detected. Please try a clearer image."
- OCR text displayed to user for reference
- User remains on scan page

**Dependencies:** User must be authenticated, Tesseract OCR installed

**Initialization:** User logged in, blurry image prepared

**Test Steps:**
1. Navigate to scan page
2. Upload blurry/unclear image
3. Click scan button
4. Wait for processing

**Post-conditions:** No scan results created, OCR text shown for debugging

---

## Use Case 5: Ingredient Analysis & Allergen Detection

### Equivalence Class Partitioning

**Ingredient List:**
- Valid: 1-100 ingredients, properly formatted strings
- Invalid: Empty list, malformed ingredient names

**User Allergens:**
- Partitions: 0 allergens, 1-5 allergens, 5-20 allergens, 20+ allergens

**Known Allergens Database:**
- Partitions: Ingredient in database, ingredient not in database, synonym match

---

### Test Case 5.1: Analyze Ingredients with User Allergen Match

**Test Case ID:** TC-ANALYSIS-001

**Description:** Verify that analysis correctly identifies user's personal allergens in ingredient list

**Test Inputs:**
- User ID: Authenticated user with allergen "Fragrance" (severity: severe)
- Ingredients: ["Water", "Glycerin", "Fragrance", "Vitamin E"]

**Expected Results:**
- Analysis identifies "Fragrance" as user allergen
- Allergen marked with severity "severe"
- Result categorized in "allergens_found"
- Warning displayed prominently in results

**Dependencies:** User must have "Fragrance" in their allergen list

**Initialization:** User logged in with "Fragrance" allergen (severity: severe)

**Test Steps:**
1. Call analyze_ingredients() function
2. Pass ingredient list containing "Fragrance"
3. Review analysis results

**Post-conditions:** Analysis results contain allergen match in correct category

---

### Test Case 5.2: Analyze Ingredients with Known Database Allergen

**Test Case ID:** TC-ANALYSIS-002

**Description:** Verify that analysis identifies known allergens from database (not in user's list)

**Test Inputs:**
- User ID: Authenticated user with no personal allergens
- Ingredients: ["Water", "Methylisothiazolinone", "Glycerin"]

**Expected Results:**
- Analysis identifies "Methylisothiazolinone" as known allergen
- Result categorized in "warnings"
- Database information displayed (where found, categories, URL)
- Yellow warning color used

**Dependencies:** "Methylisothiazolinone" must be in KnownAllergen database

**Initialization:** User logged in, known allergen database loaded

**Test Steps:**
1. Call analyze_ingredients() function
2. Pass ingredient list containing "Methylisothiazolinone"
3. Review analysis results

**Post-conditions:** Analysis results contain warning with database info

---

### Test Case 5.3: Analyze Safe Ingredients (No Allergens)

**Test Case ID:** TC-ANALYSIS-003

**Description:** Verify that analysis correctly identifies all ingredients as safe

**Test Inputs:**
- User ID: Authenticated user with no personal allergens
- Ingredients: ["Water", "Glycerin", "Vitamin E", "Shea Butter"]

**Expected Results:**
- All ingredients marked as safe
- No allergens found
- No warnings displayed
- Results show green/success indicators for all ingredients

**Dependencies:** None of the ingredients are in allergen database

**Initialization:** User logged in, ingredients are safe

**Test Steps:**
1. Call analyze_ingredients() function
2. Pass safe ingredient list
3. Review analysis results

**Post-conditions:** All ingredients in "safe_ingredients" category

---

### Test Case 5.4: Analyze with Synonym Matching

**Test Case ID:** TC-ANALYSIS-004

**Description:** Verify that analysis matches allergens using synonyms

**Test Inputs:**
- User ID: Authenticated user with allergen "Fragrance"
- Ingredients: ["Water", "Parfum", "Glycerin"]
- Note: "Parfum" is a synonym for "Fragrance"

**Expected Results:**
- Analysis identifies "Parfum" as matching user allergen "Fragrance"
- Synonym matching works correctly
- Allergen displayed with user's severity level
- Warning displayed for matched ingredient

**Dependencies:** Synonym mapping exists for Fragrance/Parfum

**Initialization:** User has "Fragrance" allergen, synonym database loaded

**Test Steps:**
1. Call analyze_ingredients() function
2. Pass ingredient list with synonym "Parfum"
3. Review analysis results

**Post-conditions:** Synonym correctly matched to user allergen

---

### Test Case 5.5: Analyze Empty Ingredient List

**Test Case ID:** TC-ANALYSIS-005

**Description:** Verify handling of empty ingredient list

**Test Inputs:**
- User ID: Authenticated user
- Ingredients: [] (empty list)

**Expected Results:**
- Analysis completes without error
- No allergens found
- No warnings
- Empty or appropriate message in results

**Dependencies:** User must be authenticated

**Initialization:** User logged in

**Test Steps:**
1. Call analyze_ingredients() function
2. Pass empty ingredient list
3. Review analysis results

**Post-conditions:** Analysis returns empty results structure

---

## Test Execution Summary

### Total Test Cases: 17

**By Use Case:**
- User Registration: 3 test cases
- User Login/Authentication: 3 test cases
- Allergen Management: 3 test cases
- Product Scanning: 3 test cases
- Ingredient Analysis: 5 test cases

### Coverage:
- ✅ Valid input testing
- ✅ Invalid input testing (boundary conditions)
- ✅ Edge cases (empty inputs, duplicates)
- ✅ Error handling
- ✅ Security (password hashing)
- ✅ Database operations (CRUD)
- ✅ Complex logic (synonym matching, cross-referencing)

---

## Section 10.2: JUnit Testing Note

The automated unit tests using pytest (Python's equivalent to JUnit) are implemented in the `tests/` directory. These test cases serve as specifications for the automated tests.

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Status:** Ready for Implementation ✅
