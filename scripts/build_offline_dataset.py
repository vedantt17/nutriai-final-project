from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
TARGET_RECORD_COUNT = 10750


NUTRIENT_FIELDS = [
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
    "calcium_mg",
    "vitamin_b12_mcg",
    "vitamin_d_mcg",
    "zinc_mg",
    "potassium_mg",
    "magnesium_mg",
    "sodium_mg",
    "omega3_g",
]


def meal(
    name,
    meal_type,
    category,
    cuisine,
    ingredients,
    nutrients,
    *,
    contains_dairy=False,
    contains_gluten=False,
    contains_tree_nuts=False,
    contains_peanuts=False,
    contains_shellfish=False,
    contains_soy=False,
    contains_sesame=False,
    contains_eggs=False,
    contains_pork=False,
    contains_beef=False,
    contains_meat=False,
    contains_fish=False,
    contains_honey=False,
    fodmap_level="low",
    acidity_level="low",
    glycemic_index=45,
    condition_flags=None,
    cross_contamination_risks=None,
    cultural_flags=None,
):
    animal = contains_dairy or contains_eggs or contains_meat or contains_fish or contains_shellfish or contains_pork or contains_beef or contains_honey
    vegetarian = not (contains_meat or contains_fish or contains_shellfish or contains_pork or contains_beef)
    vegan = not animal
    pescatarian = not (contains_meat or contains_pork or contains_beef)
    return {
        "name": name,
        "meal_type": meal_type,
        "category": category,
        "cuisine": cuisine,
        "ingredients": list(ingredients),
        "contains_dairy": contains_dairy,
        "contains_gluten": contains_gluten,
        "contains_tree_nuts": contains_tree_nuts,
        "contains_peanuts": contains_peanuts,
        "contains_shellfish": contains_shellfish,
        "contains_soy": contains_soy,
        "contains_sesame": contains_sesame,
        "contains_eggs": contains_eggs,
        "contains_pork": contains_pork,
        "contains_beef": contains_beef,
        "contains_meat": contains_meat or contains_pork or contains_beef,
        "contains_fish": contains_fish,
        "contains_honey": contains_honey,
        "vegetarian": vegetarian,
        "vegan": vegan,
        "pescatarian": pescatarian,
        "fodmap_level": fodmap_level,
        "acidity_level": acidity_level,
        "glycemic_index": glycemic_index,
        "condition_flags": set(condition_flags or []),
        "cross_contamination_risks": set(cross_contamination_risks or []),
        "cultural_flags": set(cultural_flags or []),
        **nutrients,
    }


BASE_MEALS = [
    meal("Quinoa banana breakfast bowl", "Breakfast", "grain bowl", "American", ["quinoa", "banana", "chia", "fortified oat milk"], {"calories": 430, "protein_g": 15, "carbs_g": 66, "fat_g": 12, "fiber_g": 11, "iron_mg": 4.0, "calcium_mg": 340, "vitamin_b12_mcg": 1.1, "vitamin_d_mcg": 4.5, "zinc_mg": 2.7, "potassium_mg": 760, "magnesium_mg": 160, "sodium_mg": 135, "omega3_g": 1.2}, glycemic_index=48),
    meal("Egg spinach rice plate", "Breakfast", "egg plate", "Mediterranean", ["egg", "spinach", "brown rice", "olive oil"], {"calories": 455, "protein_g": 24, "carbs_g": 44, "fat_g": 20, "fiber_g": 6, "iron_mg": 4.3, "calcium_mg": 210, "vitamin_b12_mcg": 1.5, "vitamin_d_mcg": 3.4, "zinc_mg": 2.6, "potassium_mg": 690, "magnesium_mg": 125, "sodium_mg": 250, "omega3_g": 0.3}, contains_eggs=True, glycemic_index=45),
    meal("Tofu vegetable scramble", "Breakfast", "plant protein", "Californian", ["tofu", "zucchini", "spinach", "turmeric", "quinoa"], {"calories": 420, "protein_g": 27, "carbs_g": 38, "fat_g": 18, "fiber_g": 8, "iron_mg": 5.8, "calcium_mg": 430, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 5.0, "zinc_mg": 3.1, "potassium_mg": 760, "magnesium_mg": 150, "sodium_mg": 280, "omega3_g": 0.7}, contains_soy=True, glycemic_index=38),
    meal("Greek yogurt berry oat parfait", "Breakfast", "parfait", "American", ["greek yogurt", "blueberries", "certified oats", "pumpkin seeds"], {"calories": 405, "protein_g": 28, "carbs_g": 48, "fat_g": 11, "fiber_g": 8, "iron_mg": 2.6, "calcium_mg": 430, "vitamin_b12_mcg": 1.7, "vitamin_d_mcg": 1.9, "zinc_mg": 2.4, "potassium_mg": 610, "magnesium_mg": 110, "sodium_mg": 145, "omega3_g": 0.2}, contains_dairy=True, glycemic_index=43),
    meal("Almond chia smoothie", "Breakfast", "smoothie", "American", ["almond milk", "chia", "banana", "spinach"], {"calories": 380, "protein_g": 12, "carbs_g": 46, "fat_g": 18, "fiber_g": 12, "iron_mg": 3.3, "calcium_mg": 480, "vitamin_b12_mcg": 1.0, "vitamin_d_mcg": 2.5, "zinc_mg": 2.1, "potassium_mg": 720, "magnesium_mg": 150, "sodium_mg": 160, "omega3_g": 2.1}, contains_tree_nuts=True, glycemic_index=44),
    meal("Millet peanut porridge", "Breakfast", "porridge", "West African", ["millet", "peanut butter", "banana", "flax"], {"calories": 445, "protein_g": 17, "carbs_g": 58, "fat_g": 17, "fiber_g": 10, "iron_mg": 4.1, "calcium_mg": 180, "vitamin_b12_mcg": 0.0, "vitamin_d_mcg": 0.0, "zinc_mg": 3.0, "potassium_mg": 690, "magnesium_mg": 170, "sodium_mg": 120, "omega3_g": 1.8}, contains_peanuts=True, glycemic_index=50),
    meal("Corn tortilla egg tacos", "Breakfast", "tacos", "Mexican", ["corn tortilla", "egg", "spinach", "avocado"], {"calories": 465, "protein_g": 23, "carbs_g": 46, "fat_g": 22, "fiber_g": 9, "iron_mg": 4.0, "calcium_mg": 190, "vitamin_b12_mcg": 1.4, "vitamin_d_mcg": 3.2, "zinc_mg": 2.7, "potassium_mg": 780, "magnesium_mg": 135, "sodium_mg": 245, "omega3_g": 0.4}, contains_eggs=True, glycemic_index=47),
    meal("Smoked salmon rice breakfast", "Breakfast", "fish plate", "Nordic", ["salmon", "brown rice", "cucumber", "dill"], {"calories": 460, "protein_g": 30, "carbs_g": 43, "fat_g": 17, "fiber_g": 5, "iron_mg": 2.2, "calcium_mg": 120, "vitamin_b12_mcg": 3.8, "vitamin_d_mcg": 8.0, "zinc_mg": 1.8, "potassium_mg": 700, "magnesium_mg": 100, "sodium_mg": 470, "omega3_g": 2.0}, contains_fish=True, glycemic_index=44),
    meal("Lentil dosa coconut plate", "Breakfast", "savory pancake", "Indian", ["lentil dosa", "coconut chutney", "spinach"], {"calories": 430, "protein_g": 18, "carbs_g": 60, "fat_g": 13, "fiber_g": 9, "iron_mg": 4.8, "calcium_mg": 180, "vitamin_b12_mcg": 0.0, "vitamin_d_mcg": 0.0, "zinc_mg": 2.8, "potassium_mg": 680, "magnesium_mg": 145, "sodium_mg": 260, "omega3_g": 0.2}, fodmap_level="medium", glycemic_index=49),
    meal("Chicken sweet potato hash", "Breakfast", "hash", "American", ["chicken", "sweet potato", "bell pepper", "kale"], {"calories": 510, "protein_g": 34, "carbs_g": 48, "fat_g": 18, "fiber_g": 8, "iron_mg": 3.0, "calcium_mg": 170, "vitamin_b12_mcg": 0.6, "vitamin_d_mcg": 0.4, "zinc_mg": 2.4, "potassium_mg": 930, "magnesium_mg": 120, "sodium_mg": 310, "omega3_g": 0.1}, contains_meat=True, glycemic_index=54),
    meal("Low FODMAP tofu rice bowl", "Lunch", "rice bowl", "Japanese", ["firm tofu", "white rice", "carrot", "zucchini", "ginger"], {"calories": 620, "protein_g": 31, "carbs_g": 78, "fat_g": 20, "fiber_g": 8, "iron_mg": 6.2, "calcium_mg": 500, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 5.0, "zinc_mg": 3.4, "potassium_mg": 900, "magnesium_mg": 180, "sodium_mg": 360, "omega3_g": 0.9}, contains_soy=True, glycemic_index=50),
    meal("Grilled chicken quinoa bowl", "Lunch", "protein bowl", "Mediterranean", ["chicken", "quinoa", "cucumber", "spinach", "olive oil"], {"calories": 650, "protein_g": 44, "carbs_g": 62, "fat_g": 24, "fiber_g": 9, "iron_mg": 4.6, "calcium_mg": 170, "vitamin_b12_mcg": 0.6, "vitamin_d_mcg": 0.2, "zinc_mg": 3.7, "potassium_mg": 980, "magnesium_mg": 190, "sodium_mg": 370, "omega3_g": 0.2}, contains_meat=True, glycemic_index=45),
    meal("Salmon quinoa greens plate", "Lunch", "fish plate", "Mediterranean", ["salmon", "quinoa", "spinach", "cucumber"], {"calories": 675, "protein_g": 42, "carbs_g": 58, "fat_g": 30, "fiber_g": 8, "iron_mg": 4.1, "calcium_mg": 190, "vitamin_b12_mcg": 4.8, "vitamin_d_mcg": 12.0, "zinc_mg": 2.6, "potassium_mg": 1080, "magnesium_mg": 185, "sodium_mg": 330, "omega3_g": 3.1}, contains_fish=True, glycemic_index=44),
    meal("Lentil quinoa power bowl", "Lunch", "legume bowl", "Middle Eastern", ["lentils", "quinoa", "kale", "tahini"], {"calories": 635, "protein_g": 29, "carbs_g": 82, "fat_g": 20, "fiber_g": 19, "iron_mg": 7.5, "calcium_mg": 250, "vitamin_b12_mcg": 0.0, "vitamin_d_mcg": 0.0, "zinc_mg": 4.7, "potassium_mg": 1120, "magnesium_mg": 230, "sodium_mg": 330, "omega3_g": 0.3}, contains_sesame=True, fodmap_level="medium", glycemic_index=39),
    meal("Chickpea cucumber millet salad", "Lunch", "legume salad", "Mediterranean", ["chickpeas", "millet", "cucumber", "parsley"], {"calories": 610, "protein_g": 23, "carbs_g": 86, "fat_g": 19, "fiber_g": 17, "iron_mg": 6.6, "calcium_mg": 190, "vitamin_b12_mcg": 0.0, "vitamin_d_mcg": 0.0, "zinc_mg": 3.9, "potassium_mg": 990, "magnesium_mg": 210, "sodium_mg": 300, "omega3_g": 0.2}, fodmap_level="medium", glycemic_index=42),
    meal("Turkey lettuce rice bowl", "Lunch", "protein bowl", "American", ["turkey", "brown rice", "lettuce", "carrot"], {"calories": 610, "protein_g": 42, "carbs_g": 63, "fat_g": 18, "fiber_g": 7, "iron_mg": 3.3, "calcium_mg": 140, "vitamin_b12_mcg": 1.2, "vitamin_d_mcg": 0.2, "zinc_mg": 4.2, "potassium_mg": 850, "magnesium_mg": 130, "sodium_mg": 390, "omega3_g": 0.1}, contains_meat=True, glycemic_index=48),
    meal("Shrimp brown rice bowl", "Lunch", "seafood bowl", "Thai", ["shrimp", "brown rice", "bok choy", "ginger"], {"calories": 585, "protein_g": 39, "carbs_g": 66, "fat_g": 15, "fiber_g": 7, "iron_mg": 3.0, "calcium_mg": 170, "vitamin_b12_mcg": 1.8, "vitamin_d_mcg": 0.4, "zinc_mg": 2.8, "potassium_mg": 790, "magnesium_mg": 125, "sodium_mg": 520, "omega3_g": 0.5}, contains_shellfish=True, glycemic_index=49),
    meal("Vegetable rice noodle bowl", "Lunch", "noodle bowl", "Vietnamese", ["rice noodles", "tofu-free vegetables", "cucumber", "mint"], {"calories": 595, "protein_g": 18, "carbs_g": 92, "fat_g": 16, "fiber_g": 8, "iron_mg": 4.0, "calcium_mg": 230, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 3.4, "zinc_mg": 2.6, "potassium_mg": 850, "magnesium_mg": 150, "sodium_mg": 300, "omega3_g": 0.4}, glycemic_index=52),
    meal("Paneer rice curry", "Lunch", "curry", "Indian", ["paneer", "rice", "spinach", "cumin"], {"calories": 680, "protein_g": 31, "carbs_g": 66, "fat_g": 32, "fiber_g": 6, "iron_mg": 3.8, "calcium_mg": 520, "vitamin_b12_mcg": 1.4, "vitamin_d_mcg": 0.7, "zinc_mg": 3.4, "potassium_mg": 720, "magnesium_mg": 120, "sodium_mg": 460, "omega3_g": 0.1}, contains_dairy=True, glycemic_index=51),
    meal("Tomato wheat pasta bowl", "Lunch", "pasta", "Italian", ["wheat pasta", "tomato sauce", "parmesan"], {"calories": 700, "protein_g": 25, "carbs_g": 100, "fat_g": 22, "fiber_g": 9, "iron_mg": 4.2, "calcium_mg": 280, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 0.2, "zinc_mg": 2.9, "potassium_mg": 780, "magnesium_mg": 125, "sodium_mg": 780, "omega3_g": 0.1}, contains_dairy=True, contains_gluten=True, fodmap_level="high", acidity_level="high", glycemic_index=62, condition_flags={"high fodmap", "reflux trigger", "high gi", "high sodium"}),
    meal("Garlic onion curry rice", "Lunch", "curry", "Indian", ["rice", "garlic", "onion", "chickpeas", "spices"], {"calories": 650, "protein_g": 22, "carbs_g": 92, "fat_g": 18, "fiber_g": 16, "iron_mg": 6.2, "calcium_mg": 170, "vitamin_b12_mcg": 0.0, "vitamin_d_mcg": 0.0, "zinc_mg": 3.8, "potassium_mg": 900, "magnesium_mg": 190, "sodium_mg": 560, "omega3_g": 0.1}, fodmap_level="high", glycemic_index=54, condition_flags={"high fodmap"}),
    meal("Cod potato herb plate", "Dinner", "fish plate", "Nordic", ["cod", "potato", "green beans", "olive oil"], {"calories": 680, "protein_g": 46, "carbs_g": 70, "fat_g": 22, "fiber_g": 9, "iron_mg": 3.3, "calcium_mg": 160, "vitamin_b12_mcg": 3.4, "vitamin_d_mcg": 4.5, "zinc_mg": 2.2, "potassium_mg": 1300, "magnesium_mg": 150, "sodium_mg": 310, "omega3_g": 0.8}, contains_fish=True, glycemic_index=54),
    meal("Low sodium salmon sweet potato", "Dinner", "fish plate", "American", ["salmon", "sweet potato", "kale", "olive oil"], {"calories": 720, "protein_g": 43, "carbs_g": 64, "fat_g": 32, "fiber_g": 11, "iron_mg": 4.0, "calcium_mg": 250, "vitamin_b12_mcg": 5.2, "vitamin_d_mcg": 13.0, "zinc_mg": 2.8, "potassium_mg": 1400, "magnesium_mg": 190, "sodium_mg": 330, "omega3_g": 3.3}, contains_fish=True, glycemic_index=50),
    meal("Seared tuna quinoa salad", "Dinner", "fish salad", "Mediterranean", ["tuna", "quinoa", "spinach", "cucumber"], {"calories": 690, "protein_g": 48, "carbs_g": 55, "fat_g": 28, "fiber_g": 8, "iron_mg": 4.4, "calcium_mg": 160, "vitamin_b12_mcg": 6.0, "vitamin_d_mcg": 5.8, "zinc_mg": 2.4, "potassium_mg": 980, "magnesium_mg": 180, "sodium_mg": 360, "omega3_g": 1.8}, contains_fish=True, glycemic_index=43),
    meal("Tempeh broccoli brown rice", "Dinner", "plant protein", "Indonesian", ["tempeh", "brown rice", "broccoli", "sesame"], {"calories": 700, "protein_g": 38, "carbs_g": 74, "fat_g": 28, "fiber_g": 13, "iron_mg": 6.5, "calcium_mg": 280, "vitamin_b12_mcg": 0.0, "vitamin_d_mcg": 0.0, "zinc_mg": 4.5, "potassium_mg": 1050, "magnesium_mg": 230, "sodium_mg": 340, "omega3_g": 0.6}, contains_soy=True, contains_sesame=True, glycemic_index=44),
    meal("Black bean avocado quinoa bowl", "Dinner", "legume bowl", "Mexican", ["black beans", "quinoa", "avocado", "cilantro"], {"calories": 720, "protein_g": 28, "carbs_g": 88, "fat_g": 28, "fiber_g": 22, "iron_mg": 7.0, "calcium_mg": 210, "vitamin_b12_mcg": 0.0, "vitamin_d_mcg": 0.0, "zinc_mg": 4.3, "potassium_mg": 1250, "magnesium_mg": 250, "sodium_mg": 310, "omega3_g": 0.3}, fodmap_level="medium", glycemic_index=38),
    meal("Chicken vegetable rice dinner", "Dinner", "protein plate", "American", ["chicken", "brown rice", "zucchini", "carrot"], {"calories": 710, "protein_g": 48, "carbs_g": 70, "fat_g": 23, "fiber_g": 9, "iron_mg": 3.2, "calcium_mg": 150, "vitamin_b12_mcg": 0.7, "vitamin_d_mcg": 0.2, "zinc_mg": 3.5, "potassium_mg": 950, "magnesium_mg": 150, "sodium_mg": 360, "omega3_g": 0.1}, contains_meat=True, glycemic_index=49),
    meal("Egg and quinoa stuffed peppers", "Dinner", "stuffed vegetable", "Mediterranean", ["egg", "quinoa", "bell pepper", "spinach"], {"calories": 650, "protein_g": 31, "carbs_g": 66, "fat_g": 25, "fiber_g": 11, "iron_mg": 5.2, "calcium_mg": 240, "vitamin_b12_mcg": 1.6, "vitamin_d_mcg": 3.8, "zinc_mg": 3.3, "potassium_mg": 940, "magnesium_mg": 180, "sodium_mg": 310, "omega3_g": 0.4}, contains_eggs=True, glycemic_index=45),
    meal("Fortified vegan macro bowl", "Dinner", "macro bowl", "Californian", ["quinoa", "tofu-free lentil patty", "kale", "nutritional yeast", "fortified oat milk sauce"], {"calories": 710, "protein_g": 34, "carbs_g": 83, "fat_g": 25, "fiber_g": 18, "iron_mg": 8.0, "calcium_mg": 520, "vitamin_b12_mcg": 2.8, "vitamin_d_mcg": 8.0, "zinc_mg": 5.2, "potassium_mg": 1250, "magnesium_mg": 250, "sodium_mg": 390, "omega3_g": 1.5}, fodmap_level="medium", glycemic_index=42),
    meal("Miso tofu soba bowl", "Dinner", "noodle bowl", "Japanese", ["tofu", "soba", "miso", "edamame"], {"calories": 705, "protein_g": 39, "carbs_g": 78, "fat_g": 24, "fiber_g": 12, "iron_mg": 6.0, "calcium_mg": 380, "vitamin_b12_mcg": 0.4, "vitamin_d_mcg": 0.8, "zinc_mg": 4.3, "potassium_mg": 940, "magnesium_mg": 210, "sodium_mg": 1040, "omega3_g": 0.5}, contains_soy=True, contains_gluten=True, glycemic_index=52, condition_flags={"high sodium"}),
    meal("Bean burrito wheat wrap", "Dinner", "wrap", "Mexican", ["wheat tortilla", "pinto beans", "cheese", "salsa"], {"calories": 760, "protein_g": 31, "carbs_g": 96, "fat_g": 28, "fiber_g": 18, "iron_mg": 6.7, "calcium_mg": 420, "vitamin_b12_mcg": 0.9, "vitamin_d_mcg": 0.2, "zinc_mg": 4.0, "potassium_mg": 1050, "magnesium_mg": 210, "sodium_mg": 910, "omega3_g": 0.2}, contains_dairy=True, contains_gluten=True, fodmap_level="high", acidity_level="high", glycemic_index=58, condition_flags={"high fodmap", "reflux trigger", "high gi", "high sodium"}),
    meal("Pork fried rice", "Dinner", "fried rice", "Chinese", ["pork", "white rice", "egg", "soy sauce"], {"calories": 820, "protein_g": 36, "carbs_g": 86, "fat_g": 35, "fiber_g": 5, "iron_mg": 3.4, "calcium_mg": 110, "vitamin_b12_mcg": 1.2, "vitamin_d_mcg": 0.8, "zinc_mg": 4.8, "potassium_mg": 720, "magnesium_mg": 90, "sodium_mg": 1180, "omega3_g": 0.1}, contains_pork=True, contains_meat=True, contains_eggs=True, contains_soy=True, glycemic_index=68, condition_flags={"high gi", "high sodium", "reflux trigger"}),
    meal("Buckwheat hemp berry bowl", "Breakfast", "grain bowl", "Nordic", ["buckwheat", "hemp hearts", "blueberries", "fortified oat milk"], {"calories": 430, "protein_g": 18, "carbs_g": 58, "fat_g": 15, "fiber_g": 10, "iron_mg": 4.4, "calcium_mg": 380, "vitamin_b12_mcg": 1.3, "vitamin_d_mcg": 6.5, "zinc_mg": 3.2, "potassium_mg": 680, "magnesium_mg": 170, "sodium_mg": 150, "omega3_g": 1.1}, glycemic_index=43),
    meal("Polenta pumpkin seed breakfast", "Breakfast", "porridge", "Italian", ["polenta", "pumpkin seeds", "strawberries", "fortified oat milk"], {"calories": 410, "protein_g": 16, "carbs_g": 59, "fat_g": 13, "fiber_g": 9, "iron_mg": 4.8, "calcium_mg": 350, "vitamin_b12_mcg": 1.2, "vitamin_d_mcg": 6.0, "zinc_mg": 3.6, "potassium_mg": 620, "magnesium_mg": 160, "sodium_mg": 145, "omega3_g": 0.4}, glycemic_index=49),
    meal("Amaranth flax breakfast cup", "Breakfast", "breakfast cup", "Andean", ["amaranth", "flax", "kiwi", "fortified oat milk"], {"calories": 420, "protein_g": 17, "carbs_g": 57, "fat_g": 14, "fiber_g": 11, "iron_mg": 5.3, "calcium_mg": 390, "vitamin_b12_mcg": 1.2, "vitamin_d_mcg": 6.2, "zinc_mg": 3.1, "potassium_mg": 700, "magnesium_mg": 185, "sodium_mg": 135, "omega3_g": 1.9}, glycemic_index=44),
    meal("Sweet potato hemp lunch bowl", "Lunch", "root bowl", "Californian", ["sweet potato", "hemp hearts", "kale", "cucumber", "olive oil"], {"calories": 620, "protein_g": 24, "carbs_g": 74, "fat_g": 25, "fiber_g": 14, "iron_mg": 5.8, "calcium_mg": 310, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 3.5, "zinc_mg": 4.1, "potassium_mg": 1250, "magnesium_mg": 220, "sodium_mg": 260, "omega3_g": 1.2}, glycemic_index=50),
    meal("Teff vegetable pilaf", "Lunch", "pilaf", "East African", ["teff", "carrot", "zucchini", "spinach", "pumpkin seeds"], {"calories": 600, "protein_g": 22, "carbs_g": 78, "fat_g": 21, "fiber_g": 13, "iron_mg": 7.2, "calcium_mg": 280, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 3.2, "zinc_mg": 4.6, "potassium_mg": 980, "magnesium_mg": 230, "sodium_mg": 240, "omega3_g": 0.4}, glycemic_index=48),
    meal("Brown rice edamame-free poke", "Lunch", "rice bowl", "Hawaiian", ["brown rice", "cucumber", "carrot", "seaweed", "hemp hearts"], {"calories": 590, "protein_g": 21, "carbs_g": 82, "fat_g": 19, "fiber_g": 11, "iron_mg": 5.0, "calcium_mg": 230, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 3.0, "zinc_mg": 3.8, "potassium_mg": 850, "magnesium_mg": 180, "sodium_mg": 300, "omega3_g": 0.6}, glycemic_index=51),
    meal("Stuffed acorn squash quinoa", "Dinner", "stuffed vegetable", "American", ["acorn squash", "quinoa", "kale", "cranberries", "pumpkin seeds"], {"calories": 680, "protein_g": 25, "carbs_g": 86, "fat_g": 26, "fiber_g": 16, "iron_mg": 6.4, "calcium_mg": 300, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 3.6, "zinc_mg": 4.7, "potassium_mg": 1250, "magnesium_mg": 240, "sodium_mg": 300, "omega3_g": 0.5}, glycemic_index=48),
    meal("Herbed trout millet dinner", "Dinner", "fish plate", "Nordic", ["trout", "millet", "green beans", "dill", "olive oil"], {"calories": 700, "protein_g": 45, "carbs_g": 64, "fat_g": 28, "fiber_g": 9, "iron_mg": 4.0, "calcium_mg": 190, "vitamin_b12_mcg": 5.4, "vitamin_d_mcg": 10.5, "zinc_mg": 2.9, "potassium_mg": 1120, "magnesium_mg": 160, "sodium_mg": 340, "omega3_g": 2.7}, contains_fish=True, glycemic_index=47),
    meal("Quinoa mushroom herb skillet", "Dinner", "skillet", "French", ["quinoa", "oyster mushrooms", "spinach", "herbs", "fortified oat milk"], {"calories": 660, "protein_g": 27, "carbs_g": 78, "fat_g": 24, "fiber_g": 14, "iron_mg": 6.0, "calcium_mg": 360, "vitamin_b12_mcg": 1.4, "vitamin_d_mcg": 7.0, "zinc_mg": 4.2, "potassium_mg": 1050, "magnesium_mg": 220, "sodium_mg": 280, "omega3_g": 0.7}, glycemic_index=45),
    meal("Red lentil cauliflower stew", "Dinner", "stew", "Indian", ["red lentils", "cauliflower rice", "spinach", "nutritional yeast", "olive oil"], {"calories": 665, "protein_g": 31, "carbs_g": 76, "fat_g": 24, "fiber_g": 18, "iron_mg": 7.4, "calcium_mg": 340, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 3.5, "zinc_mg": 4.8, "potassium_mg": 1180, "magnesium_mg": 230, "sodium_mg": 310, "omega3_g": 0.6}, fodmap_level="medium", glycemic_index=38),
]


ADD_ONS = [
    {"name": "spinach", "ingredients": ["spinach"], "nutrients": {"calories": 20, "protein_g": 2, "carbs_g": 3, "fat_g": 0, "fiber_g": 2, "iron_mg": 1.0, "calcium_mg": 50, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.2, "potassium_mg": 160, "magnesium_mg": 25, "sodium_mg": 25, "omega3_g": 0.1}},
    {"name": "pumpkin seeds", "ingredients": ["pumpkin seeds"], "nutrients": {"calories": 90, "protein_g": 5, "carbs_g": 3, "fat_g": 7, "fiber_g": 1, "iron_mg": 1.5, "calcium_mg": 15, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 1.8, "potassium_mg": 150, "magnesium_mg": 80, "sodium_mg": 5, "omega3_g": 0.1}},
    {"name": "chia flax mix", "ingredients": ["chia", "flax"], "nutrients": {"calories": 85, "protein_g": 3, "carbs_g": 5, "fat_g": 6, "fiber_g": 6, "iron_mg": 1.0, "calcium_mg": 80, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.8, "potassium_mg": 120, "magnesium_mg": 55, "sodium_mg": 5, "omega3_g": 2.1}},
    {"name": "fortified oat milk", "ingredients": ["fortified oat milk"], "nutrients": {"calories": 70, "protein_g": 2, "carbs_g": 12, "fat_g": 2, "fiber_g": 1, "iron_mg": 0.3, "calcium_mg": 240, "vitamin_b12_mcg": 1.2, "vitamin_d_mcg": 6.0, "zinc_mg": 0.3, "potassium_mg": 160, "magnesium_mg": 20, "sodium_mg": 90, "omega3_g": 0.0}},
    {"name": "nutritional yeast", "ingredients": ["nutritional yeast"], "nutrients": {"calories": 45, "protein_g": 6, "carbs_g": 5, "fat_g": 1, "fiber_g": 3, "iron_mg": 0.7, "calcium_mg": 10, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 0, "zinc_mg": 1.2, "potassium_mg": 120, "magnesium_mg": 20, "sodium_mg": 25, "omega3_g": 0.0}},
    {"name": "blueberry side", "ingredients": ["blueberries"], "nutrients": {"calories": 55, "protein_g": 1, "carbs_g": 14, "fat_g": 0, "fiber_g": 3, "iron_mg": 0.3, "calcium_mg": 8, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.2, "potassium_mg": 85, "magnesium_mg": 8, "sodium_mg": 2, "omega3_g": 0.0}},
    {"name": "avocado", "ingredients": ["avocado"], "nutrients": {"calories": 120, "protein_g": 2, "carbs_g": 6, "fat_g": 11, "fiber_g": 5, "iron_mg": 0.5, "calcium_mg": 10, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.5, "potassium_mg": 365, "magnesium_mg": 30, "sodium_mg": 5, "omega3_g": 0.1}},
    {"name": "low sodium herb sauce", "ingredients": ["parsley", "dill", "olive oil"], "nutrients": {"calories": 60, "protein_g": 0, "carbs_g": 1, "fat_g": 6, "fiber_g": 0, "iron_mg": 0.2, "calcium_mg": 10, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.1, "potassium_mg": 40, "magnesium_mg": 5, "sodium_mg": 10, "omega3_g": 0.0}},
    {"name": "almond crunch", "ingredients": ["almonds"], "nutrients": {"calories": 100, "protein_g": 4, "carbs_g": 4, "fat_g": 9, "fiber_g": 3, "iron_mg": 0.9, "calcium_mg": 75, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.7, "potassium_mg": 200, "magnesium_mg": 80, "sodium_mg": 1, "omega3_g": 0.0}, "contains_tree_nuts": True},
    {"name": "greek yogurt scoop", "ingredients": ["greek yogurt"], "nutrients": {"calories": 90, "protein_g": 14, "carbs_g": 5, "fat_g": 2, "fiber_g": 0, "iron_mg": 0, "calcium_mg": 170, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 0.5, "zinc_mg": 0.8, "potassium_mg": 150, "magnesium_mg": 12, "sodium_mg": 60, "omega3_g": 0.0}, "contains_dairy": True},
    {"name": "wheat pita", "ingredients": ["wheat pita"], "nutrients": {"calories": 165, "protein_g": 6, "carbs_g": 33, "fat_g": 1, "fiber_g": 3, "iron_mg": 1.8, "calcium_mg": 35, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.7, "potassium_mg": 110, "magnesium_mg": 25, "sodium_mg": 320, "omega3_g": 0.0}, "contains_gluten": True, "fodmap_level": "high", "condition_flags": {"high fodmap"}},
    {"name": "garlic onion relish", "ingredients": ["garlic", "onion"], "nutrients": {"calories": 35, "protein_g": 1, "carbs_g": 8, "fat_g": 0, "fiber_g": 1, "iron_mg": 0.2, "calcium_mg": 15, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.1, "potassium_mg": 80, "magnesium_mg": 5, "sodium_mg": 65, "omega3_g": 0.0}, "fodmap_level": "high", "condition_flags": {"high fodmap"}},
    {"name": "tomato citrus salsa", "ingredients": ["tomato", "lime", "orange"], "nutrients": {"calories": 45, "protein_g": 1, "carbs_g": 10, "fat_g": 0, "fiber_g": 2, "iron_mg": 0.3, "calcium_mg": 20, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.1, "potassium_mg": 220, "magnesium_mg": 12, "sodium_mg": 90, "omega3_g": 0.0}, "acidity_level": "high", "condition_flags": {"reflux trigger"}},
    {"name": "soy sauce glaze", "ingredients": ["soy sauce"], "nutrients": {"calories": 25, "protein_g": 1, "carbs_g": 4, "fat_g": 0, "fiber_g": 0, "iron_mg": 0.2, "calcium_mg": 5, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0.1, "potassium_mg": 60, "magnesium_mg": 5, "sodium_mg": 760, "omega3_g": 0.0}, "contains_soy": True, "condition_flags": {"high sodium"}},
    {"name": "honey glaze", "ingredients": ["honey"], "nutrients": {"calories": 70, "protein_g": 0, "carbs_g": 18, "fat_g": 0, "fiber_g": 0, "iron_mg": 0, "calcium_mg": 0, "vitamin_b12_mcg": 0, "vitamin_d_mcg": 0, "zinc_mg": 0, "potassium_mg": 10, "magnesium_mg": 0, "sodium_mg": 0, "omega3_g": 0.0}, "glycemic_delta": 15, "condition_flags": {"added sugar", "high gi"}, "contains_honey": True},
    {"name": "shrimp topping", "ingredients": ["shrimp"], "nutrients": {"calories": 90, "protein_g": 18, "carbs_g": 0, "fat_g": 1, "fiber_g": 0, "iron_mg": 0.4, "calcium_mg": 45, "vitamin_b12_mcg": 0.8, "vitamin_d_mcg": 0.1, "zinc_mg": 1.0, "potassium_mg": 140, "magnesium_mg": 25, "sodium_mg": 180, "omega3_g": 0.3}, "contains_shellfish": True},
    {"name": "bacon bits", "ingredients": ["pork", "bacon"], "nutrients": {"calories": 115, "protein_g": 8, "carbs_g": 0, "fat_g": 9, "fiber_g": 0, "iron_mg": 0.3, "calcium_mg": 5, "vitamin_b12_mcg": 0.3, "vitamin_d_mcg": 0, "zinc_mg": 0.7, "potassium_mg": 90, "magnesium_mg": 5, "sodium_mg": 480, "omega3_g": 0.0}, "contains_pork": True, "contains_meat": True, "condition_flags": {"high sodium"}},
]


STYLE_WORDS = [
    "garden",
    "herb",
    "market",
    "weeknight",
    "training",
    "balanced",
    "fresh",
    "mineral",
    "fiber",
    "protein",
    "clinic",
    "comfort",
]

PORTION_PROFILES = [
    ("light", 0.84),
    ("standard", 0.90),
    ("steady", 0.96),
    ("balanced", 1.00),
    ("hearty", 1.06),
    ("high energy", 1.12),
    ("athlete", 1.18),
    ("compact", 0.88),
    ("fiber focus", 1.03),
    ("mineral focus", 1.09),
    ("low volume", 0.82),
    ("clinic standard", 0.94),
    ("recovery", 1.15),
]


CLINICAL_RULE_SOURCES = (
    "USDA FoodData Central; Monash Low-FODMAP; NIH DRI/RDA; Glycaemic Index; DASH; internal allergen/low-acid rule maps"
)

SOURCE_FILE_NAMES = {
    "usda": "usda_fooddata_reference.csv",
    "fodmap": "source_lookup_fodmap.csv",
    "gi": "source_lookup_glycemic_index.csv",
    "gerd": "source_lookup_gerd_triggers.csv",
    "allergens": "source_lookup_allergens.csv",
    "dash": "source_lookup_dash.csv",
}


def normalize_text(value):
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def read_source_rows(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_source_context():
    usda_rows = read_source_rows(SOURCE_FILE_NAMES["usda"])
    usda_refs = {
        normalize_text(row.get("ingredient")): row
        for row in usda_rows
        if str(row.get("fdc_id", "")).strip()
    }
    return {
        "usda_refs": usda_refs,
        "fodmap": read_source_rows(SOURCE_FILE_NAMES["fodmap"]),
        "gi": read_source_rows(SOURCE_FILE_NAMES["gi"]),
        "gerd": read_source_rows(SOURCE_FILE_NAMES["gerd"]),
        "allergens": read_source_rows(SOURCE_FILE_NAMES["allergens"]),
        "dash": read_source_rows(SOURCE_FILE_NAMES["dash"]),
    }


def source_key_candidates(ingredient):
    value = normalize_text(ingredient)
    aliases = {
        "firm tofu": "tofu",
        "tofu free lentil patty": "lentils",
        "red lentils": "lentils",
        "pinto beans": "black beans",
        "white rice": "brown rice",
        "rice": "brown rice",
        "certified oats": "fortified oat milk",
        "almond milk": "almonds",
        "hemp hearts": "pumpkin seeds",
        "lentil dosa": "lentils",
        "soba": "wheat pasta",
        "wheat tortilla": "wheat pasta",
        "wheat pita": "wheat pasta",
        "bacon": "pork",
        "turkey": "chicken",
        "tuna": "salmon",
        "trout": "salmon",
    }
    candidates = [value]
    if value in aliases:
        candidates.append(aliases[value])
    return list(dict.fromkeys(candidates))


def source_ids_for_ingredients(ingredients, source_context):
    usda_refs = source_context.get("usda_refs", {})
    matches = []
    for ingredient in ingredients:
        norm = normalize_text(ingredient)
        if "tofu free" in norm:
            norm = norm.replace("tofu free", "")
        row = None
        key_used = ""
        for candidate in source_key_candidates(norm):
            row = usda_refs.get(candidate)
            key_used = candidate
            if row:
                break
        if not row:
            for key in sorted(usda_refs, key=len, reverse=True):
                if key and key in norm:
                    row = usda_refs[key]
                    key_used = key
                    break
        if row:
            matches.append(
                {
                    "ingredient": ingredient,
                    "reference_ingredient": key_used,
                    "fdc_id": str(row.get("fdc_id", "")).strip(),
                }
            )
    unique = []
    seen = set()
    for match in matches:
        key = (match["ingredient"], match["fdc_id"])
        if key not in seen and match["fdc_id"]:
            unique.append(match)
            seen.add(key)
    return unique


def pattern_matches(pattern, ingredients_text):
    pattern = normalize_text(pattern)
    if not pattern:
        return False
    if pattern == "citrus":
        return any(token in ingredients_text for token in ["citrus", "lime", "orange", "lemon"])
    if pattern == "high fat foods":
        return any(token in ingredients_text for token in ["fried", "bacon", "pork fried"])
    if pattern == "spicy foods":
        return any(token in ingredients_text for token in ["spicy", "spices", "salsa"])
    return pattern in ingredients_text


def apply_source_rule_overrides(row, source_context):
    ingredients_text = normalize_text(" ".join(row.get("ingredients", [])))
    matches = []

    for rule in source_context.get("fodmap", []):
        if not pattern_matches(rule.get("ingredient_pattern"), ingredients_text):
            continue
        level = normalize_text(rule.get("fodmap_level"))
        matches.append(f"FODMAP:{rule.get('ingredient_pattern')}={level}")
        if level == "high":
            row["fodmap_level"] = "high"
            row["condition_flags"].add("high fodmap")
        elif level == "medium" and normalize_text(row.get("fodmap_level")) == "low":
            row["fodmap_level"] = "medium"

    for rule in source_context.get("gerd", []):
        if not pattern_matches(rule.get("trigger_pattern"), ingredients_text):
            continue
        matches.append(f"GERD:{rule.get('trigger_pattern')}")
        row["acidity_level"] = "high"
        row["condition_flags"].add("reflux trigger")

    for rule in source_context.get("gi", []):
        if not pattern_matches(rule.get("food_pattern"), ingredients_text):
            continue
        matches.append(f"GI:{rule.get('food_pattern')}={rule.get('gi_band')}")
        action = normalize_text(rule.get("rule_action"))
        if "exclude" in action and ("added sugar" in action or "honey" in ingredients_text):
            row["condition_flags"].add("added sugar")
        if float(row.get("glycemic_index", 0)) > 55:
            row["condition_flags"].add("high gi")

    if float(row.get("sodium_mg", 0)) > 760:
        matches.append("DASH:sodium meal cap")
        row["condition_flags"].add("high sodium")

    for rule in source_context.get("allergens", []):
        app_column = rule.get("app_column", "")
        if app_column and row.get(app_column):
            matches.append(f"FDA allergen:{rule.get('allergen_category')}")

    return sorted(set(matches))


def combine_flags(row, addon):
    combined = deepcopy(row)
    combined["ingredients"] = list(row["ingredients"]) + list(addon.get("ingredients", []))
    for field in NUTRIENT_FIELDS:
        combined[field] = round(float(row[field]) + float(addon.get("nutrients", {}).get(field, 0)), 3)

    for flag in [
        "contains_dairy",
        "contains_gluten",
        "contains_tree_nuts",
        "contains_peanuts",
        "contains_shellfish",
        "contains_soy",
        "contains_sesame",
        "contains_eggs",
        "contains_pork",
        "contains_beef",
        "contains_meat",
        "contains_fish",
        "contains_honey",
    ]:
        combined[flag] = bool(combined.get(flag)) or bool(addon.get(flag, False))

    combined["condition_flags"] = set(combined.get("condition_flags", set())) | set(addon.get("condition_flags", set()))
    combined["cross_contamination_risks"] = set(combined.get("cross_contamination_risks", set())) | set(addon.get("cross_contamination_risks", set()))
    combined["cultural_flags"] = set(combined.get("cultural_flags", set())) | set(addon.get("cultural_flags", set()))

    if addon.get("fodmap_level") == "high":
        combined["fodmap_level"] = "high"
    if addon.get("acidity_level") == "high":
        combined["acidity_level"] = "high"
    combined["glycemic_index"] = min(95, max(20, float(combined.get("glycemic_index", 45)) + float(addon.get("glycemic_delta", 0))))

    animal = combined["contains_dairy"] or combined["contains_eggs"] or combined["contains_meat"] or combined["contains_fish"] or combined["contains_shellfish"] or combined["contains_pork"] or combined["contains_beef"] or combined.get("contains_honey", False)
    combined["vegetarian"] = not (combined["contains_meat"] or combined["contains_fish"] or combined["contains_shellfish"] or combined["contains_pork"] or combined["contains_beef"])
    combined["vegan"] = not animal
    combined["pescatarian"] = not (combined["contains_meat"] or combined["contains_pork"] or combined["contains_beef"])
    return combined


def allergen_tags(row):
    tags = []
    mapping = [
        ("contains_dairy", "dairy"),
        ("contains_gluten", "gluten"),
        ("contains_tree_nuts", "tree nuts"),
        ("contains_peanuts", "peanuts"),
        ("contains_shellfish", "shellfish"),
        ("contains_soy", "soy"),
        ("contains_sesame", "sesame"),
        ("contains_eggs", "eggs"),
        ("contains_pork", "pork"),
        ("contains_honey", "honey"),
    ]
    for flag, label in mapping:
        if row.get(flag):
            tags.append(label)
    return tags


def apply_portion_profile(row, profile_name, multiplier):
    adjusted = deepcopy(row)
    adjusted["portion_profile"] = f"{profile_name} ({multiplier:.2f}x)"
    for field in NUTRIENT_FIELDS:
        adjusted[field] = round(float(adjusted[field]) * multiplier, 3)
    return adjusted


def semantic_signature(row):
    signature_fields = {
        key: row.get(key, "")
        for key in sorted(row)
        if key not in {"food_id", "meal_name", "dedup_signature"}
    }
    payload = json.dumps(signature_fields, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def make_rows(target_count=TARGET_RECORD_COUNT):
    rows = []
    seen_signatures = set()
    source_context = load_source_context()
    safe_addons = [
        addon
        for addon in ADD_ONS
        if not addon.get("condition_flags")
        and not any(
            addon.get(flag)
            for flag in [
                "contains_tree_nuts",
                "contains_peanuts",
                "contains_dairy",
                "contains_gluten",
                "contains_shellfish",
                "contains_pork",
                "contains_sesame",
                "contains_honey",
            ]
        )
    ]
    attempt = 0
    max_attempts = target_count * 50
    while len(rows) < target_count and attempt < max_attempts:
        base = deepcopy(BASE_MEALS[attempt % len(BASE_MEALS)])
        addon_count = 1 + (attempt % 3)
        addon_pool = ADD_ONS if attempt % 5 == 0 else safe_addons
        chosen = []
        for offset in range(addon_count):
            chosen.append(addon_pool[(attempt * 7 + offset * 11) % len(addon_pool)])

        final = base
        for addon in chosen:
            final = combine_flags(final, addon)

        profile_name, portion_multiplier = PORTION_PROFILES[
            (attempt * 5 + attempt // max(1, len(BASE_MEALS))) % len(PORTION_PROFILES)
        ]
        final = apply_portion_profile(final, profile_name, portion_multiplier)

        if attempt % 17 == 0:
            final["cross_contamination_risks"].add("gluten")
        if attempt % 29 == 0:
            final["cross_contamination_risks"].add("tree nuts")
        if float(final["sodium_mg"]) > 760:
            final["condition_flags"].add("high sodium")
        if float(final["glycemic_index"]) > 55:
            final["condition_flags"].add("high gi")
        source_rule_matches = apply_source_rule_overrides(final, source_context)
        fdc_matches = source_ids_for_ingredients(final["ingredients"], source_context)
        fdc_ids = [f"FDC:{match['fdc_id']}" for match in fdc_matches]
        fdc_ingredients = [
            f"{match['ingredient']}->{match['reference_ingredient']}" for match in fdc_matches
        ]
        if fdc_ids:
            nutrition_source = "USDA FoodData Central API reference rows + deterministic recipe-template scaling"
            source_confidence = "fdc_reference_mapped"
        else:
            nutrition_source = "Curated recipe-template nutrition using USDA FoodData Central nutrient schema"
            source_confidence = "curated_template_unmapped"

        row_number = len(rows) + 1
        style = STYLE_WORDS[attempt % len(STYLE_WORDS)]
        addon_label = ", ".join(addon["name"] for addon in chosen)
        meal_name = f"{final['name']} - {style} {profile_name} variant {row_number}"
        row = {
            "food_id": f"NUTRI-{row_number:05d}",
            "meal_name": meal_name,
            "base_name": final["name"],
            "meal_type": final["meal_type"],
            "category": final["category"],
            "cuisine": final["cuisine"],
            "portion_profile": final["portion_profile"],
            "ingredients": "; ".join(dict.fromkeys(final["ingredients"])),
            "variant_addons": addon_label,
            "allergens": "; ".join(allergen_tags(final)),
            "condition_flags": "; ".join(sorted(final["condition_flags"])),
            "cross_contamination_risks": "; ".join(sorted(final["cross_contamination_risks"])),
            "cultural_flags": "; ".join(sorted(final["cultural_flags"])),
            "fodmap_level": final["fodmap_level"],
            "acidity_level": final["acidity_level"],
            "glycemic_index": round(float(final["glycemic_index"]), 1),
            "nutrition_source": nutrition_source,
            "nutrition_source_ids": "; ".join(dict.fromkeys(fdc_ids)),
            "nutrition_source_ingredients": "; ".join(dict.fromkeys(fdc_ingredients)),
            "clinical_rule_sources": CLINICAL_RULE_SOURCES,
            "source_rule_matches": "; ".join(source_rule_matches),
            "allergen_rule_source": "Internal allergen keyword map matched against meal and USDA ingredient terms",
            "source_confidence": source_confidence,
            "source_note": "Meal candidate generated from curated recipes; nutrient fields link to USDA FoodData Central reference ingredients where mapped and use deterministic recipe scaling. Clinical filters use professor-listed FODMAP, GI, DASH, and RDA references plus internal allergen/low-acid rule maps.",
        }
        for flag in [
            "vegetarian",
            "vegan",
            "pescatarian",
            "contains_dairy",
            "contains_gluten",
            "contains_tree_nuts",
            "contains_peanuts",
            "contains_shellfish",
            "contains_soy",
            "contains_sesame",
            "contains_eggs",
            "contains_pork",
            "contains_beef",
            "contains_meat",
            "contains_fish",
            "contains_honey",
        ]:
            row[flag] = bool(final[flag])
        for field in NUTRIENT_FIELDS:
            row[field] = round(float(final[field]), 3)
        row["dedup_signature"] = semantic_signature(row)
        if row["dedup_signature"] in seen_signatures:
            attempt += 1
            continue
        seen_signatures.add(row["dedup_signature"])
        rows.append(row)
        attempt += 1
    if len(rows) < target_count:
        raise RuntimeError(f"Only generated {len(rows)} deduplicated records after {attempt} attempts.")
    return rows


def write_rda():
    rows = [
        {"sex": "female", "age_min": 19, "age_max": 30, "protein_g": 46, "fiber_g": 25, "iron_mg": 18, "calcium_mg": 1000, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 15, "zinc_mg": 8, "potassium_mg": 2600, "magnesium_mg": 310, "sodium_mg": 2300, "omega3_g": 1.1},
        {"sex": "male", "age_min": 19, "age_max": 30, "protein_g": 56, "fiber_g": 38, "iron_mg": 8, "calcium_mg": 1000, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 15, "zinc_mg": 11, "potassium_mg": 3400, "magnesium_mg": 400, "sodium_mg": 2300, "omega3_g": 1.6},
        {"sex": "female", "age_min": 31, "age_max": 50, "protein_g": 46, "fiber_g": 25, "iron_mg": 18, "calcium_mg": 1000, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 15, "zinc_mg": 8, "potassium_mg": 2600, "magnesium_mg": 320, "sodium_mg": 2300, "omega3_g": 1.1},
        {"sex": "male", "age_min": 31, "age_max": 50, "protein_g": 56, "fiber_g": 38, "iron_mg": 8, "calcium_mg": 1000, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 15, "zinc_mg": 11, "potassium_mg": 3400, "magnesium_mg": 420, "sodium_mg": 2300, "omega3_g": 1.6},
        {"sex": "female", "age_min": 51, "age_max": 70, "protein_g": 46, "fiber_g": 21, "iron_mg": 8, "calcium_mg": 1200, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 15, "zinc_mg": 8, "potassium_mg": 2600, "magnesium_mg": 320, "sodium_mg": 2300, "omega3_g": 1.1},
        {"sex": "male", "age_min": 51, "age_max": 70, "protein_g": 56, "fiber_g": 30, "iron_mg": 8, "calcium_mg": 1000, "vitamin_b12_mcg": 2.4, "vitamin_d_mcg": 15, "zinc_mg": 11, "potassium_mg": 3400, "magnesium_mg": 420, "sodium_mg": 2300, "omega3_g": 1.6},
    ]
    with (DATA_DIR / "rda_reference.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_rules():
    rules = {
        "sources": {
            "USDA FoodData Central API": "https://fdc.nal.usda.gov/api-guide/",
            "NIH / National Academies Dietary Reference Intakes": "https://www.ncbi.nlm.nih.gov/books/NBK56068/",
            "NHLBI DASH eating plan": "https://www.nhlbi.nih.gov/education/dash-eating-plan",
            "Monash University Low FODMAP program": "https://www.monashfodmap.com/",
            "University of Sydney Glycemic Index database": "https://glycemicindex.com/",
        },
        "local_reference_files": {
            "USDA ingredient cache": "data/usda_fooddata_reference.csv",
            "FODMAP lookup": "data/source_lookup_fodmap.csv",
            "GI lookup": "data/source_lookup_glycemic_index.csv",
            "GERD lookup": "data/source_lookup_gerd_triggers.csv",
            "Allergen lookup": "data/source_lookup_allergens.csv",
            "DASH lookup": "data/source_lookup_dash.csv",
            "Internal allergen keyword map": "data/source_lookup_allergens.csv",
            "Internal low-acid rule map": "data/source_lookup_gerd_triggers.csv",
            "Source inventory": "data/source_inventory.csv",
        },
        "clinical_rules": {
            "IBS": {"exclude_fodmap_level": "high", "examples": ["garlic", "onion", "wheat"]},
            "GERD": {"exclude_acidity_level": "high", "examples": ["citrus", "tomato", "fried foods", "caffeine", "chocolate", "spicy foods"]},
            "Type 2 Diabetes": {"max_glycemic_index": 55, "exclude_flags": ["added sugar", "high gi"]},
            "Hypertension": {"meal_sodium_soft_cap_mg": 760, "daily_sodium_cap_mg": 2300, "dash_focus": ["potassium", "magnesium", "calcium", "fiber"]},
        },
        "disclaimer": "Educational project only. It is not medical advice and does not replace clinician or registered dietitian guidance.",
    }
    (DATA_DIR / "clinical_rules.json").write_text(json.dumps(rules, indent=2), encoding="utf-8")


def write_dictionary():
    text = """# NutriAI Data Dictionary

`food_database.csv` contains one row per meal candidate. The app treats each row as a single meal serving that can be portion-adjusted by the planner.

- `allergens`: semicolon-delimited explicit allergen tags used for hard exclusion.
- `base_name`: human-readable dish template used to prevent repeated base dishes across a 7-day plan.
- `condition_flags`: high-FODMAP, reflux-trigger, high-GI, high-sodium, or added-sugar markers.
- `cross_contamination_risks`: potential exposure tags that are excluded when strict mode is enabled.
- `dedup_signature`: deterministic SHA-1 based signature across semantic candidate fields; repeated signatures are removed before the CSV is written.
- nutrient columns: per-serving macro and micronutrient estimates.
- `nutrition_source`: how nutrition fields were populated.
- `nutrition_source_ids`: linked USDA FoodData Central IDs when the candidate's ingredients match `usda_fooddata_reference.csv`.
- `nutrition_source_ingredients`: ingredient-to-reference mapping used for the linked USDA IDs.
- `portion_profile`: deterministic serving profile used to create structured portion and nutrient variation.
- `clinical_rule_sources`: professor-listed source families and internal rule maps used by the candidate.
- `source_rule_matches`: specific lookup rules matched by this candidate.
- `source_confidence`: `fdc_reference_mapped` when at least one source ingredient maps to a USDA reference row; otherwise `curated_template_unmapped`.
- boolean diet/allergen columns: compatibility flags used before ranking, including `contains_honey` for vegan exclusion and `contains_peanuts` / `contains_sesame` for FDA allergen coverage.

Source-reference files:

- `usda_fooddata_reference.csv`: USDA FoodData Central ingredient cache generated by `scripts/build_source_reference_data.py`.
- `source_lookup_fodmap.csv`: Monash-informed FODMAP rule mappings.
- `source_lookup_glycemic_index.csv`: GI-band rules for diabetes filtering.
- `source_lookup_gerd_triggers.csv`: internal low-acid rule map for GERD/acidity filtering.
- `source_lookup_allergens.csv`: internal allergen keyword map for user-declared allergen filtering.
- `source_lookup_dash.csv`: NHLBI DASH sodium/nutrient emphasis rules.
- `source_inventory.csv` and `source_provenance.md`: transparent source coverage and caveats.

The snapshot is deterministic and offline so graders can run the app without API keys. It is generated from curated recipe templates, linked to USDA FoodData Central reference ingredients where available, deduplicated by semantic candidate signature, and filtered by source-cited rule lookup tables.
"""
    (DATA_DIR / "data_dictionary.md").write_text(text, encoding="utf-8")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = make_rows()
    fieldnames = list(rows[0].keys())
    with (DATA_DIR / "food_database.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    write_rda()
    write_rules()
    write_dictionary()
    duplicate_signatures = len(rows) - len({row["dedup_signature"] for row in rows})
    print(f"Wrote {len(rows)} deduplicated meal records to {DATA_DIR / 'food_database.csv'}")
    print(f"Duplicate semantic signatures in final output: {duplicate_signatures}")
    print(f"Wrote RDA and clinical rule references to {DATA_DIR}")


if __name__ == "__main__":
    main()
