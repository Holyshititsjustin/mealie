/**
 * Types for Meal Randomizer API
 */

export interface ProteinPreference {
  protein_type: string;
  count: number;
}

export interface RandomizerFilters {
  dietary_restrictions: string[];
  allergens: string[];
  protein_preferences: ProteinPreference[];
  avoid_repeat_days: number;
  cook_time_bands: string[];
  meal_types: string[];
  difficulty_levels: string[];
  include_expiring_ingredients: boolean;
  recipe_candidate_cap: number;
}

export interface RandomizerRequest {
  start_date: string;
  filters: RandomizerFilters;
  pinned_days: Record<string, string>; // day_name -> recipe_id
}

export interface RecipeResultCard {
  day: string;
  date: string;
  recipe_id: string;
  recipe_name: string;
  recipe_slug: string;
  cook_time: number;
  difficulty: string;
  dietary_tags: string[];
  image_url?: string;
  description?: string;
  pinned: boolean;
}

export interface ConsolidatedIngredient {
  name: string;
  quantity: number | string;
  unit: string;
  used_in_days: string[];
  expiry_date?: string;
  note?: string;
}

export interface SubstitutionSuggestion {
  ingredient: string;
  reason: string;
  suggested_alternative: string;
  estimated_savings: string;
  nutritional_comparison: string;
}

export interface RandomizerResponse {
  status: string;
  week_plan: RecipeResultCard[];
  shopping_consolidated: Record<string, ConsolidatedIngredient>;
  substitution_suggestions: SubstitutionSuggestion[];
  metadata: {
    generated_at: string;
    generation_method: string;
  };
  is_cached: boolean;
  warning_message?: string;
}

export interface RecipeRatingCreate {
  recipe_id: string;
  rating: "up" | "down" | "never_again";
}

export interface RecipeRatingOut extends RecipeRatingCreate {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface RandomizerTemplateCreate {
  template_name: string;
  week_plan_json: RecipeResultCard[];
}

export interface RandomizerTemplateOut extends RandomizerTemplateCreate {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface RandomizerTemplateSummary {
  id: string;
  template_name: string;
  recipe_names: string[];
  created_at: string;
  updated_at?: string;
}

export interface RandomizerPreferencesCreate {
  filter_defaults?: Record<string, any>;
  recipe_candidate_cap?: number;
  avoid_repeat_days?: number;
}

export interface RandomizerPreferencesOut extends RandomizerPreferencesCreate {
  id?: string;
  user_id: string;
  created_at?: string;
  updated_at?: string;
}

export interface RandomizerPreferencesUpdate {
  filter_defaults?: Record<string, any> | null;
  recipe_candidate_cap?: number | null;
  avoid_repeat_days?: number | null;
}
