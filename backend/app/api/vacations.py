from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_session
from app.models import Provider, VacationAllowance, VacationRequest
from app.schemas.common import VacationAllowanceRead, VacationRequestCreate, VacationRequestRead, VacationRequestUpdate

router = APIRouter()


def _get_session():
    with get_session() as session:
        yield session


@router.post("/requests", response_model=VacationRequestRead)
def create_vacation_request(payload: VacationRequestCreate, session=Depends(_get_session)) -> VacationRequest:
    provider = session.get(Provider, payload.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    vacation = VacationRequest(**payload.dict())
    session.add(vacation)
    session.commit()
    session.refresh(vacation)
    return vacation


@router.patch("/requests/{request_id}", response_model=VacationRequestRead)
def update_vacation_request(request_id: int, payload: VacationRequestUpdate, session=Depends(_get_session)) -> VacationRequest:
    vacation = session.get(VacationRequest, request_id)
    if not vacation:
        raise HTTPException(status_code=404, detail="Vacation request not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(vacation, key, value)

    session.add(vacation)
    session.commit()
    session.refresh(vacation)
    return vacation


@router.get("/allowances/{provider_id}/{year}", response_model=VacationAllowanceRead)
def get_allowance(provider_id: int, year: int, session=Depends(_get_session)) -> VacationAllowance:
    allowance = next(
        (
            allowance
            for allowance in session.all(VacationAllowance)
            if allowance.provider_id == provider_id and allowance.year == year
        ),
        None,
    )
    if not allowance:
        raise HTTPException(status_code=404, detail="Allowance not found")
    return allowance