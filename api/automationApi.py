from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_database
from entity.VO.AutomationVO import (
    AnsibleEnvQuery,
    AnsibleEnvSave,
    DeviceProfileQuery,
    DeviceProfileSave,
    PlaybookQuery,
    PlaybookSave,
)
from schemas.response import Response
from service import automation_service


router = APIRouter(prefix="/automation", tags=["automation"])


@router.post("/playbook/list", response_model=Response)
async def list_playbooks(query: PlaybookQuery, db: AsyncSession = Depends(get_database)):
    return await automation_service.list_playbooks(query, db)


@router.get("/playbook/{playbook_id}", response_model=Response)
async def get_playbook(playbook_id: int, db: AsyncSession = Depends(get_database)):
    return await automation_service.get_playbook(playbook_id, db)


@router.post("/playbook/save", response_model=Response)
async def save_playbook(data: PlaybookSave, db: AsyncSession = Depends(get_database)):
    return await automation_service.save_playbook(data, db)


@router.delete("/playbook/{playbook_id}", response_model=Response)
async def delete_playbook(playbook_id: int, db: AsyncSession = Depends(get_database)):
    return await automation_service.delete_playbook(playbook_id, db)


@router.post("/env/list", response_model=Response)
async def list_ansible_envs(query: AnsibleEnvQuery, db: AsyncSession = Depends(get_database)):
    return await automation_service.list_ansible_envs(query, db)


@router.get("/env/{env_id}", response_model=Response)
async def get_ansible_env(env_id: int, db: AsyncSession = Depends(get_database)):
    return await automation_service.get_ansible_env(env_id, db)


@router.post("/env/save", response_model=Response)
async def save_ansible_env(data: AnsibleEnvSave, db: AsyncSession = Depends(get_database)):
    return await automation_service.save_ansible_env(data, db)


@router.delete("/env/{env_id}", response_model=Response)
async def delete_ansible_env(env_id: int, db: AsyncSession = Depends(get_database)):
    return await automation_service.delete_ansible_env(env_id, db)


@router.post("/profile/list", response_model=Response)
async def list_device_profiles(query: DeviceProfileQuery, db: AsyncSession = Depends(get_database)):
    return await automation_service.list_device_profiles(query, db)


@router.get("/profile/{profile_id}", response_model=Response)
async def get_device_profile(profile_id: int, db: AsyncSession = Depends(get_database)):
    return await automation_service.get_device_profile(profile_id, db)


@router.post("/profile/save", response_model=Response)
async def save_device_profile(data: DeviceProfileSave, db: AsyncSession = Depends(get_database)):
    return await automation_service.save_device_profile(data, db)


@router.delete("/profile/{profile_id}", response_model=Response)
async def delete_device_profile(profile_id: int, db: AsyncSession = Depends(get_database)):
    return await automation_service.delete_device_profile(profile_id, db)
