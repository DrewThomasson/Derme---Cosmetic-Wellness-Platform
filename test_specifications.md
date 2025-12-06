# Test Specifications

## Feature 1: Analyze Product Ingredients
**Function**: `analyze_ingredients(ingredients_list, user_id)`
**Description**: Analyzes a list of ingredients against a user's known allergens, potential allergens, and a global database of known allergens.

### Equivalence Partitions

#### Input: `ingredients_list` (List[str])
1.  **Empty List**: `[]`
2.  **Safe List**: List containing only ingredients that are not allergens.
3.  **User Allergen (Direct)**: List containing an ingredient that matches a user's allergen exactly.
4.  **User Allergen (Synonym)**: List containing an ingredient that is a synonym for a user's allergen.
5.  **Known Allergen**: List containing an ingredient that is in the global `KnownAllergen` database but not in user's list.
6.  **Potential Allergen**: List containing an ingredient identified as a potential allergen for the user.
7.  **Mixed List**: List containing a combination of safe ingredients and allergens.

#### Input: `user_id` (int)
1.  **User with No Allergens**: User ID exists but has no `UserAllergen` records.
2.  **User with Allergens**: User ID exists and has `UserAllergen` records.

### Test Cases

| ID | Test Case Name | Input `ingredients_list` | Input `user_id` Context | Expected Output |
| :--- | :--- | :--- | :--- | :--- |
| TC-01 | Analyze Empty List | `[]` | User with allergens | `{'allergens_found': [], 'safe_ingredients': [], ...}` |
| TC-02 | Analyze Safe Ingredients | `['Water', 'Glycerin']` | User with allergens (not Water/Glycerin) | `{'safe_ingredients': ['Water', 'Glycerin'], ...}` |
| TC-03 | Analyze User Allergen (Direct) | `['Peanut']` | User allergic to 'Peanut' | `{'allergens_found': [{'name': 'Peanut', 'severity': 'severe'}], ...}` |
| TC-04 | Analyze User Allergen (Synonym) | `['Arachis hypogaea']` | User allergic to 'Peanut' (synonym exists) | `{'allergens_found': [{'name': 'Arachis hypogaea', 'severity': 'severe'}], ...}` |
| TC-05 | Analyze Known Allergen | `['Parabens']` | User not allergic, 'Parabens' in KnownAllergen DB | `{'warnings': [{'name': 'Parabens', ...}], ...}` |
| TC-06 | Analyze Mixed List | `['Water', 'Peanut']` | User allergic to 'Peanut' | `{'safe_ingredients': ['Water'], 'allergens_found': [{'name': 'Peanut', ...}], ...}` |

---

## Feature 2: Verify Security Answer
**Method**: `User.check_security_answer(question_num, answer)`
**Description**: Verifies if the provided answer matches the stored hashed answer for a specific security question.

### Equivalence Partitions

#### Input: `question_num` (int)
1.  **Valid Question Number**: 1, 2, or 3 (assuming these are set).
2.  **Invalid Question Number**: e.g., 99 (should handle gracefully or raise error, based on implementation). *Note: Implementation uses getattr which might raise AttributeError, but we will test valid usage primarily.*

#### Input: `answer` (str)
1.  **Correct Answer (Exact)**: Matches the stored answer exactly.
2.  **Correct Answer (Case/Whitespace)**: Matches after normalization (lowercase, strip).
3.  **Incorrect Answer**: Does not match.
4.  **Empty Answer**: `""` or `None`.

### Test Cases

| ID | Test Case Name | Input `question_num` | Input `answer` | Context | Expected Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC-07 | Verify Correct Answer | 1 | "Fido" | User Q1 answer is "Fido" | `True` |
| TC-08 | Verify Correct Answer Case/Space | 1 | "  fido  " | User Q1 answer is "Fido" | `True` |
| TC-09 | Verify Incorrect Answer | 1 | "Rex" | User Q1 answer is "Fido" | `False` |
| TC-10 | Verify Empty Answer | 1 | "" | User Q1 answer is "Fido" | `False` |
| TC-11 | Verify Unset Question | 2 | "Anything" | User Q2 is not set | `False` (or handled gracefully) |
