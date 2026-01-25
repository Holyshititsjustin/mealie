# Meal Randomizer - Build Plan & Implementation Sequence

**Status:** Ready for Development  
**Last Updated:** January 24, 2026  
**Target Platform:** Mealie v3.9.x  

---

## Overview

This document outlines the technical build plan for the Meal Randomizer feature in numerical/sequential order. Each section represents a phase, and tasks are ordered for optimal dependency management.

---

## Phase 1: Backend Data Models & Database

### 1.1 Database Migrations

**File:** `mealie/db/migrations/[timestamp]_meal_randomizer_tables.py`

**Purpose:** Create new tables for:
- `recipe_ratings` - User ratings for randomized recipes (👍 / 👎 / 🚫)
- `randomizer_templates` - User-saved meal plan templates
- `randomizer_preferences` - User profile defaults (filters, caps, repeat windows)

**Tables to Create:**
```sql
-- recipe_ratings
CREATE TABLE recipe_ratings (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL FOREIGN KEY references users(id),
  recipe_id UUID NOT NULL FOREIGN KEY references recipes(id),
  rating ENUM('up', 'down', 'never_again'),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, recipe_id)  -- One rating per user per recipe
);

-- randomizer_templates
CREATE TABLE randomizer_templates (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL FOREIGN KEY references users(id),
  template_name VARCHAR(255),
  week_plan_json JSONB,  -- Serialized week plan
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- randomizer_preferences
CREATE TABLE randomizer_preferences (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL FOREIGN KEY references users(id) UNIQUE,
  filter_defaults JSONB,  -- Default filter configuration
  recipe_candidate_cap INT DEFAULT 200,
  avoid_repeat_days INT DEFAULT 7,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Dependencies:** None (new tables)

---

### 1.2 SQLAlchemy ORM Models

**File:** `mealie/models/meal_randomizer.py`

**Purpose:** Define ORM models for the three new tables

**Key Classes:**
- `RecipeRating` - Maps to recipe_ratings table
- `RandomizerTemplate` - Maps to randomizer_templates table
- `RandomizerPreferences` - Maps to randomizer_preferences table

**Example Structure:**
```python
class RecipeRating(BaseMixin, Model):
    __tablename__ = "recipe_ratings"
    user_id: str = Column(String, ForeignKey("user.id"), nullable=False)
    recipe_id: str = Column(String, ForeignKey("recipe.id"), nullable=False)
    rating: str = Column(String, nullable=False)  # 'up', 'down', 'never_again'
    
    user = relationship("User", back_populates="recipe_ratings")
    recipe = relationship("Recipe")
    __table_args__ = (UniqueConstraint('user_id', 'recipe_id'),)

class RandomizerTemplate(BaseMixin, Model):
    __tablename__ = "randomizer_templates"
    user_id: str = Column(String, ForeignKey("user.id"), nullable=False)
    template_name: str = Column(String, nullable=False)
    week_plan_json: dict = Column(JSON, nullable=False)
    
    user = relationship("User", back_populates="randomizer_templates")

class RandomizerPreferences(BaseMixin, Model):
    __tablename__ = "randomizer_preferences"
    user_id: str = Column(String, ForeignKey("user.id"), unique=True, nullable=False)
    filter_defaults: dict = Column(JSON, nullable=True)
    recipe_candidate_cap: int = Column(Integer, default=200)
    avoid_repeat_days: int = Column(Integer, default=7)
    
    user = relationship("User", back_populates="randomizer_preferences")
```

**Dependencies:** 
- Mealie's existing models (User, Recipe, BaseMixin)
- Migration 1.1 (tables must exist)

---

### 1.3 Update User Model

**File:** `mealie/models/user.py`

**Purpose:** Add relationships to new models

**Changes:**
```python
# Add to User class:
recipe_ratings = relationship("RecipeRating", back_populates="user", cascade="all, delete-orphan")
randomizer_templates = relationship("RandomizerTemplate", back_populates="user", cascade="all, delete-orphan")
randomizer_preferences = relationship("RandomizerPreferences", back_populates="user", uselist=False)
```

**Dependencies:** Models 1.2

---

## Phase 2: API Schemas & Request/Response Models

### 2.1 Randomizer Request/Response Schemas

**File:** `mealie/schemas/meal_randomizer.py`

**Purpose:** Define Pydantic models for API validation

**Key Schemas:**
- `ProteinPreference` - User's protein distribution (e.g., {"chicken": 3, "fish": 2})
- `RandomizerFilters` - All filter parameters
- `RandomizerRequest` - POST request to generate meals
- `RecipeResultCard` - Single day's recipe in response
- `RandomizerResponse` - Complete 7-day result
- `ConsolidatedIngredient` - Shopping list ingredient with metadata
- `SubstitutionSuggestion` - Ingredient swap option
- `RecipeRatingRequest` - POST request to rate a recipe
- `RandomizerTemplateRequest` - POST request to save template
- `RandomizerTemplateResponse` - GET response for saved templates

**Example:**
```python
from pydantic import BaseModel
from typing import Dict, List, Optional

class ProteinPreference(BaseModel):
    protein_type: str  # "chicken", "fish", "beef", "pork", "tofu", "lentils", etc.
    count: int  # How many times this week

class RandomizerFilters(BaseModel):
    dietary_restrictions: List[str] = []  # "vegetarian", "vegan", "gluten_free", etc.
    allergens: List[str] = []  # "nuts", "dairy", "shellfish", etc.
    protein_preferences: List[ProteinPreference]
    avoid_repeat_days: int = 7
    cook_time_bands: List[str] = []  # "15-30", "30-60", "60+"
    meal_types: List[str] = []  # "quick_weeknight", "slow_cooker", "one_pot", "fancy"
    difficulty_levels: List[str] = []  # "easy", "medium", "complex"
    include_expiring_ingredients: bool = False
    recipe_candidate_cap: int = 200

class RandomizerRequest(BaseModel):
    start_date: str  # ISO format date
    filters: RandomizerFilters
    pinned_days: Optional[Dict[str, str]] = {}  # {"Monday": "recipe_id", ...}

class RecipeResultCard(BaseModel):
    day: str  # "Monday"
    date: str  # ISO format
    recipe_id: str
    recipe_name: str
    cook_time_minutes: int
    difficulty: str
    dietary_tags: List[str]
    image_url: Optional[str]

class ConsolidatedIngredient(BaseModel):
    name: str
    quantity: float
    unit: str
    used_in_days: List[str]  # ["Monday", "Wednesday", "Friday"]
    expiry_date: Optional[str] = None

class SubstitutionSuggestion(BaseModel):
    ingredient: str
    reason: str  # "cheaper", "seasonal", "higher_protein"
    suggested_alternative: str
    estimated_savings: Optional[float] = None

class RandomizerResponse(BaseModel):
    status: str = "success"
    week_plan: List[RecipeResultCard]
    shopping_consolidated: Dict[str, ConsolidatedIngredient]
    substitution_suggestions: List[SubstitutionSuggestion]
    metadata: Dict
    cached: bool

class RecipeRatingRequest(BaseModel):
    recipe_id: str
    rating: str  # "up", "down", "never_again"

class RandomizerTemplateRequest(BaseModel):
    template_name: str
    week_plan: List[RecipeResultCard]

class RandomizerTemplateResponse(BaseModel):
    id: str
    template_name: str
    created_at: str
    recipe_names: List[str]  # Quick preview
```

**Dependencies:** Mealie's existing schemas (User, Recipe)

---

## Phase 3: Core Randomizer Service (Logic)

### 3.1 Recipe Filtering & Query Service

**File:** `mealie/services/recipe_filter_service.py`

**Purpose:** Query recipes from database based on filters

**Key Functions:**
- `get_recipes_by_dietary_restriction(user_id, restrictions)` - Filter by dietary tags
- `get_recipes_by_allergens(allergens)` - Filter by allergen tags
- `get_recipes_by_cook_time(cook_time_bands)` - Filter by cook time ranges
- `get_recipes_by_difficulty(difficulties)` - Filter by difficulty
- `get_recipes_by_meal_type(meal_types)` - Filter by meal type tags
- `get_recipes_with_expiring_ingredients(user_id, days_until_expiry=3)` - Recipes using ingredients marked to expire
- `exclude_recent_recipes(user_id, days_window)` - Exclude recipes cooked recently
- `exclude_never_again(user_id)` - Exclude user's "never again" recipes
- `get_recipes_by_protein(protein_type)` - Filter by primary protein in recipe
- `apply_candidate_cap(recipes, cap)` - Sample if exceeds cap

**Key Logic:**
```python
def query_candidate_recipes(
    user_id: str,
    filters: RandomizerFilters,
    database_session
) -> List[Recipe]:
    """
    Apply all filters sequentially and return candidate recipes.
    Order by: favorites first, then recent cooks, then random
    """
    query = database_session.query(Recipe)
    
    # Apply filters
    if filters.dietary_restrictions:
        query = query.join(Recipe.tags).filter(Tag.name.in_(filters.dietary_restrictions))
    
    if filters.allergens:
        query = query.filter(~Recipe.tags.any(Tag.name.in_(filters.allergens)))
    
    if filters.cook_time_bands:
        # Filter by cook time ranges
        ...
    
    # Exclude recent recipes
    query = exclude_recent_recipes(query, user_id, filters.avoid_repeat_days)
    
    # Exclude never_again
    never_again_ids = get_never_again_recipes(user_id)
    query = query.filter(Recipe.id.notin_(never_again_ids))
    
    # Apply candidate cap
    recipes = query.all()
    if len(recipes) > filters.recipe_candidate_cap:
        recipes = random.sample(recipes, filters.recipe_candidate_cap)
    
    # Order by user preferences (favorites first)
    recipes = sort_by_user_preference(recipes, user_id)
    
    return recipes
```

**Dependencies:** Models (User, Recipe), Schemas

---

### 3.2 Meal Randomizer Service (Core Algorithm)

**File:** `mealie/services/meal_randomizer_service.py`

**Purpose:** Main randomization algorithm

**Key Functions:**
- `generate_week_plan(user_id, filters, start_date, pinned_days)` - Main algorithm
- `distribute_proteins(candidates, protein_preferences)` - Assign recipes to meet protein counts
- `apply_balance_rules(week_plan)` - Avoid clustering similar recipes
- `consolidate_shopping_list(week_plan)` - Merge ingredients across week
- `generate_substitution_suggestions(consolidated_list)` - Cheaper/seasonal swaps
- `cache_result(user_id, result)` - Store last result
- `get_cached_result(user_id)` - Retrieve cached result

**Core Algorithm (Pseudocode):**
```python
def generate_week_plan(
    user_id: str,
    filters: RandomizerFilters,
    start_date: str,
    pinned_days: Dict[str, str] = None
) -> RandomizerResponse:
    """
    Main algorithm: generate 7-day meal plan
    """
    
    # Step 1: Get candidate recipes (filtered, capped, ordered)
    candidates = query_candidate_recipes(user_id, filters)
    
    if len(candidates) < 7:
        # Broaden filters and retry
        candidates = broaden_filters_and_retry(user_id, filters)
        if len(candidates) < 7:
            raise NotEnoughRecipesError("Prompt user to relax filters")
    
    # Step 2: Create week plan with pinned days
    week_plan = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    pinned_days = pinned_days or {}
    unassigned_days = [d for d in days if d not in pinned_days]
    
    # Step 3: Distribute proteins across unassigned days
    protein_queue = create_protein_queue(filters.protein_preferences)
    
    for day in unassigned_days:
        protein_needed = protein_queue.pop(0)
        
        # Find recipe matching protein, avoiding recent/blacklisted
        recipe = select_recipe_for_protein(
            candidates, 
            protein_needed, 
            user_id, 
            existing_week_plan=week_plan
        )
        
        week_plan[day] = recipe
    
    # Step 4: Apply balance rules (no 3+ pasta, etc.)
    week_plan = apply_balance_rules(week_plan, candidates)
    
    # Step 5: Add pinned days
    week_plan.update(pinned_days)
    
    # Step 6: Consolidate shopping list
    shopping = consolidate_shopping_list([r for r in week_plan.values()])
    
    # Step 7: Generate substitution suggestions
    substitutions = generate_substitution_suggestions(shopping)
    
    # Step 8: Cache result
    cache_result(user_id, week_plan)
    
    return RandomizerResponse(
        week_plan=week_plan,
        shopping_consolidated=shopping,
        substitution_suggestions=substitutions,
        cached=False
    )
```

**Dependencies:** RecipeFilterService, Schemas, Models

---

### 3.3 Ingredient & Shopping Service

**File:** `mealie/services/ingredient_service.py`

**Purpose:** Shopping list consolidation and substitution logic

**Key Functions:**
- `consolidate_ingredients(recipes)` - Merge ingredients, sum quantities, group by usage
- `detect_overlaps(consolidated_ingredients)` - Find ingredients used across multiple days
- `get_ingredient_substitutes(ingredient_name)` - Query known substitutes
- `estimate_ingredient_cost(ingredient_name)` - Basic cost estimation
- `check_expiring_ingredients(user_id, ingredient_list, days_until_expiry)` - Mark expiring items

**Dependencies:** Models, Schemas

---

## Phase 4: API Endpoints & Routes

### 4.1 Randomizer Routes

**File:** `mealie/routes/meals/meal_randomizer.py`

**Purpose:** Define all REST API endpoints

**Endpoints:**

```python
# POST /api/v1/meals/randomizer/generate
# Generate a randomized 7-day meal plan
# Input: RandomizerRequest
# Output: RandomizerResponse

# GET /api/v1/meals/randomizer/templates
# List user's saved templates
# Output: List[RandomizerTemplateResponse]

# POST /api/v1/meals/randomizer/templates
# Save current week as template
# Input: RandomizerTemplateRequest
# Output: RandomizerTemplateResponse

# GET /api/v1/meals/randomizer/templates/{template_id}
# Get a specific template
# Output: RandomizerTemplateResponse

# DELETE /api/v1/meals/randomizer/templates/{template_id}
# Delete a saved template

# POST /api/v1/meals/randomizer/rate
# Rate a randomized recipe
# Input: RecipeRatingRequest
# Output: {"status": "success"}

# GET /api/v1/meals/randomizer/preferences
# Get user's randomizer preferences
# Output: RandomizerPreferences

# PUT /api/v1/meals/randomizer/preferences
# Update user's randomizer preferences
# Input: RandomizerPreferences (partial update)
# Output: RandomizerPreferences
```

**Example Endpoint Structure:**
```python
from fastapi import APIRouter, Depends
from mealie.schemas.meal_randomizer import RandomizerRequest, RandomizerResponse

router = APIRouter(tags=["meals", "randomizer"])

@router.post("/api/v1/meals/randomizer/generate", response_model=RandomizerResponse)
async def generate_randomizer(
    request: RandomizerRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Generate a randomized 7-day meal plan"""
    try:
        result = meal_randomizer_service.generate_week_plan(
            user_id=current_user.id,
            filters=request.filters,
            start_date=request.start_date,
            pinned_days=request.pinned_days
        )
        return result
    except NotEnoughRecipesError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Dependencies:** Services (3.1, 3.2, 3.3), Schemas, Models

---

### 4.2 Register Routes in Main App

**File:** `mealie/app.py` (existing file, modify)

**Change:**
```python
# Add meal randomizer router to the main app
from mealie.routes.meals.meal_randomizer import router as randomizer_router

app.include_router(randomizer_router)
```

**Dependencies:** Routes 4.1

---

## Phase 5: Frontend Components & UI

### 5.1 Filter Panel Component

**File:** `frontend/components/MealRandomizer/FilterPanel.vue`

**Purpose:** Collapsible filter form with all meal randomizer filters

**Key Props/Data:**
- `initialFilters` - Pre-filled filter values
- `onApply` - Callback when user clicks "Apply Filters"
- `onSaveDefault` - Callback to save as default profile

**Structure:**
```vue
<template>
  <div class="filter-panel">
    <!-- Dietary Restrictions Section -->
    <section>
      <h3>Dietary Restrictions</h3>
      <checkbox-group 
        v-model="filters.dietary_restrictions"
        :options="['Vegetarian', 'Vegan', 'Gluten-Free', 'Keto', ...]"
      />
    </section>
    
    <!-- Allergens Section -->
    <section>
      <h3>Allergens to Avoid</h3>
      <checkbox-group 
        v-model="filters.allergens"
        :options="['Nuts', 'Dairy', 'Shellfish', ...]"
      />
    </section>
    
    <!-- Protein Preferences -->
    <section>
      <h3>Protein Distribution</h3>
      <protein-distributor 
        v-model="filters.protein_preferences"
      />
    </section>
    
    <!-- Cook Time, Meal Type, Difficulty, etc. -->
    <!-- ... more sections ... -->
    
    <!-- Action Buttons -->
    <div class="actions">
      <button @click="applyFilters" class="btn-primary">Generate Plan</button>
      <button @click="saveAsDefault" class="btn-secondary">Save as Default</button>
      <button @click="cancel" class="btn-tertiary">Cancel</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FilterPanel',
  props: {
    initialFilters: Object,
  },
  data() {
    return {
      filters: { ...this.initialFilters },
    };
  },
  methods: {
    applyFilters() {
      this.$emit('apply', this.filters);
    },
    saveAsDefault() {
      this.$emit('save-default', this.filters);
    },
    cancel() {
      this.$emit('cancel');
    },
  },
};
</script>

<style scoped>
/* Mobile-first responsive design */
</style>
```

**Dependencies:** Vue 3, existing Mealie UI components

---

### 5.2 Results Grid Component

**File:** `frontend/components/MealRandomizer/ResultsGrid.vue`

**Purpose:** Display all 7 days with pin/regenerate controls

**Key Props/Data:**
- `weekPlan` - Array of recipe cards for the week
- `onRegenerateDay` - Callback for per-day regeneration
- `onPinDay` - Callback for pinning a day
- `onSwapRecipe` - Callback for swapping a recipe

**Structure:**
```vue
<template>
  <div class="results-grid">
    <h2>Your Week Plan</h2>
    
    <div class="grid-7-days">
      <div v-for="day in weekPlan" :key="day.day" class="day-card">
        <div class="day-header">
          <h3>{{ day.day }}</h3>
          <span class="date">{{ formatDate(day.date) }}</span>
        </div>
        
        <div class="recipe-card">
          <img :src="day.image_url" :alt="day.recipe_name" />
          <h4>{{ day.recipe_name }}</h4>
          <div class="meta">
            <span class="cook-time">⏱ {{ day.cook_time_minutes }}min</span>
            <span class="difficulty">{{ day.difficulty }}</span>
          </div>
          <div class="tags">
            <span v-for="tag in day.dietary_tags" :key="tag" class="tag">
              {{ tag }}
            </span>
          </div>
        </div>
        
        <div class="actions">
          <button 
            @click="togglePin(day.day)"
            :class="{ 'pinned': day.pinned }"
            class="btn-icon"
            title="Pin this day"
          >
            📌
          </button>
          <button 
            @click="regenerateDay(day.day)"
            class="btn-icon"
            title="Regenerate this day"
          >
            🔄
          </button>
          <button 
            @click="swapRecipe(day.day)"
            class="btn-icon"
            title="Swap recipe"
          >
            🔁
          </button>
        </div>
      </div>
    </div>
    
    <!-- Week-level Actions -->
    <div class="week-actions">
      <button @click="regenerateAll" class="btn-primary">Regenerate All</button>
      <button @click="saveTemplate" class="btn-secondary">Save as Template</button>
      <button @click="applyToPlan" class="btn-primary">Apply to Meal Plan</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ResultsGrid',
  props: {
    weekPlan: Array,
  },
  methods: {
    togglePin(day) {
      this.$emit('pin', day);
    },
    regenerateDay(day) {
      this.$emit('regenerate-day', day);
    },
    swapRecipe(day) {
      this.$emit('swap', day);
    },
    regenerateAll() {
      this.$emit('regenerate-all');
    },
    saveTemplate() {
      this.$emit('save-template');
    },
    applyToPlan() {
      this.$emit('apply');
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString();
    },
  },
};
</script>

<style scoped>
/* Grid layout, mobile-first responsive */
.grid-7-days {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .grid-7-days {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}

.day-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.day-card img {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-icon {
  flex: 1;
  padding: 0.5rem;
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}

.btn-icon.pinned {
  background: #ffd700;
  font-weight: bold;
}
</style>
```

**Dependencies:** Vue 3, existing Mealie UI components

---

### 5.3 Shopping List Integration Component

**File:** `frontend/components/MealRandomizer/ShoppingListPreview.vue`

**Purpose:** Show consolidated shopping list with overlaps and substitution suggestions

**Structure:**
```vue
<template>
  <div class="shopping-preview">
    <h3>Shopping List Preview</h3>
    
    <!-- Consolidated Ingredients -->
    <div class="ingredients-list">
      <div v-for="(item, index) in shopping" :key="index" class="ingredient-item">
        <div class="ingredient-info">
          <h4>{{ item.name }}</h4>
          <span class="quantity">{{ item.quantity }} {{ item.unit }}</span>
          <div v-if="item.used_in_days.length > 1" class="overlap-alert">
            ℹ Used in {{ item.used_in_days.join(', ') }} — buy in bulk
          </div>
        </div>
        
        <!-- Substitution Suggestion -->
        <div v-if="substitutions[index]" class="substitution-offer">
          <div class="suggestion">
            {{ substitutions[index].suggested_alternative }}
            <span v-if="substitutions[index].estimated_savings" class="savings">
              Save ~${{ substitutions[index].estimated_savings }}
            </span>
          </div>
          <button @click="acceptSubstitution(index)" class="btn-small">✓ Accept</button>
          <button @click="dismissSubstitution(index)" class="btn-small">✕ Keep</button>
        </div>
      </div>
    </div>
    
    <!-- Confirm & Apply -->
    <div class="actions">
      <button @click="confirmAndApply" class="btn-primary">Confirm & Apply to Plan</button>
      <button @click="cancel" class="btn-secondary">Cancel</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ShoppingListPreview',
  props: {
    shopping: Array,
    substitutions: Array,
  },
  methods: {
    acceptSubstitution(index) {
      this.$emit('substitute', index);
    },
    dismissSubstitution(index) {
      // Just remove the suggestion; don't apply
    },
    confirmAndApply() {
      this.$emit('apply');
    },
    cancel() {
      this.$emit('cancel');
    },
  },
};
</script>

<style scoped>
.ingredient-item {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.overlap-alert {
  font-size: 0.85rem;
  color: #0066cc;
  margin-top: 0.25rem;
}

.substitution-offer {
  background: #f9f9f9;
  padding: 0.75rem;
  border-radius: 4px;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.savings {
  color: #28a745;
  font-weight: bold;
  margin-left: 0.25rem;
}
</style>
```

**Dependencies:** Vue 3, existing Mealie UI components

---

### 5.4 Main Modal/Page Integration

**File:** `frontend/views/MealPlannerPage.vue` (existing file, modify)

**Change:** Add "Randomize Week" button and mount MealRandomizer modal

**Structure:**
```vue
<template>
  <div class="meal-planner-page">
    <header>
      <h1>Meal Planner</h1>
      <button @click="openRandomizer" class="btn-randomize">🎲 Randomize Week</button>
    </header>
    
    <!-- Existing Meal Planner content -->
    <div class="meal-planner">
      <!-- ... existing planner UI ... -->
    </div>
    
    <!-- Randomizer Modal -->
    <modal v-if="randomzerOpen" @close="closeRandomizer">
      <component v-if="randomzerStep === 'filters'" 
        :is="FilterPanel"
        :initial-filters="defaultFilters"
        @apply="generateRandomizer"
        @save-default="saveDefaultFilters"
      />
      
      <component v-if="randomzerStep === 'results'"
        :is="ResultsGrid"
        :week-plan="weekPlan"
        @regenerate-day="regenerateDay"
        @pin="pinDay"
        @regenerate-all="regenerateAll"
        @apply="showShoppingPreview"
      />
      
      <component v-if="randomzerStep === 'shopping'"
        :is="ShoppingListPreview"
        :shopping="shopping"
        :substitutions="substitutions"
        @apply="confirmAndApply"
      />
    </modal>
  </div>
</template>

<script>
import FilterPanel from '@/components/MealRandomizer/FilterPanel.vue';
import ResultsGrid from '@/components/MealRandomizer/ResultsGrid.vue';
import ShoppingListPreview from '@/components/MealRandomizer/ShoppingListPreview.vue';

export default {
  name: 'MealPlannerPage',
  components: { FilterPanel, ResultsGrid, ShoppingListPreview },
  data() {
    return {
      randomzerOpen: false,
      randomzerStep: 'filters', // 'filters', 'results', 'shopping'
      defaultFilters: {},
      weekPlan: [],
      shopping: [],
      substitutions: [],
    };
  },
  methods: {
    openRandomizer() {
      this.randomzerOpen = true;
      // Load user's default filters
      this.loadDefaultFilters();
    },
    closeRandomizer() {
      this.randomzerOpen = false;
      this.randomzerStep = 'filters';
    },
    async generateRandomizer(filters) {
      try {
        const response = await this.$api.post('/meals/randomizer/generate', {
          start_date: new Date().toISOString().split('T')[0],
          filters,
        });
        this.weekPlan = response.data.week_plan;
        this.shopping = response.data.shopping_consolidated;
        this.substitutions = response.data.substitution_suggestions;
        this.randomzerStep = 'results';
      } catch (error) {
        this.$toast.error(error.message);
      }
    },
    async regenerateDay(day) {
      // Call endpoint to regenerate a single day
      // Update weekPlan
    },
    async regenerateAll() {
      // Regenerate all unpinned days
    },
    showShoppingPreview() {
      this.randomzerStep = 'shopping';
    },
    async confirmAndApply() {
      // Apply to Meal Planner + Shopping List
      // Call existing Mealie API
    },
    async loadDefaultFilters() {
      const response = await this.$api.get('/meals/randomizer/preferences');
      this.defaultFilters = response.data.filter_defaults || {};
    },
    async saveDefaultFilters(filters) {
      await this.$api.put('/meals/randomizer/preferences', {
        filter_defaults: filters,
      });
      this.$toast.success('Default filters saved!');
    },
  },
};
</script>

<style scoped>
.btn-randomize {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.btn-randomize:hover {
  transform: scale(1.05);
}
</style>
```

**Dependencies:** Components 5.1, 5.2, 5.3, existing Mealie page structure

---

### 5.5 Vuex Store Module (State Management)

**File:** `frontend/store/modules/randomizer.js`

**Purpose:** Centralize randomizer state (optional but recommended)

**State:**
```javascript
const state = {
  weekPlan: [],
  shopping: [],
  substitutions: [],
  currentFilters: {},
  savedTemplates: [],
  userPreferences: {},
  isLoading: false,
  error: null,
};

const mutations = {
  setWeekPlan(state, plan) { state.weekPlan = plan; },
  setShopping(state, shopping) { state.shopping = shopping; },
  setError(state, error) { state.error = error; },
  setLoading(state, loading) { state.isLoading = loading; },
  // ... more mutations
};

const actions = {
  async generateWeek({ commit }, { filters, startDate, pinnedDays }) {
    commit('setLoading', true);
    try {
      const response = await api.post('/meals/randomizer/generate', {
        start_date: startDate,
        filters,
        pinned_days: pinnedDays,
      });
      commit('setWeekPlan', response.data.week_plan);
      commit('setShopping', response.data.shopping_consolidated);
      // ...
      commit('setLoading', false);
    } catch (error) {
      commit('setError', error.message);
    }
  },
  // ... more actions
};
```

**Dependencies:** Vue.js, existing Mealie Vuex setup

---

## Phase 6: Testing

### 6.1 Backend Unit Tests

**File:** `tests/unit_tests/services/test_meal_randomizer_service.py`

**Purpose:** Test randomizer logic, protein distribution, balance rules

**Test Cases:**
- `test_generate_week_plan_basic` - Happy path
- `test_protein_distribution` - Verify protein counts honored
- `test_repeat_avoidance` - Check repeat-avoid window works
- `test_small_library_broadening` - Test filter broadening
- `test_consolidate_shopping` - Verify ingredient consolidation
- `test_cache_functionality` - Cache hit/miss

**Dependencies:** pytest, existing Mealie test infrastructure

---

### 6.2 API Integration Tests

**File:** `tests/integration_tests/test_meal_randomizer_api.py`

**Purpose:** Test all endpoints with real database

**Test Cases:**
- `test_post_generate_randomizer` - POST /meals/randomizer/generate
- `test_post_rate_recipe` - POST /meals/randomizer/rate
- `test_save_load_template` - Save and retrieve templates
- `test_get_preferences` - GET /meals/randomizer/preferences

**Dependencies:** pytest, fastapi TestClient

---

### 6.3 Frontend Component Tests

**File:** `tests/unit_tests/components/test_FilterPanel.vue.spec.js`

**Purpose:** Test Vue components in isolation

**Test Cases:**
- `test_filter_panel_renders` - Component mounts correctly
- `test_apply_filters_emits_event` - Event emitted on apply
- `test_save_default_functionality` - Save default button works

**Dependencies:** Vue Test Utils, Jest, existing Mealie test setup

---

## Phase 7: Database & Migration Management

### 7.1 Create Migration Script

**File:** `mealie/db/migration_[timestamp]_meal_randomizer.py`

**Purpose:** Alembic migration to create tables

**Commands:**
```bash
# Generate migration
alembic revision --autogenerate -m "Add meal randomizer tables"

# Apply migration
alembic upgrade head
```

**Dependencies:** Alembic (existing in Mealie)

---

## Phase 8: Documentation & Deployment

### 8.1 API Documentation

**Update:** OpenAPI/Swagger docs with new endpoints

**File:** `docs/api/meal_randomizer.md` (or auto-generated from FastAPI)

### 8.2 User Guide

**File:** `docs/features/meal_randomizer_user_guide.md`

**Content:**
- How to access randomizer
- Filter explanations
- Tips for best results
- FAQ

### 8.3 Deployment Checklist

**Items:**
- [ ] All tests passing
- [ ] Database migrations tested on staging
- [ ] API endpoints documented
- [ ] Frontend tested on mobile and desktop
- [ ] Performance benchmarks met (< 3s response time)
- [ ] Cache working correctly
- [ ] Error messages clear and actionable
- [ ] Accessibility (WCAG 2.1 AA) verified
- [ ] Staging deployment successful
- [ ] Production deployment & monitoring

---

## Execution Sequence Summary

```
Phase 1: Data Models (1.1 → 1.2 → 1.3)
  ↓
Phase 2: API Schemas (2.1)
  ↓
Phase 3: Services (3.1 → 3.2 → 3.3)
  ↓
Phase 4: API Routes (4.1 → 4.2)
  ↓
Phase 5: Frontend (5.1 → 5.2 → 5.3 → 5.4 → 5.5)
  ↓
Phase 6: Testing (6.1 → 6.2 → 6.3)
  ↓
Phase 7: Migrations (7.1)
  ↓
Phase 8: Documentation & Deployment (8.1 → 8.2 → 8.3)
```

---

## Key Dependencies Summary

| Phase | Depends On | Notes |
|-------|-----------|-------|
| 1 | None | Foundation |
| 2 | Phase 1 | Schemas reference models |
| 3 | Phase 1, 2 | Services use models & schemas |
| 4 | Phase 2, 3 | Routes use services & schemas |
| 5 | Phase 4 | Frontend calls backend APIs |
| 6 | Phase 3, 4, 5 | Tests for all layers |
| 7 | Phase 1 | Database operations |
| 8 | All phases | Final documentation |

---

## Estimated Effort

- **Phase 1 (Data Models):** 2 hours
- **Phase 2 (Schemas):** 2 hours
- **Phase 3 (Services):** 8 hours (core algorithm is complex)
- **Phase 4 (API Routes):** 3 hours
- **Phase 5 (Frontend):** 10 hours (most UI components)
- **Phase 6 (Testing):** 6 hours
- **Phase 7 (Migrations):** 1 hour
- **Phase 8 (Documentation):** 2 hours

**Total Estimate: ~34 hours** (4–5 days full-time development)

---

**Ready to move to Phase 3 (Start Coding)?**

