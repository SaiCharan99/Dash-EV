from fastapi import APIRouter
from api.cache import is_ready

router = APIRouter(tags=['health'])


@router.get('/health')
def ping():
    return {'status': 'ok', 'data_loaded': is_ready()}
