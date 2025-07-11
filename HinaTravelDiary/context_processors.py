from journeys.models import Country


def global_context(request):
    """
    全域 context processor，為所有頁面提供常用資料
    """
    return {
        'highlighted_countries': Country.objects.filter(is_highlighted=True).order_by('name'),
    }