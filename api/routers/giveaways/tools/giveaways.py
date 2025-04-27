from loguru import logger
from api.routers.giveaways.schemas import Giveaway
from database import db


class GiveawaysTools:
    async def get_all(
        page: int,
        per_page: int
    ) -> list[Giveaway]:
        return [
            Giveaway.model_validate(dict(giveaway))
            for giveaway in await db.giveaways.get_all(
                page=page,
                per_page=per_page
            )
        ]