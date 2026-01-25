# Meal Randomizer Feature - Product Requirements Document (PRD)

**Status:** MVP Specification  
**Version:** 1.0  
**Last Updated:** January 24, 2026  
**Owner:** Development Team  

---

## Executive Summary

The Meal Randomizer is a core feature that generates intelligent, randomized 7-day meal plans tailored to user preferences, dietary restrictions, and available ingredients. It integrates seamlessly with Mealie's existing Meal Planner and Shopping List, reducing weekly meal planning time to under 2 minutes while increasing meal variety and planning frequency.

---

## 1. Problem Statement

### User Pain Points
- **Decision paralysis:** Users are completely undecided and need meal suggestions
- **Routine fatigue:** Home cooks want inspiration and variety to break out of repetitive meals
- **Ingredient waste:** Users struggle to use ingredients before expiration
- **Time pressure:** Busy families need quick, efficient meal planning
- **Dietary management:** Health-conscious users need plans that match dietary and allergen requirements

### Target Users
- Busy families trying to save time on meal planning
- Home cooks seeking adventure and variety
- Health-conscious people with dietary goals
- Budget-conscious households
- All of the above

---

## 2. Solution Overview

### Core Feature
A "Randomize Week" button integrated into the Meal Planner that generates a randomized 7-day meal plan using configurable filters. Results auto-populate the Meal Planner and Shopping List with intelligent ingredient consolidation and optional substitution suggestions.

### Key Differentiators
- **Intelligent filtering:** Dietary restrictions, allergens, protein distribution, cook time, difficulty, meal type, and ingredient-expiry awareness
- **Flexible control:** Per-day regeneration, day pinning, week-as-template saving
- **Smart consolidation:** Automatic shopping list merging with overlap alerts and cheaper/seasonal alternatives
- **User feedback loop:** Ratings and "never again" tracking to improve future suggestions
- **Mobile-first:** Responsive design optimized for on-the-go planning

---

## 3. Functional Requirements

### 3.1 Core Randomization Engine

#### Input Filters (MVP)
Users can configure the following filters via the randomizer interface or saved profile:

| Filter | Type | MVP | Options/Behavior |
|--------|------|-----|------------------|
| **Dietary Restrictions** | Checkbox | ✓ | Vegetarian, Vegan, Gluten-Free, Keto, Paleo, etc. |
| **Allergens** | Checkbox | ✓ | Nuts, Dairy, Shellfish, Soy, Eggs, etc. |
| **Protein Preferences** | Custom | ✓ | Set desired count per protein type (e.g., "Chicken 3x, Fish 2x, Beef 1x, Vegetarian 1x"); option to exclude entirely |
| **Avoid Repeats (Days)** | Number | ✓ | User-configurable window (e.g., "don't repeat recipe within 7 days") |
| **Cook Time** | Buttons | ✓ | 15-min, 30-min, 60+ min bands; can select multiple |
| **Meal Type** | Checkbox | ✓ | Quick Weeknight, Slow Cooker, One-Pot, Fancy; can select multiple |
| **Difficulty** | Checkbox | ✓ | Easy, Medium, Complex; can select multiple |
| **Ingredient-Expiry** | Toggle | ✓ | Include recipes using ingredients marked to expire soon |
| **Recipe Candidate Cap** | Number | ✓ | User-adjustable limit (default 200); system remembers per user |
| **Calories/Macros** | Range | ✗ | Stretch phase |
| **Budget/Cost Hints** | Toggle | ✗ | Stretch phase |

#### Output
- **7-day meal plan** with one recipe per day for the week starting from the selected date
- **Shopping list** auto-populated and consolidated by ingredient
- **Ingredient overlap alerts:** (e.g., "Chicken appears in Monday, Wednesday, Friday meals—buy in bulk")
- **Substitution suggestions:** Cheaper or seasonal ingredient swaps for user approval

#### Behavior

##### Balance & Variety
- **No excessive repetition:** Avoid suggesting the same recipe category (pasta, salad, protein prep) more than once per week
- **Protein distribution:** Honor user-specified protein counts (e.g., if user says "Chicken 3x," exactly 3 recipes with chicken appear; if "no pork," all pork recipes are excluded)
- **Repeat avoidance:** Never suggest a recipe the user cooked recently; default to user-configurable window (e.g., "don't repeat within 14 days")

##### Small Library Handling (<20 recipes)
- If filters/preferences reduce candidate pool below a viable number:
  1. **Auto-broaden:** Progressively relax least-critical filters (e.g., difficulty, then cook time)
  2. **If still short:** Prompt user: *"Only X recipes match your criteria. Would you like to broaden filters? [Options: Adjust Difficulty / Relax Allergens / Disable Expiry Filter]"*
  3. **Do not automatically repeat** without explicit user consent

##### Large Library Performance
- **Candidate cap:** If recipe database exceeds user cap (default 200), system samples randomly from recent recipes
- **UX confirmation:** If sampling occurs, show: *"Using 200 most recent recipes. [Change limit]"*
- **Cache last result:** Store result for 5 minutes; "Regenerate" button reuses cached data unless filters change
- **Server-side execution:** All randomization logic runs server-side for consistency and freshness

---

### 3.2 User Interface (Meal Planner Integration)

#### Meal Planner Page
1. **"Randomize Week" Button**
   - Primary action button in Meal Planner header
   - Opens modal or slides out filter panel

2. **Filter Panel**
   - All filters listed above (dietary, allergens, proteins, cook time, etc.)
   - Collapsible sections for organization
   - "Apply Filters" and "Cancel" buttons
   - Option to "Save as Default" (stores in user profile for future runs)

3. **Results View**
   - **All 7 days displayed at once** (Monday–Sunday grid)
   - Each day shows: recipe name, image thumbnail, cook time, difficulty badge, dietary tags
   - **Per-day actions:**
     - **Pin icon:** Lock day so regenerate doesn't change it
     - **Regenerate icon:** Re-roll this day only (respects pinned days and current filters)
     - **Swap icon:** Open modal to manually swap with a different recipe
   
4. **Week-level Actions**
   - **"Regenerate All"** button: Reroll all unpinned days
   - **"Save as Template"** button: Save this week's selection for reuse
   - **"Apply to Planner"** button: Confirm and populate Meal Planner + Shopping List
   - **"Cancel"** button: Exit without changes

#### Shopping List Integration
- **Auto-generated:** Upon "Apply to Planner," all ingredients from the 7 randomized recipes are added to Shopping List
- **Consolidation:** Group by ingredient (e.g., "Chicken" appears once with total quantity from all recipes using it)
- **Overlap alerts:** Show note: *"Chicken used in 3 meals—buy 3 lbs total"*
- **Substitution suggestions:** Display as collapsible toggles: *"Use ground turkey instead? (10% cheaper, higher protein)"* [Accept] [Dismiss]
- **Allergen warning:** Flag any shopping items with selected allergens

---

### 3.3 Per-User Profiles & Preferences

#### Profile Storage
- **Default filter set:** Each user's profile stores one default filter configuration
- **Recipe candidate cap:** Remember user's chosen cap (e.g., 150 recipes)
- **Repeat-avoid window:** Remember preferred repeat-avoid duration (e.g., 7 days)

#### Per-Run Overrides
- Users can modify filters before generating without changing their saved profile
- "Save as Default" button lets users update profile if they like the new settings

#### Templates
- **Save as Template:** Users can save a generated week as a reusable template
- **Load Template:** List saved templates and apply one to override randomization

---

### 3.4 Feedback & Learning

#### Rating System
- After cooking a randomized meal, users can rate it:
  - **Thumbs Up:** "Loved it" → improves ranking for future suggestions
  - **Thumbs Down:** "Didn't like it" → reduce likelihood in future randomizations
  - **"Never Again":** Recipe is blacklisted for this user

#### Tracking
- **Metadata stored per user:**
  - Last cooked date (for repeat-avoid window)
  - User rating (👍 / 👎 / 🚫)
  - Frequency of cooking (impacts future weighting)

#### Influence
- **Favorite recipes:** Higher probability in future randomizations
- **Blacklisted recipes:** Never suggested again
- **Group popularity:** If family/group members frequently rate a recipe highly, slightly boost for other group members (opt-in)

---

## 4. Technical Architecture

### 4.1 Backend (Python/FastAPI)

#### New Endpoints

##### `POST /api/v1/meals/randomizer/generate`
- **Input:**
  ```json
  {
    "start_date": "2026-01-27",
    "filters": {
      "dietary_restrictions": ["vegetarian"],
      "allergens": ["nuts", "dairy"],
      "protein_preferences": {
        "chicken": 3,
        "fish": 2,
        "beef": 0
      },
      "avoid_repeat_days": 7,
      "cook_time_bands": ["15-30", "30-60"],
      "meal_types": ["quick_weeknight", "fancy"],
      "difficulty_levels": ["easy", "medium"],
      "include_expiring_ingredients": true,
      "recipe_candidate_cap": 200
    }
  }
  ```
- **Output:**
  ```json
  {
    "week_plan": [
      {
        "day": "Monday",
        "recipe_id": "abc123",
        "recipe_name": "Grilled Chicken Salad",
        "image_url": "...",
        "cook_time": 20,
        "difficulty": "easy",
        "ingredients": [...]
      },
      ...
    ],
    "shopping_consolidated": {...},
    "substitution_suggestions": [...],
    "cached": false
  }
  ```

##### `POST /api/v1/meals/randomizer/save-template`
- Save a generated week as a template for reuse

##### `GET /api/v1/meals/randomizer/templates`
- List user's saved templates

##### `POST /api/v1/meals/randomizer/rate-recipe`
- User submits rating: `{"recipe_id": "...", "rating": "up" | "down" | "never_again"}`

#### Data Model Changes
- **New table:** `RecipeRating` (user_id, recipe_id, rating, created_at, updated_at)
- **New table:** `RandomizerTemplate` (user_id, template_name, week_plan_json, created_at)
- **New column on User:** `randomizer_preferences_json` (stores default filters, cap, repeat window)
- **Extend Recipe table:** Add optional fields for expiry tracking (ingredient_expiry_date, if not already present)

#### Algorithm (Core Randomizer Logic)
1. **Fetch recipe candidates:**
   - Query recipes matching user's dietary/allergen/cook-time/difficulty/meal-type filters
   - Apply recipe candidate cap; sample if needed
   - Exclude recipes in repeat-avoid window (query cooking history)
   - Exclude user's "never again" recipes
   - Order by user rating (favorites first)

2. **Protein distribution:**
   - For each day of the week:
     - Select a recipe matching next-needed protein type from user's distribution
     - Decrement protein count
     - If all proteins exhausted, return error (too few recipes) → prompt user to broaden

3. **Ingredient-expiry filter (if enabled):**
   - Prioritize recipes using ingredients marked to expire soon
   - If insufficient expiry-matching recipes, fill remainder with regular candidates

4. **Balance:**
   - Avoid clustering similar recipe types (pasta, salad, etc.) on consecutive days
   - Validate no recipe repeats within avoid window

5. **Return:** Week plan + consolidated shopping list + suggestions

---

### 4.2 Frontend (Vue.js)

#### New Components
- **`MealRandomizer.vue`** (main modal/panel)
  - Filter form
  - Results grid (7-day display)
  - Actions (regenerate, pin, save template)

- **`FilterPanel.vue`** (collapsible filters)
  - Dietary restrictions, allergens, protein controls, cook time, meal type, difficulty, expiry toggle
  - Default save option

- **`ResultsGrid.vue`** (7-day meal display)
  - Day cards with pin/regenerate/swap buttons

- **`ShoppingListIntegration.vue`** (modal/preview)
  - Consolidated ingredients
  - Substitution toggles
  - "Confirm & Apply" action

- **`TemplateManager.vue`** (save/load templates)
  - List saved templates
  - Load/delete actions

#### Mobile-First Design
- Responsive breakpoints: mobile (< 768px), tablet (768–1024px), desktop (> 1024px)
- Touch-friendly buttons and spacing
- Vertical stacking of filter sections on mobile
- Swipeable day cards (optional nice-to-have)

---

### 4.3 Data Flow
```
User clicks "Randomize Week"
  ↓
Opens filter modal
  ↓
User configures filters (or uses defaults)
  ↓
Clicks "Generate" → POST /api/v1/meals/randomizer/generate
  ↓
Backend: fetch candidates, apply filters, protein distribution, balance, return plan
  ↓
Frontend: display 7-day results grid
  ↓
User can: pin days, regenerate, save template
  ↓
Clicks "Apply to Planner" → auto-populate Meal Planner + Shopping List
  ↓
User reviews shopping list & confirms substitutions
  ↓
Confirmed → saved to Meal Planner + Shopping List DB
```

---

## 5. User Stories

### Story 1: Quick Weekly Plan
> As a busy parent, I want to generate a complete week of meals in under 2 minutes so I can spend less time planning and more time with my family.

**Acceptance Criteria:**
- User opens Meal Planner, clicks "Randomize Week"
- Pre-filled with user's saved filters (dietaries, proteins, cook times)
- Results appear in < 3 seconds
- One click applies to Meal Planner + Shopping List
- Total flow: < 2 minutes

### Story 2: Ingredient Expiry Awareness
> As someone who wastes food, I want the randomizer to prioritize recipes using ingredients I have that are about to expire so I use them before throwing them away.

**Acceptance Criteria:**
- User marks ingredients with expiry dates (existing Mealie feature or extension)
- Enables "Use Expiring Ingredients" toggle in randomizer
- Generated plan prioritizes recipes using those ingredients
- If insufficient matches, user is prompted to relax the filter

### Story 3: Protein Variety
> As a health-conscious cook, I want to specify exactly how many times I eat each protein this week so I can balance my diet.

**Acceptance Criteria:**
- Randomizer shows protein control: "Chicken: 3x, Fish: 2x, Beef: 1x, Vegetarian: 1x"
- Generated plan honors these counts exactly
- If not enough recipes match, system errors and suggests broadening filters

### Story 4: Day Tweaks
> As someone who has a dinner plan already on Wednesday, I want to pin that day and regenerate only the others so I don't lose my commitment.

**Acceptance Criteria:**
- User clicks pin icon on Wednesday card
- Clicks "Regenerate All" → only Mon, Tue, Thu–Sun regenerate
- Wednesday meal stays locked

### Story 5: Reusable Plans
> As a planner, I want to save a week I loved and reuse it on different weeks without re-randomizing.

**Acceptance Criteria:**
- After generating, user clicks "Save as Template" → prompted for name
- Stored template appears in "Load Template" dropdown
- User can load and apply any saved template anytime

### Story 6: Smart Shopping
> As a home cook, I want the randomizer to show me ingredient overlaps across meals so I buy smarter.

**Acceptance Criteria:**
- Randomized week generates shopping list with consolidated ingredients
- System alerts: "Chicken appears in 3 meals—buy 3 lbs total"
- Optional: suggests cheaper/seasonal swaps user can toggle

### Story 7: Learning from Feedback
> As a long-time user, I want my meal ratings to improve future suggestions so I see recipes I love more often.

**Acceptance Criteria:**
- After cooking, user rates meal (👍 / 👎 / 🚫)
- Thumbs-up recipes have higher probability in future randomizations
- "Never again" recipes never reappear
- System learns over time

---

## 6. Non-Functional Requirements

### Performance
- **Response time:** Randomization generates results in < 3 seconds for libraries up to 500 recipes
- **Caching:** Cache results for 5 minutes; reuse on "regenerate" unless filters change
- **Candidate cap:** Default 200; user-adjustable; system prompts if sampling

### Scalability
- **Server-side execution:** Offload all randomization logic to backend for consistency
- **Database:** Efficient indexing on recipe filters (dietary, allergens, cook time, difficulty)
- **API rate limits:** Standard Mealie rate limiting applies

### Reliability
- **Error handling:** Graceful fallback if insufficient recipes match filters; prompt user to broaden
- **Data integrity:** All randomizer selections logged for feedback/learning
- **Offline behavior:** Feature requires online access (API calls); no offline mode

### Accessibility
- **Mobile-first:** Responsive design optimized for phones and tablets
- **Voice-over:** Standard screen reader support (WCAG 2.1 AA)
- **No voice input:** Not a requirement for MVP

---

## 7. Success Metrics

### Primary Metric
- **Weekly meal planning time: < 2 minutes** (measured from randomizer launch to Meal Planner confirmation)

### Secondary Metrics
- **Meal plan variety:** % increase in distinct recipes per user, week-to-week
- **Randomizer adoption:** % of users who run the feature at least once per month
- **Feedback engagement:** % of randomized meals that receive a rating within 2 weeks
- **Repeat usage:** % of users who return to randomizer multiple times in a month
- **Template reuse:** Avg number of templates saved and loaded per user per month

### Health Metrics
- **Error rate:** % of randomization requests that fail or require filter broadening
- **Performance:** P95 API response time for randomization (target: < 2s)
- **Cache hit rate:** % of "regenerate" requests served from cache

---

## 8. Stretch Features (Post-MVP)

1. **Multiple Profiles:** Save and switch between multiple filter profiles (e.g., "Weeknight Quick," "Weekend Fancy," "Keto Month")
2. **Macros/Calories:** Filter by calorie range and macro targets (protein, carbs, fats)
3. **Budget Hints:** Show cost of meals and suggest cheaper alternatives
4. **Advanced Substitutions:** Auto-suggest swaps with estimated cost savings
5. **Popularity Influence:** Boost recipes popular with user's family/group
6. **Cuisine Filters:** Filter by cuisine type (Italian, Asian, Mediterranean, etc.)
7. **Seasonal & Trending:** Suggest seasonal recipes and trending dishes
8. **Dish-Level Randomization:** Expand from week → day → single meal randomization

---

## 9. Implementation Timeline

### Phase 1: MVP (Weeks 1–4)
- Backend: Randomizer engine, endpoints, profile storage
- Frontend: Filter modal, results grid, Meal Planner integration
- Testing: Unit tests (backend), integration tests (API), UI tests (frontend)

### Phase 2: Polish & Learning (Weeks 5–6)
- User feedback rating system
- Favorite/never-again tracking
- Caching layer
- Performance optimization

### Phase 3: Stretch Features (Post-launch)
- Multiple profiles, macros, budget hints, advanced substitutions, etc.

---

## 10. Appendices

### A. Filter Logic Examples

#### Example 1: Basic Week Generation
**User Input:**
- Dietary: Vegetarian
- Allergens: Nuts
- Cook Time: 15–60 min
- Protein: Tofu 3x, Lentils 3x, Chickpeas 1x

**Output:** 7-day plan with no meat, no nuts, all under 60 min, exact protein distribution

#### Example 2: Small Library with Broadening
**User's Recipe Library:** 15 recipes  
**User Filters:** Gluten-free, Keto, Chicken-only

**Backend Response:**
1. Query: No recipes match (0 gluten-free keto recipes with chicken)
2. Prompt User: "Only 3 recipes match. Broaden filters? [Disable Keto / Disable Gluten-free / Allow other proteins]"
3. User clicks "Allow other proteins"
4. Query: 12 recipes match
5. Generate and return week plan

#### Example 3: Large Library with Sampling
**User's Library:** 2,000 recipes  
**User Cap:** 150

**Backend Response:**
1. Query: 2,000 recipes match basic filters
2. Sample 150 most recent recipes
3. Return: "Using 150 most recent recipes. [Change limit]"
4. Generate and return week plan

---

### B. API Response Example

```json
{
  "status": "success",
  "week_plan": [
    {
      "day": "Monday",
      "date": "2026-01-27",
      "recipe_id": "rec_abc123",
      "recipe_name": "Vegetable Stir-Fry with Tofu",
      "image_url": "https://...",
      "cook_time_minutes": 25,
      "difficulty": "easy",
      "dietary_tags": ["vegetarian", "gluten_free"],
      "ingredients": [
        {"name": "Tofu", "quantity": 1, "unit": "lb"},
        {"name": "Broccoli", "quantity": 2, "unit": "cups"},
        ...
      ]
    },
    ...
  ],
  "shopping_consolidated": {
    "Tofu": {"quantity": 3, "unit": "lb", "used_in_days": ["Monday", "Wednesday", "Friday"]},
    "Broccoli": {"quantity": 5, "unit": "cups", "used_in_days": ["Monday", "Thursday"]},
    ...
  },
  "substitution_suggestions": [
    {
      "ingredient": "Olive Oil",
      "original_price_estimate": 12,
      "substitute": "Avocado Oil",
      "substitute_price_estimate": 14,
      "reason": "Higher smoke point for stir-frying"
    }
  ],
  "metadata": {
    "generated_at": "2026-01-24T15:32:00Z",
    "cached": false,
    "filters_applied": {...},
    "recipes_searched": 200
  }
}
```

---

## 11. Approval Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | — | — | — |
| Engineering Lead | — | — | — |
| Design Lead | — | — | — |

---

**Document History:**
- **v1.0** (2026-01-24): Initial MVP spec created from discovery session
