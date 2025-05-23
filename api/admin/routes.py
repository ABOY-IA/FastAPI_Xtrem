from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, AsyncGenerator
from fastapi import Request

from api.db.session import SessionLocal
from api.db.models import User
from api.db.schemas import UserOut
from api.logger import logger

router = APIRouter()

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        request.state.db = session
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Erreur lors de la gestion de la session DB")
            raise
        finally:
            await session.close()

async def get_admin_user(
    x_user: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> User:
    result = await db.execute(select(User).where(User.username == x_user))
    user = result.scalars().first()
    if not user or user.role != "admin":
        logger.warning(f"Tentative d'accès admin refusée pour {x_user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin access required"
        )
    return user

@router.get("/users", response_model=List[UserOut])
async def list_all_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    logger.info(f"Admin {admin.username} a listé tous les utilisateurs ({len(users)} trouvés)")
    return [UserOut.model_validate(u) for u in users]

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        logger.warning(f"Tentative de suppression d'utilisateur inexistant (id={user_id}) par admin {admin.username}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()
    logger.info(f"Admin {admin.username} a supprimé l'utilisateur id={user_id}")
    return
