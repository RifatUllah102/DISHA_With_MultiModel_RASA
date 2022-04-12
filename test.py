from aiohttp import web


async def call_answer(request):
    params = request.rel_url.query
    return web.Response(text='\n'.join([
        'call_id = ' + params['lang'],        
    ]))


app = web.Application()
app.router.add_get('/', call_answer)
web.run_app(app)