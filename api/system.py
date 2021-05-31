from middleware import APIRouter, auth, envelope


router = APIRouter(
    tags=['System'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/access-log')
def browse_access_logs(req: auth.Request):
    """
    會做分頁功能，格式再說
    """
    # TODO
