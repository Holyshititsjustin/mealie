from fastapi import APIRouter

from . import meal_randomizer

router = APIRouter()

router.include_router(meal_randomizer.router)
