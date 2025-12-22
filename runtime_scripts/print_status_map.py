import asyncio
import json

async def main():
    try:
        from agent.consumers import MonitorConsumer
    except Exception as e:
        print('IMPORT_ERR', e)
        return
    # Construct a consumer-like object
    c = MonitorConsumer(scope={'user': type('U',(),{'is_anonymous':False})})
    res = await c._fetch_status_map()
    print(json.dumps(res, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
