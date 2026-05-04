# app/services/seed_service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
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
                print("Users already exist, skipping seed")
                return

            # Create default admin user with hashed password from settings
            hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            
            admin_user = User(
                username="admin",
                email="admin@edutrackersa.com",
                password_hash=hashed_password,  # ✅ Now using hashed password
                is_active=True,
                is_admin=True  # ✅ Make sure this is True
            )
            
            self.db.add(admin_user)
            await self.db.commit()
            
            print(f"✅ Admin user created successfully!")
            print(f"   Username: admin")
            print(f"   Password: {settings.ADMIN_PASSWORD}")
            print(f"   Email: admin@edutrackersa.com")
            print(f"   Admin privileges: True")

        except Exception as e:
            await self.db.rollback()
            print(f"❌ Error seeding admin user: {e}")
            raise