from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User, UserRole  # ← Import UserRole
from app.core.security import get_password_hash
from app.core.config import settings


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

            # Create default admin user with hashed password from settings
            hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            
            admin_user = User(
                username="admin",
                email="admin@edutrackersa.com",
                password_hash=hashed_password,
                is_active=True,
                role=UserRole.ADMIN  
            )
            
            self.db.add(admin_user)
            await self.db.commit()
            

        except Exception as e:
            await self.db.rollback()
            raise

