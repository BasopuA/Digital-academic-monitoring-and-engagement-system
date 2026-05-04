# app/services/seed_service.py

import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User





class SeedService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_first_user(self):
        """Seed only the first default user if none exists"""
        try:
            # Check if any user already exists
            result = await self.db.execute(select(User))
            user_exists = result.first() is not None

            if user_exists:
                return

            # Create default user
            user = User(
                username="basopu@gmail.com",
                password="1234",
            )

            self.db.add(user)
            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise