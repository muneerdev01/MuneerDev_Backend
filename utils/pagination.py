"""
Pagination Helpers
Support for page/limit/total pagination pattern
"""
from typing import Optional, List, Any
from dataclasses import dataclass
from sqlalchemy import func


@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    page_size: int = 10
    
    @property
    def offset(self) -> int:
        """Calculate offset for query"""
        return (self.page - 1) * self.page_size


@dataclass
class PaginationResult:
    """Pagination result structure"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages"""
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Check if there are more pages"""
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        """Check if there are previous pages"""
        return self.page > 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev
        }


async def paginate_query(
    session,
    query,
    pagination: PaginationParams
) -> PaginationResult:
    """
    Execute a paginated query.
    
    Args:
        session: Async database session
        query: SQLAlchemy select query
        pagination: PaginationParams instance
        
    Returns:
        PaginationResult with items and pagination metadata
    """
    # Get total count
    count_query = query.with_only_columns([func.count()]).order_by(None)
    result = await session.execute(count_query)
    total = result.scalar_one()
    
    # Get paginated results
    paginated_query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await session.execute(paginated_query)
    
    # Handle different result types
    if hasattr(result, 'scalars'):
        items = result.scalars().all()
    else:
        items = result.all()
    
    return PaginationResult(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


async def paginate_list(
    items: List[Any],
    pagination: PaginationParams
) -> PaginationResult:
    """
    Paginate an in-memory list.
    
    Args:
        items: List of items to paginate
        pagination: PaginationParams instance
        
    Returns:
        PaginationResult with paginated items
    """
    total = len(items)
    start = pagination.offset
    end = start + pagination.page_size
    paginated_items = items[start:end]
    
    return PaginationResult(
        items=paginated_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )
