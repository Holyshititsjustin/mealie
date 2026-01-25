from functools import cached_property

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

from mealie.routes._base.base_controllers import BaseCrudController
from mealie.routes._base.controller import controller
from mealie.routes._base.mixins import HttpRepo
from mealie.schema.household.pantry import (
    IngredientCatalogItemCreate,
    IngredientCatalogItemOut,
    IngredientCatalogItemUpdate,
    PantryItemCreate,
    PantryItemEventOut,
    PantryItemEventPagination,
    PantryItemOut,
    PantryItemPagination,
    PantryItemUpdate,
)
from mealie.schema.response.pagination import PaginationQuery
from mealie.schema.response.responses import SuccessResponse
from mealie.services.household_services.pantry import PantryService

pantry_router = APIRouter(prefix="/households/pantry", tags=["Households: Pantry"])


@controller(pantry_router)
class PantryItemController(BaseCrudController):
    @cached_property
    def service(self) -> PantryService:
        return PantryService(self.repos)

    @cached_property
    def repo(self):
        return self.repos.pantry_items

    @cached_property
    def mixins(self):
        return HttpRepo[PantryItemCreate, PantryItemOut, PantryItemCreate](
            self.repo,
            self.logger,
        )

    # =======================================================================
    # CRUD Operations

    @pantry_router.get("/items", response_model=PantryItemPagination)
    def get_all_items(self, q: PaginationQuery = Depends()):
        response = self.repo.page_all(pagination=q, override=PantryItemOut)
        response.set_pagination_guides(pantry_router.url_path_for("get_all_items"), q.model_dump())
        return response

    @pantry_router.post("/items", response_model=PantryItemOut, status_code=201)
    def create_item(self, data: PantryItemCreate):
        return self.service.create_item(data)

    @pantry_router.get("/items/{item_id}", response_model=PantryItemOut)
    def get_one_item(self, item_id: UUID4):
        return self.mixins.get_one(item_id)

    @pantry_router.put("/items/{item_id}", response_model=PantryItemOut)
    def update_item(self, item_id: UUID4, data: PantryItemUpdate):
        return self.service.update_item(item_id, data)

    @pantry_router.delete("/items/{item_id}", response_model=SuccessResponse)
    def delete_item(self, item_id: UUID4):
        self.service.delete_item(item_id)
        return SuccessResponse.respond()

    # =======================================================================
    # Item Actions

    @pantry_router.post("/items/{item_id}/decrement", response_model=PantryItemOut)
    def decrement_item(self, item_id: UUID4, amount: float = Query(1)):
        return self.service.decrement_quantity(item_id, amount)

    @pantry_router.post("/items/{item_id}/consume", response_model=PantryItemOut)
    def consume_item(self, item_id: UUID4):
        return self.service.mark_consumed(item_id)

    @pantry_router.post("/items/{item_id}/discard", response_model=PantryItemOut)
    def discard_item(self, item_id: UUID4):
        return self.service.mark_discarded(item_id)

    # =======================================================================
    # Expiring/Expired Queries

    @pantry_router.get("/expiring", response_model=PantryItemPagination)
    def get_expiring_items(self, window_days: int | None = Query(None)):
        items = self.service.get_expiring_items(override_window_days=window_days)
        return PantryItemPagination(items=items)

    @pantry_router.get("/expired", response_model=PantryItemPagination)
    def get_expired_items(self, window_days: int | None = Query(None)):
        items = self.service.get_recently_expired_items(override_window_days=window_days)
        return PantryItemPagination(items=items)

    # =======================================================================
    # Item Events

    @pantry_router.get("/items/{item_id}/events", response_model=PantryItemEventPagination)
    def get_item_events(self, item_id: UUID4, q: PaginationQuery = Depends()):
        q.query_filter = f"pantry_item_id={item_id}"
        response = self.repos.pantry_item_events.page_all(pagination=q, override=PantryItemEventOut)
        response.set_pagination_guides(pantry_router.url_path_for("get_item_events"), q.model_dump())
        return response

    # =======================================================================
    # Ingredient Catalog

    @pantry_router.get("/catalog", response_model=list[IngredientCatalogItemOut])
    def get_catalog_items(self):
        items = self.repos.ingredient_catalog_items.page_all(
            PaginationQuery(per_page=-1)
        ).items
        return items

    @pantry_router.post("/catalog", response_model=IngredientCatalogItemOut, status_code=201)
    def create_catalog_item(self, data: IngredientCatalogItemCreate):
        return self.service.upsert_catalog_item(data)

    @pantry_router.get("/catalog/{catalog_id}", response_model=IngredientCatalogItemOut)
    def get_catalog_item(self, catalog_id: UUID4):
        return self.repos.ingredient_catalog_items.get_one(catalog_id)

    @pantry_router.put("/catalog/{catalog_id}", response_model=IngredientCatalogItemOut)
    def update_catalog_item(self, catalog_id: UUID4, data: IngredientCatalogItemUpdate):
        data.id = catalog_id
        return self.service.upsert_catalog_item(data)

    @pantry_router.delete("/catalog/{catalog_id}", response_model=SuccessResponse)
    def delete_catalog_item(self, catalog_id: UUID4):
        self.repos.ingredient_catalog_items.delete_one(catalog_id)
        return SuccessResponse.respond()
