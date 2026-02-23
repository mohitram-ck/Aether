from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.models.transaction import Transaction
from app.services.cache_service import (
    is_token_blacklisted,
    push_transaction_to_stream,
    get_stream_length
)
from typing import List
import uuid

router = APIRouter(prefix="/transactions", tags=["Transactions"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    txn = Transaction(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user["sub"]),
        amount=data.amount,
        currency=data.currency,
        merchant=data.merchant,
        location=data.location,
        status="pending",
        is_flagged=False
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    await push_transaction_to_stream({
        "transaction_id": str(txn.id),
        "user_id": str(txn.user_id),
        "amount": str(txn.amount),
        "currency": txn.currency,
        "merchant": txn.merchant,
        "location": txn.location or "",
        "status": txn.status
    })

    return txn


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == uuid.UUID(user["sub"])
        ).order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()


@router.get("/stream/length")
async def stream_length():
    length = await get_stream_length()
    return {"transactions_in_queue": length}


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == uuid.UUID(user["sub"])
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return txn