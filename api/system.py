from middleware import APIRouter, auth, EnvelopedJSONResponse


router = APIRouter(
    tags=['System'],
    route_class=auth.LoginRequiredRouter,
    default_response_class=EnvelopedJSONResponse,
)


@router.get('/access-log')
def get_access_logs(req: auth.AuthedRequest):
    """
    會做分頁功能，格式再說
    """
    # TODO
