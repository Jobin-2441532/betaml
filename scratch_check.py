import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.transaction import Transaction

async def run():
    engine = create_async_engine('sqlite+aiosqlite:///financeai.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(Transaction).order_by(Transaction.id.desc()).limit(3))
        txs = result.scalars().all()
        for t in txs:
            print(f'{t.id}: is_refund={t.is_refund} tags:{t.tags}')

if __name__ == "__main__":
    asyncio.run(run())
